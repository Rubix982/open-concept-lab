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

# ── T-015: 3-way outcome + subject-sharing ─────────────────────────────────────
if rows and "outcome" in rows[0]:
    from collections import Counter
    print("\n" + "=" * 60)
    print("T-015 · 3-way outcome (updated / stale / broken) by neighbour type")
    print("=" * 60)
    for t in ["ALL"] + config.TYPES:
        sub = rows if t == "ALL" else [r for r in rows if r["type"] == t]
        if not sub:
            continue
        c = Counter(r["outcome"] for r in sub)
        print(f"  {t:12s} n={len(sub):>3}  updated={c['updated']:>3}  "
              f"stale={c['stale']:>3}  broken={c['broken']:>3}")

    print("\nT-015 · subject-sharing hypothesis (Liu: shared-subject → over-written/broken)")
    for share in (1, 0):
        sub = [r for r in rows if r.get("subject_shared") == share]
        if not sub:
            continue
        c = Counter(r["outcome"] for r in sub)
        lab = "SHARES edit subject" if share else "different subject"
        n = len(sub)
        print(f"  {lab:20s} n={n:>3}  "
              f"updated={c['updated']/n:.0%}  stale={c['stale']/n:.0%}  broken={c['broken']/n:.0%}")
    print("\nRead: if shared-subject neighbours are disproportionately BROKEN and")
    print("different-subject ones STALE, that's a concrete, explainable rule for the")
    print("pre-flight diagnostic (which facts an edit will corrupt vs. leave un-updated).")
