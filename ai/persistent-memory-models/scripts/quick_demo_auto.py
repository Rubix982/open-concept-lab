#!/usr/bin/env python3
"""
Quick demo of the data repository and research paper system.
Run this to see everything in action!
"""

import sys

sys.path.insert(0, "src")

from persistent_memory.data_repository import DataRepository
from persistent_memory.arxiv_downloader import ArxivDownloader, PAPER_COLLECTIONS
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def demo_1_search_papers():
    """Demo 1: Search for papers on arXiv."""
    print("\n" + "=" * 70)
    print("DEMO 1: Searching arXiv")
    print("=" * 70)

    downloader = ArxivDownloader()

    query = "hierarchical attention"
    print(f"\n🔍 Searching for: '{query}'\n")

    papers = downloader.search(query, max_results=3)

    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper.title}")
        print(f"   arXiv: {paper.arxiv_id}")
        print(f"   Authors: {', '.join(paper.authors[:2])}")
        print()

    return papers


def demo_2_repository_basics():
    """Demo 2: Using the data repository."""
    print("\n" + "=" * 70)
    print("DEMO 2: Data Repository - Caching & Deduplication")
    print("=" * 70)

    repo = DataRepository(base_dir="./demo_data")

    # Get a famous paper
    arxiv_id = "1706.03762"  # Attention Is All You Need

    print(f"\n📥 Getting paper {arxiv_id} (Attention Is All You Need)...")
    print(f"   Cached before: {repo.is_cached(arxiv_id)}")

    paper = repo.get_paper(arxiv_id)

    if paper:
        print(f"\n✅ Paper retrieved!")
        print(f"   Title: {paper['metadata']['title']}")
        print(f"   Authors: {', '.join(paper['metadata']['authors'][:3])}")
        print(f"   Text length: {len(paper['text']):,} characters")
        print(f"   PDF: {paper['pdf_path']}")
        print(f"   Cached now: {repo.is_cached(arxiv_id)}")

        # Get it again (should be instant)
        print(f"\n📥 Getting same paper again (from cache)...")
        paper2 = repo.get_paper(arxiv_id)
        print(f"   ⚡ Instant! Cached: {repo.is_cached(arxiv_id)}")

    return repo


def demo_3_repository_stats(repo):
    """Demo 3: Repository statistics."""
    print("\n" + "=" * 70)
    print("DEMO 3: Repository Statistics")
    print("=" * 70)

    stats = repo.get_stats()

    print(f"\n📊 Repository Stats:")
    print(f"   Total papers: {stats['total_papers']}")
    print(f"   Total size: {stats['total_size_mb']:.2f} MB")
    print(f"   Location: {stats['base_dir']}")

    if stats["papers"]:
        print(f"\n📚 Cached papers:")
        for arxiv_id in stats["papers"]:
            paper = repo.get_paper(arxiv_id)
            if paper:
                print(f"   - {arxiv_id}: {paper['metadata']['title'][:60]}...")


def demo_4_curated_collections():
    """Demo 4: Curated paper collections."""
    print("\n" + "=" * 70)
    print("DEMO 4: Curated Paper Collections")
    print("=" * 70)

    print(f"\n📚 Available collections:")
    for name, ids in PAPER_COLLECTIONS.items():
        print(f"\n   {name}:")
        for arxiv_id in ids:
            print(f"      - {arxiv_id}")


def demo_5_text_access(repo):
    """Demo 5: Accessing paper text."""
    print("\n" + "=" * 70)
    print("DEMO 5: Accessing Paper Text")
    print("=" * 70)

    arxiv_id = "1706.03762"

    print(f"\n📄 Getting text for {arxiv_id}...")
    text = repo.get_text(arxiv_id)

    if text:
        print(f"   Length: {len(text):,} characters")
        print(f"\n   First 500 characters:")
        print(f"   {'-' * 60}")
        print(f"   {text[:500]}...")
        print(f"   {'-' * 60}")


def main():
    """Run all demos."""
    print("\n" + "🎓" * 35)
    print("Research Paper System - Interactive Demo")
    print("🎓" * 35)

    try:
        # Demo 1: Search
        papers = demo_1_search_papers()

        print("-" * 20)

        # Demo 2: Repository basics
        repo = demo_2_repository_basics()

        print("-" * 20)

        # Demo 3: Stats
        demo_3_repository_stats(repo)

        print("-" * 20)

        # Demo 4: Collections
        demo_4_curated_collections()

        print("-" * 20)

        # Demo 5: Text access
        demo_5_text_access(repo)

        print("\n" + "=" * 70)
        print("✅ Demo Complete!")
        print("=" * 70)

        print("\n📝 Summary:")
        print("   - Searched arXiv for papers")
        print("   - Downloaded and cached a paper")
        print("   - Showed instant cache access")
        print("   - Displayed repository statistics")
        print("   - Listed curated collections")
        print("   - Accessed extracted text")

        print("\n🚀 Next steps:")
        print("   1. Try: python -m persistent_memory.repo_cli stats")
        print("   2. Try: python -m persistent_memory.repo_cli get 1409.0473")
        print("   3. Try: python -m persistent_memory.repo_cli search 'transformers'")

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
