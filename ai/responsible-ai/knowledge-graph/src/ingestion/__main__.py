"""CLI entry point for ingestion.

    python -m src.ingestion --query "graph neural networks" --limit 50
"""

from __future__ import annotations

import argparse

from .pipeline import ingest


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest open papers into sentences.")
    parser.add_argument("--query", required=True, help="search query for OpenAlex")
    parser.add_argument("--limit", type=int, default=50, help="max papers")
    parser.add_argument(
        "--no-cache", action="store_true", help="ignore cached API responses"
    )
    args = parser.parse_args()

    n_papers, n_sentences = ingest(
        args.query, limit=args.limit, use_cache=not args.no_cache
    )
    print(
        f"Ingested {n_papers} papers -> {n_sentences} sentences "
        f"(data/processed/sentences.jsonl)"
    )


if __name__ == "__main__":
    main()
