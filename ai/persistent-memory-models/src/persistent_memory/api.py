"""FastAPI server for persistent memory system."""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from prometheus_client import make_asgi_app
from temporalio.client import Client

from persistent_memory.persistent_vector_store import PersistentVectorStore
from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph
from persistent_memory.ingestion_workflow import IngestBookWorkflow, IngestBookParams
from persistent_memory.metrics import query_total, query_duration, track_duration

app = FastAPI(
    title="Persistent Memory API",
    description="API for hierarchical persistent memory system",
    version="0.1.0"
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Models
class QueryRequest(BaseModel):
    query: str
    k: int = 5
    layers: Optional[List[str]] = None

class QueryResponse(BaseModel):
    results: List[dict]
    metadata: dict

class IngestRequest(BaseModel):
    file_path: str
    workflow_id: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    services: dict

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
    
    overall_status = "healthy" if all(
        "healthy" in s for s in services.values()
    ) else "degraded"
    
    return HealthResponse(status=overall_status, services=services)

@app.post("/query", response_model=QueryResponse)
@track_duration(query_duration.labels(layer="hybrid"))
async def query(request: QueryRequest):
    """Query the memory system."""
    query_total.labels(layer="hybrid").inc()
    
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
    
    return QueryResponse(
        results=results[:request.k],
        metadata={
            "total_results": len(results),
            "layers_queried": request.layers or ["vector", "graph"]
        }
    )

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
