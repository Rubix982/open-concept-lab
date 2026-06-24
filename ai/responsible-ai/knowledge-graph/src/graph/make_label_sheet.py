"""R-005 step 1b: turn candidate_pairs.jsonl into a human labeling sheet.

    python -m src.graph.make_label_sheet

Dedups pairs by (a_text, b_text) content, writes:
  - data/processed/gold_pairs.jsonl   (indexed, machine-readable — eval joins on `id`)
  - data/processed/gold_edges_sheet.md (fill in one RELATION per pair)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_IN = _PROC / "candidate_pairs.jsonl"
_PAIRS = _PROC / "gold_pairs.jsonl"
_SHEET = _PROC / "gold_edges_sheet.md"

_LEGEND = """# Gold edge labeling sheet

For each pair, write ONE label after `RELATION:` from this set (A→B direction):

- SUPPORTS                — A's result/evidence backs B's claim
- CONTRADICTS             — A's finding is logically incompatible with B's
- REFINES                 — A improves / generalizes / extends B's method or result
- ADDRESSES_SAME_PROBLEM  — A and B tackle the same problem, different approaches (symmetric)
- USES                    — A uses a method/dataset/result introduced by B
- RELATED                 — same topic, no stronger typed relation (symmetric)
- NONE                    — not meaningfully related (should be pruned)

Just fill the RELATION line. Direction is secondary — assume A→B; for a clearly
backwards directional case you may write e.g. `REFINES (B→A)`.
"""


def main() -> None:
    rows: list[dict[str, Any]] = [
        json.loads(l) for l in _IN.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    seen: set[frozenset[str]] = set()
    deduped: list[dict[str, Any]] = []
    for r in rows:
        key = frozenset((r["a_text"], r["b_text"]))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    for i, r in enumerate(deduped):
        r["id"] = i
    _PAIRS.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in deduped) + "\n"
    )

    out = [_LEGEND, f"\n_{len(deduped)} pairs to label (deduped from {len(rows)})._\n"]
    for r in deduped:
        out.append(
            f"\n## [{r['id']}]  (cosine similarity {r['similarity']})\n"
            f"**A** — _{r['a_title']}_\n"
            f"> {r['a_text']}\n\n"
            f"**B** — _{r['b_title']}_\n"
            f"> {r['b_text']}\n\n"
            f"RELATION: \n"
        )
    _SHEET.write_text("".join(out))
    print(f"{len(deduped)} unique pairs (from {len(rows)})")
    print(f"wrote {_PAIRS}")
    print(f"wrote {_SHEET}  <- fill in the RELATION lines")


if __name__ == "__main__":
    main()
