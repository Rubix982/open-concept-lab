"""
E-003: IIA Curve — Indirect Intervention Accuracy

Measures the causal contribution of each GPT-2 layer to belief tracking.

Protocol (per story pair, per layer L):
  1. Clean run:      original story → logit(clean_answer)
  2. Corrupted run:  location-swapped story → logit(clean_answer) drops
  3. Patched run:    corrupted story, but replace residual at [state_idx, :]
                     at layer L with the activation from the clean run
  4. IIA(L) = (patched_logit - corrupted_logit) / (clean_logit - corrupted_logit)
              0 = patch did nothing, 1 = fully restored clean answer

Story pairs use LOCATION SWAP (same character, same object, locations exchanged).
Patch direction: clean → corrupted (we test whether clean representation restores
the correct answer in the corrupted context).

Usage:
    source .venv/bin/activate
    python experiments/iia_curve/iia.py
"""

import json
from dataclasses import dataclass
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
OUT_DIR: Path = Path("experiments/iia_curve/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Story pairs ───────────────────────────────────────────────────────────────

@dataclass
class StoryPair:
    label: str
    clean: str        # original story text
    corrupted: str    # location-swapped story text
    answer: str       # correct answer in the CLEAN story
    state_token: str  # word that marks the belief state in the clean story

PAIRS: list[StoryPair] = [
    StoryPair(
        label="Sally·marble",
        clean=(
            "Sally puts the marble in the basket. "
            "Anne moves the marble to the box. "
            "Where does Sally think the marble is?"
        ),
        corrupted=(
            "Sally puts the marble in the box. "
            "Anne moves the marble to the basket. "
            "Where does Sally think the marble is?"
        ),
        answer="basket",
        state_token="basket",
    ),
    StoryPair(
        label="John·ball",
        clean=(
            "John puts the ball in the box. "
            "Mary moves the ball to the bag. "
            "Where does John think the ball is?"
        ),
        corrupted=(
            "John puts the ball in the bag. "
            "Mary moves the ball to the box. "
            "Where does John think the ball is?"
        ),
        answer="box",
        state_token="box",
    ),
    StoryPair(
        label="Emma·key",
        clean=(
            "Emma puts the key in the bag. "
            "Tom moves the key to the drawer. "
            "Where does Emma think the key is?"
        ),
        corrupted=(
            "Emma puts the key in the drawer. "
            "Tom moves the key to the bag. "
            "Where does Emma think the key is?"
        ),
        answer="bag",
        state_token="bag",
    ),
]

# ── Model ─────────────────────────────────────────────────────────────────────

print(f"Loading {MODEL_NAME} via NNSight...")
model: LanguageModel = LanguageModel(MODEL_NAME, device_map="cpu", dispatch=True)
n_layers: int = model.config.n_layer  # type: ignore[union-attr]
print(f"  layers: {n_layers}\n")

# ── Helpers ───────────────────────────────────────────────────────────────────

def find_state_idx(text: str, state_token: str) -> int:
    """Return index of state token in the tokenised story (after BOS)."""
    tokens: list[str] = model.tokenizer.tokenize(text, add_special_tokens=True)  # type: ignore[union-attr]
    target = state_token.lower()
    for i, t in enumerate(tokens):
        if target in t.lower():
            return i + 1   # +1 for BOS prepended by NNSight
    raise ValueError(f"State token '{state_token}' not found in tokens: {tokens}")


def get_answer_logit(logits: torch.Tensor, answer: str) -> float:
    """Return logit of the answer token at the last position."""
    tok_id: int = model.tokenizer.encode(" " + answer)[0]  # type: ignore[union-attr]
    last = logits[0, -1] if logits.ndim == 3 else logits[-1]
    return float(last[tok_id].detach())


def baseline_logit(text: str, answer: str) -> float:
    """Run a single story, return logit(answer) at the last token."""
    with model.trace(text):
        logits = model.lm_head.output.save()  # type: ignore[union-attr]
    return get_answer_logit(logits, answer)

# ── Build position mask ───────────────────────────────────────────────────────
# Probe shape once to know seq_len and d_model for mask construction.

def make_position_mask(text: str, pos: int) -> torch.Tensor:
    """Return float mask [seq_len, d_model] with 1s only at row `pos`."""
    with model.trace(text):
        probe = model.transformer.h[0].output[0].clone()  # type: ignore[index]
        shape_probe = probe.save()                         # type: ignore[union-attr]
    seq_len, d_model = shape_probe.shape
    mask = torch.zeros(seq_len, d_model)
    mask[pos, :] = 1.0
    return mask

# ── IIA sweep ─────────────────────────────────────────────────────────────────

all_iia: list[list[float]] = []   # [n_pairs, n_layers]

for pair in PAIRS:
    print(f"── Pair: {pair.label} ──────────────────────────────")

    state_idx: int = find_state_idx(pair.clean, pair.state_token)
    print(f"  state token '{pair.state_token}' → idx {state_idx}")

    # Baselines
    logit_clean:    float = baseline_logit(pair.clean, pair.answer)
    logit_corrupted: float = baseline_logit(pair.corrupted, pair.answer)
    delta: float = logit_clean - logit_corrupted
    print(f"  clean logit:     {logit_clean:+.3f}")
    print(f"  corrupted logit: {logit_corrupted:+.3f}  (Δ = {delta:+.3f})")

    mask: torch.Tensor = make_position_mask(pair.clean, state_idx)

    iia_by_layer: list[float] = []
    for layer in range(n_layers):
        # Cross-prompt trace: capture clean residual, patch into corrupted
        with model.trace() as tracer:  # type: ignore[union-attr]
            barrier = tracer.barrier(2)

            # Invoker 1 — clean story: capture activation at state_idx, this layer
            with tracer.invoke(pair.clean):
                clean_act = model.transformer.h[layer].output[0][state_idx, :].clone()  # type: ignore[index]
                barrier()

            # Invoker 2 — corrupted story: patch clean_act into residual at state_idx
            with tracer.invoke(pair.corrupted):
                barrier()
                hs = model.transformer.h[layer].output[0].clone()         # type: ignore[index]
                # Blend: keep all positions except state_idx; replace state_idx with clean_act
                patched = hs * (1.0 - mask) + clean_act.unsqueeze(0) * mask
                model.transformer.h[layer].output[0] = patched             # type: ignore[index]
                logits_patched = model.lm_head.output.save()               # type: ignore[union-attr]

        logit_patched: float = get_answer_logit(logits_patched, pair.answer)
        iia: float = (logit_patched - logit_corrupted) / delta if abs(delta) > 1e-6 else 0.0
        iia_by_layer.append(iia)
        print(f"  layer {layer:2d}  patched={logit_patched:+.3f}  IIA={iia:+.3f}")

    all_iia.append(iia_by_layer)
    print()

# ── Aggregate ─────────────────────────────────────────────────────────────────

iia_matrix: np.ndarray = np.array(all_iia)        # [n_pairs, n_layers]
iia_mean:   np.ndarray = iia_matrix.mean(axis=0)  # [n_layers]
iia_std:    np.ndarray = iia_matrix.std(axis=0)

print("── Mean IIA per layer ──────────────────────────────────")
for layer in range(n_layers):
    bar = "█" * max(0, int(iia_mean[layer] * 30))
    print(f"  layer {layer:2d}  IIA={iia_mean[layer]:+.3f} ±{iia_std[layer]:.3f}  {bar}")

peak_layer: int = int(np.argmax(iia_mean))
print(f"\nPeak IIA: layer {peak_layer}  ({iia_mean[peak_layer]:.3f})")

# ── Plot ──────────────────────────────────────────────────────────────────────

layers: list[int] = list(range(n_layers))
pair_colors: list[str] = ["#4fc3f7", "#6fcf97", "#ffb74d"]

fig = plt.figure(figsize=(11, 5), facecolor="#0a0c0f")
gs = gridspec.GridSpec(1, 1, figure=fig)
ax: Axes = fig.add_subplot(gs[0])

ax.set_facecolor("#0f1318")
ax.tick_params(colors="#4a5568", labelsize=9)
for spine in ["bottom", "left"]:
    ax.spines[spine].set_color("#1e2530")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Per-pair traces (thin)
for i, (pair, color) in enumerate(zip(PAIRS, pair_colors)):
    ax.plot(
        layers, iia_matrix[i],
        color=color, linewidth=1.2, alpha=0.55, linestyle="--",
        label=pair.label,
    )

# Mean (thick)
ax.plot(layers, iia_mean, color="#e8dcc8", linewidth=2.5, label="mean IIA", zorder=5)
ax.fill_between(
    layers,
    iia_mean - iia_std,
    iia_mean + iia_std,
    color="#e8dcc8", alpha=0.10,
)

ax.axhline(0.0, color="#4a5568", linewidth=0.8, linestyle=":")
ax.axhline(1.0, color="#4a5568", linewidth=0.8, linestyle=":", label="IIA = 1.0 (perfect restore)")
ax.axvline(peak_layer, color="#ce93d8", linewidth=1.2, linestyle="--",
           label=f"peak layer {peak_layer}")

ax.set_xticks(layers)
ax.set_xlabel("layer", color="#4a5568", fontsize=9)
ax.set_ylabel("IIA  (0 = no effect, 1 = full restore)", color="#4a5568", fontsize=9)
ax.set_title(
    f"IIA Curve — GPT-2 small · state-token patch · {len(PAIRS)} story pairs",
    color="#c8d4e0", fontsize=11, pad=10,
)
ax.legend(
    fontsize=8, facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0",
    loc="upper left",
)

out_path: Path = OUT_DIR / "iia_by_layer.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
print(f"\nPlot saved → {out_path}")
