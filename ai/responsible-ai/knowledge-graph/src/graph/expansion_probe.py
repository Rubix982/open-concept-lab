"""R-008 sizing: how much would citation-snowball expansion grow the corpus?

    python -m src.graph.expansion_probe

For each corpus paper, pulls its full S2 reference list and counts how many DISTINCT
referenced papers (outside the current corpus) are co-cited by >=2 corpus papers — the
high-value candidates whose inclusion would create multiple new intra-corpus edges.
Reports the co-citation distribution so we can pick a threshold before building.
"""

from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import requests

_PAPERS = Path(__file__).resolve().parents[2] / "data" / "processed" / "papers.jsonl"
_BASE = "https://api.semanticscholar.org/graph/v1"
_HEADERS = {"User-Agent": "claim-knowledge-graph/0.1 (mailto:islam.saif@northeastern.edu)"}


def _norm_doi(doi: str | None) -> str | None:
    return doi.replace("https://doi.org/", "").strip().lower() if doi else None


def _get(url: str, params: dict, tries: int = 5) -> dict | None:
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, headers=_HEADERS, timeout=45)
        except requests.exceptions.RequestException:
            time.sleep(2.0 * (attempt + 1))  # network blip / timeout — back off and retry
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(2.0 * (attempt + 1))
            continue
        return None
    return None


def _key(ext: dict) -> str | None:
    """Stable key for a referenced paper: prefer DOI, then arXiv, then S2 CorpusId."""
    if ext.get("DOI"):
        return "doi:" + _norm_doi(ext["DOI"])
    if ext.get("ArXiv"):
        return "arxiv:" + str(ext["ArXiv"]).lower()
    if ext.get("CorpusId"):
        return "s2:" + str(ext["CorpusId"])
    return None


def main() -> None:
    papers = [json.loads(l) for l in _PAPERS.read_text().splitlines() if l.strip()]
    corpus_keys = {"doi:" + _norm_doi(p["doi"]) for p in papers if p.get("doi")}

    cited_by: dict[str, set[str]] = defaultdict(set)  # referenced key -> {corpus paper_ids}
    titles: dict[str, str] = {}
    exts: dict[str, dict] = {}  # referenced key -> externalIds
    total_refs = 0
    for i, p in enumerate(papers):
        d = _norm_doi(p.get("doi"))
        if not d:
            continue
        data = _get(
            f"{_BASE}/paper/DOI:{d}/references",
            {"fields": "externalIds,title", "limit": 100},
        )
        time.sleep(1.1)
        for ref in (data.get("data") if data else None) or []:
            cp = ref.get("citedPaper") or {}
            k = _key(cp.get("externalIds") or {})
            if not k or k in corpus_keys:
                continue  # skip unresolvable + already-in-corpus
            total_refs += 1
            cited_by[k].add(p["paper_id"])
            titles[k] = cp.get("title") or "?"
            exts[k] = cp.get("externalIds") or {}
        print(f"  [{i + 1}/{len(papers)}] distinct external refs so far: {len(cited_by)}")

    cocite = Counter(len(v) for v in cited_by.values())
    ge2 = [k for k, v in cited_by.items() if len(v) >= 2]
    ge3 = [k for k, v in cited_by.items() if len(v) >= 3]
    new_edges_ge2 = sum(len(cited_by[k]) for k in ge2)  # each citing link = a new edge
    print(f"\n=== expansion sizing (45-paper corpus) ===")
    print(f"distinct external referenced papers: {len(cited_by)}  (from {total_refs} refs)")
    print(f"co-citation distribution (#corpus papers citing it): {dict(sorted(cocite.items()))}")
    print(f"candidates cited by >=2 corpus papers: {len(ge2)}  -> ~{new_edges_ge2} new citation edges")
    print(f"candidates cited by >=3 corpus papers: {len(ge3)}")
    print("\ntop co-cited external papers (would become hub nodes):")
    for k in sorted(ge2, key=lambda k: -len(cited_by[k]))[:12]:
        print(f"  {len(cited_by[k])}x  {titles[k][:60]}")

    # Write candidates (>=2) for the expansion build (E-013).
    out = Path(__file__).resolve().parents[2] / "data" / "processed" / "expansion_candidates.jsonl"
    rows = []
    for k in sorted(ge2, key=lambda k: -len(cited_by[k])):
        ext = exts[k]
        rows.append({
            "key": k, "cocite": len(cited_by[k]), "title": titles[k],
            "doi": _norm_doi(ext.get("DOI")), "arxiv": ext.get("ArXiv"),
            "corpusid": ext.get("CorpusId"),
            "cited_by": sorted(cited_by[k]),
        })
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"\nwrote {len(rows)} candidates (>=2) -> {out}")


if __name__ == "__main__":
    main()
