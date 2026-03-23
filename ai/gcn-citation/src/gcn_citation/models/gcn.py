from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..data import GraphData


@dataclass
class TrainingResult:
    metrics: dict[str, float]
    hidden_embeddings: np.ndarray
    logits: np.ndarray
    history: list[dict[str, float]]
    layer_embeddings: list[np.ndarray]
    diagnostics: dict[str, object] | None = None


class ManualGCN:
    """Manual GCN implementation using the standard normalized propagation rule.

    For each layer we apply:
        H^{l+1} = activation(A_hat @ H^l @ W^l)

    where:
    - A_hat is the normalized adjacency matrix with self-loops
    - H^0 is the input feature matrix X
    - W^l is the trainable weight matrix for layer l
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
            self._glorot((layer_dims[index], layer_dims[index + 1]))
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
        adjacency_hat: np.ndarray,
        features: np.ndarray,
        training: bool,
    ) -> tuple[np.ndarray, list[np.ndarray], list[dict[str, np.ndarray]]]:
        activations = [features]
        layer_caches: list[dict[str, np.ndarray]] = []
        current = features

        for layer_index, weight in enumerate(self.weights):
            # First aggregate neighbor information with A_hat, then project it
            # into the next feature space with the layer weight matrix W.
            support = adjacency_hat @ current
            pre_activation = support @ weight
            is_output_layer = layer_index == len(self.weights) - 1

            if is_output_layer:
                # Final layer outputs class logits directly, so no ReLU/dropout.
                current = pre_activation
                dropout_mask = np.ones_like(current, dtype=np.float32)
            else:
                # Hidden layers use ReLU, then inverted dropout during training.
                hidden = np.maximum(pre_activation, 0.0)
                if training and self.dropout > 0.0:
                    dropout_mask = (self.rng.random(hidden.shape) >= self.dropout).astype(np.float32)
                    dropout_mask /= 1.0 - self.dropout
                else:
                    dropout_mask = np.ones_like(hidden, dtype=np.float32)
                current = hidden * dropout_mask

            layer_caches.append(
                {
                    "input": activations[-1],
                    "support": support,
                    "pre_activation": pre_activation,
                    "dropout_mask": dropout_mask,
                    "is_output_layer": np.array([1 if is_output_layer else 0], dtype=np.int8),
                }
            )
            activations.append(current)

        logits = activations[-1]
        hidden_layers = activations[1:-1]
        return logits, hidden_layers, layer_caches

    @staticmethod
    def softmax(logits: np.ndarray) -> np.ndarray:
        shifted = logits - logits.max(axis=1, keepdims=True)
        exp_logits = np.exp(shifted)
        return exp_logits / exp_logits.sum(axis=1, keepdims=True)


def masked_cross_entropy(logits: np.ndarray, labels: np.ndarray, mask: np.ndarray) -> tuple[float, np.ndarray]:
    # Semi-supervised Cora training only uses labeled training nodes in the loss.
    probs = ManualGCN.softmax(logits)
    active_indices = np.where(mask)[0]
    active_probs = probs[active_indices, labels[active_indices]]
    loss = -np.log(active_probs + 1e-12).mean()

    # For softmax + cross-entropy, the gradient w.r.t. logits is simply:
    # p - y_one_hot, averaged over the active nodes.
    grad_logits = np.zeros_like(logits, dtype=np.float32)
    grad_logits[active_indices] = probs[active_indices]
    grad_logits[active_indices, labels[active_indices]] -= 1.0
    grad_logits[active_indices] /= float(active_indices.shape[0])
    return float(loss), grad_logits


def accuracy(logits: np.ndarray, labels: np.ndarray, mask: np.ndarray) -> float:
    predictions = logits.argmax(axis=1)
    return float((predictions[mask] == labels[mask]).mean())


def _build_history_row(epoch: int, loss: float, logits: np.ndarray, graph: GraphData) -> dict[str, float]:
    return {
        "epoch": float(epoch),
        "loss": float(loss),
        "train_accuracy": accuracy(logits, graph.labels, graph.train_mask),
        "val_accuracy": accuracy(logits, graph.labels, graph.val_mask),
        "test_accuracy": accuracy(logits, graph.labels, graph.test_mask),
    }


def train_gcn(
    graph: GraphData,
    hidden_dim: int = 16,
    hidden_dims: list[int] | None = None,
    epochs: int = 250,
    learning_rate: float = 0.2,
    weight_decay: float = 5e-4,
    dropout: float = 0.5,
    seed: int = 7,
) -> TrainingResult:
    rng = np.random.default_rng(seed)
    effective_hidden_dims = [hidden_dim] if hidden_dims is None else hidden_dims
    model = ManualGCN(
        input_dim=graph.features.shape[1],
        hidden_dims=effective_hidden_dims,
        output_dim=len(graph.label_names),
        rng=rng,
        dropout=dropout,
    )

    history: list[dict[str, float]] = []
    best_state = model.state_dict()
    best_val_accuracy = -np.inf

    for epoch in range(1, epochs + 1):
        # Forward pass through all graph-convolution layers.
        logits, _, layer_caches = model.forward(graph.adjacency_hat, graph.features, training=True)
        data_loss, grad_logits = masked_cross_entropy(logits, graph.labels, graph.train_mask)
        reg_loss = 0.5 * weight_decay * sum(np.sum(weight ** 2) for weight in model.weights)
        loss = data_loss + float(reg_loss)

        grads = [np.zeros_like(weight, dtype=np.float32) for weight in model.weights]
        grad_current = grad_logits

        for layer_index in range(len(model.weights) - 1, -1, -1):
            cache = layer_caches[layer_index]
            # dL/dW = (A_hat @ H_prev)^T @ dL/dZ, plus L2 regularization.
            grads[layer_index] = cache["support"].T @ grad_current + weight_decay * model.weights[layer_index]

            if layer_index == 0:
                continue

            # Backprop goes right-to-left through:
            # logits/hidden -> linear projection W -> graph propagation A_hat
            # -> dropout mask -> ReLU gate.
            grad_support = grad_current @ model.weights[layer_index].T
            grad_previous_activation = graph.adjacency_hat.T @ grad_support
            previous_cache = layer_caches[layer_index - 1]
            grad_previous_hidden = grad_previous_activation * previous_cache["dropout_mask"]
            grad_current = grad_previous_hidden * (previous_cache["pre_activation"] > 0)

        # Plain gradient descent update for each layer weight matrix.
        for layer_index, grad_weight in enumerate(grads):
            model.weights[layer_index] -= learning_rate * grad_weight.astype(np.float32)

        # Evaluate without dropout so train/val/test metrics are comparable.
        eval_logits, _, _ = model.forward(graph.adjacency_hat, graph.features, training=False)
        history.append(_build_history_row(epoch, loss, eval_logits, graph))

        current_val_accuracy = history[-1]["val_accuracy"]
        if current_val_accuracy > best_val_accuracy:
            best_val_accuracy = current_val_accuracy
            best_state = model.state_dict()

    # Restore the best validation checkpoint before returning final artifacts.
    model.load_state_dict(best_state)
    final_logits, hidden_layers, _ = model.forward(graph.adjacency_hat, graph.features, training=False)
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
