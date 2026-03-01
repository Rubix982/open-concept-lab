import asyncio
import os
from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow, activity

from persistent_memory.core.persistent_context_engine import PersistentVectorStore, PersistentKnowledgeGraph
from persistent_memory.core.fact_extractor import FactExtractor, MockFactExtractor


# IngestBookParams, IngestBookResult, and activity functions are defined below in this module


@workflow.defn
class IngestBookWorkflow:
    @workflow.run
    async def run(self, params: IngestBookParams) -> IngestBookResult:
        # 1. Download/Read Book
        text_content = await workflow.execute_activity(
            download_book_activity,
            params.book_path,
            start_to_close_timeout=timedelta(seconds=60),
        )

        # 2. Chunk Text
        chunks = await workflow.execute_activity(
            chunk_text_activity,
            text_content,
            start_to_close_timeout=timedelta(seconds=60),
        )

        # 3. Process Chunks (Embed & Extract) in Parallel
        # We batch them to avoid overwhelming downstream services
        results = []
        batch_size = 10

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            # Launch parallel activities for this batch
            batch_futures = []
            for chunk in batch:
                # Embed and Store (Vector DB)
                batch_futures.append(
                    workflow.execute_activity(
                        embed_and_store_activity,
                        chunk,
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                )
                # Extract Facts (Knowledge Graph)
                batch_futures.append(
                    workflow.execute_activity(
                        extract_facts_activity,
                        chunk,
                        start_to_close_timeout=timedelta(seconds=60),
                    )
                )

            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_futures)
            results.extend(batch_results)

        return IngestBookResult(total_chunks=len(chunks), status="COMPLETED")


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
        with open(book_path, encoding="utf-8") as f:
            return f.read()
    return f"Mock content for {book_path}. This is a placeholder."


@activity.defn
async def chunk_text_activity(text: str) -> list[str]:
    """
    Splits text into manageable chunks.
    """
    activity.logger.info(f"Chunking text of length {len(text)}")
    chunk_size = 1000
    chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
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
        texts=[chunk], metadatas=[{"source": "ingestion_workflow"}], ids=[chunk_id]
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
            metadata={"confidence": fact.confidence, "source_chunk": chunk[:20]},
        )

    return f"extracted {len(result.facts)} facts"
