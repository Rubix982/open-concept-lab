"""
E-007 (v0.5) — raw representation similarity by neighbour type, on REAL RippleEdits

Upgrades the hand-curated demo to the actual RippleEdits benchmark
(github.com/edenbiran/RippleEdits), so we evaluate on real, larger, published data
with the community's own neighbour taxonomy.

SETUP (one-time):
    git clone https://github.com/edenbiran/RippleEdits
    # data files live in RippleEdits/data/benchmark/ : RECENT / RANDOM / POPULAR
    # point DATA_PATH below at one of them (add .json if the files carry it)

RippleEdits schema (VERIFIED against random.json/popular.json, 2026-08-09):
  entry.edit.prompt                          → the edited-fact statement (BASE anchor)
  entry.<Criterion>                          → LIST of query-groups
  entry.<Criterion>[g].test_queries[].prompt → neighbour prompts
  (each group also has condition_queries + test_condition; each query has
   prompt / answers[{value,aliases}] / relation / subject_id / target_ids)
  six criteria → our neighbour types:
    Logical_Generalization → 1hop      Compositionality_I/II → 2hop
    Subject_Aliasing       → paraphrase  Relation_Specifity   → locality (control)
    Forgetfulness          → control
We represent each prompt by the residual at its last token (layer LAYER), then
cosine-sim BASE vs each neighbour, aggregated by type — plus a token-overlap
(Jaccard) readout to expose the surface-form confound. Baseline predictor only.

Usage:
    python experiments/demo_distance_by_type/demo_rippleedits.py
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

# ── Config ──────────────────────────────────────────────────────────────────────
# EDIT this to point at your cloned RippleEdits data file:
DATA_PATH = Path(os.environ.get(
    "RIPPLEEDITS_FILE",
    # popular.json = well-known entities GPT-J actually knows (random.json uses
    # obscure entities → meaningless representations; this IS the competence filter).
    str(Path.home() / "code" / "RippleEdits" / "data" / "benchmark" / "popular.json"),
))
OUT_DIR = Path("experiments/demo_distance_by_type/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LAYER = 15
N_EDITS = 40             # subsample this many edits (keeps NDIF budget small)
MAX_PER_CRITERION = 3    # cap neighbour prompts per criterion per edit
SEED = 1538

TYPES = ["paraphrase", "1hop", "2hop", "locality", "control"]

# RippleEdits criterion → our neighbour type. Keys normalised (lower, underscores);
# both the repo's misspelling "Relation_Specifity" and a corrected form are handled.
CRITERION_TO_TYPE = {
    "logical_generalization": "1hop",
    "compositionality_i": "2hop",
    "compositionality_ii": "2hop",
    "subject_aliasing": "paraphrase",
    "relation_specifity": "locality",
    "relation_specificity": "locality",
    "forgetfulness": "control",
}


def norm_key(k: str) -> str:
    return k.strip().lower().replace(" ", "_")


# ── Load & flatten RippleEdits defensively ───────────────────────────────────────
def load_pairs(path: Path) -> list[dict[str, Any]]:
    """Return list of {base_prompt, neighbour_prompt, type} from RippleEdits."""
    if not path.exists():
        raise FileNotFoundError(
            f"RippleEdits file not found at {path}. Clone edenbiran/RippleEdits and "
            f"set RIPPLEEDITS_FILE, or edit DATA_PATH."
        )
    entries: list[dict[str, Any]] = json.loads(path.read_text())
    random.Random(SEED).shuffle(entries)
    entries = entries[:N_EDITS]

    pairs: list[dict[str, Any]] = []
    for e in entries:
        edit = e.get("edit") or {}
        base_prompt = edit.get("prompt")
        if not base_prompt:
            continue
        # each criterion is a LIST of query-groups; each group has test_queries.
        for key, val in e.items():
            ntype = CRITERION_TO_TYPE.get(norm_key(key))
            if ntype is None or not isinstance(val, list):
                continue
            # flatten test_queries across all groups in this criterion, then cap
            prompts: list[str] = []
            for group in val:
                if not isinstance(group, dict):
                    continue
                for q in group.get("test_queries") or []:
                    p = q.get("prompt") if isinstance(q, dict) else None
                    if p:
                        prompts.append(p)
            for p in prompts[:MAX_PER_CRITERION]:
                pairs.append({"base": base_prompt, "neighbour": p, "type": ntype})
    return pairs


model = LanguageModel("EleutherAI/gpt-j-6b")
pairs = load_pairs(DATA_PATH)
print(f"Loaded {len(pairs)} (base, neighbour) pairs from {DATA_PATH.name} "
      f"({N_EDITS} edits, layer {LAYER})\n")

# cache fact vectors by prompt (avoid recomputing shared base prompts)
_vec_cache: dict[str, torch.Tensor] = {}


def fact_vector(prompt: str) -> torch.Tensor:
    if prompt not in _vec_cache:
        with model.trace(prompt, remote=True):                        # type: ignore[union-attr]
            v = model.transformer.h[LAYER].output[0][0, -1].save()     # type: ignore[index]
        _vec_cache[prompt] = v
    return _vec_cache[prompt]


def token_jaccard(a: str, b: str) -> float:
    ta = set(model.tokenizer.encode(a))    # type: ignore[union-attr]
    tb = set(model.tokenizer.encode(b))
    return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0


# ── Compute cosine + overlap per pair ────────────────────────────────────────────
by_type: dict[str, list[tuple[float, float]]] = {t: [] for t in TYPES}
for i, pr in enumerate(pairs):
    bv, nv = fact_vector(pr["base"]), fact_vector(pr["neighbour"])
    cos = float(torch.nn.functional.cosine_similarity(bv, nv, dim=0))
    jac = token_jaccard(pr["base"], pr["neighbour"])
    by_type[pr["type"]].append((cos, jac))
    if i % 25 == 0:
        print(f"  ...{i}/{len(pairs)} pairs")

# ── Aggregate ─────────────────────────────────────────────────────────────────────
print("\n── mean by neighbour type ──────────────────────────────")
print(f"{'type':12s}  {'n':>4}  {'cos sim':>10}  {'tok overlap':>12}")
print("─" * 44)
means: dict[str, tuple[float, float]] = {}
for t in TYPES:
    vals = by_type[t]
    if not vals:
        continue
    mc = sum(c for c, _ in vals) / len(vals)
    mj = sum(j for _, j in vals) / len(vals)
    means[t] = (mc, mj)
    print(f"{t:12s}  {len(vals):>4}  {mc:>10.3f}  {mj:>12.2f}")

print("\nRead cos WITH the overlap column: if cosine tracks overlap, raw similarity")
print("is measuring surface form, not fact-relatedness — the confound that motivates")
print("the structured (Kim) + alignment (Jeong) predictors in design.md.")

# ── Plot ────────────────────────────────────────────────────────────────────────
try:
    import matplotlib.pyplot as plt
    import numpy as np

    present = [t for t in TYPES if t in means]
    fig, ax = plt.subplots(figsize=(8.5, 4.5), facecolor="#0a0c0f")
    ax.set_facecolor("#0f1318")
    x = np.arange(len(present))
    w = 0.38
    ax.bar(x - w / 2, [means[t][0] for t in present], w, color="#4fc3f7", label="cosine similarity")
    ax.bar(x + w / 2, [means[t][1] for t in present], w, color="#e57373", label="token overlap (Jaccard)")
    ax.set_xticks(x); ax.set_xticklabels(present, color="#c8d4e0")
    ax.tick_params(colors="#4a5568")
    for s in ax.spines.values():
        s.set_color("#1e2530")
    ax.set_title(f"RippleEdits · raw similarity vs. overlap by type — GPT-J L{LAYER} "
                 f"(n={len(pairs)} pairs)", color="#c8d4e0", fontsize=11)
    ax.legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    out = OUT_DIR / "similarity_by_type_rippleedits.png"
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"\nPlot saved → {out}")
except ImportError:
    print("\n(matplotlib not installed — table above is complete)")
