"""
E-013 (T-B) — Does the geometry predictor predict REAL propagation?

Loads per-neighbour rows {type, propagated 0/1, predictor} from the edit run and
asks, against ground-truth labels (not a proxy): do neighbours the edit REACHED
sit closer (higher predictor) than the ones it missed?

Reports, overall and per hop type:
  - mean predictor for propagated vs. not-propagated
  - AUC (predictor ranks propagated above not) — 0.5 = no signal, 1.0 = perfect
Small n on gpt2-small → indicative, not conclusive. The point is the METHOD:
predictor measured against a real causal outcome.

Usage:  python experiments/edit_propagation/analyze_tb.py
"""

import json
from pathlib import Path

from ripplekit import config

rows = json.loads((config.RESULTS_DIR / "tb_rows.json").read_text())
print(f"{len(rows)} neighbour rows\n")


def auc(pos, neg):
    """P(predictor(propagated) > predictor(not)) — rank-based AUC."""
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def report(label, subset):
    prop = [r["predictor"] for r in subset if r["propagated"] == 1]
    nopr = [r["predictor"] for r in subset if r["propagated"] == 0]
    mp = sum(prop) / len(prop) if prop else float("nan")
    mn = sum(nopr) / len(nopr) if nopr else float("nan")
    a = auc(prop, nopr)
    print(f"{label:14s} n={len(subset):>3} (prop {len(prop)}/{len(subset)})  "
          f"mean pred: propagated={mp:.3f} vs missed={mn:.3f}  AUC={a:.3f}")


print("Does higher predictor (representational closeness) → propagation?")
print("(AUC > 0.5 = closer neighbours propagate more; = the thesis signal)\n")
report("ALL", rows)
print()
for t in config.TYPES:
    sub = [r for r in rows if r["type"] == t]
    if sub:
        report(t, sub)

print("\nRead: AUC meaningfully > 0.5 (esp. within a hop type) = geometry predicts")
print("which neighbours the edit reached. ~0.5 = raw closeness doesn't forecast it")
print("→ motivates structured predictors (bilinear / edit-difference) next.")
