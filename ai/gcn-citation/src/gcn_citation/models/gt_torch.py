from __future__ import annotations

"""PyTorch Graph Transformer baseline for node classification.

This implementation is intentionally practical rather than paper-complete:

- full-batch training over all nodes
- graph-aware attention mask built from the adjacency
- Transformer-style residual + feedforward blocks
- degree signal injected as a small structural feature

The goal is to give the repo a reusable `GT` path that feels like the next
conceptual step after GAT, while staying simple enough to learn from.
"""

from dataclasses import dataclass

import numpy as np

from ..data import GraphData
from .gcn import TrainingResult
from .gcn import accuracy
from .gt_nnsight import trace_gt_modules_with_nnsight

try:
    import torch
    import torch.nn as nn
except ImportError:  # pragma: no cover
    torch = None
    nn = None


def torch_available() -> bool:
    return torch is not None and nn is not None


def ensure_torch_available() -> None:
    if not torch_available():
        raise ImportError("PyTorch is not installed. Install `torch` before using the Graph Transformer model.")


@dataclass
class GTConfig:
    hidden_dim: int
    heads: int
    layers: int
    epochs: int
    learning_rate: float
    weight_decay: float
    dropout: float
    seed: int


def _build_attention_mask(num_nodes: int, edges: np.ndarray) -> np.ndarray:
    adjacency = np.zeros((num_nodes, num_nodes), dtype=bool)
    adjacency[edges[:, 0], edges[:, 1]] = True
    adjacency = np.logical_or(adjacency, adjacency.T)
    np.fill_diagonal(adjacency, True)
    # PyTorch MultiheadAttention uses True for positions that should be masked.
    return ~adjacency


def _degree_features(num_nodes: int, edges: np.ndarray) -> np.ndarray:
    adjacency = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    adjacency[edges[:, 0], edges[:, 1]] = 1.0
    adjacency = np.maximum(adjacency, adjacency.T)
    degree = adjacency.sum(axis=1, keepdims=True)
    return np.log1p(degree).astype(np.float32)


class GTBlock(nn.Module):
    """One graph-transformer block with masked multi-head self-attention."""

    def __init__(self, hidden_dim: int, heads: int, dropout: float) -> None:
        super().__init__()
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_dim,
            num_heads=heads,
            dropout=dropout,
            batch_first=True,
        )
        self.norm_1 = nn.LayerNorm(hidden_dim)
        self.ffn = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
        )
        self.norm_2 = nn.LayerNorm(hidden_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        hidden: torch.Tensor,
        *,
        attn_mask: torch.Tensor,
        need_weights: bool,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        attended, attention_weights = self.attention(
            hidden,
            hidden,
            hidden,
            attn_mask=attn_mask,
            need_weights=need_weights,
            average_attn_weights=False,
        )
        hidden = self.norm_1(hidden + self.dropout(attended))
        ff_hidden = self.ffn(hidden)
        hidden = self.norm_2(hidden + self.dropout(ff_hidden))
        return hidden, attention_weights


class GraphTransformer(nn.Module):
    """Graph-aware Transformer encoder for node classification."""

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        heads: int,
        layers: int,
        dropout: float,
    ) -> None:
        super().__init__()
        self.input_projection = nn.Linear(input_dim + 1, hidden_dim)
        self.blocks = nn.ModuleList([GTBlock(hidden_dim, heads, dropout) for _ in range(layers)])
        self.classifier = nn.Linear(hidden_dim, output_dim)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        features: torch.Tensor,
        degree_features: torch.Tensor,
        *,
        attn_mask: torch.Tensor,
        collect_attention: bool,
    ) -> tuple[torch.Tensor, list[torch.Tensor], list[torch.Tensor]]:
        hidden = torch.cat([features, degree_features], dim=1)
        hidden = self.dropout(self.input_projection(hidden))
        hidden = hidden.unsqueeze(0)

        hidden_layers: list[torch.Tensor] = []
        attention_layers: list[torch.Tensor] = []

        for block in self.blocks:
            hidden, attention = block(
                hidden,
                attn_mask=attn_mask,
                need_weights=collect_attention,
            )
            hidden_layers.append(hidden.squeeze(0))
            if attention is not None:
                attention_layers.append(attention.squeeze(0))

        logits = self.classifier(hidden.squeeze(0))
        return logits, hidden_layers, attention_layers


def _masked_cross_entropy(logits: torch.Tensor, labels: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    active_indices = torch.where(mask)[0]
    return nn.functional.cross_entropy(logits[active_indices], labels[active_indices])


def _summarize_attention_layers(
    attention_layers: list[np.ndarray],
    adjacency_mask: np.ndarray,
    *,
    max_nodes: int = 5,
    top_k_neighbors: int = 3,
) -> dict[str, object]:
    summaries: list[dict[str, object]] = []
    for layer_index, attention in enumerate(attention_layers):
        # attention shape after squeeze: [heads, source_node, target_node]
        head_summaries: list[dict[str, object]] = []
        for head_index in range(attention.shape[0]):
            head_attention = attention[head_index]
            allowed = ~adjacency_mask
            neighbor_counts = np.clip(allowed.sum(axis=1), 1, None)
            entropy = -np.sum(head_attention * np.log(np.clip(head_attention, 1e-12, None)), axis=1)
            normalized_entropy = entropy / np.log(neighbor_counts)
            normalized_entropy = np.nan_to_num(normalized_entropy, nan=0.0, posinf=0.0, neginf=0.0)
            node_indices = np.arange(head_attention.shape[0], dtype=np.int32)
            self_attention = head_attention[node_indices, node_indices]
            max_attention = head_attention.max(axis=1)

            sample_nodes: list[dict[str, object]] = []
            for node_index in range(min(max_nodes, head_attention.shape[0])):
                neighbor_indices = np.flatnonzero(allowed[node_index])
                ranked = neighbor_indices[np.argsort(head_attention[node_index, neighbor_indices])[::-1]]
                top_indices = ranked[:top_k_neighbors]
                sample_nodes.append(
                    {
                        "node_index": int(node_index),
                        "top_neighbors": [
                            {
                                "neighbor_index": int(neighbor_index),
                                "attention": float(head_attention[node_index, neighbor_index]),
                            }
                            for neighbor_index in top_indices
                        ],
                    }
                )

            head_summaries.append(
                {
                    "head_index": head_index,
                    "mean_entropy": float(normalized_entropy.mean()),
                    "mean_self_attention": float(self_attention.mean()),
                    "mean_max_attention": float(max_attention.mean()),
                    "sample_nodes": sample_nodes,
                }
            )

        summaries.append({"layer_index": layer_index, "num_heads": attention.shape[0], "heads": head_summaries})

    return {"attention_layers": summaries}


def train_gt_torch(
    graph: GraphData,
    *,
    hidden_dim: int,
    heads: int,
    layers: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    dropout: float,
    seed: int,
    trace_with_nnsight: bool = False,
) -> TrainingResult:
    ensure_torch_available()
    _ = GTConfig(
        hidden_dim=hidden_dim,
        heads=heads,
        layers=layers,
        epochs=epochs,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        dropout=dropout,
        seed=seed,
    )

    torch.manual_seed(seed)
    np.random.seed(seed)

    features = torch.tensor(graph.features, dtype=torch.float32)
    degree_features = torch.tensor(_degree_features(graph.features.shape[0], graph.edges), dtype=torch.float32)
    labels = torch.tensor(graph.labels, dtype=torch.long)
    train_mask = torch.tensor(graph.train_mask, dtype=torch.bool)
    attention_mask = torch.tensor(_build_attention_mask(graph.features.shape[0], graph.edges), dtype=torch.bool)

    model = GraphTransformer(
        input_dim=graph.features.shape[1],
        hidden_dim=hidden_dim,
        output_dim=len(graph.label_names),
        heads=heads,
        layers=layers,
        dropout=dropout,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    history: list[dict[str, float]] = []
    best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}
    best_val_accuracy = -np.inf

    for epoch in range(1, epochs + 1):
        model.train()
        optimizer.zero_grad()
        logits, _, _ = model(features, degree_features, attn_mask=attention_mask, collect_attention=False)
        loss = _masked_cross_entropy(logits, labels, train_mask)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            eval_logits, hidden_layers, _ = model(features, degree_features, attn_mask=attention_mask, collect_attention=False)
        eval_logits_np = eval_logits.detach().cpu().numpy()
        history.append(
            {
                "epoch": float(epoch),
                "loss": float(loss.detach().cpu().item()),
                "train_accuracy": accuracy(eval_logits_np, graph.labels, graph.train_mask),
                "val_accuracy": accuracy(eval_logits_np, graph.labels, graph.val_mask),
                "test_accuracy": accuracy(eval_logits_np, graph.labels, graph.test_mask),
            }
        )
        if history[-1]["val_accuracy"] > best_val_accuracy:
            best_val_accuracy = history[-1]["val_accuracy"]
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        final_logits, final_hidden_layers, final_attention_layers = model(
            features,
            degree_features,
            attn_mask=attention_mask,
            collect_attention=True,
        )

    final_logits_np = final_logits.detach().cpu().numpy()
    hidden_layers_np = [layer.detach().cpu().numpy() for layer in final_hidden_layers]
    attention_layers_np = [layer.detach().cpu().numpy() for layer in final_attention_layers]
    hidden_embeddings = hidden_layers_np[-1] if hidden_layers_np else final_logits_np

    metrics = {
        "train_accuracy": accuracy(final_logits_np, graph.labels, graph.train_mask),
        "val_accuracy": accuracy(final_logits_np, graph.labels, graph.val_mask),
        "test_accuracy": accuracy(final_logits_np, graph.labels, graph.test_mask),
        "num_train_nodes": int(graph.train_mask.sum()),
        "num_val_nodes": int(graph.val_mask.sum()),
        "num_test_nodes": int(graph.test_mask.sum()),
        "num_layers": int(layers + 1),
    }

    return TrainingResult(
        metrics=metrics,
        hidden_embeddings=hidden_embeddings,
        logits=final_logits_np,
        history=history,
        layer_embeddings=hidden_layers_np,
        diagnostics={
            "backend": "torch",
            "heads": heads,
            "layers": layers,
            "nnsight_enabled": trace_with_nnsight,
            **_summarize_attention_layers(attention_layers_np, np.asarray(attention_mask)),
            **(
                {
                    "nnsight_trace": trace_gt_modules_with_nnsight(
                        model,
                        features=features,
                        degree_features=degree_features,
                        attn_mask=attention_mask,
                    )
                }
                if trace_with_nnsight
                else {}
            ),
        },
    )
