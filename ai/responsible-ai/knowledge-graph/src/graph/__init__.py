"""Graph layer: claims -> Kùzu property graph with typed edges.

    python -m src.graph.build      # build ckg.kuzu from ingested + classified claims
"""

from .store import GraphStore

__all__ = ["GraphStore"]
