from __future__ import annotations

import math
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.manifold import TSNE

warnings.filterwarnings(
    "ignore",
    message="Could not find the number of physical cores",
    module="joblib.externals.loky.backend.context",
)


def compute_tsne_coordinates(embeddings: np.ndarray, seed: int) -> np.ndarray:
    tsne = TSNE(
        n_components=2,
        init="pca",
        learning_rate="auto",
        perplexity=30,
        n_jobs=1,
        random_state=seed,
    )
    return tsne.fit_transform(embeddings)


def _scatter_embeddings(
    axis: plt.Axes,
    coordinates: np.ndarray,
    labels: np.ndarray,
    label_names: list[str],
    title: str,
) -> None:
    cmap = plt.get_cmap("tab10", len(label_names))
    for label_id, label_name in enumerate(label_names):
        mask = labels == label_id
        axis.scatter(
            coordinates[mask, 0],
            coordinates[mask, 1],
            s=14,
            alpha=0.75,
            label=label_name,
            color=cmap(label_id),
        )
    axis.set_title(title)
    axis.set_xlabel("t-SNE 1")
    axis.set_ylabel("t-SNE 2")


def save_tsne_plot(
    embeddings: np.ndarray,
    labels: np.ndarray,
    label_names: list[str],
    output_path: Path,
    seed: int,
) -> np.ndarray:
    coordinates = compute_tsne_coordinates(embeddings, seed=seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 8))
    _scatter_embeddings(axis, coordinates, labels, label_names, "Cora Node Embeddings (t-SNE)")
    handles, legend_labels = axis.get_legend_handles_labels()
    figure.legend(handles, legend_labels, loc="upper right", fontsize=8)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
    return coordinates


def save_tsne_grid(
    *,
    runs: list[dict[str, object]],
    labels: np.ndarray,
    label_names: list[str],
    output_path: Path,
) -> None:
    if not runs:
        return

    columns = min(2, len(runs))
    rows = math.ceil(len(runs) / columns)
    figure, axes = plt.subplots(rows, columns, figsize=(columns * 7, rows * 5.5))
    axes_array = np.atleast_1d(axes).ravel()

    for axis, run in zip(axes_array, runs):
        _scatter_embeddings(
            axis,
            run["tsne_coordinates"],
            labels,
            label_names,
            str(run["name"]),
        )

    for axis in axes_array[len(runs) :]:
        axis.axis("off")

    handles, legend_labels = axes_array[0].get_legend_handles_labels()
    figure.legend(handles, legend_labels, loc="upper right", fontsize=8)
    figure.suptitle("Mode Embedding Comparison", fontsize=14)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_accuracy_comparison_chart(runs: list[dict[str, object]], output_path: Path) -> None:
    names = [str(run["name"]) for run in runs]
    train_values = [float(run["metrics"]["train_accuracy"]) for run in runs]
    val_values = [float(run["metrics"]["val_accuracy"]) for run in runs]
    test_values = [float(run["metrics"]["test_accuracy"]) for run in runs]

    x = np.arange(len(names))
    width = 0.24
    figure, axis = plt.subplots(figsize=(max(7, len(names) * 2.2), 5))
    axis.bar(x - width, train_values, width, label="Train")
    axis.bar(x, val_values, width, label="Val")
    axis.bar(x + width, test_values, width, label="Test")
    axis.set_xticks(x)
    axis.set_xticklabels(names)
    axis.set_ylim(0.0, 1.0)
    axis.set_ylabel("Accuracy")
    axis.set_title("Accuracy Comparison Across Runs")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_history_chart(runs: list[dict[str, object]], output_path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    for run in runs:
        history = run["history"]
        epochs = [row["epoch"] for row in history]
        axes[0].plot(epochs, [row["loss"] for row in history], label=run["name"])
        axes[1].plot(epochs, [row["val_accuracy"] for row in history], label=f"{run['name']} val")
        axes[1].plot(epochs, [row["test_accuracy"] for row in history], linestyle="--", alpha=0.8, label=f"{run['name']} test")

    axes[0].set_title("Training Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[1].set_title("Validation And Test Accuracy")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_ylim(0.0, 1.0)
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8, ncol=2)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_over_smoothing_chart(runs: list[dict[str, object]], output_path: Path) -> None:
    depths = [int(run["details"]["depth"]) for run in runs]
    cosine_values = [float(run["details"]["mean_pairwise_cosine"]) for run in runs]
    variance_values = [float(run["details"]["embedding_variance"]) for run in runs]

    figure, axis_left = plt.subplots(figsize=(8, 5))
    axis_right = axis_left.twinx()
    axis_left.plot(depths, cosine_values, marker="o", color="#C44E52", label="Mean pairwise cosine")
    axis_right.plot(depths, variance_values, marker="s", color="#4C72B0", label="Embedding variance")
    axis_left.set_xlabel("GCN Depth")
    axis_left.set_ylabel("Mean Pairwise Cosine", color="#C44E52")
    axis_right.set_ylabel("Embedding Variance", color="#4C72B0")
    axis_left.set_title("Over-smoothing Diagnostics")
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)


def save_embedding_separation_chart(runs: list[dict[str, object]], output_path: Path) -> None:
    run = runs[0]
    labels = ["Mean centroid", "Min centroid", "Max centroid", "Within-class"]
    values = [
        float(run["details"]["mean_centroid_distance"]),
        float(run["details"]["min_centroid_distance"]),
        float(run["details"]["max_centroid_distance"]),
        float(run["details"]["within_class_dispersion"]),
    ]

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(labels, values, color=["#55A868", "#8172B2", "#CCB974", "#64B5CD"])
    axis.set_ylabel("Distance")
    axis.set_title("Embedding Separation Summary")
    axis.tick_params(axis="x", rotation=15)
    figure.tight_layout()
    figure.savefig(output_path, dpi=200)
    plt.close(figure)
