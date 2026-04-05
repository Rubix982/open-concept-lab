"""Residual stream isolation experiment for the Graph Transformer on Cora.

Asks: which transformer block does more "heavy lifting"?
- Run 1: Zero block 0's output → only block 1 + raw features doing the work
- Run 2: Zero block 1's output → only block 0 + raw features doing the work
- Run 3: Baseline (no zeroing) → reference accuracy

The block whose zeroing causes the larger accuracy drop is the more important one.

Run:
    python3 run_residual_isolation.py
"""

from __future__ import annotations

import numpy as np
import torch

from pathlib import Path

from src.gcn_citation.data import ensure_cora_dataset, load_graph_data
from src.gcn_citation.models.gt_torch import (
    GraphTransformer,
    _build_attention_mask,
    _degree_features,
)

try:
    from nnsight import NNsight
except ImportError:
    raise ImportError("nnsight is required. Install it with: pip install nnsight")

# ── Config ────────────────────────────────────────────────────────────────────
HIDDEN_DIM = 64
HEADS = 4
LAYERS = 2
EPOCHS = 200
LR = 1e-3
WEIGHT_DECAY = 5e-4
DROPOUT = 0.1
SEED = 42

DATA_DIR = Path("data")

# ── Data ──────────────────────────────────────────────────────────────────────
print("Loading Cora...")
ensure_cora_dataset(DATA_DIR)
graph = load_graph_data(
    data_dir=DATA_DIR,
    db_path=Path("/tmp/residual_isolation_cora.duckdb"),
    seed=SEED,
)

features = torch.tensor(graph.features, dtype=torch.float32)
degree_features = torch.tensor(
    _degree_features(graph.features.shape[0], graph.edges), dtype=torch.float32
)
labels = torch.tensor(graph.labels, dtype=torch.long)
train_mask = torch.tensor(graph.train_mask, dtype=torch.bool)
attn_mask = torch.tensor(
    _build_attention_mask(graph.features.shape[0], graph.edges), dtype=torch.bool
)

# ── Train ─────────────────────────────────────────────────────────────────────
torch.manual_seed(SEED)
np.random.seed(SEED)

model = GraphTransformer(
    input_dim=graph.features.shape[1],
    hidden_dim=HIDDEN_DIM,
    output_dim=len(graph.label_names),
    heads=HEADS,
    layers=LAYERS,
    dropout=DROPOUT,
)
optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

print(f"Training GT on Cora for {EPOCHS} epochs...")
for epoch in range(1, EPOCHS + 1):
    model.train()
    optimizer.zero_grad()
    logits, _, _ = model(
        features, degree_features, attn_mask=attn_mask, collect_attention=False
    )
    active = torch.where(train_mask)[0]
    loss = torch.nn.functional.cross_entropy(logits[active], labels[active])
    loss.backward()
    optimizer.step()

    if epoch % 50 == 0:
        model.eval()
        with torch.no_grad():
            eval_logits, _, _ = model(
                features, degree_features, attn_mask=attn_mask, collect_attention=False
            )
        preds = eval_logits.argmax(dim=1).numpy()
        train_acc = (preds[graph.train_mask] == graph.labels[graph.train_mask]).mean()
        val_acc = (preds[graph.val_mask] == graph.labels[graph.val_mask]).mean()
        print(
            f"  epoch {epoch:3d} | loss {loss.item():.4f} | train {train_acc:.3f} | val {val_acc:.3f}"
        )

model.eval()

# ── Helper: accuracy from logit array ────────────────────────────────────────


def accuracy_from_logits(logits_np: np.ndarray) -> dict[str, float]:
    preds = logits_np.argmax(axis=1)
    return {
        "train": float(
            (preds[graph.train_mask] == graph.labels[graph.train_mask]).mean()
        ),
        "val": float((preds[graph.val_mask] == graph.labels[graph.val_mask]).mean()),
        "test": float((preds[graph.test_mask] == graph.labels[graph.test_mask]).mean()),
    }


# ── Baseline: normal forward pass ─────────────────────────────────────────────
print("\nRunning baseline (no intervention)...")
wrapped = NNsight(model)
with wrapped.trace(
    features, degree_features, attn_mask=attn_mask, collect_attention=False
):
    baseline_logits_saved = wrapped.output[0].save()

baseline_logits_np = baseline_logits_saved.detach().cpu().numpy()
baseline_acc = accuracy_from_logits(baseline_logits_np)

# ── Run 1: Zero block 0 output ────────────────────────────────────────────────
print("Running intervention: zero block 0 output...")
wrapped = NNsight(model)
with wrapped.trace(
    features, degree_features, attn_mask=attn_mask, collect_attention=False
):
    original_output_b0 = wrapped.blocks[0].output
    zeroed_hidden_b0 = original_output_b0[0] * 0.0
    wrapped.blocks[0].output = (zeroed_hidden_b0, original_output_b0[1])
    block0_zeroed_logits_saved = wrapped.output[0].save()

block0_zeroed_logits_np = block0_zeroed_logits_saved.detach().cpu().numpy()
block0_zeroed_acc = accuracy_from_logits(block0_zeroed_logits_np)

# Count prediction changes vs baseline
baseline_preds = baseline_logits_np.argmax(axis=1)
block0_preds = block0_zeroed_logits_np.argmax(axis=1)
block0_pred_changes = int((baseline_preds != block0_preds).sum())

# ── Run 2: Zero block 1 output ────────────────────────────────────────────────
print("Running intervention: zero block 1 output...")
wrapped = NNsight(model)
with wrapped.trace(
    features, degree_features, attn_mask=attn_mask, collect_attention=False
):
    original_output_b1 = wrapped.blocks[1].output
    zeroed_hidden_b1 = original_output_b1[0] * 0.0
    wrapped.blocks[1].output = (zeroed_hidden_b1, original_output_b1[1])
    block1_zeroed_logits_saved = wrapped.output[0].save()

block1_zeroed_logits_np = block1_zeroed_logits_saved.detach().cpu().numpy()
block1_zeroed_acc = accuracy_from_logits(block1_zeroed_logits_np)

block1_preds = block1_zeroed_logits_np.argmax(axis=1)
block1_pred_changes = int((baseline_preds != block1_preds).sum())

# ── Compute accuracy drops ─────────────────────────────────────────────────────
n_nodes = graph.features.shape[0]

block0_test_drop = baseline_acc["test"] - block0_zeroed_acc["test"]
block1_test_drop = baseline_acc["test"] - block1_zeroed_acc["test"]

# ── Print results ─────────────────────────────────────────────────────────────
print()
print("=" * 65)
print("RESIDUAL STREAM ISOLATION RESULTS")
print("=" * 65)
print(
    f"  {'Condition':<22} {'Train':>7}  {'Val':>7}  {'Test':>7}  {'Pred Changes':>14}"
)
print(f"  {chr(8212)*60}")


def fmt(acc_dict, pred_changes=None):
    train = f"{acc_dict['train']:.3f}"
    val = f"{acc_dict['val']:.3f}"
    test = f"{acc_dict['test']:.3f}"
    if pred_changes is None:
        changes = "—"
    else:
        changes = f"{pred_changes}/{n_nodes}"
    return train, val, test, changes


t, v, te, c = fmt(baseline_acc)
print(f"  {'Baseline':<22} {t:>7}  {v:>7}  {te:>7}  {c:>14}")

t, v, te, c = fmt(block0_zeroed_acc, block0_pred_changes)
drop0_str = f"(Δtest={-block0_test_drop:+.3f})"
print(f"  {'Block 0 zeroed':<22} {t:>7}  {v:>7}  {te:>7}  {c:>14}  {drop0_str}")

t, v, te, c = fmt(block1_zeroed_acc, block1_pred_changes)
drop1_str = f"(Δtest={-block1_test_drop:+.3f})"
print(f"  {'Block 1 zeroed':<22} {t:>7}  {v:>7}  {te:>7}  {c:>14}  {drop1_str}")

print("=" * 65)

# ── Finding ────────────────────────────────────────────────────────────────────
if abs(block0_test_drop) > abs(block1_test_drop):
    more_important = 0
    less_important = 1
    drop_pct = block0_test_drop * 100
else:
    more_important = 1
    less_important = 0
    drop_pct = block1_test_drop * 100

print(
    f"FINDING: Block {more_important} contributes more "
    f"(zeroing it drops test accuracy by {drop_pct:.1f}pp)"
)

if block0_test_drop > 0 and block1_test_drop > 0:
    ratio = max(abs(block0_test_drop), abs(block1_test_drop)) / max(
        min(abs(block0_test_drop), abs(block1_test_drop)), 1e-6
    )
    print(f"         Block importance ratio: {ratio:.2f}x")
elif block0_test_drop <= 0 and block1_test_drop <= 0:
    print(
        "         NOTE: Both interventions *improved* accuracy — "
        "the trained model may rely on the classifier bypass path."
    )

print()
print("Accuracy drops when zeroed (positive = hurts accuracy):")
print(
    f"  Block 0 zeroed → test drop: {block0_test_drop:+.4f}  ({block0_pred_changes} prediction changes)"
)
print(
    f"  Block 1 zeroed → test drop: {block1_test_drop:+.4f}  ({block1_pred_changes} prediction changes)"
)
