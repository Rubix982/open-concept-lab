#!/usr/bin/env python3
"""
CLI commands for data repository management.
"""

import typer

from persistent_memory.data_repository import get_repository

app = typer.Typer()


@app.command()
def stats():
    """Show repository statistics."""
    repo = get_repository()
    stats = repo.get_stats()

    print("\n📊 Data Repository Statistics")
    print("=" * 50)
    print(f"Total papers: {stats['total_papers']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Location: {stats['base_dir']}")

    if stats["papers"]:
        print("\nCached papers:")
        for arxiv_id in stats["papers"]:
            print(f"  - {arxiv_id}")


@app.command()
def get(arxiv_id: str, show_text: bool = False):
    """Get a specific paper (downloads if not cached)."""
    repo = get_repository()

    print(f"\n📄 Getting paper {arxiv_id}...")
    paper = repo.get_paper(arxiv_id)

    if not paper:
        print(f"❌ Failed to get paper {arxiv_id}")
        return

    print("\n✅ Paper retrieved!")
    print(f"   Title: {paper['metadata']['title']}")
    print(f"   Authors: {', '.join(paper['metadata']['authors'][:3])}")
    print(f"   Published: {paper['metadata']['published']}")
    print(f"   PDF: {paper['pdf_path']}")
    print(f"   Text: {paper['text_path']}")
    print(f"   Text length: {len(paper['text'])} characters")
    print(f"   Cached: {repo.is_cached(arxiv_id)}")

    if show_text:
        print("\n📝 Text preview:")
        print(paper["text"][:500] + "...")


@app.command()
def search(query: str, max_results: int = 5):
    """Search and cache papers."""
    repo = get_repository()

    print(f"\n🔍 Searching for: '{query}'")
    papers = repo.search_and_cache(query, max_results=max_results)

    print(f"\n✅ Found and cached {len(papers)} papers:")
    for i, paper in enumerate(papers, 1):
        print(f"\n{i}. {paper['metadata']['title']}")
        print(f"   arXiv: {paper['arxiv_id']}")
        print(f"   Cached: {repo.is_cached(paper['arxiv_id'])}")


@app.command()
def list_cached():
    """List all cached papers."""
    repo = get_repository()
    papers = repo.get_cached_papers()

    print(f"\n📚 Cached Papers ({len(papers)}):")
    for arxiv_id in papers:
        paper = repo.get_paper(arxiv_id)
        if paper:
            print(f"\n  {arxiv_id}")
            print(f"    {paper['metadata']['title']}")


@app.command()
def clear(
    arxiv_id: str = typer.Option(None, help="Specific paper to clear"),
    all: bool = typer.Option(False, help="Clear entire cache"),
):
    """Clear cache."""
    repo = get_repository()

    if all:
        confirm = typer.confirm("⚠️  Clear entire cache?")
        if confirm:
            repo.clear_cache()
            print("✅ Cache cleared")
    elif arxiv_id:
        repo.clear_cache(arxiv_id)
        print(f"✅ Cleared cache for {arxiv_id}")
    else:
        print("❌ Specify --arxiv-id or --all")


@app.command()
def get_text(arxiv_id: str):
    """Get extracted text for a paper."""
    repo = get_repository()
    text = repo.get_text(arxiv_id)

    if text:
        print(f"\n📝 Text for {arxiv_id}:")
        print(f"Length: {len(text)} characters")
        print(f"\nPreview:\n{text[:1000]}...")
    else:
        print(f"❌ No text found for {arxiv_id}")


if __name__ == "__main__":
    app()
