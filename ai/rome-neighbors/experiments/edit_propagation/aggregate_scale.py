"""
E-014 aggregate: turn scale_study.json (random-sample ripple run) into shareable,
rigorous artifacts — distribution figure + summary with 95% CIs + target-bleed
(over-propagation) rate + concrete failure examples.

Run in the analysis venv:
    .venv/bin/python experiments/edit_propagation/aggregate_scale.py
Out: final/figures/scale_distribution.png, scale_summary.txt, scale_examples.txt
"""
import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS = Path(__file__).resolve().parent.parent.parent / "results"
DATA = RESULTS / "final" / "data"
TABLES = RESULTS / "final" / "tables"
FIGS = RESULTS / "final" / "figures"
for d in (DATA, TABLES, FIGS):
    d.mkdir(parents=True, exist_ok=True)
rows = json.loads((DATA / "scale_study.json").read_text())

ORDER = ["updated", "stale", "broken", "fine"]
COLOR = {"updated": "#6FD39A", "stale": "#F6A96B", "broken": "#F58AA0", "fine": "#7C9CFF"}
TYPES = ["paraphrase", "1hop", "2hop", "locality", "control"]


def wilson(k, n, z=1.96):
    """95% Wilson score interval for a proportion — honest for small/large n."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def has(a, b):
    if not a or not b or not b.strip():
        return False
    return b.strip().lower()[:12] in a.lower()


by = defaultdict(Counter)
for r in rows:
    by[r["type"]][r["outcome"]] += 1
n_edits = len(set(r["edit"] for r in rows))

# target-bleed / over-propagation: a BROKEN neighbour whose post = the edit's target
bleed = defaultdict(lambda: [0, 0])   # type -> [bleed_broken, total_broken]
for r in rows:
    if r["outcome"] == "broken":
        bleed[r["type"]][1] += 1
        if has(r["post"], r["target_new"]):
            bleed[r["type"]][0] += 1

# ── summary with CIs ──────────────────────────────────────────────────────────
lines = ["scale ripple run · gpt2-small · ROME(mom2) · RANDOM RippleEdits(popular) · seed=1538",
         f"flipped_edits={n_edits}  neighbour_rows={len(rows)}  (rates ± 95% Wilson CI)", ""]
for t in TYPES:
    c = by[t]; n = sum(c.values())
    if not n:
        continue
    lines.append(f"  {t} (n={n}):")
    for o in ORDER:
        if c[o]:
            p, lo, hi = wilson(c[o], n)
            lines.append(f"      {o:8s} {c[o]:>3}  {p:>4.0%}  [{lo:.0%}, {hi:.0%}]")
    bb, tb = bleed[t]
    if tb:
        p, lo, hi = wilson(bb, tb)
        lines.append(f"      └ of the broken, {bb}/{tb} = {p:.0%} are TARGET-BLEED "
                     f"(edit's new value injected) [{lo:.0%}, {hi:.0%}]")
lines += [
    "",
    "note: locality here = RippleEdits Relation_Specificity (SAME edited subject,",
    "      different relation) — ROME's HARDEST specificity case (subject-token key is",
    "      shared). n=3 after the competence filter (gpt2-small knows almost none of",
    "      these facts) → NOT measurable. Distinct-subject specificity (ROME's actual",
    "      strength, ~90 in MEMIT) is a different, easier test and is UNMEASURED here.",
]
summary = "\n".join(lines)
(TABLES / "scale_summary.txt").write_text(summary)
print(summary)

# ── concrete failure examples (real rows) ─────────────────────────────────────
rng = random.Random(0)
ex = ["CONCRETE EXAMPLES (real rows from scale_study.json)\n" + "=" * 60]


def sample(pred, k, label):
    hits = [r for r in rows if pred(r)]
    rng.shuffle(hits)
    out = [f"\n{label}  ({len(hits)} total; showing {min(k, len(hits))}):"]
    for r in hits[:k]:
        out.append(f"  · [{r['type']}] {r['prompt']!r}")
        out.append(f"      expected={r['expected']!r}  pre={r['pre']!r}  post={r['post']!r}"
                   f"  (edit target={r['target_new']!r})")
    return "\n".join(out)


ex.append(sample(lambda r: r["type"] in ("1hop", "2hop") and r["outcome"] == "stale",
                 4, "STALE entailed (edit didn't reach it)"))
ex.append(sample(lambda r: r["outcome"] == "broken" and has(r["post"], r["target_new"]),
                 4, "TARGET-BLEED / OVER-PROPAGATION (edit's value injected)"))
ex.append(sample(lambda r: r["outcome"] == "broken" and not has(r["post"], r["target_new"]),
                 4, "BROKEN incoherent (neither old, new, nor target)"))
ex.append(sample(lambda r: r["type"] == "paraphrase" and r["outcome"] == "updated",
                 3, "UPDATED paraphrase (clean generalization)"))
(TABLES / "scale_examples.txt").write_text("\n".join(ex))
print("\nSaved examples → final/tables/scale_examples.txt")

# ── figure ────────────────────────────────────────────────────────────────────
plt.rcParams.update({"figure.facecolor": "#0F1320", "axes.facecolor": "#0F1320",
                     "text.color": "#EAECF4", "axes.labelcolor": "#EAECF4",
                     "xtick.color": "#8A93A8", "ytick.color": "#EAECF4", "font.size": 11})
# figure shows ENTAILED types only; locality/control excluded (n too small to plot —
# see footnote). They remain in scale_summary.txt with the honest caveat.
FIG_TYPES = ["paraphrase", "1hop", "2hop"]
present = [t for t in FIG_TYPES if sum(by[t].values())]
fig, ax = plt.subplots(figsize=(10, 0.9 * len(present) + 2.0))
for i, t in enumerate(present):
    c = by[t]; n = sum(c.values()); left = 0
    for o in ORDER:
        frac = c[o] / n
        if frac <= 0:
            continue
        ax.barh(i, frac, left=left, color=COLOR[o], edgecolor="#0F1320")
        if frac > 0.06:
            ax.text(left + frac / 2, i, f"{frac:.0%}", ha="center", va="center",
                    color="#0F1320", fontweight="bold", fontsize=10)
        left += frac
    ax.text(1.015, i, f"n={n}", va="center", color="#8A93A8", fontsize=10)
ax.set_yticks(range(len(present))); ax.set_yticklabels(present)
ax.set_xlim(0, 1); ax.set_xlabel("share of neighbours"); ax.invert_yaxis()
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title(f"ROME edit → neighbour outcomes · RANDOM RippleEdits sample\n"
             f"{n_edits} edits · {len(rows)} neighbours · gpt2-small · seed 1538 (no cherry-picking)",
             color="#EAECF4", fontsize=12, pad=14)
handles = [plt.Rectangle((0, 0), 1, 1, color=COLOR[o]) for o in ORDER[:3]]
ax.legend(handles, ORDER[:3], ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22),
          frameon=False, labelcolor="#EAECF4")
n_loc = sum(by["locality"].values())
fig.text(0.5, 0.005,
         f"locality/specificity excluded: n={n_loc} after competence filter "
         f"(gpt2-small knows too few facts) — not measurable; needs a capable model.",
         ha="center", color="#8A93A8", fontsize=9, style="italic")
plt.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(FIGS / "scale_distribution.png", dpi=150, bbox_inches="tight")
print(f"Saved figure → final/figures/scale_distribution.png")
