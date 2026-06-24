"""E-013: citation-snowball corpus expansion (ingest step, via Semantic Scholar).

Reads data/processed/expansion_candidates.jsonl (from expansion_probe), keeps those cited by
>= MIN_COCITE corpus papers, fetches each one's abstract from Semantic Scholar by CorpusId
(the hubs — GCN, GAT, GraphSAGE — are arXiv-only with no DOI, so S2/CorpusId is the reliable
key), and APPENDS new Paper + sentence records to the corpus. Idempotent: skips papers
already present. New paper records carry `arxiv`/`corpusid` so the citation matcher can
resolve references by any id.

    python -m src.graph.expand_corpus --min-cocite 3
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any, cast

import requests

from ..ingestion.models import PaperMeta
from ..ingestion.pipeline import SentencesForPaper

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_CANDS = _PROC / "expansion_candidates.jsonl"
_PAPERS = _PROC / "papers.jsonl"
_SENTS = _PROC / "sentences.jsonl"
_S2 = "https://api.semanticscholar.org/graph/v1"
_HEADERS = {"User-Agent": "claim-knowledge-graph/0.1 (mailto:islam.saif@northeastern.edu)"}


def _fetch_s2(corpusid: str, tries: int = 3) -> Dict[Any, Any] | None:
    fields = "title,abstract,year,venue,externalIds,authors"
    for attempt in range(tries):
        try:
            r = requests.get(f"{_S2}/paper/CorpusId:{corpusid}", params={"fields": fields},
                             headers=_HEADERS, timeout=20)  # fail fast on flaky calls
        except requests.exceptions.RequestException:
            time.sleep(1.0 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(2.0 * (attempt + 1))
            continue
        return None
    return None


def _guess_pid(c: Dict[str, Any]) -> str:
    """Predict the paper_id from the candidate record (no S2 call needed to dedupe)."""
    return f"arxiv:{c['arxiv']}" if c.get("arxiv") else f"s2:{c['corpusid']}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-cocite", type=int, default=3)
    args = ap.parse_args()

    existing = {json.loads(l)["paper_id"] for l in _PAPERS.read_text().splitlines() if l.strip()}
    cands = [json.loads(l) for l in _CANDS.read_text().splitlines() if l.strip()]
    picked = [c for c in cands if c["cocite"] >= args.min_cocite and c.get("corpusid")]
    print(f"{len(picked)} candidates >= {args.min_cocite} co-cites (by CorpusId)")

    # Pre-skip already-present papers WITHOUT an S2 call (the dedupe fix).
    todo = [c for c in picked if _guess_pid(c) not in existing]
    print(f"{len(picked) - len(todo)} already present (skipped, no fetch); fetching {len(todo)}")

    added, sents, skipped = 0, 0, 0
    with _PAPERS.open("a", encoding="utf-8") as pf, _SENTS.open("a", encoding="utf-8") as sf:
        for i, c in enumerate(todo):
            d = _fetch_s2(str(c["corpusid"]))
            time.sleep(1.0)
            if not d or not d.get("abstract"):
                skipped += 1
                continue
            ext: Dict[str, Any] = d.get("externalIds") or {}
            arxiv = str(ext.get("ArXiv") or "")
            doi: str | None = ext.get("DOI")
            cid = str(c["corpusid"])
            pid = f"arxiv:{arxiv}" if arxiv else f"s2:{cid}"
            if pid in existing:
                skipped += 1
                continue
            existing.add(pid)
            authors_raw = d.get("authors")
            authors: list[str] = []
            if isinstance(authors_raw, list):
                for a in cast(list[dict[str, Any]], authors_raw):
                    name = str(a.get("name") or "")
                    if name:
                        authors.append(name)
            meta = PaperMeta(
                paper_id=pid, title=d.get("title") or c["title"], year=d.get("year"),
                venue=d.get("venue"), authors=authors, source="s2",
                url=f"https://www.semanticscholar.org/paper/{cid}",
                doi=(f"https://doi.org/{doi}" if doi else None),
            )
            rec: object = {**meta.to_dict(), "arxiv": arxiv, "corpusid": cid}
            pf.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
            for s in SentencesForPaper(meta, d["abstract"]):
                sf.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")
                sents += 1
            pf.flush()
            sf.flush()  # durable + observable progress; survives interruption
            if (i + 1) % 10 == 0:
                print(f"  [{i + 1}/{len(todo)}] added {added}", flush=True)

    print(f"\nadded {added} papers ({sents} sentences), skipped {skipped} (no abstract/dupe)")
    print(f"corpus now: {len(existing)} papers")


if __name__ == "__main__":
    main()
