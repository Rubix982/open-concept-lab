"""
E-014 → the AGREED direction: does representational geometry predict edit propagation,
hop-resolved, comparing raw-distance vs. structured (edit-difference) vs. alignment?

Scores each ENTAILED neighbour in scale_study.json (the real 397-row propagation ground
truth) with three pre-edit geometric predictors on gpt2-small (the model the edits were
done on), then reports AUC per predictor × hop (updated vs. not).

Predictors (all last-token reps, layer sweep):
  raw        cos(rep(edit_cloze), rep(neighbour))                 — the baseline
  structured cos(rep(neighbour), edit_direction)                 — edit-difference:
             edit_direction = rep(cloze+" "+target_new) − rep(cloze)
  alignment  cos(rep(neighbour), rep(target_new))                — Jeong/STEAM-style
             anchor = semantic vector of the new answer

Run in the analysis venv:
    .venv/bin/python experiments/edit_propagation/predict_scale.py
Out: results/final/tables/predict_scale.txt, results/final/figures/predict_scale_auc.png
"""
from __future__ import annotations

import json
from pathlib import Path

import torch
from sklearn.metrics import roc_auc_score
from transformers import AutoModelForCausalLM, AutoTokenizer

FINAL = Path(__file__).resolve().parent.parent.parent / "results" / "final"
rows = json.loads((FINAL / "data" / "scale_study.json").read_text())

MODEL = "gpt2"
LAYERS = [3, 6, 9, 12]                 # gpt2-small has 12 blocks (hidden_states 0..12)
ENTAILED = {"paraphrase", "1hop", "2hop"}

tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, output_hidden_states=True).eval()

_cache: dict[tuple[str, int], torch.Tensor] = {}


@torch.no_grad()
def rep(prompt: str, layer: int) -> torch.Tensor:
    key = (prompt, layer)
    if key not in _cache:
        ids = tok(prompt, return_tensors="pt")
        hs = model(**ids).hidden_states[layer][0, -1]     # last-token, this layer
        _cache[key] = hs / hs.norm()
    return _cache[key]


def cos(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.dot(a, b))                          # reps are pre-normalised


# ── score every entailed neighbour with each predictor, at each layer ──────────
data = [r for r in rows if r["type"] in ENTAILED]
labels = [1 if r["outcome"] == "updated" else 0 for r in data]

results: dict[int, dict[str, list[float]]] = {}
for L in LAYERS:
    raw, struct, align = [], [], []
    for r in data:
        cloze, tnew, nb = r["cloze"], r["target_new"], r["prompt"]
        rc, rn = rep(cloze, L), rep(nb, L)
        d = rep(f"{cloze} {tnew}", L) - rc
        d = d / (d.norm() + 1e-8)
        raw.append(cos(rc, rn))
        struct.append(cos(rn, d))
        align.append(cos(rn, rep(tnew, L)))
    results[L] = {"raw": raw, "structured": struct, "alignment": align}


def auc(scores: list[float], y: list[int]) -> float | None:
    if len(set(y)) < 2:
        return None
    return roc_auc_score(y, scores)


def hop_auc(pred_scores: list[float], hop: str | None) -> tuple[float | None, int, int]:
    idx = [i for i, r in enumerate(data) if hop is None or r["type"] == hop]
    y = [labels[i] for i in idx]
    s = [pred_scores[i] for i in idx]
    return auc(s, y), sum(y), len(y)


# ── report: best layer per predictor + per-hop AUC ─────────────────────────────
PREDS = ["raw", "structured", "alignment"]
HOPS = [None, "paraphrase", "1hop", "2hop"]
lines = [f"Does geometry predict propagation? AUC vs. real 'updated' label · {MODEL}",
         f"entailed neighbours n={len(data)} (updated={sum(labels)})  · layer sweep {LAYERS}",
         "AUC>0.5 = predictor separates propagated from not; ~0.5 = no signal.", ""]

# pick the layer maximising overall AUC per predictor
best = {}
for p in PREDS:
    scored = [(L, auc(results[L][p], labels)) for L in LAYERS]
    scored = [(L, a) for L, a in scored if a is not None]
    best[p] = max(scored, key=lambda t: t[1]) if scored else (None, None)

hdr = f"{'predictor':11s} {'bestL':>5} " + "".join(f"{(h or 'ALL'):>12}" for h in HOPS)
lines.append(hdr)
lines.append("-" * len(hdr))
for p in PREDS:
    L, _ = best[p]
    cells = []
    for h in HOPS:
        a, pos, n = hop_auc(results[L][p], h)
        cells.append(f"{a:.2f}({pos}/{n})" if a is not None else f"  -- ({pos}/{n})")
    lines.append(f"{p:11s} {L:>5} " + "".join(f"{c:>12}" for c in cells))

report = "\n".join(lines)
(FINAL / "tables" / "predict_scale.txt").write_text(report)
print(report)

# ── figure: overall + per-hop AUC bars per predictor (best layer) ──────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"figure.facecolor": "#0F1320", "axes.facecolor": "#0F1320",
                     "text.color": "#EAECF4", "axes.labelcolor": "#EAECF4",
                     "xtick.color": "#EAECF4", "ytick.color": "#8A93A8", "font.size": 11})
COLORS = {"raw": "#8A93A8", "structured": "#7C9CFF", "alignment": "#F6A96B"}
hop_labels = ["ALL", "paraphrase", "1hop", "2hop"]
x = np.arange(len(hop_labels)); w = 0.26
fig, ax = plt.subplots(figsize=(9, 4.8))
for j, p in enumerate(PREDS):
    L, _ = best[p]
    ys = []
    for h in HOPS:
        a, _, _ = hop_auc(results[L][p], h)
        ys.append(a if a is not None else 0)
    ax.bar(x + (j - 1) * w, ys, w, label=f"{p} (L{L})", color=COLORS[p], edgecolor="#0F1320")
ax.axhline(0.5, color="#F58AA0", ls="--", lw=1, label="chance (0.5)")
ax.set_xticks(x); ax.set_xticklabels(hop_labels)
ax.set_ylim(0, 1); ax.set_ylabel("AUC (predict 'updated')")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color("#2A3247")
ax.set_title(f"Does geometry predict propagation? · {MODEL} · n={len(data)} entailed neighbours\n"
             f"raw-distance vs. structured (edit-diff) vs. alignment — vs. real labels",
             fontsize=12, pad=12)
ax.legend(ncol=2, frameon=False, labelcolor="#EAECF4", fontsize=9)
fig.text(0.5, 0.005, "1hop has few positives (2/46) → its AUC is unreliable; ALL and "
         "paraphrase are the trustworthy cells.", ha="center", color="#8A93A8",
         fontsize=8, style="italic")
plt.tight_layout(rect=(0, 0.04, 1, 1))
out = FINAL / "figures" / "predict_scale_auc.png"
fig.savefig(out, dpi=150, bbox_inches="tight")
print(f"\nSaved → {out}, {FINAL/'tables'/'predict_scale.txt'}")
