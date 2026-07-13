"""
E-004b: NNSight trace — Llama 3.1 8B over NDIF (remote=True)

Same four steps as trace.py but against a model that can actually do ToM tasks:
  Step 1: Read — logits at the answer token, no intervention
  Step 2: Zero — ablate a mid-layer entirely
  Step 3: Noise — sweep σ across that layer
  Step 4: Targeted — zero only the state-token position at that layer

Llama 3.1 8B module paths (different from GPT-2):
  Residual stream at layer L : model.model.layers[L].output[0]
  Final logits               : model.lm_head.output
  n_layers                   : 32   (model.config.num_hidden_layers)
  d_model                    : 4096 (model.config.hidden_size)

API key is read from NNSIGHT_API_KEY environment variable — never hardcoded.

Usage:
    source ~/.zshrc
    source .venv/bin/activate
    python experiments/nnsight_trace/trace_llama.py
"""

import os
from pathlib import Path
from typing import Any

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import torch
from nnsight import LanguageModel, CONFIG

# ── API key ───────────────────────────────────────────────────────────────────

api_key: str = os.environ.get("NNSIGHT_API_KEY", "")
if not api_key:
    raise EnvironmentError(
        "NNSIGHT_API_KEY not set. Run: source ~/.zshrc"
    )
CONFIG.set_default_api_key(api_key)

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_ID: str = "meta-llama/Meta-Llama-3.1-8B"
OUT_DIR: Path = Path("experiments/nnsight_trace/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Llama 3.1 8B has 32 layers — target the middle where belief info tends to live
TARGET_LAYER: int = 16
NOISE_SIGMAS: list[float] = [0.01, 0.1, 1.0]

# ── Story ─────────────────────────────────────────────────────────────────────

text: str = (
    "Sally puts the marble in the basket. "
    "Anne moves the marble to the box. "
    "Where does Sally think the marble is?"
)
correct_answer: str = "basket"

print(f"Model : {MODEL_ID}  (remote via NDIF)")
print(f"Story : {text}")
print(f"Answer: {correct_answer}\n")
print("─" * 70)

# ── Load model skeleton ────────────────────────────────────────────────────────
# With remote=True, NNSight loads the config and tokenizer locally but keeps
# the weights on NDIF servers. No GPU or large download required.

print("Loading model skeleton (config + tokenizer only, weights stay on NDIF)...")
model: LanguageModel = LanguageModel(MODEL_ID)
n_layers: int = model.config.num_hidden_layers   # type: ignore[union-attr]
d_model:  int = model.config.hidden_size          # type: ignore[union-attr]
print(f"  layers: {n_layers}  d_model: {d_model}\n")

# ── Tokenize locally to find state token position ─────────────────────────────
# Note: Llama 3.1 tokenizer adds BOS token automatically.
token_strs: list[str] = model.tokenizer.tokenize(text)  # type: ignore[union-attr]
state_idx: int = 0
for i, t in enumerate(token_strs):
    if correct_answer.lower() in t.lower():
        state_idx = i
        break
print(f"State token '{correct_answer}' → position {state_idx} / {len(token_strs)} tokens")
print(f"Tokens: {token_strs[:state_idx+3]}…\n")

# ── Helper ────────────────────────────────────────────────────────────────────

def answer_logit(logits_tensor: torch.Tensor, label: str) -> float:
    """Return logit of the answer token at the last position."""
    tok_id: int = model.tokenizer.encode(" " + correct_answer)[-1]  # type: ignore[union-attr]
    last = logits_tensor[-1] if logits_tensor.ndim == 2 else logits_tensor[0, -1]
    return float(last[tok_id].detach())


def top5(logits_tensor: torch.Tensor, label: str) -> float:
    last = logits_tensor[-1] if logits_tensor.ndim == 2 else logits_tensor[0, -1]
    probs = torch.softmax(last.float(), dim=-1)
    top_ids = probs.topk(5).indices
    tok_id: int = model.tokenizer.encode(" " + correct_answer)[-1]  # type: ignore[union-attr]
    logit_val: float = float(last[tok_id].detach())
    print(f"\n[{label}]")
    for rank, tid in enumerate(top_ids):
        tok = model.tokenizer.decode([int(tid)])  # type: ignore[union-attr]
        marker = " ◀" if int(tid) == tok_id else ""
        print(f"  {rank+1}. {tok!r:20s}  p={float(probs[tid]):.4f}{marker}")
    print(f"  → logit('{correct_answer}') = {logit_val:.4f}")
    return logit_val

# ── STEP 1 — Read ─────────────────────────────────────────────────────────────

print("\n══ STEP 1: Read (no intervention) ══")
with model.trace(text, remote=True):   # type: ignore[union-attr]
    logits_clean = model.lm_head.output.save()  # type: ignore[union-attr]
logit_clean: float = top5(logits_clean, "clean")

# ── STEP 2 — Zero layer TARGET_LAYER entirely ─────────────────────────────────

print(f"\n══ STEP 2: Zero layer {TARGET_LAYER} (full ablation) ══")
with model.trace(text, remote=True):   # type: ignore[union-attr]
    model.model.layers[TARGET_LAYER].output[0][:] = 0   # type: ignore[index]
    logits_zero = model.lm_head.output.save()           # type: ignore[union-attr]
logit_zero: float = top5(logits_zero, f"zero layer {TARGET_LAYER}")

# ── STEP 3 — Noise sweep ──────────────────────────────────────────────────────

print(f"\n══ STEP 3: Noise sweep at layer {TARGET_LAYER} ══")
logits_noise: list[float] = []
for sigma in NOISE_SIGMAS:
    with model.trace(text, remote=True):   # type: ignore[union-attr]
        hs = model.model.layers[TARGET_LAYER].output[0].clone()   # type: ignore[index]
        model.model.layers[TARGET_LAYER].output[0] = hs + sigma * torch.randn(hs.shape)  # type: ignore[index]
        logits_noisy = model.lm_head.output.save()  # type: ignore[union-attr]
    logit_n: float = top5(logits_noisy, f"noise σ={sigma}")
    logits_noise.append(logit_n)

# ── STEP 4 — Targeted: zero state-token position only ────────────────────────
# Build mask locally (d_model known from config), then send to NDIF.
# seq_len = len(token_strs) + 1 for BOS; mask shape [seq_len, d_model].

print(f"\n══ STEP 4: Targeted — zero state-token position {state_idx} only ══")
seq_len: int = len(token_strs)
mask: torch.Tensor = torch.zeros(seq_len, d_model)
mask[state_idx, :] = 1.0   # 1 = positions to zero out

with model.trace(text, remote=True):   # type: ignore[union-attr]
    hs_full = model.model.layers[TARGET_LAYER].output[0].clone()   # type: ignore[index]
    model.model.layers[TARGET_LAYER].output[0] = hs_full * (1.0 - mask)  # type: ignore[index]
    logits_targeted = model.lm_head.output.save()  # type: ignore[union-attr]
logit_targeted: float = top5(logits_targeted, "zero state-tok position only")

# ── Summary ───────────────────────────────────────────────────────────────────

rows: list[tuple[str, float]] = [
    ("clean (no intervention)", logit_clean),
    (f"zero layer {TARGET_LAYER} (full)", logit_zero),
    *[(f"noise σ={s}", l) for s, l in zip(NOISE_SIGMAS, logits_noise)],
    ("zero state-token pos only", logit_targeted),
]

print("\n" + "═" * 70)
print(f"{'Condition':<35}  logit('{correct_answer}')")
print("─" * 70)
for label, logit in rows:
    print(f"  {label:<33}  {logit:+.4f}")

# ── Plot ──────────────────────────────────────────────────────────────────────

fig = plt.figure(figsize=(10, 4), facecolor="#0a0c0f")
gs = gridspec.GridSpec(1, 1, figure=fig)
ax: Axes = fig.add_subplot(gs[0])

ax.set_facecolor("#0f1318")
ax.tick_params(colors="#4a5568", labelsize=9)
for spine in ["bottom", "left"]:
    ax.spines[spine].set_color("#1e2530")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

labels  = [r[0] for r in rows]
values  = [r[1] for r in rows]
colors  = ["#4fc3f7", "#e57373", "#ffb74d", "#ff8a65", "#e64a19", "#ce93d8"]
x = list(range(len(labels)))
bars = ax.bar(x, values, color=colors, width=0.6, edgecolor="#1e2530")
ax.axhline(logit_clean, color="#4fc3f7", linewidth=1, linestyle="--", alpha=0.4,
           label=f"clean baseline ({logit_clean:.2f})")
ax.set_xticks(x)
ax.set_xticklabels(
    [l.replace(" (", "\n(").replace(" σ=", "\nσ=") for l in labels],
    color="#c8d4e0", fontsize=8,
)
ax.set_ylabel(f"logit('{correct_answer}')", color="#4a5568", fontsize=9)
ax.set_title(
    f"NNSight Intervention — Llama 3.1 8B (NDIF) · layer {TARGET_LAYER}",
    color="#c8d4e0", fontsize=10, pad=10,
)
ax.legend(fontsize=8, facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
for bar, val in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3,
            f"{val:.1f}", ha="center", va="bottom", color="#c8d4e0", fontsize=7)

out_path: Path = OUT_DIR / "logit_comparison_llama.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
print(f"\nPlot saved → {out_path}")
