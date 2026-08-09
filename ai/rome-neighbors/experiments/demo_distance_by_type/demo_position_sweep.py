"""
E-008 — Position/layer sweep: is E-007's flat raw-distance signal a SINK artifact?

E-007 found raw last-token cosine ≈ flat (~0.6) across neighbour types. But our
own 03/12 findings say the LAST token is sink-dominated (attention sinks on
token 0; the last-token residual is largely shared template). So the flatness may
be a POSITION artifact, not a truth about raw distance.

This script re-runs the RippleEdits similarity-by-type pipeline comparing TWO
representation strategies — LAST token vs MEAN-pooled over prompt tokens — across
a LAYER sweep. If mean-pool (or some layer) separates propagate-types from
locality where last-token did not, the flatness was the sink. If it stays flat,
raw distance is genuinely weak. Either way it hardens design.md construct validity.

Usage:
    python experiments/demo_distance_by_type/demo_position_sweep.py
"""

import json
import os
import random
from pathlib import Path
from typing import Any

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

DATA_PATH = Path(os.environ.get(
    "RIPPLEEDITS_FILE",
    str(Path.home() / "code" / "RippleEdits" / "data" / "benchmark" / "popular.json"),
))
OUT_DIR = Path("experiments/demo_distance_by_type/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SWEEP_LAYERS = [6, 9, 12, 15, 18]
N_EDITS = 40
MAX_PER_CRITERION = 3
SEED = 1538
TYPES = ["paraphrase", "1hop", "2hop", "locality", "control"]

CRITERION_TO_TYPE = {
    "logical_generalization": "1hop", "compositionality_i": "2hop",
    "compositionality_ii": "2hop", "subject_aliasing": "paraphrase",
    "relation_specifity": "locality", "relation_specificity": "locality",
    "forgetfulness": "control",
}


def norm_key(k: str) -> str:
    return k.strip().lower().replace(" ", "_")


def load_pairs(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = json.loads(path.read_text())
    random.Random(SEED).shuffle(entries)
    pairs: list[dict[str, Any]] = []
    for e in entries[:N_EDITS]:
        base = (e.get("edit") or {}).get("prompt")
        if not base:
            continue
        for key, val in e.items():
            ntype = CRITERION_TO_TYPE.get(norm_key(key))
            if ntype is None or not isinstance(val, list):
                continue
            prompts: list[str] = []
            for group in val:
                if isinstance(group, dict):
                    for q in group.get("test_queries") or []:
                        p = q.get("prompt") if isinstance(q, dict) else None
                        if p:
                            prompts.append(p)
            for p in prompts[:MAX_PER_CRITERION]:
                pairs.append({"base": base, "neighbour": p, "type": ntype})
    return pairs


model = LanguageModel("EleutherAI/gpt-j-6b")
pairs = load_pairs(DATA_PATH)
print(f"{len(pairs)} pairs · layers {SWEEP_LAYERS} · last vs mean-pool\n")

# cache per prompt: dict[prompt] -> {"last": [n_layers, d], "mean": [n_layers, d]}
_cache: dict[str, dict[str, torch.Tensor]] = {}


def vectors(prompt: str) -> dict[str, torch.Tensor]:
    if prompt not in _cache:
        with model.trace(prompt, remote=True):                         # type: ignore[union-attr]
            lasts, means = [], []
            for L in SWEEP_LAYERS:
                resid = model.transformer.h[L].output[0][0]            # type: ignore[index]  [seq, d]
                lasts.append(resid[-1])
                means.append(resid.mean(dim=0))
            last_stack = torch.stack(lasts).save()                      # [n_layers, d]
            mean_stack = torch.stack(means).save()
        _cache[prompt] = {"last": last_stack, "mean": mean_stack}
    return _cache[prompt]


def cos(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0))


# results[strategy][layer_idx][type] -> list of cosines
results: dict[str, list[dict[str, list[float]]]] = {
    s: [{t: [] for t in TYPES} for _ in SWEEP_LAYERS] for s in ("last", "mean")
}

for i, pr in enumerate(pairs):
    bv, nv = vectors(pr["base"]), vectors(pr["neighbour"])
    for strat in ("last", "mean"):
        for li in range(len(SWEEP_LAYERS)):
            results[strat][li][pr["type"]].append(cos(bv[strat][li], nv[strat][li]))
    if i % 40 == 0:
        print(f"  ...{i}/{len(pairs)}")


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


# ── tables ────────────────────────────────────────────────────────────────────
for strat in ("last", "mean"):
    print(f"\n── strategy: {strat} — mean cosine by type × layer ──")
    print("layer  " + "".join(f"{t[:6]:>9}" for t in TYPES) + f"{'sep*':>9}")
    for li, L in enumerate(SWEEP_LAYERS):
        row = results[strat][li]
        cells = "".join(f"{mean(row[t]):>9.3f}" for t in TYPES)
        # separation* = mean(propagate types) - locality ; >0 means distance is informative
        prop = mean(row["paraphrase"] + row["1hop"] + row["2hop"])
        sep = prop - mean(row["locality"])
        print(f"{L:>5}  {cells}{sep:>9.3f}")

print("\nsep* = mean(paraphrase+1hop+2hop) − locality. If sep* is ~0 everywhere,")
print("raw distance is genuinely flat. If mean-pool or some layer lifts sep* well")
print("above 0, the last-token flatness (E-007) was the attention-sink artifact.")

# ── plot: cos-by-type vs layer, one panel per strategy ─────────────────────────
try:
    import matplotlib.pyplot as plt

    colors = {"paraphrase": "#4fc3f7", "1hop": "#6fcf97", "2hop": "#ffb74d",
              "locality": "#e57373", "control": "#ce93d8"}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), facecolor="#0a0c0f")
    for ax, strat in zip(axes, ("last", "mean")):
        ax.set_facecolor("#0f1318")
        for t in TYPES:
            ys = [mean(results[strat][li][t]) for li in range(len(SWEEP_LAYERS))]
            ax.plot(SWEEP_LAYERS, ys, marker="o", color=colors[t], label=t, linewidth=2)
        ax.set_title(f"{strat}-token", color="#c8d4e0")
        ax.set_xlabel("layer", color="#4a5568")
        ax.set_ylabel("mean cosine (base ↔ neighbour)", color="#4a5568")
        ax.tick_params(colors="#4a5568")
        for s in ax.spines.values():
            s.set_color("#1e2530")
    axes[1].legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    fig.suptitle(f"Does position/layer separate neighbour types? — GPT-J, RippleEdits "
                 f"(n={len(pairs)})", color="#e8dcc8")
    out = OUT_DIR / "position_layer_sweep.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"\nPlot saved → {out}")
except ImportError:
    print("\n(matplotlib not installed — tables above are complete)")
