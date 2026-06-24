"""Ingestion pipeline: source -> segment -> sentences.jsonl with provenance."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .models import PaperMeta, SentenceRecord
from .segment import split_sentences
from .sources import fetch_openalex

_PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
_SENTENCES_PATH = _PROCESSED_DIR / "sentences.jsonl"
_PAPERS_PATH = _PROCESSED_DIR / "papers.jsonl"


def SentencesForPaper(meta: PaperMeta, abstract: str) -> Iterator[SentenceRecord]:
    """Yield SentenceRecords for a paper's title and abstract, with provenance."""
    # Title as a single sentence (section="title").
    title = meta.title.strip()
    if title:
        yield SentenceRecord(
            paper_id=meta.paper_id,
            section="title",
            sentence_index=0,
            char_start=0,
            char_end=len(title),
            text=title,
        )
    # Abstract, segmented (section="abstract").
    for idx, (start, end, sentence) in enumerate(split_sentences(abstract)):
        yield SentenceRecord(
            paper_id=meta.paper_id,
            section="abstract",
            sentence_index=idx,
            char_start=start,
            char_end=end,
            text=sentence,
        )


def ingest(
    query: str,
    limit: int = 50,
    *,
    use_cache: bool = True,
) -> tuple[int, int]:
    """Run ingestion for `query`, write papers.jsonl + sentences.jsonl.

    Returns (num_papers, num_sentences).
    """
    _PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    papers = fetch_openalex(query, limit=limit, use_cache=use_cache)

    n_papers = 0
    n_sentences = 0
    with (
        _PAPERS_PATH.open("w", encoding="utf-8") as pf,
        _SENTENCES_PATH.open("w", encoding="utf-8") as sf,
    ):
        for meta, abstract in papers:
            pf.write(json.dumps(meta.to_dict(), ensure_ascii=False) + "\n")
            n_papers += 1
            for record in SentencesForPaper(meta, abstract or ""):
                sf.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
                n_sentences += 1

    return n_papers, n_sentences
