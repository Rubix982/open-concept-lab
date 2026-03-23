"""Backward-compatible re-exports for the GCN implementation.

Prefer importing from `gcn_citation.models.gcn` or `gcn_citation.models`.
"""

from .models.gcn import ManualGCN
from .models.gcn import TrainingResult
from .models.gcn import accuracy
from .models.gcn import masked_cross_entropy
from .models.gcn import train_gcn

__all__ = [
    "ManualGCN",
    "TrainingResult",
    "accuracy",
    "masked_cross_entropy",
    "train_gcn",
]
