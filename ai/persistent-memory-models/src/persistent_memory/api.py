"""FastAPI server for persistent memory system."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json
from prometheus_client import make_asgi_app
from temporalio.client import Client

from persistent_memory.persistent_vector_store import PersistentVectorStore
from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph
from persistent_memory.ingestion_workflow import IngestBookWorkflow, IngestBookParams
from persistent_memory.metrics import query_total, query_duration, track_duration
from persistent_memory.streaming_query import StreamingQueryEngine
from persistent_memory.query_cache import QueryCache, CachedVectorStore

app = FastAPI(
    title="Persistent Memory API",
    description="API for hierarchical persistent memory system",
    version="0.2.0"
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
    layers: Optional[List[str]] = None
    use_cache: bool = True

class QueryResponse(BaseModel):
    results: List[dict]
    metadata: dict

class IngestRequest(BaseModel):
    file_path: str
    workflow_id: Optional[str] = None

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
        vs = PersistentVectorStore()
        services["vector_store"] = "healthy"
    except Exception as e:
        services["vector_store"] = f"unhealthy: {str(e)}"
    
    # Check Knowledge Graph
    try:
        kg = PersistentKnowledgeGraph()
        services["knowledge_graph"] = "healthy"
    except Exception as e:
        services["knowledge_graph"] = f"unhealthy: {str(e)}"
    
    # Check Temporal
    try:
        client = await Client.connect("temporal:7233")
        services["temporal"] = "healthy"
    except Exception as e:
        services["temporal"] = f"unhealthy: {str(e)}"
    
    # Check Cache
    services["cache"] = "healthy" if query_cache.client else "disabled"
    
    overall_status = "healthy" if all(
        "healthy" in s for s in services.values() if s != "disabled"
    ) else "degraded"
    
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
        vs = PersistentVectorStore()
        vector_results = vs.search(request.query, k=request.k)
        results.extend([{**r, "source": "vector"} for r in vector_results])
    
    # Query knowledge graph
    if not request.layers or "graph" in request.layers:
        kg = PersistentKnowledgeGraph()
        graph_results = kg.query(request.query)
        results.extend([{**r, "source": "graph"} for r in graph_results])
    
    response_data = {
        "results": results[:request.k],
        "metadata": {
            "total_results": len(results),
            "layers_queried": request.layers or ["vector", "graph"],
            "cached": False
        }
    }
    
    # Cache the result
    if request.use_cache:
        await query_cache.set(request.query, response_data, k=request.k)
    
    return QueryResponse(**response_data)

@app.get("/query/stream")
async def stream_query(query: str, k: int = 5):
    """Stream query results in real-time."""
    engine = StreamingQueryEngine()
    
    async def generate():
        async for chunk in engine.stream_query(query, k=k):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )

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
        
        workflow_id = request.workflow_id or f"ingest-{request.file_path.split('/')[-1]}"
        
        handle = await client.start_workflow(
            IngestBookWorkflow.run,
            IngestBookParams(book_path=request.file_path),
            id=workflow_id,
            task_queue="ingestion-task-queue"
        )
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "run_id": handle.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest/batch")
async def batch_ingest(request: BatchIngestRequest):
    """Ingest multiple documents from a directory."""
    from persistent_memory.batch_processor import DocumentScanner, BatchProcessor
    from persistent_memory.cli import trigger_ingestion
    
    try:
        # Scan directory
        scanner = DocumentScanner()
        files = scanner.scan_directory(
            request.directory,
            recursive=request.recursive
        )
        
        if not files:
            raise HTTPException(status_code=404, detail="No documents found")
        
        # Start batch processing
        processor = BatchProcessor()
        
        async def process_file(file_path: str):
            return await trigger_ingestion(file_path)
        
        summary = await processor.process_documents(files, process_file)
        
        return {
            "message": "Batch ingestion complete",
            "summary": summary
        }
        
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
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "result": result
            }
        except:
            return {
                "workflow_id": workflow_id,
                "status": "running"
            }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
