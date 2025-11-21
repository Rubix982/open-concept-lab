from dataclasses import dataclass
from temporalio import activity
import os
import asyncio

# Import core components
from persistent_memory.persistent_vector_store import PersistentVectorStore
from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph
from persistent_memory.fact_extractor import FactExtractor, MockFactExtractor

# Data Classes
@dataclass
class IngestBookParams:
    book_path: str

@dataclass
class IngestBookResult:
    total_chunks: int
    status: str

# Activities
@activity.defn
async def download_book_activity(book_path: str) -> str:
    """
    Reads the content of a book from a file path.
    """
    activity.logger.info(f"Reading book from {book_path}")
    if os.path.exists(book_path):
        with open(book_path, 'r', encoding='utf-8') as f:
            return f.read()
    return f"Mock content for {book_path}. This is a placeholder."

@activity.defn
async def chunk_text_activity(text: str) -> list[str]:
    """
    Splits text into manageable chunks.
    """
    activity.logger.info(f"Chunking text of length {len(text)}")
    chunk_size = 1000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    return chunks

@activity.defn
async def embed_and_store_activity(chunk: str) -> str:
    """
    Generates embeddings and stores in ChromaDB.
    """
    activity.logger.info(f"Embedding chunk: {chunk[:50]}...")
    
    # Initialize store
    vector_store = PersistentVectorStore()
    
    # Store chunk
    # We use a simple hash as ID for now
    chunk_id = f"chunk_{hash(chunk)}"
    vector_store.add_texts(
        texts=[chunk],
        metadatas=[{"source": "ingestion_workflow"}],
        ids=[chunk_id]
    )
    
    return "stored"

@activity.defn
async def extract_facts_activity(chunk: str) -> str:
    """
    Extracts facts and stores in Knowledge Graph.
    """
    activity.logger.info(f"Extracting facts from chunk: {chunk[:50]}...")
    
    # Initialize components
    # Use MockFactExtractor if no API key to avoid errors during testing
    if os.getenv("OPENAI_API_KEY"):
        extractor = FactExtractor()
    else:
        extractor = MockFactExtractor()
        
    kg = PersistentKnowledgeGraph()
    
    # Extract facts
    result = await extractor.extract_from_chunk(chunk)
    
    # Store in graph
    for fact in result.facts:
        kg.add_fact(
            subject=fact.subject,
            predicate=fact.predicate,
            object=fact.object,
            metadata={"confidence": fact.confidence, "source_chunk": chunk[:20]}
        )
    
    return f"extracted {len(result.facts)} facts"
