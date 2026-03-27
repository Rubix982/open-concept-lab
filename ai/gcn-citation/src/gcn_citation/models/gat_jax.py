from __future__ import annotations

"""First JAX implementation of a Graph Attention Network (GAT).

This file is intentionally written as a learning-oriented baseline:

- full-batch training
- single-head attention
- dense adjacency masking

The central idea of GAT is that neighbors are not averaged uniformly.
Instead, the model learns an attention score for each node-neighbor pair,
then normalizes those scores with a softmax before aggregating messages.
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


def _init_params(
    input_dim: int,
    hidden_dims: list[int],
    output_dim: int,
    rng: np.random.Generator,
) -> dict[str, list[jnp.ndarray]]:
    layer_dims = [input_dim, *hidden_dims, output_dim]
    # Each GAT layer learns:
    # 1. a feature projection W
    # 2. a source-side attention vector a_src
    # 3. a destination-side attention vector a_dst
    #
    # The source/destination split gives us pairwise edge scores without
    # explicitly learning a full N x N edge-parameter matrix.
    return {
        "weights": [
            numpy_to_jax(_glorot(rng, (layer_dims[index], layer_dims[index + 1])))
            for index in range(len(layer_dims) - 1)
        ],
        "attention_src": [
            numpy_to_jax(_glorot(rng, (layer_dims[index + 1], 1)))
            for index in range(len(layer_dims) - 1)
        ],
        "attention_dst": [
            numpy_to_jax(_glorot(rng, (layer_dims[index + 1], 1)))
            for index in range(len(layer_dims) - 1)
        ],
    }


def _gat_layer(
    current: jnp.ndarray,
    weight: jnp.ndarray,
    attention_src: jnp.ndarray,
    attention_dst: jnp.ndarray,
    adjacency_mask: jnp.ndarray,
    *,
    training: bool,
    dropout: float,
    rng_key,
    is_output_layer: bool,
) -> jnp.ndarray:
    # First project node features into the layer's hidden space.
    projected = current @ weight

    # Compute one score contribution from the "source" node and one from the
    # "destination" node, then add them to get edge logits e_ij.
    src_logits = projected @ attention_src
    dst_logits = projected @ attention_dst
    attention_scores = jax.nn.leaky_relu(src_logits + dst_logits.T, negative_slope=0.2)

    # Non-neighbors should never receive attention mass, so we mask them to a
    # very negative value before the softmax.
    masked_scores = jnp.where(adjacency_mask, attention_scores, -1e9)
    attention = jax.nn.softmax(masked_scores, axis=1)

    if training and dropout > 0.0:
        keep_probability = 1.0 - dropout
        # We regularize both projected node features and the attention map.
        # This mirrors the idea that GAT can overfit both what it says and
        # which neighbors it listens to.
        feature_mask = jax.random.bernoulli(rng_key, p=keep_probability, shape=projected.shape)
        projected = projected * feature_mask.astype(projected.dtype) / keep_probability
        attention_mask = jax.random.bernoulli(rng_key, p=keep_probability, shape=attention.shape)
        attention = attention * attention_mask.astype(attention.dtype) / keep_probability

    # Attention-weighted message passing:
    # each row of `attention` contains normalized coefficients for the
    # neighbors of one node.
    aggregated = attention @ projected
    if is_output_layer:
        return aggregated
    return jax.nn.elu(aggregated)


def _forward(
    params: dict[str, list[jnp.ndarray]],
    features: jnp.ndarray,
    adjacency_mask: jnp.ndarray,
    *,
    training: bool,
    dropout: float,
    rng_key,
) -> tuple[jnp.ndarray, list[jnp.ndarray]]:
    current = features
    hidden_layers: list[jnp.ndarray] = []
    if training:
        # One RNG key per layer keeps dropout reproducible and layer-local.
        keys = jax.random.split(rng_key, len(params["weights"]))
    else:
        keys = [rng_key for _ in params["weights"]]

    for layer_index, weight in enumerate(params["weights"]):
        current = _gat_layer(
            current,
            weight,
            params["attention_src"][layer_index],
            params["attention_dst"][layer_index],
            adjacency_mask,
            training=training,
            dropout=dropout,
            rng_key=keys[layer_index],
            is_output_layer=layer_index == len(params["weights"]) - 1,
        )
        if layer_index != len(params["weights"]) - 1:
            hidden_layers.append(current)

    return current, hidden_layers


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
        rng=np_rng,
    )
    best_params = {key: [value.copy() for value in values] for key, values in params.items()}
    best_val_accuracy = -np.inf
    history: list[dict[str, float]] = []

    @partial(jax.jit, static_argnames=("training",))
    def predict(current_params, rng_key, *, training: bool):
        # This is the reusable forward pass for both training and evaluation.
        # JIT-compiling it is where JAX starts to pay off.
        return _forward(
            current_params,
            features,
            adjacency_mask,
            training=training,
            dropout=dropout,
            rng_key=rng_key,
        )

    @jax.jit
    def train_step(current_params, rng_key):
        def loss_fn(model_params):
            logits, _ = predict(model_params, rng_key, training=True)
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

    # As with the other models in the repo, we restore the best validation
    # checkpoint before saving final metrics and embeddings.
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
            "heads": heads,
        },
    )
