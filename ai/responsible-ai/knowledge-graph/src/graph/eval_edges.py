"""R-005 step 3: NLI-vs-LLM edge-typing eval against the user-labeled gold set.

    python -m src.graph.eval_edges

Reads the filled labeling sheet (data/processed/gold_edges_sheet.md), joins to
gold_pairs.jsonl, runs both typers, and reports:
  - exact-match accuracy (note: NLI can only emit SUPPORTS/CONTRADICTS/RELATED, so it
    structurally cannot hit REFINES/ADDRESSES_SAME_PROBLEM/USES/NONE),
  - the headline FALSE-CONTRADICTS rate (gold != CONTRADICTS but predicted CONTRADICTS),
  - the NONE-pruning rate (gold == NONE correctly pruned).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_PROC = Path(__file__).resolve().parents[2] / "data" / "processed"
_SHEET = _PROC / "gold_edges_sheet.md"
_PAIRS = _PROC / "gold_pairs.jsonl"

_VALID = {
    "SUPPORTS", "CONTRADICTS", "REFINES", "ADDRESSES_SAME_PROBLEM",
    "USES", "RELATED", "NONE",
}


def _parse_sheet() -> dict[int, str]:
    """Return {pair_id: gold_relation} for entries with a filled RELATION line."""
    labels: dict[int, str] = {}
    cur: int | None = None
    for line in _SHEET.read_text(encoding="utf-8").splitlines():
        m = re.match(r"##\s*\[(\d+)\]", line)
        if m:
            cur = int(m.group(1))
            continue
        if cur is not None and line.strip().upper().startswith("RELATION:"):
            val = line.split(":", 1)[1].strip().upper()
            token = val.split()[0] if val else ""  # drop any "(B→A)" suffix
            if token in _VALID:
                labels[cur] = token
            cur = None
    return labels


def main() -> None:
    gold = _parse_sheet()
    pairs = {r["id"]: r for r in (json.loads(l) for l in _PAIRS.read_text().splitlines() if l.strip())}
    ids = sorted(gold)
    if not ids:
        print(f"No filled RELATION lines in {_SHEET}. Label some pairs first.")
        return
    print(f"{len(ids)} labeled pairs (of {len(pairs)} in the sheet)\n")

    rows = [pairs[i] for i in ids]
    golds = [gold[i] for i in ids]

    preds: dict[str, list[str]] = {}
    # NLI
    try:
        from .edges import type_pairs
        nli = type_pairs([(r["a_text"], r["b_text"]) for r in rows])
        preds["NLI (distilbert-mnli)"] = [t for t, _ in nli]
    except Exception as e:  # noqa: BLE001
        print(f"NLI skipped: {e}")
    # LLM
    try:
        from .llm_edges import LLMEdgeTyper
        eval_model = "claude-opus-4-8"  # evals run the quality-ceiling model
        llm = LLMEdgeTyper(model=eval_model).type_pairs(rows)
        preds[f"LLM ({eval_model})"] = [o["relation"] for o in llm]
    except Exception as e:  # noqa: BLE001
        print(f"LLM skipped: {e}")

    n = len(golds)
    non_contra = sum(1 for g in golds if g != "CONTRADICTS")
    n_none = sum(1 for g in golds if g == "NONE")
    for name, pr in preds.items():
        exact = sum(p == g for p, g in zip(pr, golds)) / n
        false_contra = sum(
            1 for p, g in zip(pr, golds) if p == "CONTRADICTS" and g != "CONTRADICTS"
        )
        fc_rate = false_contra / non_contra if non_contra else 0.0
        none_ok = sum(1 for p, g in zip(pr, golds) if g == "NONE" and p == "NONE")
        none_rate = none_ok / n_none if n_none else float("nan")
        print(f"### {name}")
        print(f"  exact-match accuracy : {exact:.3f}")
        print(f"  false-CONTRADICTS    : {false_contra}/{non_contra}  (rate {fc_rate:.3f})")
        print(f"  NONE pruned correctly: {none_ok}/{n_none}  (rate {none_rate:.3f})")
        print()


if __name__ == "__main__":
    main()
