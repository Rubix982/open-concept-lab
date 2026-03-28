from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from .arxiv_data import build_cached_arxiv_dataset
from .arxiv_data import load_arxiv_graph_data
from .data import load_graph_data
from .experiments import MODE_TO_RUNNER

SINGLE_RUN_MODES = sorted(MODE_TO_RUNNER.keys())
ALL_MODES = sorted([*SINGLE_RUN_MODES, "compare-runs", "full-experiment"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run manual NumPy GCN experiments on the Cora citation graph.")
    parser.add_argument("--model", choices=["gcn", "graphsage", "gat", "gt"], default="gcn")
    parser.add_argument("--dataset", choices=["cora", "arxiv"], default="cora")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument(
        "--mode",
        choices=ALL_MODES,
        default="baseline",
        help="Experiment mode to run.",
    )
    parser.add_argument("--epochs", type=int, default=250)
    parser.add_argument("--hidden-dim", type=int, default=16)
    parser.add_argument("--gat-heads", type=int, default=1)
    parser.add_argument("--gat-attention-dropout", type=float, default=0.5)
    parser.add_argument("--gt-heads", type=int, default=4)
    parser.add_argument("--gt-layers", type=int, default=2)
    parser.add_argument("--gt-trace-with-nnsight", action="store_true")
    parser.add_argument("--learning-rate", type=float, default=0.2)
    parser.add_argument("--weight-decay", type=float, default=5e-4)
    parser.add_argument("--dropout", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--graphsage-fanouts",
        nargs="+",
        type=int,
        default=[10, 5],
        help="Neighbor sample sizes per GraphSAGE layer. Extra layers reuse the last value.",
    )
    parser.add_argument("--graphsage-variant", choices=["v1", "v2"], default="v1")
    parser.add_argument("--graphsage-backend", choices=["numpy", "jax"], default="numpy")
    parser.add_argument("--graphsage-batch-size", type=int, default=64)
    parser.add_argument("--graphsage-aggregator", choices=["mean", "pool", "lstm"], default="mean")
    parser.add_argument(
        "--graphsage-sampler",
        choices=["uniform", "with-replacement", "degree-weighted"],
        default="uniform",
    )
    parser.add_argument(
        "--arxiv-categories",
        nargs="+",
        default=["cs.AI", "cs.LG", "cs.CL", "cs.CV"],
        help="arXiv categories to fetch when --dataset arxiv is selected.",
    )
    parser.add_argument("--arxiv-max-results", type=int, default=280)
    parser.add_argument("--arxiv-batch-size", type=int, default=100)
    parser.add_argument("--arxiv-delay-seconds", type=float, default=3.0)
    parser.add_argument("--arxiv-top-k", type=int, default=10)
    parser.add_argument("--density-top-k-values", nargs="+", type=int, default=[5, 10, 20, 40])
    parser.add_argument("--arxiv-max-features", type=int, default=1000)
    parser.add_argument("--compare-config-a", type=Path, default=None)
    parser.add_argument("--compare-config-b", type=Path, default=None)
    parser.add_argument("--compare-name", type=str, default="default")
    parser.add_argument("--cache-only", action="store_true", help="Fetch/cache arXiv data and stop before training.")
    parser.add_argument(
        "--refresh-arxiv-cache",
        action="store_true",
        help="Refresh cached arXiv raw and processed artifacts before building the dataset.",
    )
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


def _artifact_root_dir(args: argparse.Namespace) -> Path:
    model_root_dir = args.artifacts_dir / args.model
    if args.model == "graphsage":
        model_root_dir = (
            model_root_dir
            / args.graphsage_backend
            / args.graphsage_variant
            / args.graphsage_aggregator
            / args.graphsage_sampler
        )
    return model_root_dir


def _load_compare_config(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"Compare config must be a JSON object: {path}")
    if payload.get("mode") == "compare-runs":
        raise ValueError(f"Nested compare-runs is not allowed: {path}")
    return payload


def _config_to_cli_args(config: dict[str, object]) -> list[str]:
    args: list[str] = []
    for key, value in config.items():
        if key in {"compare_label", "run_label"}:
            continue
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                args.append(flag)
            continue
        if isinstance(value, list):
            args.append(flag)
            args.extend(str(item) for item in value)
            continue
        if value is None:
            continue
        args.extend([flag, str(value)])
    return args


def _extract_report_path(stdout: str) -> str:
    for line in reversed(stdout.splitlines()):
        prefix = "Experiment report saved to: "
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
        cache_prefix = "Cache report saved to: "
        if line.startswith(cache_prefix):
            return line[len(cache_prefix) :].strip()
    raise ValueError("Could not locate report path in subprocess output.")


def _summarize_report(report: dict[str, object], label: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for run in report.get("runs", []):
        metrics = run.get("metrics", {})
        rows.append(
            {
                "label": label,
                "model": report.get("model", ""),
                "mode": report.get("mode", ""),
                "gat_heads": report.get("gat_heads", ""),
                "gt_heads": report.get("gt_heads", ""),
                "gt_layers": report.get("gt_layers", ""),
                "graphsage_backend": report.get("graphsage_backend", ""),
                "graphsage_variant": report.get("graphsage_variant", ""),
                "graphsage_aggregator": report.get("graphsage_aggregator", ""),
                "graphsage_sampler": report.get("graphsage_sampler", ""),
                "run_name": run.get("name", ""),
                "train_accuracy": metrics.get("train_accuracy", None),
                "val_accuracy": metrics.get("val_accuracy", None),
                "test_accuracy": metrics.get("test_accuracy", None),
                "num_layers": metrics.get("num_layers", None),
            }
        )
    return rows


def _format_metric(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _best_row(rows: list[dict[str, object]], metric: str) -> dict[str, object] | None:
    valid_rows = [row for row in rows if isinstance(row.get(metric), (int, float))]
    if not valid_rows:
        return None
    return max(valid_rows, key=lambda row: float(row[metric]))


def _build_winner_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for metric in ("train_accuracy", "val_accuracy", "test_accuracy"):
        winner = _best_row(rows, metric)
        if winner is None:
            continue
        summary.append(
            {
                "metric": metric,
                "label": winner.get("label", ""),
                "value": winner.get(metric),
                "model": winner.get("model", ""),
                "gt_heads": winner.get("gt_heads", ""),
                "gt_layers": winner.get("gt_layers", ""),
                "graphsage_backend": winner.get("graphsage_backend", ""),
                "graphsage_aggregator": winner.get("graphsage_aggregator", ""),
                "graphsage_sampler": winner.get("graphsage_sampler", ""),
            }
        )
    return summary


def _write_comparison_table(output_path: Path, rows: list[dict[str, object]]) -> None:
    headers = [
        "label",
        "model",
        "mode",
        "gat_heads",
        "gt_heads",
        "gt_layers",
        "graphsage_backend",
        "graphsage_variant",
        "graphsage_aggregator",
        "graphsage_sampler",
        "run_name",
        "train_accuracy",
        "val_accuracy",
        "test_accuracy",
        "num_layers",
    ]
    winner_summary = _build_winner_summary(rows)
    lines: list[str] = []
    if winner_summary:
        lines.append("## Winners")
        lines.append("")
        for item in winner_summary:
            lines.append(
                "- "
                f"{item['metric']}: {item['label']} "
                f"({ _format_metric(item['value']) })"
            )
        lines.append("")
        lines.append("## Comparison Table")
        lines.append("")

    lines.extend(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
    )
    for row in rows:
        lines.append("| " + " | ".join(_format_metric(row.get(header, "")) for header in headers) + " |")
    output_path.write_text("\n".join(lines) + "\n")


def _run_compare_subprocess(
    *,
    config_path: Path,
    label: str,
    run_dir: Path,
    data_dir: Path,
) -> dict[str, object]:
    config = _load_compare_config(config_path)
    display_label = str(config.get("compare_label") or config.get("run_label") or label)
    config.setdefault("data_dir", str(data_dir))
    config["artifacts_dir"] = str(run_dir)
    command = [sys.executable, "main.py", *_config_to_cli_args(config)]
    completed = subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],
        text=True,
        capture_output=True,
        check=False,
    )
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    stdout_path.write_text(completed.stdout)
    stderr_path.write_text(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Compare run '{label}' failed with exit code {completed.returncode}.\n"
            f"stderr:\n{completed.stderr}"
        )
    report_path = Path(_extract_report_path(completed.stdout))
    report = json.loads(report_path.read_text())
    return {
        "label": display_label,
        "config_path": str(config_path),
        "report_path": str(report_path),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "report": report,
    }


def _run_compare_mode(args: argparse.Namespace) -> tuple[dict[str, object], Path]:
    if args.compare_config_a is None or args.compare_config_b is None:
        raise ValueError("--compare-config-a and --compare-config-b are required for --mode compare-runs.")

    compare_dir = args.artifacts_dir / "compare_runs" / args.compare_name
    compare_dir.mkdir(parents=True, exist_ok=True)
    run_a_dir = compare_dir / "run_a"
    run_b_dir = compare_dir / "run_b"
    run_a_dir.mkdir(parents=True, exist_ok=True)
    run_b_dir.mkdir(parents=True, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            _run_compare_subprocess,
            config_path=args.compare_config_a,
            label="run_a",
            run_dir=run_a_dir,
            data_dir=args.data_dir,
        )
        future_b = executor.submit(
            _run_compare_subprocess,
            config_path=args.compare_config_b,
            label="run_b",
            run_dir=run_b_dir,
            data_dir=args.data_dir,
        )
        result_a = future_a.result()
        result_b = future_b.result()

    comparison_rows = [
        *_summarize_report(result_a["report"], result_a["label"]),
        *_summarize_report(result_b["report"], result_b["label"]),
    ]
    comparison_table_path = compare_dir / "comparison.md"
    _write_comparison_table(comparison_table_path, comparison_rows)

    winner_summary = _build_winner_summary(comparison_rows)
    comparison_json = {
        "mode": "compare-runs",
        "name": args.compare_name,
        "config_a": str(args.compare_config_a),
        "config_b": str(args.compare_config_b),
        "runs": [
            {
                "label": result_a["label"],
                "config_path": result_a["config_path"],
                "report_path": result_a["report_path"],
                "stdout_path": result_a["stdout_path"],
                "stderr_path": result_a["stderr_path"],
            },
            {
                "label": result_b["label"],
                "config_path": result_b["config_path"],
                "report_path": result_b["report_path"],
                "stdout_path": result_b["stdout_path"],
                "stderr_path": result_b["stderr_path"],
            },
        ],
        "comparison_rows": comparison_rows,
        "winner_summary": winner_summary,
        "comparison_table_path": str(comparison_table_path),
    }
    report_path = compare_dir / "report.json"
    report_path.write_text(json.dumps(comparison_json, indent=2))
    return comparison_json, report_path


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


def _load_dataset(
    args: argparse.Namespace,
    mode_dir: Path,
    *,
    top_k_override: int | None = None,
) -> tuple[object, Path, dict[str, object]]:
    if args.dataset == "cora":
        graph = load_graph_data(
            data_dir=args.data_dir,
            db_path=mode_dir / "cora.duckdb",
            seed=args.seed,
        )
        return graph, mode_dir / "cora.duckdb", {}

    graph, dataset_summary = build_cached_arxiv_dataset(
        data_dir=args.data_dir / "arxiv",
        db_path=mode_dir / "arxiv.duckdb",
        seed=args.seed,
        categories=args.arxiv_categories,
        max_results=args.arxiv_max_results,
        top_k=args.arxiv_top_k if top_k_override is None else top_k_override,
        max_features=args.arxiv_max_features,
        page_size=args.arxiv_batch_size,
        delay_seconds=args.arxiv_delay_seconds,
        refresh_cache=args.refresh_arxiv_cache,
        cache_only=args.cache_only,
    )
    return graph, mode_dir / "arxiv.duckdb", dataset_summary


def _run_single_mode(
    *,
    args: argparse.Namespace,
    graph: object,
    dataset_summary: dict[str, object],
    mode_dir: Path,
    mode_name: str,
    top_k_override: int | None = None,
) -> dict[str, object]:
    runner = MODE_TO_RUNNER[mode_name]
    original_mode = args.mode
    args.mode = mode_name
    try:
        artifacts = runner(graph, args)
        runs = [
            _save_experiment_outputs(args=args, graph=graph, artifact=artifact, mode_dir=mode_dir)
            for artifact in artifacts
        ]
        visuals = _build_mode_visualizations(args=args, graph=graph, runs=runs, mode_dir=mode_dir)
    finally:
        args.mode = original_mode

    return {
        "dataset": args.dataset,
        "model": args.model,
        "gat_heads": args.gat_heads if args.model == "gat" else 0,
        "gt_heads": args.gt_heads if args.model == "gt" else 0,
        "gt_layers": args.gt_layers if args.model == "gt" else 0,
        "graphsage_backend": args.graphsage_backend if args.model == "graphsage" else "",
        "graphsage_variant": args.graphsage_variant if args.model == "graphsage" else "",
        "graphsage_aggregator": args.graphsage_aggregator if args.model == "graphsage" else "",
        "graphsage_sampler": args.graphsage_sampler if args.model == "graphsage" else "",
        "mode": mode_name,
        "top_k": top_k_override,
        "dataset_summary": dataset_summary,
        "question_count": len(artifacts),
        "visualizations": visuals,
        "runs": [
            {key: value for key, value in run.items() if key not in {"history", "tsne_coordinates"}}
            for run in runs
        ],
    }


def _run_full_experiment(args: argparse.Namespace, suite_dir: Path) -> tuple[dict[str, object], Path]:
    suite_reports: list[dict[str, object]] = []

    base_mode_names = ["baseline", "feature-only", "graph-only", "depth-ablation", "over-smoothing", "embedding-separation"]
    density_values = sorted(dict.fromkeys(args.density_top_k_values))

    base_graph, base_db_path, base_dataset_summary = _load_dataset(args, suite_dir / "baseline")
    if args.cache_only:
        cache_report = {
            "dataset": args.dataset,
            "model": args.model,
            "gat_heads": args.gat_heads if args.model == "gat" else 0,
            "gt_heads": args.gt_heads if args.model == "gt" else 0,
            "gt_layers": args.gt_layers if args.model == "gt" else 0,
            "graphsage_backend": args.graphsage_backend if args.model == "graphsage" else "",
            "graphsage_variant": args.graphsage_variant if args.model == "graphsage" else "",
            "graphsage_aggregator": args.graphsage_aggregator if args.model == "graphsage" else "",
            "graphsage_sampler": args.graphsage_sampler if args.model == "graphsage" else "",
            "mode": "full-experiment",
            "cache_only": True,
            "dataset_summary": base_dataset_summary,
        }
        report_path = suite_dir / "cache_report.json"
        report_path.write_text(json.dumps(cache_report, indent=2))
        return cache_report, report_path

    for mode_name in base_mode_names:
        mode_dir = suite_dir / mode_name.replace("-", "_")
        mode_dir.mkdir(parents=True, exist_ok=True)
        graph = base_graph
        dataset_summary = base_dataset_summary
        if mode_name != "baseline":
            # Reuse the already-built graph object for same-top_k mode runs.
            graph = base_graph
        report = _run_single_mode(
            args=args,
            graph=graph,
            dataset_summary=dataset_summary,
            mode_dir=mode_dir,
            mode_name=mode_name,
        )
        mode_report_path = mode_dir / "report.json"
        mode_report_path.write_text(json.dumps(report, indent=2))
        suite_reports.append(report)

    density_reports: list[dict[str, object]] = []
    for top_k in density_values:
        density_dir = suite_dir / f"density_top_k_{top_k}"
        density_dir.mkdir(parents=True, exist_ok=True)
        graph, _, dataset_summary = _load_dataset(args, density_dir, top_k_override=top_k)
        report = _run_single_mode(
            args=args,
            graph=graph,
            dataset_summary=dataset_summary,
            mode_dir=density_dir,
            mode_name="baseline",
            top_k_override=top_k,
        )
        mode_report_path = density_dir / "report.json"
        mode_report_path.write_text(json.dumps(report, indent=2))
        density_reports.append(report)

    suite_report = {
        "dataset": args.dataset,
        "model": args.model,
        "gat_heads": args.gat_heads if args.model == "gat" else 0,
        "gt_heads": args.gt_heads if args.model == "gt" else 0,
        "gt_layers": args.gt_layers if args.model == "gt" else 0,
        "graphsage_backend": args.graphsage_backend if args.model == "graphsage" else "",
        "graphsage_variant": args.graphsage_variant if args.model == "graphsage" else "",
        "graphsage_aggregator": args.graphsage_aggregator if args.model == "graphsage" else "",
        "graphsage_sampler": args.graphsage_sampler if args.model == "graphsage" else "",
        "mode": "full-experiment",
        "dataset_summary": base_dataset_summary,
        "included_modes": base_mode_names,
        "density_top_k_values": density_values,
        "mode_reports": [
            {
                "mode": report["mode"],
                "top_k": report.get("top_k"),
                "report_path": str((suite_dir / report["mode"].replace("-", "_") / "report.json"))
                if report.get("top_k") is None
                else str((suite_dir / f"density_top_k_{report['top_k']}" / "report.json")),
            }
            for report in [*suite_reports, *density_reports]
        ],
    }
    report_path = suite_dir / "report.json"
    report_path.write_text(json.dumps(suite_report, indent=2))
    return suite_report, report_path


def main() -> None:
    args = build_parser().parse_args()
    _configure_environment(args.artifacts_dir)

    if args.mode == "compare-runs":
        report, report_path = _run_compare_mode(args)
        print(json.dumps(report, indent=2))
        print(f"Comparison report saved to: {report_path}")
        return

    model_root_dir = _artifact_root_dir(args)
    mode_dir = model_root_dir / args.mode.replace("-", "_")
    mode_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "full-experiment":
        report, report_path = _run_full_experiment(args, mode_dir)
        print(json.dumps(report, indent=2))
        print(f"Experiment report saved to: {report_path}")
        return

    graph, db_path, dataset_summary = _load_dataset(args, mode_dir)
    if args.cache_only:
        cache_report = {
            "dataset": args.dataset,
            "model": args.model,
            "gat_heads": args.gat_heads if args.model == "gat" else 0,
            "gt_heads": args.gt_heads if args.model == "gt" else 0,
            "gt_layers": args.gt_layers if args.model == "gt" else 0,
            "graphsage_backend": args.graphsage_backend if args.model == "graphsage" else "",
            "graphsage_variant": args.graphsage_variant if args.model == "graphsage" else "",
            "graphsage_aggregator": args.graphsage_aggregator if args.model == "graphsage" else "",
            "graphsage_sampler": args.graphsage_sampler if args.model == "graphsage" else "",
            "cache_only": True,
            "summary": dataset_summary,
        }
        report_path = mode_dir / "cache_report.json"
        report_path.write_text(json.dumps(cache_report, indent=2))
        print(json.dumps(cache_report, indent=2))
        print(f"Cache report saved to: {report_path}")
        return

    report = _run_single_mode(
        args=args,
        graph=graph,
        dataset_summary=dataset_summary,
        mode_dir=mode_dir,
        mode_name=args.mode,
    )
    report_path = mode_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    print(f"DuckDB saved to: {db_path}")
    print(f"Experiment report saved to: {report_path}")
