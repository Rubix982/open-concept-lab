"""
E-009 — Structured predictor v1: Jeong-style semantic alignment (GPT-J / NDIF)

Chases the thesis (T-006): does STRUCTURED geometry separate neighbour types
where raw distance was flat (E-007's ~0.6 for everything)?

Structured predictor = semantic ALIGNMENT (Jeong/STEAM, formula adopted in
design.md §5). For a neighbour with gold answer o:
  anchor φ(o) = mean representation of K reference prompts (from RippleEdits
                itself) whose gold answer is also o  [excludes the neighbour]
  alignment   = cos( rep(neighbour_prompt) , φ(o) )
Head-to-head against raw base↔neighbour cosine, aggregated by neighbour type.

Representation = MEAN-POOL over tokens at a mid layer (avoids the last-token
sink that confounded E-007; E-008 sweeps the best position/layer).

HONEST SCOPE: predictor half only. Alignment-by-type tests whether structure
carries signal raw distance missed — NOT yet whether it predicts PROPAGATION.
Causal outcome (IIA per neighbour) is E-010, the required companion.

Usage:  python experiments/demo_distance_by_type/demo_alignment.py
"""

import json
import os
import random
from collections import defaultdict
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
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAYER = 15
N_EDITS = 40
MAX_PER_CRITERION = 3
K_ANCHOR = 3          # reference prompts averaged into each answer anchor
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


def answer_of(q: dict[str, Any]) -> str | None:
    anss = q.get("answers") or []
    return anss[0].get("value") if anss and isinstance(anss[0], dict) else None


# ── build answer → reference prompts map (whole file) + the typed pairs ─────────
all_entries: list[dict[str, Any]] = json.loads(DATA_PATH.read_text())
ans2prompts: dict[str, set[str]] = defaultdict(set)
for entry in all_entries:
    for key, val in entry.items():
        if not isinstance(val, list):
            continue
        for group in val:
            if not isinstance(group, dict):
                continue
            for q in group.get("test_queries") or []:
                a, p = answer_of(q), q.get("prompt")
                if a and p:
                    ans2prompts[a].add(p)

random.Random(SEED).shuffle(all_entries)
pairs: list[dict[str, Any]] = []
for e in all_entries[:N_EDITS]:
    base = (e.get("edit") or {}).get("prompt")
    if not base:
        continue
    for key, val in e.items():
        ntype = CRITERION_TO_TYPE.get(norm_key(key))
        if ntype is None or not isinstance(val, list):
            continue
        collected: list[tuple[str, str]] = []
        for group in val:
            if isinstance(group, dict):
                for q in group.get("test_queries") or []:
                    p, a = q.get("prompt"), answer_of(q)
                    if p and a:
                        collected.append((p, a))
        for p, a in collected[:MAX_PER_CRITERION]:
            pairs.append({"base": base, "neighbour": p, "answer": a, "type": ntype})

model = LanguageModel("EleutherAI/gpt-j-6b")
print(f"{len(pairs)} pairs · layer {LAYER} · mean-pool · K_anchor={K_ANCHOR}\n")

_cache: dict[str, torch.Tensor] = {}


def rep(prompt: str) -> torch.Tensor:
    if prompt not in _cache:
        with model.trace(prompt, remote=True):                        # type: ignore[union-attr]
            v = model.transformer.h[LAYER].output[0][0].mean(dim=0).save()  # type: ignore[index]
        _cache[prompt] = v
    return _cache[prompt]


def anchor(ans: str, exclude: str) -> torch.Tensor | None:
    refs = [p for p in ans2prompts.get(ans, set()) if p != exclude]
    if len(refs) < K_ANCHOR:
        return None
    refs = sorted(refs)[:K_ANCHOR]
    return torch.stack([rep(p) for p in refs]).mean(dim=0)


def cos(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.nn.functional.cosine_similarity(a, b, dim=0))


# ── compute alignment + raw distance per pair ──────────────────────────────────
align_by: dict[str, list[float]] = {t: [] for t in TYPES}
raw_by: dict[str, list[float]] = {t: [] for t in TYPES}

for i, pr in enumerate(pairs):
    nv = rep(pr["neighbour"])
    raw_by[pr["type"]].append(cos(rep(pr["base"]), nv))
    phi = anchor(pr["answer"], pr["neighbour"])
    if phi is not None:
        align_by[pr["type"]].append(cos(nv, phi))
    if i % 40 == 0:
        print(f"  ...{i}/{len(pairs)}")


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


print("\n── raw distance vs. structured alignment, by type ──────────")
print(f"{'type':12s}  {'raw cos':>9}  {'align n':>8}  {'alignment':>10}")
print("─" * 44)
for t in TYPES:
    print(f"{t:12s}  {mean(raw_by[t]):>9.3f}  {len(align_by[t]):>8}  {mean(align_by[t]):>10.3f}")

# separation metric: propagate-types minus locality (higher = predictor informative)
def sep(d: dict[str, list[float]]) -> float:
    prop = d["paraphrase"] + d["1hop"] + d["2hop"]
    return mean(prop) - mean(d["locality"])

print(f"\nsep(raw)       = {sep(raw_by):+.3f}")
print(f"sep(alignment) = {sep(align_by):+.3f}")
print("\nThesis check: if sep(alignment) >> sep(raw) (~0), structured geometry")
print("carries the relational signal raw distance missed. (Predictor half only —")
print("propagation prediction needs the causal outcome in E-010.)")

# ── plot ────────────────────────────────────────────────────────────────────────
try:
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(8.5, 4.5), facecolor="#0a0c0f")
    ax.set_facecolor("#0f1318")
    x = np.arange(len(TYPES)); w = 0.38
    ax.bar(x - w / 2, [mean(raw_by[t]) for t in TYPES], w, color="#e57373", label="raw distance (E-007)")
    ax.bar(x + w / 2, [mean(align_by[t]) for t in TYPES], w, color="#4fc3f7", label="structured alignment")
    ax.set_xticks(x); ax.set_xticklabels(TYPES, color="#c8d4e0")
    ax.tick_params(colors="#4a5568")
    for s in ax.spines.values():
        s.set_color("#1e2530")
    ax.set_title(f"Raw distance vs. structured alignment by type — GPT-J L{LAYER} "
                 f"(n={len(pairs)})", color="#c8d4e0", fontsize=11)
    ax.legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    out = OUT_DIR / "alignment_vs_rawdist.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"\nPlot saved → {out}")
except ImportError:
    print("\n(matplotlib not installed — table above is complete)")
