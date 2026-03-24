from __future__ import annotations

"""JAX-backed GraphSAGE implementations.

This module starts with a deliberately small but real JAX training path:

- full-batch GraphSAGE
- mean aggregation
- shared sampler logic from the NumPy GraphSAGE path

That gives the project a working JAX backend before moving on to the more
ambitious LSTM aggregator.
"""

from dataclasses import dataclass
from functools import partial

import numpy as np

from ..data import GraphData
from .gcn import TrainingResult
from .gcn import accuracy
from .graphsage import _build_adjacency_lists
from .graphsage import _fanouts_for_depth
from .graphsage import _sample_neighbor_mean_matrix

try:
    import jax
    import jax.numpy as jnp
except ImportError:  # pragma: no cover - exercised only when JAX is unavailable
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
    """Convert the existing GraphData container into JAX-friendly arrays."""

    ensure_jax_available()
    return {
        "features": numpy_to_jax(graph.features),
        "labels": numpy_to_jax(graph.labels.astype(np.int32)),
        "edges": numpy_to_jax(graph.edges.astype(np.int32)),
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
) -> dict[str, list[jnp.ndarray]]:
    layer_dims = [input_dim, *hidden_dims, output_dim]
    weights = [
        numpy_to_jax(_glorot(rng, (layer_dims[index] * 2, layer_dims[index + 1])))
        for index in range(len(layer_dims) - 1)
    ]
    return {"weights": weights}


def _forward(
    params: dict[str, list[jnp.ndarray]],
    sampled_neighbor_matrices: list[jnp.ndarray],
    features: jnp.ndarray,
    *,
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
        neighbor_mean = sampled_neighbor_matrices[layer_index] @ current
        concat_input = jnp.concatenate([current, neighbor_mean], axis=1)
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


def _masked_cross_entropy(
    logits: jnp.ndarray,
    labels: jnp.ndarray,
    mask: jnp.ndarray,
) -> jnp.ndarray:
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
    """Train a first real JAX GraphSAGE path.

    Current scope:
    - full-batch GraphSAGE only (`variant="v1"`)
    - mean aggregation only
    - shared sampler logic with the NumPy implementation
    """

    ensure_jax_available()
    if variant != "v1":
        raise NotImplementedError("The first JAX GraphSAGE path currently supports only variant='v1'.")
    if aggregator != "mean":
        raise NotImplementedError("The first JAX GraphSAGE path currently supports only aggregator='mean'.")

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

    params = _init_params(
        input_dim=graph.features.shape[1],
        hidden_dims=hidden_dims,
        output_dim=len(graph.label_names),
        rng=np_rng,
    )
    best_params = {"weights": [weight.copy() for weight in params["weights"]]}
    best_val_accuracy = -np.inf
    history: list[dict[str, float]] = []

    @partial(jax.jit, static_argnames=("training",))
    def predict(
        current_params: dict[str, list[jnp.ndarray]],
        rng_key,
        *,
        training: bool,
    ) -> tuple[jnp.ndarray, list[jnp.ndarray]]:
        return _forward(
            current_params,
            sampled_neighbor_matrices,
            features,
            dropout=dropout,
            training=training,
            rng_key=rng_key,
        )

    @jax.jit
    def train_step(
        current_params: dict[str, list[jnp.ndarray]],
        rng_key,
    ) -> tuple[dict[str, list[jnp.ndarray]], jnp.ndarray]:
        def loss_fn(model_params):
            logits, _ = predict(model_params, rng_key, training=True)
            data_loss = _masked_cross_entropy(logits, labels, train_mask)
            reg_loss = 0.5 * weight_decay * sum(jnp.sum(weight ** 2) for weight in model_params["weights"])
            return data_loss + reg_loss

        loss, grads = jax.value_and_grad(loss_fn)(current_params)
        updated_params = {
            "weights": [
                weight - learning_rate * grad
                for weight, grad in zip(current_params["weights"], grads["weights"], strict=True)
            ]
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

        current_val_accuracy = history[-1]["val_accuracy"]
        if current_val_accuracy > best_val_accuracy:
            best_val_accuracy = current_val_accuracy
            best_params = {"weights": [weight.copy() for weight in params["weights"]]}

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
