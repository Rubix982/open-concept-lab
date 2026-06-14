"""Build the claim knowledge graph from ingested sentences.

Pipeline (E-003):
  sentences.jsonl + papers.jsonl
    -> classify (keep CLAIM)
    -> embed claims
    -> store Claim/Paper nodes (Kùzu) with provenance
    -> candidate pairs by cosine similarity (top-k, thresholded)
    -> type each pair via NLI -> SUPPORTS / CONTRADICTS / RELATED
    -> store typed edges

    python -m src.graph.build [--limit-claims N]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from .embed import EMBED_DIM, embed
from .edges import type_pairs
from .store import GraphStore

_ROOT = Path(__file__).resolve().parents[2]
_PROCESSED = _ROOT / "data" / "processed"
_DB_PATH = _ROOT / "data" / "ckg.kuzu"

# Edge-construction knobs.
MIN_CLAIM_CONF = 0.50   # keep CLAIM predictions at/above this confidence
TOP_K = 5               # candidate neighbors per claim
SIM_THRESHOLD = 0.55    # min cosine similarity to be a candidate
DUP_THRESHOLD = 0.985   # skip near-identical pairs (ingestion duplicates)


def _make_tagger(name: str):
    """Return a tagger with a `.tag(texts) -> [(label, conf)]` interface."""
    if name == "llm":
        from ..extraction.llm_predict import LLMClaimTagger

        return LLMClaimTagger()
    if name == "distilbert":
        from ..extraction.predict import ClaimTagger

        return ClaimTagger()
    raise ValueError(f"unknown tagger: {name!r} (use 'llm' or 'distilbert')")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]


def _claim_id(rec: dict[str, Any]) -> str:
    return f"{rec['paper_id']}::{rec['section']}{rec['sentence_index']}"


def _candidate_pairs(emb: np.ndarray) -> list[tuple[int, int, float]]:
    """Unordered (i, j, cosine) candidate pairs via top-k over normalized embeddings."""
    sim = emb @ emb.T  # cosine (rows normalized)
    n = sim.shape[0]
    seen: set[tuple[int, int]] = set()
    pairs: list[tuple[int, int, float]] = []
    for i in range(n):
        order = np.argsort(-sim[i])
        taken = 0
        for j in order:
            j = int(j)
            if j == i:
                continue
            s = float(sim[i, j])
            if s < SIM_THRESHOLD:
                break
            if s >= DUP_THRESHOLD:
                continue  # near-duplicate sentence, not an informative edge
            key = (min(i, j), max(i, j))
            if key not in seen:
                seen.add(key)
                pairs.append((key[0], key[1], s))
            taken += 1
            if taken >= TOP_K:
                break
    return pairs


def build(limit_claims: int | None = None, tagger: str = "llm") -> dict[str, int]:
    sentences = _load_jsonl(_PROCESSED / "sentences.jsonl")
    papers = {p["paper_id"]: p for p in _load_jsonl(_PROCESSED / "papers.jsonl")}

    print(f"Classifying {len(sentences)} sentences with '{tagger}' tagger...")
    labels = _make_tagger(tagger).tag([s["text"] for s in sentences])

    claims = [
        rec
        for rec, (label, conf) in zip(sentences, labels)
        if label == "CLAIM" and conf >= MIN_CLAIM_CONF
    ]
    if limit_claims:
        claims = claims[:limit_claims]
    print(f"Kept {len(claims)} CLAIM sentences (conf >= {MIN_CLAIM_CONF}).")
    if not claims:
        raise RuntimeError("No claims found — check the classifier / thresholds.")

    print("Embedding claims...")
    emb = embed([c["text"] for c in claims])

    store = GraphStore(_DB_PATH, embed_dim=EMBED_DIM, fresh=True)
    used_papers = {c["paper_id"] for c in claims}
    for pid in used_papers:
        if pid in papers:
            store.add_paper(papers[pid])
    for rec, vec in zip(claims, emb):
        store.add_claim(
            _claim_id(rec),
            rec["text"],
            rec["paper_id"],
            rec["section"],
            rec["char_start"],
            rec["char_end"],
            vec.tolist(),
        )

    print("Finding candidate pairs...")
    cand = _candidate_pairs(emb)
    print(f"{len(cand)} candidate pairs -> typing with NLI...")
    typed = type_pairs([(claims[i]["text"], claims[j]["text"]) for i, j, _ in cand])
    for (i, j, sim), (rel_type, score) in zip(cand, typed):
        store.add_relation(_claim_id(claims[i]), _claim_id(claims[j]), rel_type, score, sim)

    counts = store.counts()
    print(f"\nBuilt {_DB_PATH.name}: {counts}")

    # Spot-check a few SUPPORTS / CONTRADICTS edges.
    print("\nSample typed edges:")
    res = store.con.execute(
        "MATCH (a:Claim)-[r:RELATES]->(b:Claim)"
        " WHERE r.rel_type IN ['SUPPORTS','CONTRADICTS']"
        " RETURN r.rel_type, r.score, a.text, b.text LIMIT 8"
    )
    while res.has_next():
        rt, score, a, b = res.get_next()
        print(f"  [{rt} {score:.2f}] {a[:60]!r} -> {b[:60]!r}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-claims", type=int, default=None)
    parser.add_argument(
        "--tagger", choices=["llm", "distilbert"], default="llm",
        help="claim classifier: 'llm' (Claude, default) or 'distilbert'",
    )
    args = parser.parse_args()
    build(limit_claims=args.limit_claims, tagger=args.tagger)


if __name__ == "__main__":
    main()
