"""
E-001: OID Co-location Linear Probe

Tests whether character identity and object identity can both be decoded
from the residual stream at the state token position across GPT-2 layers.
Co-location is confirmed if both probes peak at the same layer(s).

Usage:
    source .venv/bin/activate
    python experiments/oid_colocation/probe.py
"""

import json
import os
from pathlib import Path
from typing import Any

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np
import torch
import transformer_lens
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

# suppress MPS warning — known issue, results match CPU for this use case
os.environ.setdefault("TRANSFORMERLENS_ALLOW_MPS", "1")

# ── Config ────────────────────────────────────────────────────────────────────

MODEL_NAME: str = "gpt2"
DATA_PATH: Path = Path("data/stories/belief_stories.json")
OUT_DIR: Path = Path("experiments/oid_colocation/output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE: str = "mps" if torch.backends.mps.is_available() else "cpu"

# ── Load model ────────────────────────────────────────────────────────────────

print(f"Loading {MODEL_NAME} on {DEVICE}...")
model: transformer_lens.HookedTransformer = (
    transformer_lens.HookedTransformer.from_pretrained(MODEL_NAME)
)
model = model.to(DEVICE)
model.eval()
n_layers: int = model.cfg.n_layers
print(f"  layers: {n_layers}  d_model: {model.cfg.d_model}")

# ── Load stories ──────────────────────────────────────────────────────────────

stories: list[dict[str, Any]] = json.loads(DATA_PATH.read_text())
print(f"Loaded {len(stories)} stories")

# ── Token utilities ───────────────────────────────────────────────────────────

def find_state_token_idx(
    m: transformer_lens.HookedTransformer,
    story: dict[str, Any],
) -> int:
    """Return the index of the state token within the tokenised story."""
    tokens = m.to_tokens(story["story"], prepend_bos=True)
    token_strs: list[str] = m.to_str_tokens(story["story"], prepend_bos=True)  # type: ignore[assignment]
    target: str = story["state_token"].lower().strip()
    for i, t in enumerate(token_strs):
        if t.strip().lower() == target:
            return i
    # fallback: substring match
    for i, t in enumerate(token_strs):
        if target in t.lower():
            return i
    raise ValueError(
        f"State token '{story['state_token']}' not found in: {token_strs}"
    )

# ── Extract residual stream at state token ────────────────────────────────────

layer_activations: dict[int, list[np.ndarray]] = {
    layer: [] for layer in range(n_layers)
}
char_labels: list[int] = []
obj_labels: list[int] = []

print("\nExtracting residual stream activations...")
for story in stories:
    tokens = model.to_tokens(story["story"], prepend_bos=True).to(DEVICE)
    state_idx: int = find_state_token_idx(model, story)

    with torch.no_grad():
        _, cache = model.run_with_cache(tokens)

    for layer in range(n_layers):
        resid: torch.Tensor = cache["resid_post", layer]   # [1, seq, d_model]
        vec: np.ndarray = resid[0, state_idx, :].cpu().float().numpy()
        layer_activations[layer].append(vec)

    char_labels.append(story["character_label"])
    obj_labels.append(story["object_label"])
    print(f"  [{story['id']:20s}] state token idx: {state_idx}")

char_arr: np.ndarray = np.array(char_labels)
obj_arr: np.ndarray = np.array(obj_labels)

# ── Train linear probes per layer ─────────────────────────────────────────────
# 20 stories → 5 per class → stratified 5-fold CV.
# Each fold trains on 16 examples, tests on 4. Small but gives a real
# generalisation estimate (not train-set accuracy).

n_folds: int = min(5, min(len([l for l in char_labels if l == c]) for c in set(char_labels)))
cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)

print(f"\nTraining linear probes ({n_folds}-fold stratified CV, n={len(stories)})...")
char_scores: list[float] = []
obj_scores: list[float] = []

for layer in range(n_layers):
    X: np.ndarray = np.stack(layer_activations[layer])  # [n_stories, d_model]

    # z-score per feature: stabilises LR in high-d space
    scaler = StandardScaler()
    X_scaled: np.ndarray = scaler.fit_transform(X)

    clf_char = LogisticRegression(max_iter=2000, random_state=42, C=0.1)
    clf_obj  = LogisticRegression(max_iter=2000, random_state=42, C=0.1)

    c_cv = cross_val_score(clf_char, X_scaled, char_arr, cv=cv, scoring="accuracy")
    o_cv = cross_val_score(clf_obj,  X_scaled, obj_arr,  cv=cv, scoring="accuracy")

    c_score: float = float(c_cv.mean())
    o_score: float = float(o_cv.mean())

    char_scores.append(c_score)
    obj_scores.append(o_score)
    print(f"  layer {layer:2d}  char={c_score:.3f}±{c_cv.std():.3f}  obj={o_score:.3f}±{o_cv.std():.3f}")

# ── Plot ──────────────────────────────────────────────────────────────────────

layers: list[int] = list(range(n_layers))
n_char_classes: int = len(set(char_labels))
chance: float = 1.0 / n_char_classes

fig = plt.figure(figsize=(12, 5), facecolor="#0a0c0f")
gs = gridspec.GridSpec(1, 2, figure=fig, wspace=0.35)


def style_ax(ax: Axes, title: str) -> None:
    ax.set_facecolor("#0f1318")
    ax.tick_params(colors="#4a5568", labelsize=9)
    for spine in ["bottom", "left"]:
        ax.spines[spine].set_color("#1e2530")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title(title, color="#c8d4e0", fontsize=11, pad=12)
    ax.set_xlabel("layer", color="#4a5568", fontsize=9)
    ax.set_ylabel(f"probe accuracy ({n_folds}-fold CV)", color="#4a5568", fontsize=9)
    ax.set_xlim(-0.5, n_layers - 0.5)
    ax.set_ylim(0, 1.05)
    ax.axhline(
        chance, color="#4a5568", linewidth=1, linestyle="--",
        label=f"chance ({chance:.2f})",
    )
    ax.axhline(
        0.7, color="#2d3748", linewidth=0.8, linestyle=":",
        label="0.70 threshold",
    )


ax1: Axes = fig.add_subplot(gs[0])
style_ax(ax1, "Character Identity Probe")
ax1.plot(
    layers, char_scores,
    color="#4fc3f7", linewidth=2, marker="o", markersize=5,
    label="character probe",
)
ax1.legend(
    fontsize=8, facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0"
)

ax2: Axes = fig.add_subplot(gs[1])
style_ax(ax2, "Object Identity Probe")
ax2.plot(
    layers, obj_scores,
    color="#6fcf97", linewidth=2, marker="o", markersize=5,
    label="object probe",
)
ax2.legend(
    fontsize=8, facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0"
)

fig.suptitle(
    f"OID Co-location Probe — {MODEL_NAME}  |  state token residual stream  "
    f"|  n={len(stories)} stories  ({n_folds}-fold CV)",
    color="#e8dcc8", fontsize=11, y=1.02,
)

out_path: Path = OUT_DIR / "probe_accuracy.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
print(f"\nPlot saved → {out_path}")

# ── Summary ───────────────────────────────────────────────────────────────────

char_peak: int = int(np.argmax(char_scores))
obj_peak: int  = int(np.argmax(obj_scores))

print("\n── Results ──────────────────────────────────────────────────────────────")
print(f"Character probe peak : layer {char_peak:2d}  ({char_scores[char_peak]:.3f})")
print(f"Object probe peak    : layer {obj_peak:2d}  ({obj_scores[obj_peak]:.3f})")
print(
    f"Co-location          : {'YES' if abs(char_peak - obj_peak) <= 1 else 'NO'} "
    f"(peaks within 1 layer of each other)"
)
print(f"Chance level         : {chance:.3f}")
print(f"CV folds             : {n_folds}-fold stratified")
print(
    "\nNote: scores are cross-validated (real generalisation estimate). "
    "5 stories per class is still small — add more for statistical power."
)
