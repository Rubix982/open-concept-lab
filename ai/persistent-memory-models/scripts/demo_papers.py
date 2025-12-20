#!/usr/bin/env python3
"""
Demo script for research paper ingestion and querying.

Shows practical use case of the hierarchical attention system
with real research papers from arXiv.
"""

import asyncio
import logging
import time
from persistent_memory.arxiv_downloader import ArxivDownloader, PAPER_COLLECTIONS
from persistent_memory.paper_ingestion_workflow import (
    ResearchPaperIngestionWorkflow,
    PaperIngestionParams,
)
from persistent_memory.attention_retrieval import AttentionEnhancedRetrieval
from persistent_memory.persistent_vector_store import PersistentVectorStore
from persistent_memory.persistent_knowledge_graph import PersistentKnowledgeGraph
from persistent_memory.query_cache import QueryCache
from persistent_memory.streaming_query import StreamingQueryEngine
from temporalio.client import Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_paper_search():
    """Demo: Search for papers on arXiv."""
    print("=" * 70)
    print("DEMO 1: Searching arXiv for Papers")
    print("=" * 70)

    downloader = ArxivDownloader()

    # Search for papers
    query = "hierarchical attention mechanisms"
    print(f"\nSearching for: '{query}'\n")

    papers = downloader.search(query, max_results=5)

    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   arXiv ID: {paper.arxiv_id}")
        print(f"   Published: {paper.published}")
        print(f"   Categories: {', '.join(paper.categories)}")
        print(f"   Abstract: {paper.abstract[:250]}...")

    return papers


async def demo_paper_ingestion():
    """Demo: Ingest curated collection of papers."""
    print("\n" + "=" * 70)
    print("DEMO 2: Ingesting Curated Paper Collection")
    print("=" * 70)

    # Show available collections
    print("\nAvailable collections:")
    for name, ids in PAPER_COLLECTIONS.items():
        print(f"  - {name}: {len(ids)} papers")

    # Ingest attention mechanisms collection
    collection = "attention_mechanisms"
    print(f"\nIngesting collection: {collection}")

    try:
        client = await Client.connect("temporal:7233")

        params = PaperIngestionParams(
            collection_name=collection,
            max_papers=3,  # Limit for demo
            use_attention=True,
        )

        workflow_id = f"demo-ingest-{collection}"

        handle = await client.start_workflow(
            ResearchPaperIngestionWorkflow.run,
            params,
            id=workflow_id,
            task_queue="ingestion-task-queue",
        )

        print("Workflow started! Waiting for completion...")
        result = await handle.result()

        print(f"\n✅ Ingestion Complete!")
        print(f"   Papers processed: {result['papers_processed']}/{result['total_papers']}")
        print(f"   Total chunks: {result['total_chunks']}")
        print(f"   Total facts extracted: {result['total_facts']}")

        if result.get("papers"):
            print(f"\n📚 Ingested Papers:")
            for paper in result["papers"]:
                print(f"   - {paper['title']}")
                print(f"     ({paper['num_chunks']} chunks)")

        return result

    except Exception as e:
        logger.error(f"Error in ingestion: {e}")
        print(f"\n❌ Ingestion failed: {e}")
        return None


async def demo_research_assistant():
    """
    Demo: Complete Research Assistant Workflow.

    Combines:
    1. Query Caching (Redis)
    2. Hierarchical Attention Retrieval
    3. Knowledge Graph
    4. Streaming Response
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Full Research Assistant (Advanced)")
    print("=" * 70)

    query = "What are the key benefits of self-attention?"
    print(f"\nUser Query: '{query}'")

    # 1. Initialize Components
    print("\n[1] Initializing Memory Components...")
    vs = PersistentVectorStore()
    kg = PersistentKnowledgeGraph()
    cache = QueryCache()

    # 2. Check Cache
    print("\n[2] Checking Query Cache (Redis)...")
    cached_response = await cache.get(query)
    if cached_response:
        print("   ✅ Cache HIT! Returning instant response.")
        print(f"   Response: {cached_response[:100]}...")
        return

    print("   ❌ Cache MISS. Proceeding to retrieval.")

    # 3. Hierarchical Attention Retrieval
    print("\n[3] Retrieving Context with Hierarchical Attention...")
    retrieval = AttentionEnhancedRetrieval(vs)
    retrieval_result = retrieval.retrieve_with_attention(query, k=5, return_attention=True)

    contexts = retrieval_result["contexts"]
    print(f"   Selected {len(contexts)} contexts based on attention scores.")

    # Show attention scores
    print("\n   Top Contexts by Attention:")
    for i, ctx in enumerate(contexts[:3], 1):
        print(
            f"   {i}. Score: {ctx['attention_score']:.3f} | Source: {ctx.get('metadata', {}).get('title', 'Unknown')}"
        )
        print(f"      Key Sentence: {ctx.get('key_sentence', '')[:80]}...")

    # 4. Knowledge Graph Lookup
    print("\n[4] Consulting Knowledge Graph...")
    # Extract key entities from query (simple mock for demo if no LLM)
    entities = ["self-attention", "transformer"]
    kg_facts = []
    for entity in entities:
        facts = kg.query(entity, depth=1)
        if facts:
            kg_facts.extend(facts)
            print(f"   Found facts for '{entity}': {len(facts)}")

    if not kg_facts:
        print("   No direct facts found in graph yet (needs more ingestion).")

    # 5. Stream Response
    print("\n[5] Streaming Response...")
    print("-" * 40)

    # Simulate streaming if no LLM connected, or use real engine
    engine = StreamingQueryEngine(vs, kg, None)  # Pass None for LLM to simulate or use real

    response_text = ""
    start_time = time.time()

    # Mocking the stream for visual demo purposes if LLM is not configured
    # In a real scenario, engine.stream_query would yield tokens
    simulated_response = (
        "Self-attention allows the model to weigh the importance of different words "
        "in the input sequence regardless of their distance. Key benefits include: "
        "1) Parallelization of computation, 2) Capturing long-range dependencies, "
        "and 3) Interpretable attention weights."
    )

    for word in simulated_response.split():
        print(word, end=" ", flush=True)
        time.sleep(0.05)  # Simulate typing effect
        response_text += word + " "

    print("\n" + "-" * 40)
    print(f"\n✅ Response complete in {time.time() - start_time:.2f}s")

    # 6. Cache Result
    print("\n[6] Caching result for future...")
    await cache.set(query, response_text, ttl=3600)
    print("   ✅ Saved to Redis cache.")


async def main():
    """Run all demos."""
    print("\n" + "🎓" * 35)
    print("Research Paper Ingestion & Hierarchical Attention Demo")
    print("🎓" * 35 + "\n")

    # Demo 1: Search
    await demo_paper_search()

    input("\nPress Enter to continue to ingestion demo...")

    # Demo 2: Ingest
    result = await demo_paper_ingestion()

    if result:
        input("\nPress Enter to continue to Research Assistant demo...")

        # Demo 3: Full Research Assistant
        await demo_research_assistant()

    print("\n" + "=" * 70)
    print("Demo Complete! 🎉")
    print("=" * 70)
    print("\nNext steps:")
    print(
        "1. Try your own queries with: docker-compose exec app python -m persistent_memory.cli query 'your question'"
    )
    print(
        "2. Ingest more papers with: docker-compose exec app python -m persistent_memory.cli ingest-papers --search='your topic'"
    )
    print(
        "3. Train attention model with: docker-compose exec app python -m persistent_memory.train_attention"
    )


if __name__ == "__main__":
    asyncio.run(main())
