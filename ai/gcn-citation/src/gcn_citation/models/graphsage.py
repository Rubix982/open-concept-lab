from __future__ import annotations

import time
from dataclasses import dataclass

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
    node_degrees: np.ndarray,
    fanout: int,
    rng: np.random.Generator,
    sampler: str,
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
            chosen = _sample_neighbors_for_node(neighbors, node_degrees, fanout, rng, sampler)
        unique_neighbors, weights = _sample_weights(chosen)
        sampled[node_index, unique_neighbors] = weights

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


def _sample_neighbors_for_node(
    neighbors: np.ndarray,
    node_degrees: np.ndarray,
    fanout: int,
    rng: np.random.Generator,
    sampler: str,
) -> np.ndarray:
    if neighbors.shape[0] == 0:
        return neighbors
    if sampler in {"uniform", "degree-weighted"} and neighbors.shape[0] <= fanout:
        return neighbors

    if sampler == "uniform":
        return np.asarray(rng.choice(neighbors, size=fanout, replace=False), dtype=np.int64)

    if sampler == "with-replacement":
        return np.asarray(rng.choice(neighbors, size=fanout, replace=True), dtype=np.int64)

    if sampler == "degree-weighted":
        neighbor_weights = node_degrees[neighbors].astype(np.float64)
        neighbor_weights = np.clip(neighbor_weights, 1.0, None)
        probabilities = neighbor_weights / neighbor_weights.sum()
        return np.asarray(rng.choice(neighbors, size=fanout, replace=False, p=probabilities), dtype=np.int64)

    raise ValueError(f"Unsupported GraphSAGE sampler: {sampler}")


def _sample_weights(chosen: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if chosen.shape[0] == 0:
        return chosen, np.asarray([], dtype=np.float32)
    unique_neighbors, counts = np.unique(chosen, return_counts=True)
    weights = counts.astype(np.float32) / float(chosen.shape[0])
    return unique_neighbors.astype(np.int64), weights


@dataclass
class LayerBatchContext:
    active_nodes: np.ndarray
    expanded_nodes: np.ndarray
    sampled_map: dict[int, np.ndarray]


@dataclass
class BatchSubgraph:
    local_nodes: np.ndarray
    layer_contexts: list[LayerBatchContext]


@dataclass
class BatchDiagnostics:
    target_nodes: int
    local_nodes: int
    sampled_links: int
    layer_active_counts: list[int]
    layer_expanded_counts: list[int]


def _batch_layer_contexts(
    target_nodes: np.ndarray,
    adjacency_lists: list[np.ndarray],
    node_degrees: np.ndarray,
    fanouts: list[int],
    rng: np.random.Generator,
    sampler: str,
) -> BatchSubgraph:
    layer_contexts_rev: list[LayerBatchContext] = []
    current_targets = np.asarray(sorted(set(target_nodes.tolist())), dtype=np.int64)

    for fanout in reversed(fanouts):
        sampled_map: dict[int, np.ndarray] = {}
        expanded: set[int] = set(current_targets.tolist())
        for node_idx in current_targets:
            chosen = _sample_neighbors_for_node(adjacency_lists[int(node_idx)], node_degrees, fanout, rng, sampler)
            sampled_map[int(node_idx)] = chosen
            expanded.update(int(neighbor) for neighbor in chosen.tolist())

        expanded_nodes = np.asarray(sorted(expanded), dtype=np.int64)
        layer_contexts_rev.append(
            LayerBatchContext(
                active_nodes=current_targets,
                expanded_nodes=expanded_nodes,
                sampled_map=sampled_map,
            )
        )
        current_targets = expanded_nodes

    return BatchSubgraph(
        local_nodes=current_targets,
        layer_contexts=list(reversed(layer_contexts_rev)),
    )


def _batch_diagnostics(batch_subgraph: BatchSubgraph) -> BatchDiagnostics:
    sampled_links = sum(
        int(sum(neighbors.shape[0] for neighbors in context.sampled_map.values()))
        for context in batch_subgraph.layer_contexts
    )
    return BatchDiagnostics(
        target_nodes=int(batch_subgraph.layer_contexts[-1].active_nodes.shape[0]) if batch_subgraph.layer_contexts else 0,
        local_nodes=int(batch_subgraph.local_nodes.shape[0]),
        sampled_links=sampled_links,
        layer_active_counts=[int(context.active_nodes.shape[0]) for context in batch_subgraph.layer_contexts],
        layer_expanded_counts=[int(context.expanded_nodes.shape[0]) for context in batch_subgraph.layer_contexts],
    )


def _local_row_stochastic_matrix(
    local_nodes: np.ndarray,
    active_nodes: np.ndarray,
    sampled_map: dict[int, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    node_to_local = {int(node): index for index, node in enumerate(local_nodes.tolist())}
    matrix = np.zeros((local_nodes.shape[0], local_nodes.shape[0]), dtype=np.float32)
    active_mask = np.zeros(local_nodes.shape[0], dtype=bool)

    for node in active_nodes:
        local_row = node_to_local[int(node)]
        active_mask[local_row] = True
        chosen = sampled_map.get(int(node), np.asarray([], dtype=np.int64))
        if chosen.shape[0] == 0:
            matrix[local_row, local_row] = 1.0
            continue
        local_neighbors = [node_to_local[int(neighbor)] for neighbor in chosen if int(neighbor) in node_to_local]
        if not local_neighbors:
            matrix[local_row, local_row] = 1.0
            continue
        unique_neighbors, weights = _sample_weights(np.asarray(local_neighbors, dtype=np.int64))
        matrix[local_row, unique_neighbors] = weights

    return matrix, active_mask


@dataclass
class GraphSAGETrainingDiagnostics:
    variant: str
    sampler: str
    batch_size: int
    effective_fanouts: list[int]
    num_batches_last_epoch: int
    avg_target_nodes_per_batch: float
    avg_local_nodes_per_batch: float
    avg_sampled_links_per_batch: float
    avg_layer_active_counts: list[float]
    avg_layer_expanded_counts: list[float]
    avg_epoch_seconds: float
    total_training_seconds: float


def train_graphsage(
    graph: GraphData,
    hidden_dim: int = 16,
    hidden_dims: list[int] | None = None,
    fanouts: list[int] | None = None,
    variant: str = "v1",
    batch_size: int = 64,
    sampler: str = "uniform",
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
    node_degrees = np.asarray([neighbors.shape[0] for neighbors in adjacency_lists], dtype=np.int64)
    effective_fanouts = _fanouts_for_depth(len(model.weights), fanouts or [10, 5])
    sampled_neighbor_matrices = [
        _sample_neighbor_mean_matrix(
            adjacency_lists,
            node_degrees=node_degrees,
            fanout=fanout,
            rng=rng,
            sampler=sampler,
        )
        for fanout in effective_fanouts
    ]

    history: list[dict[str, float]] = []
    best_state = model.state_dict()
    best_val_accuracy = -np.inf
    train_indices = np.where(graph.train_mask)[0]
    epoch_durations: list[float] = []
    total_batch_count = 0
    total_target_nodes = 0
    total_local_nodes = 0
    total_sampled_links = 0
    batch_count_last_epoch = 0
    layer_active_sums = [0.0 for _ in effective_fanouts]
    layer_expanded_sums = [0.0 for _ in effective_fanouts]

    if variant not in {"v1", "v2"}:
        raise ValueError(f"Unsupported GraphSAGE variant: {variant}")
    if sampler not in {"uniform", "with-replacement", "degree-weighted"}:
        raise ValueError(f"Unsupported GraphSAGE sampler: {sampler}")

    for epoch in range(1, epochs + 1):
        epoch_start = time.perf_counter()
        if variant == "v1":
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
            batch_count_last_epoch = 1
            total_batch_count += 1
            total_target_nodes += int(train_indices.shape[0])
            total_local_nodes += int(graph.features.shape[0])
            total_sampled_links += int(sum(np.count_nonzero(matrix) for matrix in sampled_neighbor_matrices))
            for layer_index in range(len(effective_fanouts)):
                layer_active_sums[layer_index] += float(graph.features.shape[0])
                layer_expanded_sums[layer_index] += float(graph.features.shape[0])
        else:
            shuffled_train = rng.permutation(train_indices)
            batch_losses: list[float] = []
            batch_count_last_epoch = 0
            for batch_start in range(0, shuffled_train.shape[0], batch_size):
                batch_targets = shuffled_train[batch_start : batch_start + batch_size]
                batch_subgraph = _batch_layer_contexts(
                    batch_targets,
                    adjacency_lists,
                    node_degrees,
                    effective_fanouts,
                    rng,
                    sampler,
                )
                batch_diagnostics = _batch_diagnostics(batch_subgraph)
                local_nodes = batch_subgraph.local_nodes
                layer_contexts = batch_subgraph.layer_contexts
                local_features = graph.features[local_nodes]
                local_labels = graph.labels[local_nodes]
                local_train_mask = np.isin(local_nodes, batch_targets)
                batch_count_last_epoch += 1
                total_batch_count += 1
                total_target_nodes += batch_diagnostics.target_nodes
                total_local_nodes += batch_diagnostics.local_nodes
                total_sampled_links += batch_diagnostics.sampled_links
                for layer_index in range(len(effective_fanouts)):
                    layer_active_sums[layer_index] += float(batch_diagnostics.layer_active_counts[layer_index])
                    layer_expanded_sums[layer_index] += float(batch_diagnostics.layer_expanded_counts[layer_index])

                local_matrices: list[np.ndarray] = []
                active_masks: list[np.ndarray] = []
                for context in layer_contexts:
                    matrix, active_mask = _local_row_stochastic_matrix(
                        local_nodes=local_nodes,
                        active_nodes=context.active_nodes,
                        sampled_map=context.sampled_map,
                    )
                    local_matrices.append(matrix)
                    active_masks.append(active_mask)

                logits, _, layer_caches = model.forward(local_matrices, local_features, training=True)
                data_loss, grad_logits = masked_cross_entropy(logits, local_labels, local_train_mask)
                reg_loss = 0.5 * weight_decay * sum(np.sum(weight ** 2) for weight in model.weights)
                batch_losses.append(data_loss + float(reg_loss))

                grads = [np.zeros_like(weight, dtype=np.float32) for weight in model.weights]
                grad_current = grad_logits

                for layer_index in range(len(model.weights) - 1, -1, -1):
                    cache = layer_caches[layer_index]
                    active_mask = active_masks[layer_index][:, None].astype(np.float32)
                    masked_grad_current = grad_current * active_mask
                    grads[layer_index] = cache["concat_input"].T @ masked_grad_current + weight_decay * model.weights[layer_index]

                    if layer_index == 0:
                        continue

                    grad_concat = masked_grad_current @ model.weights[layer_index].T
                    input_dim = int(cache["input_dim"][0])
                    grad_self = grad_concat[:, :input_dim]
                    grad_neighbors = grad_concat[:, input_dim:]
                    grad_previous = grad_self + cache["sampled_neighbor_matrix"].T @ grad_neighbors
                    previous_cache = layer_caches[layer_index - 1]
                    prev_active_mask = active_masks[layer_index - 1][:, None].astype(np.float32)
                    grad_previous_hidden = grad_previous * previous_cache["dropout_mask"] * prev_active_mask
                    grad_current = grad_previous_hidden * (previous_cache["pre_activation"] > 0)

                for layer_index, grad_weight in enumerate(grads):
                    model.weights[layer_index] -= learning_rate * grad_weight.astype(np.float32)

            loss = float(np.mean(batch_losses))

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
        epoch_durations.append(time.perf_counter() - epoch_start)

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
        "avg_epoch_seconds": float(np.mean(epoch_durations)),
    }
    diagnostics = GraphSAGETrainingDiagnostics(
        variant=variant,
        sampler=sampler,
        batch_size=batch_size,
        effective_fanouts=effective_fanouts,
        num_batches_last_epoch=batch_count_last_epoch,
        avg_target_nodes_per_batch=float(total_target_nodes / max(1, total_batch_count)),
        avg_local_nodes_per_batch=float(total_local_nodes / max(1, total_batch_count)),
        avg_sampled_links_per_batch=float(total_sampled_links / max(1, total_batch_count)),
        avg_layer_active_counts=[value / max(1, total_batch_count) for value in layer_active_sums],
        avg_layer_expanded_counts=[value / max(1, total_batch_count) for value in layer_expanded_sums],
        avg_epoch_seconds=float(np.mean(epoch_durations)),
        total_training_seconds=float(np.sum(epoch_durations)),
    )
    metrics["num_batches_last_epoch"] = float(diagnostics.num_batches_last_epoch)
    metrics["avg_local_nodes_per_batch"] = diagnostics.avg_local_nodes_per_batch

    hidden_embeddings = hidden_layers[-1] if hidden_layers else final_logits
    return TrainingResult(
        metrics=metrics,
        hidden_embeddings=hidden_embeddings,
        logits=final_logits,
        history=history,
        layer_embeddings=hidden_layers,
        diagnostics={
            "variant": diagnostics.variant,
            "sampler": diagnostics.sampler,
            "batch_size": diagnostics.batch_size,
            "effective_fanouts": diagnostics.effective_fanouts,
            "num_batches_last_epoch": diagnostics.num_batches_last_epoch,
            "avg_target_nodes_per_batch": diagnostics.avg_target_nodes_per_batch,
            "avg_local_nodes_per_batch": diagnostics.avg_local_nodes_per_batch,
            "avg_sampled_links_per_batch": diagnostics.avg_sampled_links_per_batch,
            "avg_layer_active_counts": diagnostics.avg_layer_active_counts,
            "avg_layer_expanded_counts": diagnostics.avg_layer_expanded_counts,
            "avg_epoch_seconds": diagnostics.avg_epoch_seconds,
            "total_training_seconds": diagnostics.total_training_seconds,
        },
    )
