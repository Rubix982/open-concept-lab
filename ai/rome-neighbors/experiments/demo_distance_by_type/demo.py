"""
E-007 — v0.1 demo: raw representation similarity by neighbour type (GPT-J / NDIF)

Smallest end-to-end slice of design.md that produces real numbers. For each base
fact and its typed neighbours (paraphrase / 1-hop / 2-hop / locality-control), we
represent every prompt by its residual stream at the last token of a mid layer,
then measure cosine similarity between the base fact and each neighbour. We
aggregate by neighbour type.

HONEST FRAMING: this is the BASELINE predictor only (raw distance), and it is
deliberately confounded — we also report token-overlap (Jaccard) so you can SEE
that raw last-token similarity tracks surface/template overlap as much as
fact-relatedness. That confound is exactly why the full design adds structured
(Kim bilinear) and alignment (Jeong) predictors. v0.1 = pipeline + first look,
NOT a result to publish. No editing, no IIA, no hop-resolved propagation yet.

Usage:
    python experiments/demo_distance_by_type/demo.py
"""

import json
import os
from pathlib import Path
from typing import Any

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from nnsight import CONFIG
from nnsight.modeling.language import LanguageModel

CONFIG.set_default_api_key(os.environ["NNSIGHT_API_KEY"])

DATA = Path(__file__).resolve().parent / "data" / "demo_facts.json"
OUT_DIR = Path(__file__).resolve().parent / "output"   # robust to run-location
OUT_DIR.mkdir(parents=True, exist_ok=True)
LAYER = 15                      # mid layer; v1 sweeps this
TYPES = ["paraphrase", "1hop", "2hop", "locality"]

model = LanguageModel("EleutherAI/gpt-j-6b")
facts: list[dict[str, Any]] = json.loads(DATA.read_text())


def fact_vector(prompt: str) -> torch.Tensor:
    """Residual stream at the LAST token of `prompt`, at LAYER. Shape [d_model]."""
    with model.trace(prompt, remote=True):                       # type: ignore[union-attr]
        vec = model.transformer.h[LAYER].output[0][0, -1].save()  # type: ignore[index]
    return vec


def token_jaccard(a: str, b: str) -> float:
    """Surface-overlap confound readout: Jaccard of the two prompts' token-id sets."""
    ta = set(model.tokenizer.encode(a))   # type: ignore[union-attr]
    tb = set(model.tokenizer.encode(b))
    return len(ta & tb) / len(ta | tb)


# ── collect cosine similarity + token overlap, per (fact, neighbour) ───────────
rows: list[tuple[str, str, float, float]] = []   # (fact_id, type, cos, jaccard)
print(f"GPT-J · layer {LAYER} · last-token residual · {len(facts)} base facts\n")

for f in facts:
    base_prompt = f["base"]["prompt"]
    base_vec = fact_vector(base_prompt)
    for nb in f["neighbors"]:
        nb_vec = fact_vector(nb["prompt"])
        cos = float(torch.nn.functional.cosine_similarity(base_vec, nb_vec, dim=0))
        jac = token_jaccard(base_prompt, nb["prompt"])
        rows.append((f["id"], nb["type"], cos, jac))
        print(f"  {f['id']:12s} {nb['type']:10s}  cos={cos:+.3f}  overlap={jac:.2f}")

# ── aggregate by neighbour type ────────────────────────────────────────────────
print("\n── mean by neighbour type ──────────────────────────────")
print(f"{'type':12s}  {'cos sim':>10}  {'tok overlap':>12}")
print("─" * 38)
means: dict[str, tuple[float, float]] = {}
for t in TYPES:
    cs = [c for (_, tt, c, _) in rows if tt == t]
    js = [j for (_, tt, _, j) in rows if tt == t]
    mc, mj = sum(cs) / len(cs), sum(js) / len(js)
    means[t] = (mc, mj)
    print(f"{t:12s}  {mc:>10.3f}  {mj:>12.2f}")

print("\nRead it WITH the overlap column: if cos tracks overlap, raw similarity is")
print("measuring template surface form, not fact-relatedness — the confound that")
print("motivates the structured/alignment predictors in design.md.")

# ── plot ────────────────────────────────────────────────────────────────────────
try:
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor="#0a0c0f")
    ax.set_facecolor("#0f1318")
    x = np.arange(len(TYPES))
    w = 0.38
    cos_vals = [means[t][0] for t in TYPES]
    jac_vals = [means[t][1] for t in TYPES]
    ax.bar(x - w / 2, cos_vals, w, color="#4fc3f7", label="cosine similarity")
    ax.bar(x + w / 2, jac_vals, w, color="#e57373", label="token overlap (Jaccard)")
    ax.set_xticks(x)
    ax.set_xticklabels(TYPES, color="#c8d4e0")
    ax.tick_params(colors="#4a5568")
    for s in ax.spines.values():
        s.set_color("#1e2530")
    ax.set_title(f"Raw similarity vs. token overlap by neighbour type — GPT-J L{LAYER}",
                 color="#c8d4e0", fontsize=11)
    ax.legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    out = OUT_DIR / "similarity_by_type.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"\nPlot saved → {out}")
except ImportError:
    print("\n(matplotlib not installed — table above is complete)")
