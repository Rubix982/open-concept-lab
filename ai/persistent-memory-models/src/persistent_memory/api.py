"""FastAPI server for persistent memory system."""

import json

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from prometheus_client import make_asgi_app
from pydantic import BaseModel
from temporalio.client import Client

from persistent_memory.workflows.book_ingestion_workflow import IngestBookParams, IngestBookWorkflow
from persistent_memory.utils.metrics import query_duration, query_total, track_duration
from persistent_memory.core.persistent_context_engine import PersistentKnowledgeGraph, PersistentVectorStore
from persistent_memory.stores import QueryCache
from persistent_memory.processors.streaming_query import StreamingQueryEngine

app = FastAPI(
    title="Persistent Memory API",
    description="API for hierarchical persistent memory system",
    version="0.2.0",
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Initialize cache
query_cache = QueryCache()


@app.on_event("startup")
async def startup():
    """Initialize services on startup."""
    await query_cache.connect()


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    await query_cache.disconnect()


# Models
class QueryRequest(BaseModel):
    query: str
    k: int = 5
    layers: list[str] | None = None
    use_cache: bool = True


class QueryResponse(BaseModel):
    results: list[dict]
    metadata: dict


class IngestRequest(BaseModel):
    file_path: str
    workflow_id: str | None = None


class BatchIngestRequest(BaseModel):
    directory: str
    recursive: bool = True
    batch_size: int = 10


class HealthResponse(BaseModel):
    status: str
    services: dict


class CacheStatsResponse(BaseModel):
    hits: int
    misses: int
    hit_rate: float
    enabled: bool


# Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    services = {}

    # Check Vector Store
    try:
        _ = PersistentVectorStore()
        services["vector_store"] = "healthy"
    except Exception as e:
        services["vector_store"] = f"unhealthy: {str(e)}"

    # Check Knowledge Graph
    try:
        _ = PersistentKnowledgeGraph()
        services["knowledge_graph"] = "healthy"
    except Exception as e:
        services["knowledge_graph"] = f"unhealthy: {str(e)}"

    # Check Temporal
    try:
        _ = await Client.connect("temporal:7233")
        services["temporal"] = "healthy"
    except Exception as e:
        services["temporal"] = f"unhealthy: {str(e)}"

    # Check Cache
    services["cache"] = "healthy" if query_cache.client else "disabled"

    overall_status = (
        "healthy"
        if all("healthy" in s for s in services.values() if s != "disabled")
        else "degraded"
    )

    return HealthResponse(status=overall_status, services=services)


@app.post("/query", response_model=QueryResponse)
@track_duration(query_duration.labels(layer="hybrid"))
async def query(request: QueryRequest):
    """Query the memory system with optional caching."""
    query_total.labels(layer="hybrid").inc()

    # Try cache first if enabled
    if request.use_cache:
        cached = await query_cache.get(request.query, k=request.k)
        if cached:
            return QueryResponse(**cached)

    results = []

    # Query vector store
    if not request.layers or "vector" in request.layers:
        vector_results = PersistentVectorStore().search(request.query, k=request.k)
        results.extend([{**r, "source": "vector"} for r in vector_results])

    # Query knowledge graph
    if not request.layers or "graph" in request.layers:
        graph_results = PersistentKnowledgeGraph().query(request.query)
        # graph_results is a dict with 'nodes' and 'edges', not a list
        if graph_results.get("nodes"):
            results.append({"data": graph_results, "source": "graph"})

    response_metadata = {
        "total_results": len(results),
        "layers_queried": request.layers or ["vector", "graph"],
        "cached": False,
    }

    response_obj = QueryResponse(
        results=results[: request.k],
        metadata=response_metadata,
    )

    # Cache the result
    if request.use_cache:
        await query_cache.set(
            request.query,
            {"results": response_obj.results, "metadata": response_obj.metadata},
            k=request.k,
        )

    return response_obj


@app.get("/query/stream")
async def stream_query(query: str, k: int = 5):
    """Stream query results in real-time."""
    engine = StreamingQueryEngine()

    async def generate():
        async for chunk in engine.stream_query(query, k=k):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """Get cache statistics."""
    stats = query_cache.get_stats()
    return CacheStatsResponse(**stats)


@app.post("/cache/invalidate")
async def invalidate_cache(pattern: str = "*"):
    """Invalidate cached queries."""
    await query_cache.invalidate_pattern(pattern)
    return {"message": f"Invalidated cache for pattern: {pattern}"}


@app.post("/ingest")
async def ingest(request: IngestRequest, background_tasks: BackgroundTasks):
    """Start an ingestion workflow."""
    try:
        client = await Client.connect("temporal:7233")

        workflow_id = (
            request.workflow_id or f"ingest-{request.file_path.split('/')[-1]}"
        )

        handle = await client.start_workflow(
            IngestBookWorkflow.run,
            IngestBookParams(book_path=request.file_path),
            id=workflow_id,
            task_queue="ingestion-task-queue",
        )

        return {"workflow_id": workflow_id, "status": "started", "run_id": handle.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/batch")
async def batch_ingest(request: BatchIngestRequest):
    """Ingest multiple documents from a directory."""
    from persistent_memory.processors.batch_processor import BatchProcessor, DocumentScanner
    from persistent_memory.utils.cli import trigger_ingestion

    try:
        # Scan directory
        scanner = DocumentScanner()
        files = scanner.scan_directory(request.directory, recursive=request.recursive)

        if not files:
            raise HTTPException(status_code=404, detail="No documents found")

        # Start batch processing
        processor = BatchProcessor()

        async def process_file(file_path: str):
            return await trigger_ingestion(file_path)

        summary = await processor.process_documents(files, process_file)

        return {"message": "Batch ingestion complete", "summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of an ingestion workflow."""
    try:
        client = await Client.connect("temporal:7233")
        handle = client.get_workflow_handle(workflow_id)

        # Try to get result (will raise if still running)
        try:
            result = await handle.result()
            return {"workflow_id": workflow_id, "status": "completed", "result": result}
        except Exception:
            return {"workflow_id": workflow_id, "status": "running"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
