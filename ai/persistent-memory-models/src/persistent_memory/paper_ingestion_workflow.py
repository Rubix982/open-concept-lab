"""
Temporal Workflow for Research Paper Ingestion.

Downloads papers from arXiv, processes them with hierarchical attention,
and stores in the persistent memory system.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class PaperIngestionParams:
    """Parameters for paper ingestion workflow."""

    arxiv_ids: list[str] | None = None
    search_query: str | None = None
    collection_name: str | None = None
    max_papers: int = 10
    use_attention: bool = True


@dataclass
class PaperMetadata:
    """Metadata for an ingested paper."""

    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    num_chunks: int
    text_length: int


@workflow.defn
class ResearchPaperIngestionWorkflow:
    """
    Workflow to ingest research papers from arXiv.

    Steps:
    1. Search/fetch papers from arXiv
    2. Download PDFs
    3. Extract text
    4. Chunk and embed text
    5. Extract facts using LLM
    6. Store in vector store + knowledge graph
    7. (Optional) Train attention model
    """

    @workflow.run
    async def run(self, params: PaperIngestionParams) -> dict[str, Any]:
        """Execute the paper ingestion workflow."""

        workflow.logger.info(f"Starting paper ingestion: {params}")

        # Step 1: Fetch paper metadata
        papers = await workflow.execute_activity(
            fetch_papers_activity,
            params,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

        if not papers:
            return {"status": "failed", "message": "No papers found", "papers_processed": 0}

        workflow.logger.info(f"Found {len(papers)} papers to process")

        # Step 2: Process each paper in parallel
        paper_results = []

        for paper in papers:
            result = await workflow.execute_activity(
                process_paper_activity,
                paper,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=2, initial_interval=timedelta(seconds=1)),
            )
            paper_results.append(result)

        # Step 3: Extract facts from all papers
        fact_extraction_tasks = []
        for result in paper_results:
            if result["success"]:
                task = workflow.execute_activity(
                    extract_facts_from_paper_activity,
                    result,
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=RetryPolicy(maximum_attempts=2),
                )
                fact_extraction_tasks.append(task)

        # Wait for all fact extractions
        fact_results = await workflow.wait_for_all(*fact_extraction_tasks)

        # Step 4: (Optional) Update attention model
        if params.use_attention and len(paper_results) >= 5:
            await workflow.execute_activity(
                update_attention_model_activity,
                {"papers": paper_results},
                start_to_close_timeout=timedelta(minutes=15),
            )

        # Compile results
        successful = sum(1 for r in paper_results if r["success"])
        total_chunks = sum(r.get("num_chunks", 0) for r in paper_results)
        total_facts = sum(len(r) for r in fact_results if r)

        return {
            "status": "completed",
            "papers_processed": successful,
            "total_papers": len(papers),
            "total_chunks": total_chunks,
            "total_facts": total_facts,
            "papers": [r["metadata"] for r in paper_results if r["success"]],
        }


# Activities


@activity.defn
async def fetch_papers_activity(params: PaperIngestionParams) -> list[dict[str, Any]]:
    """Fetch papers from arXiv based on parameters."""
    from persistent_memory.arxiv_downloader import ArxivDownloader, get_curated_papers

    downloader = ArxivDownloader()
    papers = []

    # Option 1: Specific arXiv IDs
    if params.arxiv_ids:
        for arxiv_id in params.arxiv_ids:
            paper = downloader.get_paper_by_id(arxiv_id)
            if paper:
                papers.append(paper.to_dict())

    # Option 2: Search query
    elif params.search_query:
        results = downloader.search(params.search_query, max_results=params.max_papers)
        papers = [p.to_dict() for p in results]

    # Option 3: Curated collection
    elif params.collection_name:
        arxiv_ids = get_curated_papers(params.collection_name)
        for arxiv_id in arxiv_ids[: params.max_papers]:
            paper = downloader.get_paper_by_id(arxiv_id)
            if paper:
                papers.append(paper.to_dict())

    logger.info(f"Fetched {len(papers)} papers")
    return papers


@activity.defn
async def process_paper_activity(paper: dict[str, Any]) -> dict[str, Any]:
    """Download and process a single paper using DataRepository."""
    from persistent_memory.data_repository import get_repository
    from persistent_memory.persistent_vector_store import PersistentVectorStore

    vector_store = PersistentVectorStore()
    repo = get_repository()

    try:
        arxiv_id = paper["arxiv_id"]

        # Use repository to get paper (will cache automatically)
        paper_data = repo.get_paper(arxiv_id)

        if not paper_data or not paper_data.get("text"):
            return {"success": False, "arxiv_id": arxiv_id, "error": "Failed to get paper data"}

        text = paper_data["text"]

        # Chunk text
        chunks = chunk_text(text, chunk_size=1000, overlap=200)

        # Embed and store chunks
        for i, chunk in enumerate(chunks):
            metadata = {
                "arxiv_id": arxiv_id,
                "title": paper_data["metadata"]["title"],
                "authors": paper_data["metadata"]["authors"],
                "chunk_index": i,
                "source": "arxiv",
                "pdf_path": paper_data["pdf_path"],
                "text_path": paper_data["text_path"],
            }

            vector_store.add_text(chunk, metadata=metadata)

        logger.info(
            f"Processed paper {arxiv_id}: {len(chunks)} chunks (cached: {repo.is_cached(arxiv_id)})"
        )

        return {
            "success": True,
            "arxiv_id": arxiv_id,
            "num_chunks": len(chunks),
            "text_length": len(text),
            "cached": repo.is_cached(arxiv_id),
            "metadata": {
                "arxiv_id": arxiv_id,
                "title": paper_data["metadata"]["title"],
                "authors": paper_data["metadata"]["authors"],
                "num_chunks": len(chunks),
            },
        }

    except Exception as e:
        logger.error(f"Error processing paper {paper['arxiv_id']}: {e}")
        return {"success": False, "arxiv_id": paper["arxiv_id"], "error": str(e)}


@activity.defn
async def extract_facts_from_paper_activity(paper_result: dict[str, Any]) -> list[dict]:
    """Extract facts from paper using LLM."""
    from persistent_memory.fact_extractor import FactExtractor
    from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph
    from persistent_memory.persistent_vector_store import PersistentVectorStore

    if not paper_result["success"]:
        return []

    try:
        extractor = FactExtractor()
        kg = PersistentKnowledgeGraph()
        vs = PersistentVectorStore()

        # Get chunks for this paper
        arxiv_id = paper_result["arxiv_id"]

        # Search for chunks from this paper
        # (In practice, we'd have a better way to retrieve by metadata)
        results = vs.search(arxiv_id, k=50)

        paper_chunks = [r for r in results if r.get("metadata", {}).get("arxiv_id") == arxiv_id]

        all_facts = []

        # Extract facts from each chunk
        for chunk_data in paper_chunks[:10]:  # Limit to first 10 chunks
            chunk_text = chunk_data.get("text", "")

            result = await extractor.extract_from_chunk(chunk_text)

            # Add facts to knowledge graph
            for fact in result.facts:
                kg.add_fact(
                    fact.subject,
                    fact.predicate,
                    fact.object,
                    metadata={
                        "source": "arxiv",
                        "arxiv_id": arxiv_id,
                        "confidence": fact.confidence,
                    },
                )
                all_facts.append(fact.dict())

        logger.info(f"Extracted {len(all_facts)} facts from {arxiv_id}")
        return all_facts

    except Exception as e:
        logger.error(f"Error extracting facts: {e}")
        return []


@activity.defn
async def update_attention_model_activity(data: dict[str, Any]) -> dict[str, Any]:
    """Update attention model with new papers."""
    # This would trigger retraining of the attention model
    # For now, just log
    logger.info(f"Would update attention model with {len(data['papers'])} papers")
    return {"status": "skipped"}


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """Chunk text with overlap."""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind(".")
            if last_period > chunk_size * 0.7:  # At least 70% of chunk
                end = start + last_period + 1
                chunk = text[start:end]

        chunks.append(chunk.strip())
        start = end - overlap

    return chunks


if __name__ == "__main__":
    # This would be run by the Temporal worker
    pass
