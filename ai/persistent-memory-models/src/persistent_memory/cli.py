import asyncio
import typer
import os
from temporalio.client import Client
from persistent_memory.ingestion_workflow import IngestBookWorkflow
from persistent_memory.activities import IngestBookParams
from persistent_memory.persistent_vector_store import PersistentVectorStore
from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph

app = typer.Typer()

@app.command()
def ingest(file_path: str):
    """
    Ingest a book or text file into persistent memory.
    """
    async def run_workflow():
        temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
        client = await Client.connect(temporal_host)
        
        print(f"Starting ingestion for {file_path}...")
        result = await client.execute_workflow(
            IngestBookWorkflow.run,
            IngestBookParams(book_path=file_path),
            id=f"ingest-{os.path.basename(file_path)}",
            task_queue="ingestion-task-queue",
        )
        print(f"Ingestion complete! Processed {result.total_chunks} chunks.")

    asyncio.run(run_workflow())

@app.command()
def query(text: str):
    """
    Query the persistent memory (Vector Store + Knowledge Graph).
    """
    print(f"Querying: {text}")
    
    # 1. Vector Search
    vector_store = PersistentVectorStore()
    vector_results = vector_store.search(text, k=3)
    
    print("\n--- Vector Search Results ---")
    for res in vector_results:
        print(f"[{res['distance']:.4f}] {res['text'][:100]}...")

    # 2. Graph Search (Simple entity lookup for MVP)
    # In a real system, we would extract entities from the query first
    kg = PersistentKnowledgeGraph()
    words = text.split()
    
    print("\n--- Knowledge Graph Results ---")
    found_entities = False
    for word in words:
        subgraph = kg.get_subgraph(word)
        if subgraph['nodes']:
            found_entities = True
            print(f"Entity: {word}")
            for link in subgraph['links']:
                print(f"  -> {link['relation']} -> {link['target']}")
    
    if not found_entities:
        print("No direct entity matches found in graph.")

if __name__ == "__main__":
    app()
