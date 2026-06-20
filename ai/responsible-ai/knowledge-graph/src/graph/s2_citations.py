"""R-007 / E-010 / E-013: pull citances from Semantic Scholar and find intra-corpus
citation links (one corpus paper citing another), resolving by DOI / arXiv / CorpusId.

    python -m src.graph.s2_citations

Matches references to corpus papers by ANY id (DOI, arXiv, or S2 CorpusId), so citation
links to arXiv-only hubs (GCN, GAT, GraphSAGE) resolve. Writes the resolved citances to
data/processed/intra_corpus_citations.jsonl.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path

import requests

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_PAPERS = _PROC / "papers.jsonl"
_OUT = _PROC / "intra_corpus_citations.jsonl"
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


def _index_keys(rec: dict) -> list[str]:
    """All resolvable id-keys for a corpus paper record."""
    keys = []
    d = _norm_doi(rec.get("doi"))
    if d:
        keys.append("doi:" + d)
    if rec.get("arxiv"):
        keys.append("arxiv:" + str(rec["arxiv"]).lower())
    if rec.get("corpusid"):
        keys.append("s2:" + str(rec["corpusid"]))
    return keys


def _ref_keys(ext: dict) -> list[str]:
    keys = []
    d = _norm_doi(ext.get("DOI"))
    if d:
        keys.append("doi:" + d)
    if ext.get("ArXiv"):
        keys.append("arxiv:" + str(ext["ArXiv"]).lower())
    if ext.get("CorpusId"):
        keys.append("s2:" + str(ext["CorpusId"]))
    return keys


def _query_path(rec: dict) -> str | None:
    """S2 references endpoint for this paper, by best available id."""
    d = _norm_doi(rec.get("doi"))
    if d:
        return f"{_BASE}/paper/DOI:{d}/references"
    if rec.get("corpusid"):
        return f"{_BASE}/paper/CorpusId:{rec['corpusid']}/references"
    if rec.get("arxiv"):
        return f"{_BASE}/paper/ARXIV:{rec['arxiv']}/references"
    return None


def main() -> None:
    papers = [json.loads(l) for l in _PAPERS.read_text().splitlines() if l.strip()]
    index: dict[str, str] = {}
    for p in papers:
        for k in _index_keys(p):
            index[k] = p["paper_id"]
    print(f"{len(papers)} corpus papers, {len(index)} id-keys")

    edges = []
    for i, p in enumerate(papers):
        path = _query_path(p)
        if not path:
            continue
        data = _get(path, {"fields": "contexts,intents,isInfluential,externalIds,title",
                           "limit": 100})
        time.sleep(1.1)
        if not data:
            continue
        for ref in (data.get("data") or []):
            cp = ref.get("citedPaper") or {}
            cited_pid = None
            for k in _ref_keys(cp.get("externalIds") or {}):
                if k in index and index[k] != p["paper_id"]:
                    cited_pid = index[k]
                    break
            if cited_pid:
                edges.append({
                    "citing": p["paper_id"], "cited": cited_pid,
                    "citing_title": p["title"], "cited_title": cp.get("title"),
                    "intents": ref.get("intents") or [],
                    "is_influential": ref.get("isInfluential"),
                    "citances": ref.get("contexts") or [],
                })
        if (i + 1) % 20 == 0:
            print(f"  [{i + 1}/{len(papers)}] intra-corpus edges so far: {len(edges)}")

    _OUT.write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in edges) + "\n")
    intents = Counter(t for e in edges for t in e["intents"])
    print(f"\n=== {len(edges)} intra-corpus citation edges ===")
    print("intent distribution:", dict(intents))
    print(f"with >=1 citance: {sum(1 for e in edges if e['citances'])}/{len(edges)}")
    print(f"wrote {_OUT}")


if __name__ == "__main__":
    main()
