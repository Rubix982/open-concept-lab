"""
E-004: NNSight trace — read → zero → noise → targeted replace

Four self-contained steps that build intuition for NNSight's intervention API
before we use it for IIA causal patching in E-003.

Usage:
    source .venv/bin/activate
    python experiments/nnsight_trace/trace.py

Key NNSight idea:
    Code inside `with model.trace(...)` is DEFERRED — it records a computation
    graph, not immediate execution. `.save()` marks a tensor to materialise
    after the trace exits. Assigning to `.output` replaces what flows forward.
"""

import json
from pathlib import Path
from typing import Any

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
import torch
from nnsight import LanguageModel

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_NAME: str = "gpt2"
DATA_PATH: Path = Path("data/stories/belief_stories.json")
OUT_DIR: Path = Path("experiments/nnsight_trace/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Layer 6 is where object identity peaked in the E-001 probe.
TARGET_LAYER: int = 6
NOISE_SIGMAS: list[float] = [0.01, 0.1, 1.0]

# ── Load model ────────────────────────────────────────────────────────────────

print(f"Loading {MODEL_NAME} via NNSight...")
model: LanguageModel = LanguageModel(MODEL_NAME, device_map="cpu", dispatch=True)
print("  ready.\n")

# ── Pick a story ──────────────────────────────────────────────────────────────

stories: list[dict[str, Any]] = json.loads(DATA_PATH.read_text())
story: dict[str, Any] = next(s for s in stories if s["id"] == "sally_marble_basket")
text: str = story["story"]
correct_answer: str = story["answer"]   # "basket"

print(f"Story : {text}")
print(f"Answer: {correct_answer}\n")
print("─" * 70)

# ── Helper ────────────────────────────────────────────────────────────────────

def top5(logits_tensor: torch.Tensor, label: str) -> float:
    """Print top-5 predictions at the last token; return logit of correct answer."""
    last: torch.Tensor = logits_tensor[0, -1]   # [vocab]
    probs = torch.softmax(last, dim=-1)
    top_ids = probs.topk(5).indices
    correct_id: int = model.tokenizer.encode(" " + correct_answer)[0]
    correct_logit: float = float(last[correct_id])
    print(f"\n[{label}]")
    for rank, tok_id in enumerate(top_ids):
        tok = model.tokenizer.decode(int(tok_id))  # type: ignore[arg-type]
        marker = " ◀" if tok_id == correct_id else ""
        print(f"  {rank+1}. {tok!r:15s}  p={float(probs[tok_id]):.4f}{marker}")
    print(f"  → logit('{correct_answer}') = {correct_logit:.4f}")
    return correct_logit

# ── STEP 1 — Read ─────────────────────────────────────────────────────────────
# Run the story through GPT-2, save the final logits. No intervention.

print("\n══ STEP 1: Read (no intervention) ══")

with model.trace(text):
    logits_clean = model.lm_head.output.save()  # type: ignore[union-attr]

logit_clean: float = top5(logits_clean, "clean")

# ── STEP 2 — Zero layer 6 entirely ───────────────────────────────────────────
# Set every position in layer 6's residual output to 0.
# NNSight: assigning to `.output[0]` replaces the tensor in-place before it
# flows to layer 7. The model sees a zero residual stream from layer 6 onward.

print("\n══ STEP 2: Zero layer 6 (full ablation) ══")

with model.trace(text):
    model.transformer.h[TARGET_LAYER].output[0][:] = 0  # type: ignore[index]
    logits_zero = model.lm_head.output.save()  # type: ignore[union-attr]

logit_zero: float = top5(logits_zero, f"zero layer {TARGET_LAYER}")

# ── STEP 3 — Noise at layer 6 (σ sweep) ──────────────────────────────────────
# Add Gaussian noise to the residual stream at layer 6.
# Sweep three magnitudes to see how sensitive the answer logit is to noise.

print("\n══ STEP 3: Noise sweep at layer 6 ══")

logits_noise: list[float] = []
for sigma in NOISE_SIGMAS:
    with model.trace(text):
        hs = model.transformer.h[TARGET_LAYER].output[0].clone()  # type: ignore[index]
        noise = sigma * torch.randn(hs.shape)
        model.transformer.h[TARGET_LAYER].output[0] = hs + noise  # type: ignore[index]
        logits_noisy = model.lm_head.output.save()  # type: ignore[union-attr]
    logit_n: float = top5(logits_noisy, f"noise σ={sigma}")
    logits_noise.append(logit_n)

# ── STEP 4 — Targeted replace: zero only the state token position ─────────────
# Instead of wiping all positions, zero only the state-token position (idx 8).
# NNSight proxies don't support in-place multi-dim indexed assignment inside a
# trace. Pattern: clone → build mask outside trace → multiply → assign back.

print("\n══ STEP 4: Targeted replace — state token position only ══")

# Find the state token index
token_strs: list[str] = model.tokenizer.tokenize(text, add_special_tokens=True)  # type: ignore[union-attr]
state_target: str = story["state_token"].lower()
state_idx: int = 0
for i, t in enumerate(token_strs):
    if state_target in t.lower():
        state_idx = i
        break
# Account for BOS token added by NNSight
state_idx_with_bos: int = state_idx + 1
print(f"  state token '{story['state_token']}' → position index {state_idx_with_bos}")

# Probe trace to learn the actual tensor shape (NNSight may keep or drop batch dim)
with model.trace(text):
    _shape_probe = model.transformer.h[TARGET_LAYER].output[0].clone()  # type: ignore[index]
    _shape_saved = _shape_probe.save()  # type: ignore[union-attr]

act_shape: torch.Size = _shape_saved.shape
print(f"  activation shape at layer {TARGET_LAYER}: {tuple(act_shape)}")

# Build mask outside the trace: 1 everywhere, 0 at the state token position
mask: torch.Tensor = torch.ones(act_shape)
if mask.ndim == 3:
    mask[:, state_idx_with_bos, :] = 0.0   # [batch, seq, d]
else:
    mask[state_idx_with_bos, :] = 0.0      # [seq, d]

with model.trace(text):
    hs_full = model.transformer.h[TARGET_LAYER].output[0].clone()  # type: ignore[index]
    model.transformer.h[TARGET_LAYER].output[0] = hs_full * mask   # type: ignore[index]
    logits_targeted = model.lm_head.output.save()  # type: ignore[union-attr]

logit_targeted: float = top5(logits_targeted, "zero state-tok position only")

# ── Summary table ─────────────────────────────────────────────────────────────

print("\n" + "═" * 70)
print(f"{'Condition':<35}  logit('{correct_answer}')")
print("─" * 70)

rows: list[tuple[str, float]] = [
    ("clean (no intervention)", logit_clean),
    (f"zero layer {TARGET_LAYER} (full)", logit_zero),
    *[(f"noise σ={s}", l) for s, l in zip(NOISE_SIGMAS, logits_noise)],
    ("zero state-token pos only", logit_targeted),
]
for label, logit in rows:
    bar = "█" * max(0, int((logit + 10) * 1.5))   # crude bar, centred at -10
    print(f"  {label:<33}  {logit:+.4f}  {bar}")

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

labels: list[str] = [r[0] for r in rows]
values: list[float] = [r[1] for r in rows]
colors: list[str] = (
    ["#4fc3f7"]       # clean — blue
    + ["#e57373"]     # zero full — red
    + ["#ffb74d", "#ff8a65", "#e64a19"]  # noise σ — orange gradient
    + ["#ce93d8"]     # targeted — purple
)

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
    f"NNSight Intervention — GPT-2 · layer {TARGET_LAYER} · \"{text[:50]}…\"",
    color="#c8d4e0", fontsize=10, pad=10,
)
ax.legend(fontsize=8, facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")

for bar, val in zip(bars, values):
    ax.text(
        bar.get_x() + bar.get_width() / 2, val + 0.05,
        f"{val:.2f}", ha="center", va="bottom", color="#c8d4e0", fontsize=7,
    )

out_path: Path = OUT_DIR / "logit_comparison.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
print(f"\nPlot saved → {out_path}")
