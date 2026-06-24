"""R-005 step 1: dump candidate claim pairs (with paper context) for gold labeling.

    python -m src.graph.sample_pairs [--limit 50]

Reads the current ckg.kuzu, regenerates candidate pairs the same way build.py does
(cosine top-k via _candidate_pairs), and writes data/processed/candidate_pairs.jsonl with
each pair's claim texts and source paper titles — the input a human (or the LLM) labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

import numpy as np

from .build import CandidatePairs
from .embed import EMBED_DIM
from .store import GraphStore

_DB = Path(__file__).resolve().parents[2] / "data" / "ckg.kuzu"
_OUT = Path(__file__).resolve().parents[2] / "data" / "processed" / "candidate_pairs.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    store = GraphStore(_DB, embed_dim=EMBED_DIM)
    claims = store.all_claims()
    emb = np.asarray([list(c["emb"]) for c in claims], dtype=np.float32)
    pairs = CandidatePairs(emb)
    print(f"{len(claims)} claims -> {len(pairs)} candidate pairs")

    # title lookup per claim id
    title: dict[str, str] = {}
    for c in claims:
        prov = store.claim_with_paper(c["id"])
        title[c["id"]] = (prov or {}).get("title", "?")

    rows: list[dict[str, str | float]] = []
    for i, j, sim in pairs[: args.limit]:
        a, b = claims[i], claims[j]
        rows.append(
            {
                "a_id": a["id"], "b_id": b["id"], "similarity": round(sim, 3),
                "a_text": a["text"], "b_text": b["text"],
                "a_title": title[a["id"]], "b_title": title[b["id"]],
            }
        )
    _OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    print(f"wrote {len(rows)} pairs -> {_OUT}")
    # preview
    for k, r in enumerate(rows[:6]):
        a_title: str = cast(str, r['a_title'])
        b_title: str = cast(str, r['b_title'])
        a_text: str = cast(str, r['a_text'])
        b_text: str = cast(str, r['b_text'])
        print(f"\n[{k}] sim={r['similarity']}")
        print(f"  A ({a_title[:40]}): {a_text[:90]}")
        print(f"  B ({b_title[:40]}): {b_text[:90]}")


if __name__ == "__main__":
    main()
