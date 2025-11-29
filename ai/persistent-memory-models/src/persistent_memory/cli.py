"""Command-line interface for the persistent memory system."""

import asyncio
import os

import typer
from temporalio.client import Client

app = typer.Typer()


async def trigger_ingestion(file_path: str):
    """Trigger the ingestion workflow."""
    from persistent_memory.ingestion_workflow import IngestBookParams, IngestBookWorkflow

    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)

    workflow_id = f"ingest-{os.path.basename(file_path)}"

    handle = await client.start_workflow(
        IngestBookWorkflow.run,
        IngestBookParams(book_path=file_path),
        id=workflow_id,
        task_queue="ingestion-task-queue",
    )

    print(f"Starting ingestion for {file_path}...")
    result = await handle.result()
    return result


async def trigger_paper_ingestion(
    arxiv_ids: list[str] | None = None,
    search_query: str | None = None,
    collection: str | None = None,
    max_papers: int = 10,
):
    """Trigger paper ingestion workflow."""
    from persistent_memory.paper_ingestion_workflow import (
        PaperIngestionParams,
        ResearchPaperIngestionWorkflow,
    )

    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    client = await Client.connect(temporal_host)

    params = PaperIngestionParams(
        arxiv_ids=arxiv_ids,
        search_query=search_query,
        collection_name=collection,
        max_papers=max_papers,
        use_attention=True,
    )

    workflow_id = f"ingest-papers-{collection or search_query or 'custom'}"

    handle = await client.start_workflow(
        ResearchPaperIngestionWorkflow.run,
        params,
        id=workflow_id,
        task_queue="ingestion-task-queue",
    )

    print("Starting paper ingestion...")
    result = await handle.result()
    return result


@app.command()
def ingest(file_path: str):
    """Ingest a book or document."""
    result = asyncio.run(trigger_ingestion(file_path))
    print(f"Ingestion complete! Processed {result.get('chunks_processed', 0)} chunks.")


@app.command()
def ingest_papers(
    arxiv_ids: str = typer.Option(None, help="Comma-separated arXiv IDs"),
    search: str = typer.Option(None, help="Search query"),
    collection: str = typer.Option(None, help="Curated collection name"),
    max_papers: int = typer.Option(10, help="Maximum papers to ingest"),
):
    """
    Ingest research papers from arXiv.

    Examples:
        # Ingest specific papers
        cli ingest-papers --arxiv-ids="1706.03762,1409.0473"

        # Search and ingest
        cli ingest-papers --search="hierarchical attention" --max-papers=5

        # Use curated collection
        cli ingest-papers --collection=attention_mechanisms
    """
    ids = arxiv_ids.split(",") if arxiv_ids else None

    result = asyncio.run(
        trigger_paper_ingestion(
            arxiv_ids=ids, search_query=search, collection=collection, max_papers=max_papers
        )
    )

    print("\n✅ Paper Ingestion Complete!")
    print(f"   Papers processed: {result['papers_processed']}/{result['total_papers']}")
    print(f"   Total chunks: {result['total_chunks']}")
    print(f"   Total facts: {result['total_facts']}")

    if result.get("papers"):
        print("\n📚 Ingested Papers:")
        for paper in result["papers"]:
            print(f"   - {paper['title']}")
            print(f"     arXiv: {paper['arxiv_id']} ({paper['num_chunks']} chunks)")


@app.command()
def search_papers(query: str, max_results: int = typer.Option(10, help="Maximum results")):
    """Search for papers on arXiv without ingesting."""
    from persistent_memory.arxiv_downloader import ArxivDownloader

    downloader = ArxivDownloader()
    papers = downloader.search(query, max_results=max_results)

    print(f"\n🔍 Found {len(papers)} papers for '{query}':\n")

    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   arXiv ID: {paper.arxiv_id}")
        print(f"   Categories: {', '.join(paper.categories)}")
        print(f"   Abstract: {paper.abstract[:200]}...")
        print()


@app.command()
def list_conferences():
    """List supported AI conferences."""
    from persistent_memory.conference_connector import ConferenceConnector

    connector = ConferenceConnector()
    conferences = connector.list_conferences()

    print("\n🏛️  Supported AI Conferences:")
    print("=" * 40)

    for conf in conferences:
        print(f"\n📌 {conf['name']} ({conf['full_name']})")
        print(f"   Topics: {', '.join(conf['topics'])}")
        print(f"   Years: {conf['years'][0]} - {conf['years'][-1]}")


@app.command()
def ingest_conference(
    name: str = typer.Option(..., help="Conference name (e.g., neurips, icml)"),
    year: int = typer.Option(None, help="Year (e.g., 2023)"),
    max_papers: int = typer.Option(10, help="Maximum papers to ingest"),
):
    """
    Ingest papers from a specific conference.

    Example:
        cli ingest-conference --name=neurips --year=2023
    """
    from persistent_memory.conference_connector import ConferenceConnector

    connector = ConferenceConnector()

    try:
        print(f"\n🏛️  Fetching papers from {name.upper()} {year or ''}...")
        papers = connector.get_conference_papers(name.lower(), year, max_results=max_papers)

        if not papers:
            print("❌ No papers found.")
            return

        arxiv_ids = [p.arxiv_id for p in papers]

        print(f"✅ Found {len(papers)} papers. Starting ingestion...")

        # Trigger ingestion workflow
        result = asyncio.run(
            trigger_paper_ingestion(
                arxiv_ids=arxiv_ids,
                collection=f"{name}_{year}" if year else name,
                max_papers=max_papers,
            )
        )

        print("\n✅ Conference Ingestion Complete!")
        print(f"   Papers processed: {result['papers_processed']}/{result['total_papers']}")

    except Exception as e:
        print(f"❌ Error: {e}")


@app.command()
def query(query_text: str, k: int = 5):
    """Query the memory system."""
    from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph
    from persistent_memory.persistent_vector_store import PersistentVectorStore

    vs = PersistentVectorStore()
    kg = PersistentKnowledgeGraph()

    print(f"Querying: {query_text}\n")

    # Vector search
    print("--- Vector Search Results ---")
    vector_results = vs.search(query_text, k=k)

    for result in vector_results:
        distance = result.get("distance", 0)
        text = result.get("text", "")
        metadata = result.get("metadata", {})

        print(f"[{distance:.4f}] {text[:100]}...")
        if metadata.get("arxiv_id"):
            print(f"   Source: {metadata.get('title', 'Unknown')} ({metadata['arxiv_id']})")
        print()

    # Knowledge graph
    print("\n--- Knowledge Graph Results ---")
    graph_results = kg.query(query_text)

    if graph_results:
        for result in graph_results[:k]:
            print(f"{result.get('subject')} -> {result.get('predicate')} -> {result.get('object')}")
    else:
        print("No direct entity matches found in graph.")


if __name__ == "__main__":
    app()
