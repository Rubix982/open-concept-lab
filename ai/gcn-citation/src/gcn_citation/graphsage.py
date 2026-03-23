"""Backward-compatible re-exports for the GraphSAGE implementation.

Prefer importing from `gcn_citation.models.graphsage` or `gcn_citation.models`.
"""

from .models.graphsage import ManualGraphSAGE
from .models.graphsage import train_graphsage

__all__ = ["ManualGraphSAGE", "train_graphsage"]
