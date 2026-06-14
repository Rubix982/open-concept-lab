"""CLI: python -m src.query "<topic or claim text>" [--top-n N]"""

from __future__ import annotations

import argparse

from .search import format_results, search


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the claim knowledge graph.")
    parser.add_argument("query", help="topic or claim text")
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()
    results = search(args.query, top_n=args.top_n)
    print(format_results(args.query, results))


if __name__ == "__main__":
    main()
