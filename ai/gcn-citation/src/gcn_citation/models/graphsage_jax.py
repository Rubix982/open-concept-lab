from __future__ import annotations

"""JAX-backed GraphSAGE implementations."""

from dataclasses import dataclass
from functools import partial

import numpy as np

from ..data import GraphData
from .gcn import TrainingResult
from .gcn import accuracy
from .graphsage import _build_adjacency_lists
from .graphsage import _fanouts_for_depth
from .graphsage import _sample_neighbor_mean_matrix
from .graphsage import _sample_neighbors_for_node

try:
    import jax
    import jax.numpy as jnp
except ImportError:  # pragma: no cover
    jax = None
    jnp = None


@dataclass
class JAXGraphSAGEConfig:
    hidden_dims: list[int]
    fanouts: list[int]
    sampler: str
    aggregator: str
    epochs: int
    learning_rate: float
    weight_decay: float
    dropout: float
    seed: int


def jax_available() -> bool:
    return jax is not None and jnp is not None


def ensure_jax_available() -> None:
    if not jax_available():
        raise ImportError(
            "JAX is not installed. Add `jax` and `jaxlib` to the environment before using the JAX GraphSAGE backend."
        )


def numpy_to_jax(array: np.ndarray):
    ensure_jax_available()
    return jnp.asarray(array)


def build_jax_graph_inputs(graph: GraphData) -> dict[str, object]:
    ensure_jax_available()
    return {
        "features": numpy_to_jax(graph.features),
        "labels": numpy_to_jax(graph.labels.astype(np.int32)),
        "train_mask": numpy_to_jax(graph.train_mask.astype(np.float32)),
        "val_mask": numpy_to_jax(graph.val_mask.astype(np.float32)),
        "test_mask": numpy_to_jax(graph.test_mask.astype(np.float32)),
        "label_names": graph.label_names,
    }


def _glorot(rng: np.random.Generator, shape: tuple[int, int]) -> np.ndarray:
    limit = np.sqrt(6.0 / (shape[0] + shape[1]))
    return rng.uniform(-limit, limit, size=shape).astype(np.float32)


def _init_params(
    input_dim: int,
    hidden_dims: list[int],
    output_dim: int,
    rng: np.random.Generator,
    aggregator: str,
) -> dict[str, list[jnp.ndarray]]:
    layer_dims = [input_dim, *hidden_dims, output_dim]
    params: dict[str, list[jnp.ndarray]] = {
        "weights": [
            numpy_to_jax(_glorot(rng, (layer_dims[index] * 2, layer_dims[index + 1])))
            for index in range(len(layer_dims) - 1)
        ]
    }
    if aggregator == "lstm":
        params["lstm_input_weights"] = []
        params["lstm_hidden_weights"] = []
        params["lstm_biases"] = []
        for layer_input_dim in layer_dims[:-1]:
            params["lstm_input_weights"].append(numpy_to_jax(_glorot(rng, (layer_input_dim, layer_input_dim * 4))))
            params["lstm_hidden_weights"].append(numpy_to_jax(_glorot(rng, (layer_input_dim, layer_input_dim * 4))))
            params["lstm_biases"].append(jnp.zeros((layer_input_dim * 4,), dtype=jnp.float32))
    return params


def _build_sampled_neighbor_sequences(
    adjacency_lists: list[np.ndarray],
    node_degrees: np.ndarray,
    fanout: int,
    rng: np.random.Generator,
    sampler: str,
) -> tuple[np.ndarray, np.ndarray]:
    num_nodes = len(adjacency_lists)
    indices = np.zeros((num_nodes, fanout), dtype=np.int32)
    mask = np.zeros((num_nodes, fanout), dtype=np.float32)

    for node_index, neighbors in enumerate(adjacency_lists):
        if neighbors.shape[0] == 0:
            indices[node_index, :] = node_index
            continue

        if neighbors.shape[0] <= fanout and sampler != "with-replacement":
            chosen = neighbors
        else:
            chosen = _sample_neighbors_for_node(neighbors, node_degrees, fanout, rng, sampler)

        chosen_count = min(chosen.shape[0], fanout)
        if chosen_count > 0:
            indices[node_index, :chosen_count] = chosen[:chosen_count]
            mask[node_index, :chosen_count] = 1.0
        if chosen_count < fanout:
            indices[node_index, chosen_count:] = node_index

    return indices, mask


def _lstm_aggregate(
    current: jnp.ndarray,
    neighbor_indices: jnp.ndarray,
    neighbor_mask: jnp.ndarray,
    input_weight: jnp.ndarray,
    hidden_weight: jnp.ndarray,
    bias: jnp.ndarray,
) -> jnp.ndarray:
    neighbor_embeddings = current[neighbor_indices]
    hidden_dim = current.shape[1]
    batch_size = neighbor_embeddings.shape[0]
    initial_hidden = jnp.zeros((batch_size, hidden_dim), dtype=current.dtype)
    initial_cell = jnp.zeros((batch_size, hidden_dim), dtype=current.dtype)

    def step(carry, inputs):
        hidden_state, cell_state = carry
        x_t, mask_t = inputs
        gates = x_t @ input_weight + hidden_state @ hidden_weight + bias
        input_gate, forget_gate, output_gate, candidate = jnp.split(gates, 4, axis=1)
        input_gate = jax.nn.sigmoid(input_gate)
        forget_gate = jax.nn.sigmoid(forget_gate)
        output_gate = jax.nn.sigmoid(output_gate)
        candidate = jnp.tanh(candidate)
        next_cell = forget_gate * cell_state + input_gate * candidate
        next_hidden = output_gate * jnp.tanh(next_cell)
        mask_column = mask_t[:, None]
        masked_hidden = mask_column * next_hidden + (1.0 - mask_column) * hidden_state
        masked_cell = mask_column * next_cell + (1.0 - mask_column) * cell_state
        return (masked_hidden, masked_cell), masked_hidden

    (final_hidden, _), _ = jax.lax.scan(
        step,
        (initial_hidden, initial_cell),
        (jnp.swapaxes(neighbor_embeddings, 0, 1), jnp.swapaxes(neighbor_mask, 0, 1)),
    )
    return final_hidden


def _forward(
    params: dict[str, list[jnp.ndarray]],
    sampled_neighbor_matrices: list[jnp.ndarray],
    sampled_neighbor_sequences: list[tuple[jnp.ndarray, jnp.ndarray]] | None,
    features: jnp.ndarray,
    *,
    aggregator: str,
    dropout: float,
    training: bool,
    rng_key,
) -> tuple[jnp.ndarray, list[jnp.ndarray]]:
    current = features
    hidden_layers: list[jnp.ndarray] = []
    if training:
        keys = jax.random.split(rng_key, len(params["weights"]))
    else:
        keys = [rng_key for _ in params["weights"]]

    for layer_index, weight in enumerate(params["weights"]):
        if aggregator == "lstm":
            assert sampled_neighbor_sequences is not None
            neighbor_indices, neighbor_mask = sampled_neighbor_sequences[layer_index]
            neighbor_aggregate = _lstm_aggregate(
                current,
                neighbor_indices,
                neighbor_mask,
                params["lstm_input_weights"][layer_index],
                params["lstm_hidden_weights"][layer_index],
                params["lstm_biases"][layer_index],
            )
        else:
            neighbor_aggregate = sampled_neighbor_matrices[layer_index] @ current

        concat_input = jnp.concatenate([current, neighbor_aggregate], axis=1)
        pre_activation = concat_input @ weight
        is_output_layer = layer_index == len(params["weights"]) - 1

        if is_output_layer:
            current = pre_activation
        else:
            hidden = jax.nn.relu(pre_activation)
            if training and dropout > 0.0:
                keep_probability = 1.0 - dropout
                mask = jax.random.bernoulli(keys[layer_index], p=keep_probability, shape=hidden.shape)
                current = hidden * mask.astype(hidden.dtype) / keep_probability
            else:
                current = hidden
            hidden_layers.append(current)

    return current, hidden_layers


def _masked_cross_entropy(logits: jnp.ndarray, labels: jnp.ndarray, mask: jnp.ndarray) -> jnp.ndarray:
    log_probs = jax.nn.log_softmax(logits, axis=1)
    one_hot = jax.nn.one_hot(labels, logits.shape[1])
    per_node_loss = -jnp.sum(one_hot * log_probs, axis=1)
    normalizer = jnp.clip(jnp.sum(mask), a_min=1.0)
    return jnp.sum(per_node_loss * mask) / normalizer


def train_graphsage_jax(
    graph: GraphData,
    *,
    hidden_dims: list[int],
    fanouts: list[int],
    sampler: str,
    aggregator: str,
    variant: str,
    batch_size: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    dropout: float,
    seed: int,
) -> TrainingResult:
    ensure_jax_available()
    if variant != "v1":
        raise NotImplementedError("The current JAX GraphSAGE path supports only variant='v1'.")
    if aggregator not in {"mean", "lstm"}:
        raise NotImplementedError("The current JAX GraphSAGE path supports only aggregators 'mean' and 'lstm'.")

    _ = JAXGraphSAGEConfig(
        hidden_dims=hidden_dims,
        fanouts=fanouts,
        sampler=sampler,
        aggregator=aggregator,
        epochs=epochs,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        dropout=dropout,
        seed=seed,
    )

    np_rng = np.random.default_rng(seed)
    graph_inputs = build_jax_graph_inputs(graph)
    features = graph_inputs["features"]
    labels = graph_inputs["labels"]
    train_mask = graph_inputs["train_mask"]

    adjacency_lists = _build_adjacency_lists(graph.features.shape[0], graph.edges)
    node_degrees = np.asarray([neighbors.shape[0] for neighbors in adjacency_lists], dtype=np.int64)
    effective_fanouts = _fanouts_for_depth(len(hidden_dims) + 1, fanouts or [10, 5])

    sampled_neighbor_matrices_np = [
        _sample_neighbor_mean_matrix(
            adjacency_lists,
            node_degrees=node_degrees,
            fanout=fanout,
            rng=np_rng,
            sampler=sampler,
        )
        for fanout in effective_fanouts
    ]
    sampled_neighbor_matrices = [numpy_to_jax(matrix) for matrix in sampled_neighbor_matrices_np]

    sampled_neighbor_sequences = None
    if aggregator == "lstm":
        sampled_neighbor_sequences_np = [
            _build_sampled_neighbor_sequences(
                adjacency_lists,
                node_degrees=node_degrees,
                fanout=fanout,
                rng=np_rng,
                sampler=sampler,
            )
            for fanout in effective_fanouts
        ]
        sampled_neighbor_sequences = [
            (numpy_to_jax(indices), numpy_to_jax(mask))
            for indices, mask in sampled_neighbor_sequences_np
        ]

    params = _init_params(
        input_dim=graph.features.shape[1],
        hidden_dims=hidden_dims,
        output_dim=len(graph.label_names),
        rng=np_rng,
        aggregator=aggregator,
    )
    best_params = {key: [value.copy() for value in values] for key, values in params.items()}
    best_val_accuracy = -np.inf
    history: list[dict[str, float]] = []

    @partial(jax.jit, static_argnames=("training",))
    def predict(current_params, rng_key, *, training: bool):
        return _forward(
            current_params,
            sampled_neighbor_matrices,
            sampled_neighbor_sequences,
            features,
            aggregator=aggregator,
            dropout=dropout,
            training=training,
            rng_key=rng_key,
        )

    @jax.jit
    def train_step(current_params, rng_key):
        def loss_fn(model_params):
            logits, _ = predict(model_params, rng_key, training=True)
            data_loss = _masked_cross_entropy(logits, labels, train_mask)
            reg_loss = 0.5 * weight_decay * sum(
                jnp.sum(weight ** 2)
                for group in model_params.values()
                for weight in group
            )
            return data_loss + reg_loss

        loss, grads = jax.value_and_grad(loss_fn)(current_params)
        updated_params = {
            key: [
                weight - learning_rate * grad
                for weight, grad in zip(current_params[key], grads[key], strict=True)
            ]
            for key in current_params
        }
        return updated_params, loss

    rng_key = jax.random.PRNGKey(seed)

    for epoch in range(1, epochs + 1):
        rng_key, step_key, eval_key = jax.random.split(rng_key, 3)
        params, loss = train_step(params, step_key)
        eval_logits, hidden_layers = predict(params, eval_key, training=False)
        eval_logits_np = np.asarray(eval_logits)
        history.append(
            {
                "epoch": float(epoch),
                "loss": float(loss),
                "train_accuracy": accuracy(eval_logits_np, graph.labels, graph.train_mask),
                "val_accuracy": accuracy(eval_logits_np, graph.labels, graph.val_mask),
                "test_accuracy": accuracy(eval_logits_np, graph.labels, graph.test_mask),
            }
        )
        if history[-1]["val_accuracy"] > best_val_accuracy:
            best_val_accuracy = history[-1]["val_accuracy"]
            best_params = {key: [value.copy() for value in values] for key, values in params.items()}

    final_logits, final_hidden_layers = predict(best_params, rng_key, training=False)
    final_logits_np = np.asarray(final_logits)
    hidden_layers_np = [np.asarray(layer) for layer in final_hidden_layers]
    hidden_embeddings = hidden_layers_np[-1] if hidden_layers_np else final_logits_np

    metrics = {
        "train_accuracy": accuracy(final_logits_np, graph.labels, graph.train_mask),
        "val_accuracy": accuracy(final_logits_np, graph.labels, graph.val_mask),
        "test_accuracy": accuracy(final_logits_np, graph.labels, graph.test_mask),
        "num_train_nodes": int(graph.train_mask.sum()),
        "num_val_nodes": int(graph.val_mask.sum()),
        "num_test_nodes": int(graph.test_mask.sum()),
        "num_layers": int(len(hidden_dims) + 1),
    }

    return TrainingResult(
        metrics=metrics,
        hidden_embeddings=hidden_embeddings,
        logits=final_logits_np,
        history=history,
        layer_embeddings=hidden_layers_np,
        diagnostics={
            "backend": "jax",
            "variant": variant,
            "aggregator": aggregator,
            "sampler": sampler,
            "effective_fanouts": effective_fanouts,
            "batch_size": batch_size,
        },
    )
