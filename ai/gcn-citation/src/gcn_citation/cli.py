from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from .data import load_graph_data
from .experiments import MODE_TO_RUNNER


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run manual NumPy GCN experiments on the Cora citation graph.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument(
        "--mode",
        choices=sorted(MODE_TO_RUNNER.keys()),
        default="baseline",
        help="Experiment mode to run.",
    )
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--hidden-dim", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=0.2)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--dropout", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--skip-tsne",
        action="store_true",
        help="Skip t-SNE generation for faster batch runs.",
    )
    return parser


def _configure_environment(artifacts_dir: Path) -> None:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    mpl_config_dir = artifacts_dir / ".mplconfig"
    cache_dir = artifacts_dir / ".cache"
    mpl_config_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "fontconfig").mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(mpl_config_dir)
    os.environ["XDG_CACHE_HOME"] = str(cache_dir)
    os.environ["LOKY_MAX_CPU_COUNT"] = str(os.cpu_count() or 1)


def _save_experiment_outputs(
    *,
    args: argparse.Namespace,
    graph: object,
    artifact: object,
    mode_dir: Path,
) -> dict[str, str | dict[str, float] | dict[str, object]]:
    metrics_path = mode_dir / f"{artifact.name}_metrics.json"
    history_path = mode_dir / f"{artifact.name}_history.json"
    details_path = mode_dir / f"{artifact.name}_details.json"
    embeddings_path = mode_dir / f"{artifact.name}_embeddings.npy"
    logits_path = mode_dir / f"{artifact.name}_logits.npy"

    metrics_path.write_text(json.dumps(artifact.metrics, indent=2))
    history_path.write_text(json.dumps(artifact.history, indent=2))
    details_path.write_text(json.dumps(artifact.details, indent=2))
    np.save(embeddings_path, artifact.embeddings)
    np.save(logits_path, artifact.logits)

    tsne_path = mode_dir / f"{artifact.name}_tsne.png"
    tsne_coordinates: np.ndarray | None = None
    if not args.skip_tsne:
        from .visualize import save_tsne_plot

        tsne_coordinates = save_tsne_plot(
            embeddings=artifact.embeddings,
            labels=graph.labels,
            label_names=graph.label_names,
            output_path=tsne_path,
            seed=args.seed,
        )

    return {
        "name": artifact.name,
        "metrics": artifact.metrics,
        "details": artifact.details,
        "history": artifact.history,
        "tsne_coordinates": tsne_coordinates,
        "paths": {
            "metrics": str(metrics_path),
            "history": str(history_path),
            "details": str(details_path),
            "embeddings": str(embeddings_path),
            "logits": str(logits_path),
            "tsne": str(tsne_path) if not args.skip_tsne else "",
        },
    }


def _build_mode_visualizations(
    *,
    args: argparse.Namespace,
    graph: object,
    runs: list[dict[str, object]],
    mode_dir: Path,
) -> dict[str, str]:
    from .visualize import save_accuracy_comparison_chart
    from .visualize import save_embedding_separation_chart
    from .visualize import save_history_chart
    from .visualize import save_over_smoothing_chart
    from .visualize import save_tsne_grid

    visuals: dict[str, str] = {}

    comparison_path = mode_dir / "accuracy_comparison.png"
    save_accuracy_comparison_chart(runs, comparison_path)
    visuals["accuracy_comparison"] = str(comparison_path)

    history_path = mode_dir / "history_comparison.png"
    save_history_chart(runs, history_path)
    visuals["history_comparison"] = str(history_path)

    if not args.skip_tsne and all(run["tsne_coordinates"] is not None for run in runs):
        tsne_grid_path = mode_dir / "tsne_grid.png"
        save_tsne_grid(
            runs=runs,
            labels=graph.labels,
            label_names=graph.label_names,
            output_path=tsne_grid_path,
        )
        visuals["tsne_grid"] = str(tsne_grid_path)

    if args.mode == "over-smoothing":
        smoothing_path = mode_dir / "over_smoothing_diagnostics.png"
        save_over_smoothing_chart(runs, smoothing_path)
        visuals["over_smoothing_diagnostics"] = str(smoothing_path)

    if args.mode == "embedding-separation":
        separation_path = mode_dir / "embedding_separation_summary.png"
        save_embedding_separation_chart(runs, separation_path)
        visuals["embedding_separation_summary"] = str(separation_path)

    return visuals


def main() -> None:
    args = build_parser().parse_args()
    _configure_environment(args.artifacts_dir)
    mode_dir = args.artifacts_dir / args.mode.replace("-", "_")
    mode_dir.mkdir(parents=True, exist_ok=True)

    graph = load_graph_data(
        data_dir=args.data_dir,
        db_path=mode_dir / "cora.duckdb",
        seed=args.seed,
    )

    runner = MODE_TO_RUNNER[args.mode]
    artifacts = runner(graph, args)

    runs = [
        _save_experiment_outputs(args=args, graph=graph, artifact=artifact, mode_dir=mode_dir)
        for artifact in artifacts
    ]
    visuals = _build_mode_visualizations(args=args, graph=graph, runs=runs, mode_dir=mode_dir)

    report = {
        "mode": args.mode,
        "question_count": len(artifacts),
        "visualizations": visuals,
        "runs": [
            {
                key: value
                for key, value in run.items()
                if key != "history" and key != "tsne_coordinates"
            }
            for run in runs
        ],
    }
    report_path = mode_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"DuckDB saved to: {mode_dir / 'cora.duckdb'}")
    print(f"Experiment report saved to: {report_path}")
