from __future__ import annotations

"""First reusable JAX implementation of a Graph Attention Network (GAT).

This file is intentionally written as a learning-oriented baseline:

- full-batch training
- single-head attention
- dense adjacency masking

The central idea of GAT is that neighbors are not averaged uniformly.
Instead, the model learns an attention score for each node-neighbor pair,
then normalizes those scores with a softmax before aggregating messages.

This file now supports real multi-head hidden attention, which makes it a
better foundation for future experiments and reuse:

- hidden layers can use multiple attention heads
- hidden heads are concatenated, following the original GAT intuition
- the output layer stays single-head for stable class logits
"""

from dataclasses import dataclass
from functools import partial

import numpy as np

from ..data import GraphData
from .gcn import TrainingResult
from .gcn import accuracy
from .graphsage_jax import ensure_jax_available
from .graphsage_jax import numpy_to_jax

try:
    import jax
    import jax.numpy as jnp
except ImportError:  # pragma: no cover
    jax = None
    jnp = None


@dataclass
class GATConfig:
    hidden_dims: list[int]
    heads: int
    epochs: int
    learning_rate: float
    weight_decay: float
    dropout: float
    attention_dropout: float
    seed: int


def _glorot(rng: np.random.Generator, shape: tuple[int, int]) -> np.ndarray:
    limit = np.sqrt(6.0 / (shape[0] + shape[1]))
    return rng.uniform(-limit, limit, size=shape).astype(np.float32)


def _build_attention_mask(num_nodes: int, edges: np.ndarray) -> np.ndarray:
    # GAT should only attend over real graph neighbors. We also keep self-loops
    # so each node can retain its own information during message passing.
    adjacency = np.zeros((num_nodes, num_nodes), dtype=bool)
    adjacency[edges[:, 0], edges[:, 1]] = True
    adjacency = np.logical_or(adjacency, adjacency.T)
    np.fill_diagonal(adjacency, True)
    return adjacency


def _layer_head_counts(hidden_dims: list[int], heads: int) -> list[int]:
    # Hidden layers get multi-head attention; the final classifier layer uses a
    # single head so logits stay in [num_nodes, num_classes].
    hidden_layer_count = len(hidden_dims)
    return [heads] * hidden_layer_count + [1]


def _init_params(
    input_dim: int,
    hidden_dims: list[int],
    output_dim: int,
    heads: int,
    rng: np.random.Generator,
) -> dict[str, list[jnp.ndarray]]:
    layer_output_dims = [*hidden_dims, output_dim]
    head_counts = _layer_head_counts(hidden_dims, heads)
    params = {
        "weights": [],
        "attention_src": [],
        "attention_dst": [],
    }

    current_input_dim = input_dim
    for output_dim_for_layer, head_count in zip(layer_output_dims, head_counts, strict=True):
        # Each head has its own projection and its own source/destination
        # attention vectors. This is the real "multi-view neighborhood"
        # mechanism of multi-head GAT.
        params["weights"].append(
            numpy_to_jax(_glorot(rng, (current_input_dim, output_dim_for_layer * head_count)))
        )
        params["attention_src"].append(
            numpy_to_jax(_glorot(rng, (head_count, output_dim_for_layer)))
        )
        params["attention_dst"].append(
            numpy_to_jax(_glorot(rng, (head_count, output_dim_for_layer)))
        )
        current_input_dim = output_dim_for_layer * head_count

    return params


def _gat_layer(
    current: jnp.ndarray,
    weight: jnp.ndarray,
    attention_src: jnp.ndarray,
    attention_dst: jnp.ndarray,
    adjacency_mask: jnp.ndarray,
    *,
    training: bool,
    feature_dropout: float,
    attention_dropout: float,
    rng_key,
    is_output_layer: bool,
    collect_attention: bool,
) -> tuple[jnp.ndarray, jnp.ndarray | None]:
    num_heads = attention_src.shape[0]
    head_dim = attention_src.shape[1]

    # First project features, then reshape into [nodes, heads, head_dim].
    projected = (current @ weight).reshape(current.shape[0], num_heads, head_dim)

    feature_key, attention_key = jax.random.split(rng_key)
    if training and feature_dropout > 0.0:
        keep_probability = 1.0 - feature_dropout
        feature_mask = jax.random.bernoulli(feature_key, p=keep_probability, shape=projected.shape)
        projected = projected * feature_mask.astype(projected.dtype) / keep_probability

    # Each head independently scores node i as a source and node j as a
    # destination, then combines those scores into edge logits e_ij.
    src_logits = jnp.einsum("nhd,hd->nh", projected, attention_src)
    dst_logits = jnp.einsum("nhd,hd->nh", projected, attention_dst)
    attention_scores = jax.nn.leaky_relu(
        src_logits.T[:, :, None] + dst_logits.T[:, None, :],
        negative_slope=0.2,
    )

    adjacency_mask_per_head = adjacency_mask[None, :, :]
    masked_scores = jnp.where(adjacency_mask_per_head, attention_scores, -1e9)
    attention = jax.nn.softmax(masked_scores, axis=2)

    if training and attention_dropout > 0.0:
        keep_probability = 1.0 - attention_dropout
        attention_mask = jax.random.bernoulli(attention_key, p=keep_probability, shape=attention.shape)
        attention = attention * attention_mask.astype(attention.dtype) / keep_probability

    # Each head aggregates its own weighted neighbor mixture. Hidden layers
    # concatenate heads; the output layer averages them to keep logits stable.
    aggregated = jnp.einsum("hij,jhd->ihd", attention, projected)
    if is_output_layer:
        output = jnp.mean(aggregated, axis=1)
        return output, attention if collect_attention else None
    concatenated = aggregated.reshape(aggregated.shape[0], num_heads * head_dim)
    return jax.nn.elu(concatenated), attention if collect_attention else None


def _forward(
    params: dict[str, list[jnp.ndarray]],
    features: jnp.ndarray,
    adjacency_mask: jnp.ndarray,
    *,
    training: bool,
    dropout: float,
    attention_dropout: float,
    rng_key,
    collect_attention: bool,
) -> tuple[jnp.ndarray, list[jnp.ndarray], list[jnp.ndarray]]:
    current = features
    hidden_layers: list[jnp.ndarray] = []
    attention_layers: list[jnp.ndarray] = []
    if training:
        # One RNG key per layer keeps dropout reproducible and layer-local.
        keys = jax.random.split(rng_key, len(params["weights"]))
    else:
        keys = [rng_key for _ in params["weights"]]

    for layer_index, weight in enumerate(params["weights"]):
        current, attention = _gat_layer(
            current,
            weight,
            params["attention_src"][layer_index],
            params["attention_dst"][layer_index],
            adjacency_mask,
            training=training,
            feature_dropout=dropout,
            attention_dropout=attention_dropout,
            rng_key=keys[layer_index],
            is_output_layer=layer_index == len(params["weights"]) - 1,
            collect_attention=collect_attention,
        )
        if attention is not None:
            attention_layers.append(attention)
        if layer_index != len(params["weights"]) - 1:
            hidden_layers.append(current)

    return current, hidden_layers, attention_layers


def _summarize_attention_maps(
    attention_layers: list[np.ndarray],
    adjacency_mask: np.ndarray,
    *,
    max_nodes: int = 5,
    top_k_neighbors: int = 3,
) -> dict[str, object]:
    summaries: list[dict[str, object]] = []
    node_indices = np.arange(adjacency_mask.shape[0], dtype=np.int32)

    for layer_index, attention in enumerate(attention_layers):
        # attention shape: [heads, source_node, target_node]
        head_summaries: list[dict[str, object]] = []
        for head_index in range(attention.shape[0]):
            head_attention = attention[head_index]
            neighbor_counts = np.clip(adjacency_mask.sum(axis=1), 1, None)
            entropy = -np.sum(head_attention * np.log(np.clip(head_attention, 1e-12, None)), axis=1)
            normalized_entropy = entropy / np.log(neighbor_counts)
            normalized_entropy = np.nan_to_num(normalized_entropy, nan=0.0, posinf=0.0, neginf=0.0)
            max_attention = head_attention.max(axis=1)
            self_attention = head_attention[node_indices, node_indices]
            sparsity_over_01 = (head_attention > 0.1).mean(axis=1)

            sample_nodes: list[dict[str, object]] = []
            for node_index in range(min(max_nodes, head_attention.shape[0])):
                weights = head_attention[node_index]
                neighbor_indices = np.flatnonzero(adjacency_mask[node_index])
                ranked_neighbors = neighbor_indices[np.argsort(weights[neighbor_indices])[::-1]]
                top_indices = ranked_neighbors[:top_k_neighbors]
                sample_nodes.append(
                    {
                        "node_index": int(node_index),
                        "top_neighbors": [
                            {
                                "neighbor_index": int(neighbor_index),
                                "attention": float(weights[neighbor_index]),
                            }
                            for neighbor_index in top_indices
                        ],
                    }
                )

            head_summaries.append(
                {
                    "head_index": head_index,
                    "mean_entropy": float(normalized_entropy.mean()),
                    "mean_max_attention": float(max_attention.mean()),
                    "mean_self_attention": float(self_attention.mean()),
                    "mean_fraction_over_0_1": float(sparsity_over_01.mean()),
                    "sample_nodes": sample_nodes,
                }
            )

        summaries.append(
            {
                "layer_index": layer_index,
                "num_heads": attention.shape[0],
                "heads": head_summaries,
            }
        )

    return {"attention_layers": summaries}


def _masked_cross_entropy(logits: jnp.ndarray, labels: jnp.ndarray, mask: jnp.ndarray) -> jnp.ndarray:
    # We only train on labeled nodes, so the loss is averaged over the active
    # mask instead of all nodes in the graph.
    log_probs = jax.nn.log_softmax(logits, axis=1)
    one_hot = jax.nn.one_hot(labels, logits.shape[1])
    per_node_loss = -jnp.sum(one_hot * log_probs, axis=1)
    normalizer = jnp.clip(jnp.sum(mask), a_min=1.0)
    return jnp.sum(per_node_loss * mask) / normalizer


def train_gat_jax(
    graph: GraphData,
    *,
    hidden_dims: list[int],
    heads: int,
    epochs: int,
    learning_rate: float,
    weight_decay: float,
    dropout: float,
    attention_dropout: float,
    seed: int,
) -> TrainingResult:
    ensure_jax_available()
    _ = GATConfig(
        hidden_dims=hidden_dims,
        heads=heads,
        epochs=epochs,
        learning_rate=learning_rate,
        weight_decay=weight_decay,
        dropout=dropout,
        attention_dropout=attention_dropout,
        seed=seed,
    )

    np_rng = np.random.default_rng(seed)
    # We keep the same GraphData container used elsewhere in the repo, then
    # convert only the pieces we need into JAX arrays.
    features = numpy_to_jax(graph.features)
    labels = numpy_to_jax(graph.labels.astype(np.int32))
    train_mask = numpy_to_jax(graph.train_mask.astype(np.float32))
    adjacency_mask = numpy_to_jax(_build_attention_mask(graph.features.shape[0], graph.edges))

    params = _init_params(
        input_dim=graph.features.shape[1],
        hidden_dims=hidden_dims,
        output_dim=len(graph.label_names),
        heads=heads,
        rng=np_rng,
    )
    best_params = {key: [value.copy() for value in values] for key, values in params.items()}
    best_val_accuracy = -np.inf
    history: list[dict[str, float]] = []

    @partial(jax.jit, static_argnames=("training", "collect_attention"))
    def predict(current_params, rng_key, *, training: bool, collect_attention: bool):
        # This is the reusable forward pass for both training and evaluation.
        # JIT-compiling it is where JAX starts to pay off.
        return _forward(
            current_params,
            features,
            adjacency_mask,
            training=training,
            dropout=dropout,
            attention_dropout=attention_dropout,
            rng_key=rng_key,
            collect_attention=collect_attention,
        )

    @jax.jit
    def train_step(current_params, rng_key):
        def loss_fn(model_params):
            logits, _, _ = predict(model_params, rng_key, training=True, collect_attention=False)
            data_loss = _masked_cross_entropy(logits, labels, train_mask)
            # L2 regularization across all learned tensors keeps the first GAT
            # baseline comparable to the rest of the repo's models.
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
        # Split RNG so the update step and the eval step do not share dropout
        # randomness. That makes evaluation deterministic for a given state.
        rng_key, step_key, eval_key = jax.random.split(rng_key, 3)
        params, loss = train_step(params, step_key)
        eval_logits, hidden_layers, _ = predict(params, eval_key, training=False, collect_attention=False)
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

    # As with the other models in the repo, we restore the best validation
    # checkpoint before saving final metrics and embeddings.
    final_logits, final_hidden_layers, final_attention_layers = predict(
        best_params,
        rng_key,
        training=False,
        collect_attention=True,
    )
    final_logits_np = np.asarray(final_logits)
    hidden_layers_np = [np.asarray(layer) for layer in final_hidden_layers]
    attention_layers_np = [np.asarray(layer) for layer in final_attention_layers]
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
            "heads": heads,
            "attention_dropout": attention_dropout,
            "layer_head_counts": _layer_head_counts(hidden_dims, heads),
            **_summarize_attention_maps(attention_layers_np, np.asarray(adjacency_mask)),
        },
    )
