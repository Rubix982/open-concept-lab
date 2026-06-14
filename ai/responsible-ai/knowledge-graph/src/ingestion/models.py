"""Typed records for ingested papers and sentences.

Plain dataclasses (no extra dependency) with full type hints. Each record is
JSON-serialisable for the `sentences.jsonl` output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class PaperMeta:
    """Metadata + provenance for one source paper."""

    paper_id: str            # canonical id, e.g. "openalex:W123" or "arxiv:2401.00001"
    title: str
    year: int | None
    venue: str | None
    authors: list[str] = field(default_factory=list)
    source: str = "openalex"  # openalex | arxiv
    url: str | None = None
    doi: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SentenceRecord:
    """One sentence with provenance back to its source paper."""

    paper_id: str
    section: str             # e.g. "abstract", "title"
    sentence_index: int      # 0-based index within (paper, section)
    char_start: int          # offset within the section text
    char_end: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
