from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from typing import TypedDict

import numpy as np

from .data import GraphData
from .data import clone_graph_data
from .data import identity_adjacency
from .data import structural_identity_features
from .models import train_gat_jax
from .models import train_gcn
from .models import train_graphsage
from .models import train_graphsage_jax


@dataclass
class ExperimentArtifact:
    name: str
    metrics: dict[str, float]
    embeddings: np.ndarray
    logits: np.ndarray
    history: list[dict[str, float]]
    details: dict[str, float | int | str | list[float] | list[int] | dict[str, float]]


class ExperimentArgs(Protocol):
    epochs: int
    learning_rate: float
    weight_decay: float
    dropout: float
    seed: int
    hidden_dim: int
    model: str
    gat_heads: int
    graphsage_fanouts: list[int]
    graphsage_backend: str
    graphsage_variant: str
    graphsage_batch_size: int
    graphsage_aggregator: str
    graphsage_sampler: str


class TrainingKwargs(TypedDict):
    epochs: int
    learning_rate: float
    weight_decay: float
    dropout: float
    seed: int


def _base_training_kwargs(args: ExperimentArgs) -> TrainingKwargs:
    return {
        "epochs": int(args.epochs),
        "learning_rate": float(args.learning_rate),
        "weight_decay": float(args.weight_decay),
        "dropout": float(args.dropout),
        "seed": int(args.seed),
    }


def _model_label(args: ExperimentArgs) -> str:
    if args.model == "gcn":
        return "GCN"
    if args.model == "gat":
        return "GAT-jax"
    return f"GraphSAGE-{args.graphsage_backend}-{args.graphsage_variant}-{args.graphsage_aggregator}"


def _train_selected_model(graph: GraphData, hidden_dims: list[int], args: ExperimentArgs):
    if args.model == "gcn":
        return train_gcn(
            graph,
            hidden_dims=hidden_dims,
            **_base_training_kwargs(args),
        )
    if args.model == "gat":
        return train_gat_jax(
            graph,
            hidden_dims=hidden_dims,
            heads=args.gat_heads,
            **_base_training_kwargs(args),
        )
    if args.graphsage_backend == "jax":
        return train_graphsage_jax(
            graph,
            hidden_dims=hidden_dims,
            fanouts=args.graphsage_fanouts,
            variant=args.graphsage_variant,
            batch_size=args.graphsage_batch_size,
            aggregator=args.graphsage_aggregator,
            sampler=args.graphsage_sampler,
            **_base_training_kwargs(args),
        )
    return train_graphsage(
        graph,
        hidden_dims=hidden_dims,
        fanouts=args.graphsage_fanouts,
        variant=args.graphsage_variant,
        batch_size=args.graphsage_batch_size,
        aggregator=args.graphsage_aggregator,
        sampler=args.graphsage_sampler,
        **_base_training_kwargs(args),
    )


def _run_named_training(
    graph: GraphData,
    name: str,
    *,
    hidden_dims: list[int],
    args: ExperimentArgs,
    details: dict[str, float | int | str | list[float] | list[int] | dict[str, float]] | None = None,
) -> ExperimentArtifact:
    result = _train_selected_model(graph, hidden_dims, args)
    final_details = {} if details is None else dict(details)
    diagnostics = result.diagnostics
    if diagnostics is not None:
        final_details["diagnostics"] = diagnostics
    return ExperimentArtifact(
        name=name,
        metrics=result.metrics,
        embeddings=result.hidden_embeddings,
        logits=result.logits,
        history=result.history,
        details=final_details,
    )


def run_baseline_mode(graph: GraphData, args: ExperimentArgs) -> list[ExperimentArtifact]:
    return [
        _run_named_training(
            graph,
            name="baseline",
            hidden_dims=[args.hidden_dim],
            args=args,
            details={"question": f"What does the standard 2-layer {_model_label(args)} achieve on this split?"},
        )
    ]


def run_feature_only_mode(graph: GraphData, args: ExperimentArgs) -> list[ExperimentArtifact]:
    feature_graph = clone_graph_data(graph, adjacency_hat=identity_adjacency(graph.features.shape[0]))
    return [
        _run_named_training(
            feature_graph,
            name="feature_only",
            hidden_dims=[args.hidden_dim],
            args=args,
            details={"question": f"How much signal remains for {_model_label(args)} when graph propagation is removed?"},
        )
    ]


def run_graph_only_mode(graph: GraphData, args: ExperimentArgs) -> list[ExperimentArtifact]:
    graph_only = clone_graph_data(graph, features=structural_identity_features(graph.features.shape[0]))
    return [
        _run_named_training(
            graph_only,
            name="graph_only",
            hidden_dims=[args.hidden_dim],
            args=args,
            details={"question": f"How much signal remains for {_model_label(args)} when lexical node features are removed?"},
        )
    ]


def run_depth_ablation_mode(graph: GraphData, args: ExperimentArgs) -> list[ExperimentArtifact]:
    if args.model == "graphsage":
        depth_map = {
            "depth_1": [],
            "depth_2": [args.hidden_dim],
        }
    else:
        depth_map = {
            "depth_1": [],
            "depth_2": [args.hidden_dim],
            "depth_3": [args.hidden_dim, args.hidden_dim],
        }
    return [
        _run_named_training(
            graph,
            name=name,
            hidden_dims=hidden_dims,
            args=args,
            details={
                "question": f"How does {_model_label(args)} performance change with network depth?",
                "depth": len(hidden_dims) + 1,
            },
        )
        for name, hidden_dims in depth_map.items()
    ]


def _mean_pairwise_cosine(embeddings: np.ndarray) -> float:
    normalized = embeddings / np.clip(np.linalg.norm(embeddings, axis=1, keepdims=True), 1e-12, None)
    sample = normalized[: min(500, normalized.shape[0])]
    similarity = sample @ sample.T
    upper = similarity[np.triu_indices(sample.shape[0], k=1)]
    return float(upper.mean())


def _embedding_variance(embeddings: np.ndarray) -> float:
    centered = embeddings - embeddings.mean(axis=0, keepdims=True)
    return float(np.mean(np.sum(centered ** 2, axis=1)))


def run_over_smoothing_mode(graph: GraphData, args: ExperimentArgs) -> list[ExperimentArtifact]:
    artifacts = run_depth_ablation_mode(graph, args)
    for artifact in artifacts:
        artifact.details["mean_pairwise_cosine"] = _mean_pairwise_cosine(artifact.embeddings)
        artifact.details["embedding_variance"] = _embedding_variance(artifact.embeddings)
        artifact.details["question"] = "Do deeper models collapse node representations toward one another?"
    return artifacts


def _pairwise_class_distance(embeddings: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    centroids: list[np.ndarray] = []
    for label in np.unique(labels):
        centroids.append(embeddings[labels == label].mean(axis=0))

    distances: list[float] = []
    for index in range(len(centroids)):
        for other_index in range(index + 1, len(centroids)):
            distances.append(float(np.linalg.norm(centroids[index] - centroids[other_index])))
    return {
        "mean_centroid_distance": float(np.mean(distances)),
        "min_centroid_distance": float(np.min(distances)),
        "max_centroid_distance": float(np.max(distances)),
    }


def _within_class_dispersion(embeddings: np.ndarray, labels: np.ndarray) -> float:
    dispersion: list[float] = []
    for label in np.unique(labels):
        class_embeddings = embeddings[labels == label]
        centroid = class_embeddings.mean(axis=0, keepdims=True)
        dispersion.append(float(np.mean(np.linalg.norm(class_embeddings - centroid, axis=1))))
    return float(np.mean(dispersion))


def run_embedding_separation_mode(graph: GraphData, args: ExperimentArgs) -> list[ExperimentArtifact]:
    baseline = run_baseline_mode(graph, args)[0]
    baseline.details.update(_pairwise_class_distance(baseline.embeddings, graph.labels))
    baseline.details["within_class_dispersion"] = _within_class_dispersion(baseline.embeddings, graph.labels)
    baseline.details["question"] = "How cleanly do learned embeddings separate topic classes?"
    return [baseline]


MODE_TO_RUNNER = {
    "baseline": run_baseline_mode,
    "feature-only": run_feature_only_mode,
    "graph-only": run_graph_only_mode,
    "depth-ablation": run_depth_ablation_mode,
    "over-smoothing": run_over_smoothing_mode,
    "embedding-separation": run_embedding_separation_mode,
}
