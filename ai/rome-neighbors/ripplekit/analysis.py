"""Aggregation, the separation metric, and plotting — shared across experiments."""

from pathlib import Path

from . import config


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def aggregate_by_type(scores: list[tuple[str, float]]) -> dict[str, list[float]]:
    """Group (type, score) pairs into {type: [scores]} over the known TYPES."""
    out: dict[str, list[float]] = {t: [] for t in config.TYPES}
    for t, s in scores:
        if t in out:
            out[t].append(s)
    return out


def sep(by_type: dict[str, list[float]]) -> float:
    """Separation metric = mean(propagate types) − mean(locality).
    >0 means the predictor distinguishes should-propagate from should-not."""
    prop = [s for t in config.PROPAGATE_TYPES for s in by_type.get(t, [])]
    return mean(prop) - mean(by_type.get("locality", []))


def print_table(title: str, by_type: dict[str, list[float]]) -> None:
    print(f"\n── {title} ──")
    print(f"{'type':12s}  {'n':>4}  {'mean':>8}")
    print("─" * 28)
    for t in config.TYPES:
        v = by_type.get(t, [])
        print(f"{t:12s}  {len(v):>4}  {mean(v):>8.3f}")
    print(f"sep = {sep(by_type):+.3f}")


def bar_by_type(series: dict[str, dict[str, list[float]]], title: str,
                out: Path, ylabel: str = "score") -> None:
    """Grouped bar plot: one bar-group per neighbour type, one series per key.
    `series` = {series_name: by_type_dict}. Dark theme (project house style)."""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("(matplotlib unavailable — skipping plot)")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    colors = ["#e57373", "#4fc3f7", "#6fcf97", "#ffb74d", "#ce93d8"]
    fig, ax = plt.subplots(figsize=(9, 4.5), facecolor="#0a0c0f")
    ax.set_facecolor("#0f1318")
    x = np.arange(len(config.TYPES))
    n = len(series)
    w = 0.8 / max(n, 1)
    for i, (name, bt) in enumerate(series.items()):
        vals = [mean(bt.get(t, [])) for t in config.TYPES]
        ax.bar(x + (i - (n - 1) / 2) * w, vals, w, color=colors[i % len(colors)], label=name)
    ax.set_xticks(x); ax.set_xticklabels(config.TYPES, color="#c8d4e0")
    ax.tick_params(colors="#4a5568")
    ax.set_ylabel(ylabel, color="#4a5568")
    for s in ax.spines.values():
        s.set_color("#1e2530")
    ax.set_title(title, color="#c8d4e0", fontsize=11)
    ax.legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"Plot saved → {out}")
