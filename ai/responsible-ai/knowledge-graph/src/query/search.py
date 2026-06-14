"""Semantic search over claims + their supporting/contradicting links."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ..graph.embed import EMBED_DIM, embed
from ..graph.store import GraphStore

_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "ckg.kuzu"


def search(query: str, top_n: int = 5) -> list[dict[str, Any]]:
    """Return the top_n claims most similar to `query`, each with provenance + edges."""
    if not _DB_PATH.exists():
        raise FileNotFoundError(
            f"{_DB_PATH} not found — build the graph first: python -m src.graph.build"
        )
    store = GraphStore(_DB_PATH, embed_dim=EMBED_DIM)
    claims = store.all_claims()
    if not claims:
        return []

    mat = np.asarray([list(c["emb"]) for c in claims], dtype=np.float32)
    qv = embed([query])[0]
    sims = mat @ qv  # both normalized -> cosine
    order = np.argsort(-sims)[:top_n]

    results: list[dict[str, Any]] = []
    for idx in order:
        c = claims[int(idx)]
        prov = store.claim_with_paper(c["id"]) or {}
        edges = store.related(c["id"])
        results.append(
            {
                "score": float(sims[int(idx)]),
                "claim": c["text"],
                "paper": prov.get("title"),
                "year": prov.get("year"),
                "url": prov.get("url"),
                "supports": [e for e in edges if e["rel_type"] == "SUPPORTS"],
                "contradicts": [e for e in edges if e["rel_type"] == "CONTRADICTS"],
            }
        )
    return results


def format_results(query: str, results: list[dict[str, Any]]) -> str:
    if not results:
        return f'No claims found for "{query}".'
    lines = [f'Top claims for "{query}":\n']
    for i, r in enumerate(results, 1):
        yr = f", {r['year']}" if r.get("year") else ""
        lines.append(f"{i}. ({r['score']:.2f}) {r['claim']}")
        lines.append(f"     — {r['paper']}{yr}")
        if r.get("url"):
            lines.append(f"       {r['url']}")
        for e in r["supports"][:3]:
            lines.append(f"     ⊕ supported by: {e['text'][:80]} ({e['title']})")
        for e in r["contradicts"][:3]:
            lines.append(f"     ⊗ contradicted by: {e['text'][:80]} ({e['title']})")
        lines.append("")
    return "\n".join(lines)
