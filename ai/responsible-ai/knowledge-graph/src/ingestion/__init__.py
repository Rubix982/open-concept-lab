"""Ingestion layer: open paper sources -> sentences with provenance.

Entry point: `python -m src.ingestion --query "..." --limit 50`
"""

from .models import PaperMeta, SentenceRecord
from .pipeline import ingest

__all__ = ["PaperMeta", "SentenceRecord", "ingest"]
