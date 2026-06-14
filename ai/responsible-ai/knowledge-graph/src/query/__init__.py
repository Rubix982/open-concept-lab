"""Query layer over the claim knowledge graph.

    python -m src.query "graph neural networks for recommendation"
"""

from .search import search

__all__ = ["search"]
