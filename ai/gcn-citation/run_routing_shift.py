"""Attention routing shift experiment for the Graph Transformer.

Trains a GT on Cora, then asks: does zeroing block 0's output change
*which* neighbors block 1 attends to (routing), or only *what values*
get aggregated?

Run:
    python3 run_routing_shift.py
"""

from __future__ import annotations

import torch

from pathlib import Path

from src.gcn_citation.data import ensure_cora_dataset, load_graph_data
from src.gcn_citation.models.gt_nnsight import compare_attention_routing_with_nnsight
from src.gcn_citation.models.gt_torch import (
    GraphTransformer,
    _build_attention_mask,
    _degree_features,
)

import numpy as np

# ── Config ────────────────────────────────────────────────────────────────────
HIDDEN_DIM = 64
HEADS = 4
LAYERS = 2
EPOCHS = 200
LR = 1e-3
WEIGHT_DECAY = 5e-4
DROPOUT = 0.1
SEED = 42

# ── Data ──────────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
print("Loading Cora...")
ensure_cora_dataset(DATA_DIR)
graph = load_graph_data(
    data_dir=DATA_DIR, db_path=Path("/tmp/routing_shift_cora.duckdb"), seed=SEED
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

# ── Experiment ────────────────────────────────────────────────────────────────
print("\nRunning routing shift experiment...")
print("  Baseline: normal forward pass, capture block-1 attention weights")
print("  Patched:  zero block-0 output, then capture block-1 attention weights")
print()

result = compare_attention_routing_with_nnsight(
    model,
    features=features,
    degree_features=degree_features,
    attn_mask=attn_mask,
    patch_block_index=0,
    observe_block_index=1,
)

# ── Print results ─────────────────────────────────────────────────────────────
rs = result["routing_shift"]
ls = result["logit_shift"]

print("=" * 60)
print("ROUTING SHIFT SUMMARY")
print("=" * 60)
print(f"  Nodes: {rs['num_nodes']}  |  Heads: {rs['num_heads']}")
print(f"  Overall mean shift: {rs['overall_mean_shift']:.4f}")
print(f"  Overall max  shift: {rs['overall_max_shift']:.4f}")
print()

for head in rs["heads"]:
    h = head["head_index"]
    print(
        f"  Head {h}:  mean shift = {head['mean_routing_shift']:.4f}  |  max = {head['max_routing_shift']:.4f}"
    )
    for node in head["top_shifted_nodes"]:
        changed = "CHANGED" if node["top_neighbor_changed"] else "same"
        print(
            f"    node {node['node_index']:4d}  shift={node['mean_shift']:.4f}"
            f"  baseline top→{node['baseline_top_neighbor']:4d}"
            f"  patched top→{node['patched_top_neighbor']:4d}"
            f"  [{changed}]"
        )
    print()

print("=" * 60)
print("LOGIT SHIFT (downstream effect on predictions)")
print("=" * 60)
print(f"  Mean abs logit shift:    {ls['mean_abs_logit_shift']:.4f}")
print(
    f"  Prediction changes:      {ls['num_prediction_changes']} / {rs['num_nodes']} nodes"
)
print()
