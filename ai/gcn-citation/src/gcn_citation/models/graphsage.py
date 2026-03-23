from __future__ import annotations

import numpy as np

from ..data import GraphData
from .gcn import TrainingResult
from .gcn import accuracy
from .gcn import masked_cross_entropy


def _build_adjacency_lists(num_nodes: int, edges: np.ndarray) -> list[np.ndarray]:
    neighbors: list[list[int]] = [[] for _ in range(num_nodes)]
    for src_idx, dst_idx in edges:
        neighbors[int(src_idx)].append(int(dst_idx))
    return [np.asarray(sorted(set(node_neighbors)), dtype=np.int64) for node_neighbors in neighbors]


def _sample_neighbor_mean_matrix(
    adjacency_lists: list[np.ndarray],
    fanout: int,
    rng: np.random.Generator,
) -> np.ndarray:
    num_nodes = len(adjacency_lists)
    sampled = np.zeros((num_nodes, num_nodes), dtype=np.float32)

    for node_index, neighbors in enumerate(adjacency_lists):
        if neighbors.shape[0] == 0:
            sampled[node_index, node_index] = 1.0
            continue

        if neighbors.shape[0] <= fanout:
            chosen = neighbors
        else:
            chosen = rng.choice(neighbors, size=fanout, replace=False)
        sampled[node_index, chosen] = 1.0 / float(chosen.shape[0])

    return sampled


class ManualGraphSAGE:
    """Mean-aggregator GraphSAGE.

    Each layer samples a fixed-size neighborhood, computes the mean neighbor
    representation, concatenates it with the node's current representation, and
    then applies a learned linear transform.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dims: list[int],
        output_dim: int,
        rng: np.random.Generator,
        dropout: float = 0.5,
    ) -> None:
        self.rng = rng
        self.dropout = dropout
        layer_dims = [input_dim, *hidden_dims, output_dim]
        self.weights = [
            self._glorot((layer_dims[index] * 2, layer_dims[index + 1]))
            for index in range(len(layer_dims) - 1)
        ]

    def _glorot(self, shape: tuple[int, int]) -> np.ndarray:
        limit = np.sqrt(6.0 / (shape[0] + shape[1]))
        return self.rng.uniform(-limit, limit, size=shape).astype(np.float32)

    def state_dict(self) -> list[np.ndarray]:
        return [weight.copy() for weight in self.weights]

    def load_state_dict(self, weights: list[np.ndarray]) -> None:
        self.weights = [weight.copy() for weight in weights]

    def forward(
        self,
        sampled_neighbor_matrices: list[np.ndarray],
        features: np.ndarray,
        training: bool,
    ) -> tuple[np.ndarray, list[np.ndarray], list[dict[str, np.ndarray]]]:
        activations = [features]
        layer_caches: list[dict[str, np.ndarray]] = []
        current = features

        for layer_index, weight in enumerate(self.weights):
            neighbor_mean = sampled_neighbor_matrices[layer_index] @ current
            concat_input = np.concatenate([current, neighbor_mean], axis=1)
            pre_activation = concat_input @ weight
            is_output_layer = layer_index == len(self.weights) - 1

            if is_output_layer:
                current = pre_activation
                dropout_mask = np.ones_like(current, dtype=np.float32)
            else:
                hidden = np.maximum(pre_activation, 0.0)
                if training and self.dropout > 0.0:
                    dropout_mask = (self.rng.random(hidden.shape) >= self.dropout).astype(np.float32)
                    dropout_mask /= 1.0 - self.dropout
                else:
                    dropout_mask = np.ones_like(hidden, dtype=np.float32)
                current = hidden * dropout_mask

            layer_caches.append(
                {
                    "concat_input": concat_input,
                    "pre_activation": pre_activation,
                    "dropout_mask": dropout_mask,
                    "sampled_neighbor_matrix": sampled_neighbor_matrices[layer_index],
                    "input_dim": np.array([activations[-1].shape[1]], dtype=np.int64),
                }
            )
            activations.append(current)

        logits = activations[-1]
        hidden_layers = activations[1:-1]
        return logits, hidden_layers, layer_caches


def _fanouts_for_depth(num_layers: int, fanouts: list[int]) -> list[int]:
    if not fanouts:
        return [10 for _ in range(num_layers)]
    if len(fanouts) >= num_layers:
        return fanouts[:num_layers]
    return [*fanouts, *([fanouts[-1]] * (num_layers - len(fanouts)))]


def train_graphsage(
    graph: GraphData,
    hidden_dim: int = 16,
    hidden_dims: list[int] | None = None,
    fanouts: list[int] | None = None,
    epochs: int = 250,
    learning_rate: float = 0.2,
    weight_decay: float = 5e-4,
    dropout: float = 0.5,
    seed: int = 7,
) -> TrainingResult:
    rng = np.random.default_rng(seed)
    effective_hidden_dims = [hidden_dim] if hidden_dims is None else hidden_dims
    model = ManualGraphSAGE(
        input_dim=graph.features.shape[1],
        hidden_dims=effective_hidden_dims,
        output_dim=len(graph.label_names),
        rng=rng,
        dropout=dropout,
    )

    adjacency_lists = _build_adjacency_lists(graph.features.shape[0], graph.edges)
    effective_fanouts = _fanouts_for_depth(len(model.weights), fanouts or [10, 5])
    sampled_neighbor_matrices = [
        _sample_neighbor_mean_matrix(adjacency_lists, fanout=fanout, rng=rng)
        for fanout in effective_fanouts
    ]

    history: list[dict[str, float]] = []
    best_state = model.state_dict()
    best_val_accuracy = -np.inf

    for epoch in range(1, epochs + 1):
        logits, _, layer_caches = model.forward(sampled_neighbor_matrices, graph.features, training=True)
        data_loss, grad_logits = masked_cross_entropy(logits, graph.labels, graph.train_mask)
        reg_loss = 0.5 * weight_decay * sum(np.sum(weight ** 2) for weight in model.weights)
        loss = data_loss + float(reg_loss)

        grads = [np.zeros_like(weight, dtype=np.float32) for weight in model.weights]
        grad_current = grad_logits

        for layer_index in range(len(model.weights) - 1, -1, -1):
            cache = layer_caches[layer_index]
            grads[layer_index] = cache["concat_input"].T @ grad_current + weight_decay * model.weights[layer_index]

            if layer_index == 0:
                continue

            grad_concat = grad_current @ model.weights[layer_index].T
            input_dim = int(cache["input_dim"][0])
            grad_self = grad_concat[:, :input_dim]
            grad_neighbors = grad_concat[:, input_dim:]
            grad_previous = grad_self + cache["sampled_neighbor_matrix"].T @ grad_neighbors
            previous_cache = layer_caches[layer_index - 1]
            grad_previous_hidden = grad_previous * previous_cache["dropout_mask"]
            grad_current = grad_previous_hidden * (previous_cache["pre_activation"] > 0)

        for layer_index, grad_weight in enumerate(grads):
            model.weights[layer_index] -= learning_rate * grad_weight.astype(np.float32)

        eval_logits, _, _ = model.forward(sampled_neighbor_matrices, graph.features, training=False)
        history.append(
            {
                "epoch": float(epoch),
                "loss": float(loss),
                "train_accuracy": accuracy(eval_logits, graph.labels, graph.train_mask),
                "val_accuracy": accuracy(eval_logits, graph.labels, graph.val_mask),
                "test_accuracy": accuracy(eval_logits, graph.labels, graph.test_mask),
            }
        )

        if history[-1]["val_accuracy"] > best_val_accuracy:
            best_val_accuracy = history[-1]["val_accuracy"]
            best_state = model.state_dict()

    model.load_state_dict(best_state)
    final_logits, hidden_layers, _ = model.forward(sampled_neighbor_matrices, graph.features, training=False)
    metrics = {
        "train_accuracy": accuracy(final_logits, graph.labels, graph.train_mask),
        "val_accuracy": accuracy(final_logits, graph.labels, graph.val_mask),
        "test_accuracy": accuracy(final_logits, graph.labels, graph.test_mask),
        "num_train_nodes": int(graph.train_mask.sum()),
        "num_val_nodes": int(graph.val_mask.sum()),
        "num_test_nodes": int(graph.test_mask.sum()),
        "num_layers": int(len(model.weights)),
    }

    hidden_embeddings = hidden_layers[-1] if hidden_layers else final_logits
    return TrainingResult(
        metrics=metrics,
        hidden_embeddings=hidden_embeddings,
        logits=final_logits,
        history=history,
        layer_embeddings=hidden_layers,
    )
