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
from typing import Any, Dict, cast, List

import requests

_PAPERS = Path(__file__).resolve().parents[2] / "data" / "processed" / "papers.jsonl"
_BASE = "https://api.semanticscholar.org/graph/v1"
_HEADERS = {"User-Agent": "claim-knowledge-graph/0.1 (mailto:islam.saif@northeastern.edu)"}


def _norm_doi(doi: str | None) -> str | None:
    return doi.replace("https://doi.org/", "").strip().lower() if doi else None


def _get(url: str, params: Any, tries: int = 5) -> Dict[Any, Any] | None:
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

def _get_normalized_doi(ext: Dict[str, Any]) -> str | None:
    """Return a normalized DOI if present in the externalIds dict."""
    normalized_doi = _norm_doi(ext["DOI"])
    if not isinstance(normalized_doi, str):
        return None
    return "doi:" + normalized_doi


def _key(ext: Dict[str, Any]) -> str | None:
    """Stable key for a referenced paper: prefer DOI, then arXiv, then S2 CorpusId."""
    if ext.get("DOI"):
        return _get_normalized_doi(ext)
    if ext.get("ArXiv"):
        return "arxiv:" + str(ext["ArXiv"]).lower()
    if ext.get("CorpusId"):
        return "s2:" + str(ext["CorpusId"])
    return None


def main() -> None:
    papers = [json.loads(l) for l in _PAPERS.read_text().splitlines() if l.strip()]
    corpus_keys = {_get_normalized_doi(p) for p in papers if p.get("doi")}

    cited_by: Dict[str, set[str]] = defaultdict(set)  # referenced key -> {corpus paper_ids}
    titles: Dict[str, str] = {}
    exts: Dict[str, Dict[str, Any]] = {}  # referenced key -> externalIds
    total_refs = 0
    for i, p in enumerate(papers):
        d = _get_normalized_doi(p)
        if not d:
            continue
        data = _get(
            f"{_BASE}/paper/DOI:{d}/references",
            {"fields": "externalIds,title", "limit": 100},
        )
        time.sleep(1.1)
        refs_data = data.get("data") if data else None
        refs_raw: List[Dict[str, Any]] = []
        if isinstance(refs_data, list):
            refs_raw = [cast(Dict[str, Any], item) for item in refs_data if isinstance(item, dict)]
        for ref_item in refs_raw:
            ref = ref_item
            cp_raw = ref.get("citedPaper")
            cp: Dict[str, Any] = cast(Dict[str, Any], cp_raw) if isinstance(cp_raw, dict) else {}
            ext_raw = cp.get("externalIds")
            ext_ids: Dict[str, Any] = cast(Dict[str, Any], ext_raw) if isinstance(ext_raw, dict) else {}
            k = _key(ext_ids)
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
    rows: List[Dict[str, Any]] = []
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
