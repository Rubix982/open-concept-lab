"""
RetrievalProfile — structured uncertainty measurement from IIA data.

Implements the concept from sections/09-research-insights/belief-revision-and-uncertainty.md

Computes a 7-dimension profile from pre-computed IIA JSON files.
No model or API keys required — works entirely from saved results.

Usage:
    python scripts/retrieval_profile.py
    python scripts/retrieval_profile.py --model Qwen2.5-14B-Instruct
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

RESULTS_ROOT = Path(__file__).parent.parent / "belief_tracking" / "results"
SCRIPTS_DIR  = Path(__file__).parent
OUT_DIR      = SCRIPTS_DIR / "retrieval_profile_output"
OUT_DIR.mkdir(exist_ok=True)

THRESHOLD = 0.5   # IIA > this = "active"


# =============================================================================
# Epistemic classification
# =============================================================================

class EpistemicClass(Enum):
    ESTABLISHED  = "established"   # high coherence, no gap, early load
    PRELIMINARY  = "preliminary"   # lower coherence, late load, narrow window
    CONTESTED    = "contested"     # high competition, wide gap
    UNGROUNDED   = "ungrounded"    # mechanism never fired


# =============================================================================
# RetrievalProfile dataclass
# =============================================================================

@dataclass
class RetrievalProfile:
    """
    Structured uncertainty profile for one mechanism in one model.

    Each dimension captures a different aspect of how the retrieval unfolded.
    Together they approximate the 'mushy feeling' — the pre-linguistic
    signal of uncertainty that triggers metacognitive verification in humans.
    """

    mechanism:         str
    model:             str
    total_layers:      int

    # --- The 7 dimensions ---

    oid_coherence: float
    """Peak IIA of the binding mechanism (0.0–1.0).
    High = OID was strongly encoded. Low = encoding was tentative."""

    subspace_stability: float
    """Window width as fraction of total layers (0.0–1.0).
    Wide = mechanism active for many layers (stable, redundant).
    Narrow = mechanism compressed into few layers (brittle)."""

    attention_entropy: float
    """Spread of active window across model depth (start% to end%).
    Captures where in the model the mechanism fires.
    Later = deferred processing. Earlier = immediate encoding."""

    residual_competition: float
    """Peak IIA of the source_2 control experiment.
    High = competing signals are contesting the binding destination.
    Near zero = clean, uncontested binding."""

    layer_of_first_load: int
    """First layer where IIA exceeds threshold.
    Very late first load = context was hard to process."""

    gap_width: int
    """Layers between source-phase end and payload-phase start.
    Only meaningful for mechanisms with distinct source and payload phases.
    Wide gap = vulnerability window where mechanism is inactive."""

    load_count: int
    """Number of distinct IIA peaks (separated by dips below threshold).
    1 = clean single load. 2+ = model had to reload the mechanism."""

    # --- Derived ---
    active_layers: list[int] = field(default_factory=list)
    iia_curve:     list[float] = field(default_factory=list)
    layers:        list[int]   = field(default_factory=list)

    @property
    def epistemic_class(self) -> EpistemicClass:
        """
        Map profile pattern to epistemic classification.

        This operationalises the research insight from section 09:
        the pattern across dimensions — not any single value — determines class.
        """
        if self.oid_coherence == 0.0 and len(self.active_layers) == 0:
            return EpistemicClass.UNGROUNDED

        if (self.residual_competition > 0.3 or
                self.gap_width > int(self.total_layers * 0.10) or
                self.load_count > 1):
            return EpistemicClass.CONTESTED

        if (self.oid_coherence > 0.85 and
                self.subspace_stability > 0.05 and
                self.layer_of_first_load < int(self.total_layers * 0.50)):
            return EpistemicClass.ESTABLISHED

        return EpistemicClass.PRELIMINARY

    def summary(self) -> str:
        active_rng = (f"L{min(self.active_layers)}-{max(self.active_layers)}"
                      if self.active_layers else "none")
        return (
            f"  mechanism:          {self.mechanism}\n"
            f"  model:              {self.model} ({self.total_layers} layers)\n"
            f"  oid_coherence:      {self.oid_coherence:.3f}   (peak IIA)\n"
            f"  subspace_stability: {self.subspace_stability:.3f}   (window / total)\n"
            f"  attention_entropy:  {self.attention_entropy:.1f}%   (window start %)\n"
            f"  residual_competition:{self.residual_competition:.3f}   (source_2 peak IIA)\n"
            f"  layer_of_first_load:{self.layer_of_first_load}\n"
            f"  gap_width:          {self.gap_width} layers\n"
            f"  load_count:         {self.load_count}\n"
            f"  active_window:      {active_rng}\n"
            f"  epistemic_class:    {self.epistemic_class.value.upper()}"
        )


# =============================================================================
# IIA loader
# =============================================================================

def load_iia(path: Path) -> tuple[list[int], list[float]]:
    """Load IIA scores from a results directory. Returns (layers, scores)."""
    if not path.exists():
        return [], []
    layers, scores = [], []
    for fname in sorted(os.listdir(path), key=lambda x: int(x.replace(".json", ""))):
        data = json.load(open(path / fname))
        layers.append(int(fname.replace(".json", "")))
        if isinstance(data, dict) and "full_rank" in data:
            scores.append(data["full_rank"]["accuracy"])
        elif isinstance(data, dict) and "accuracy" in data:
            scores.append(data["accuracy"])
        else:
            scores.append(float(list(data.values())[0]))
    return layers, scores


# =============================================================================
# Profile computation
# =============================================================================

def count_peaks(layers: list[int], scores: list[float]) -> int:
    """Count distinct IIA peaks separated by dips below threshold."""
    active   = [s > THRESHOLD for s in scores]
    peaks    = 0
    in_peak  = False
    for a in active:
        if a and not in_peak:
            peaks   += 1
            in_peak  = True
        elif not a:
            in_peak  = False
    return max(peaks, 1 if any(active) else 0)


def compute_profile(
    mechanism:    str,
    model_label:  str,
    total_layers: int,
    novis_root:   Path,
    vis_root:     Optional[Path] = None,
) -> RetrievalProfile:
    """Compute RetrievalProfile for one mechanism from IIA data."""

    # Choose result paths based on mechanism type
    path_map: dict[str, tuple[Path, Optional[Path]]] = {
        "binding_address_payload": (
            novis_root / "binding_lookback" / "address_and_payload", None),
        "binding_char_oi": (
            novis_root / "binding_lookback" / "character_oi", None),
        "binding_obj_oi": (
            novis_root / "binding_lookback" / "object_oi", None),
        "binding_source_2": (
            novis_root / "binding_lookback" / "source_2", None),
        "answer_pointer": (
            novis_root / "answer_lookback" / "pointer", None),
        "answer_payload": (
            novis_root / "answer_lookback" / "payload", None),
        "vis_source": (
            vis_root / "visibility_lookback" / "source"
            if vis_root else None, None),
        "vis_addr_ptr": (
            vis_root / "visibility_lookback" / "address_and_pointer"
            if vis_root else None, None),
        "vis_payload": (
            vis_root / "visibility_lookback" / "payload"
            if vis_root else None, None),
    }

    main_path, _ = path_map.get(mechanism, (None, None))
    source2_path = novis_root / "binding_lookback" / "source_2"

    layers, scores = load_iia(main_path) if main_path else ([], [])
    _, source2_scores = load_iia(source2_path)

    active = [l for l, s in zip(layers, scores) if s > THRESHOLD]
    peak   = max(scores, default=0.0)
    peak_l = layers[scores.index(peak)] if scores and peak > 0 else 0

    # gap_width: only meaningful for vis mechanisms
    gap = 0
    if mechanism == "vis_source" and vis_root:
        src_ly, src_sc  = load_iia(vis_root / "visibility_lookback" / "source")
        pay_ly, pay_sc  = load_iia(vis_root / "visibility_lookback" / "payload")
        src_active = [l for l, s in zip(src_ly, src_sc) if s > THRESHOLD]
        pay_active = [l for l, s in zip(pay_ly, pay_sc) if s > THRESHOLD]
        if src_active and pay_active:
            gap = max(0, min(pay_active) - max(src_active))

    window_width = (len(active) / total_layers) if active else 0.0
    start_pct    = (min(active) / total_layers * 100) if active else 0.0
    first_load   = min(active) if active else total_layers

    return RetrievalProfile(
        mechanism=mechanism,
        model=model_label,
        total_layers=total_layers,
        oid_coherence=round(peak, 4),
        subspace_stability=round(window_width, 4),
        attention_entropy=round(start_pct, 1),
        residual_competition=round(max(source2_scores, default=0.0), 4),
        layer_of_first_load=first_load,
        gap_width=gap,
        load_count=count_peaks(layers, scores),
        active_layers=active,
        iia_curve=scores,
        layers=layers,
    )


# =============================================================================
# Profile comparison visualisation
# =============================================================================

def visualise_profiles(profiles: list[RetrievalProfile], out_path: Path) -> None:
    """
    Heatmap: mechanisms as rows, dimensions as columns.
    Each cell = normalised score (0=bad/brittle, 1=good/established).
    Rightmost column = epistemic class label.
    Immediately readable — dark green = healthy, dark red = problem.
    """

    mech_labels = [p.mechanism.replace("_", " ") for p in profiles]

    # --- 7 dimensions, all normalised to 0-1 where 1 = "better" ---
    dim_labels = [
        "Peak IIA\n(coherence)",
        "Window\nwidth",
        "Early\nload",
        "Clean\nbinding",
        "Narrow\ngap",
        "Single\nload",
        "Low\ncompetition",
    ]

    def to_row(p: RetrievalProfile) -> list[float]:
        return [
            p.oid_coherence,
            min(p.subspace_stability / 0.30, 1.0),           # 30%+ of depth = fully stable
            1.0 - min(p.attention_entropy / 100.0, 1.0),      # earlier = better
            1.0 - min(p.gap_width / max(p.total_layers * 0.15, 1), 1.0),
            1.0 - min((p.load_count - 1) / 2.0, 1.0),
            1.0 - p.residual_competition,
            1.0 - min(p.layer_of_first_load / p.total_layers, 1.0),
        ]

    matrix = np.array([to_row(p) for p in profiles])   # shape: (n_mechs, 7)

    class_colors = {
        EpistemicClass.ESTABLISHED: "#2E7D32",
        EpistemicClass.PRELIMINARY: "#E65100",
        EpistemicClass.CONTESTED:   "#B71C1C",
        EpistemicClass.UNGROUNDED:  "#616161",
    }

    fig, axes = plt.subplots(
        1, 2,
        figsize=(16, max(5, len(profiles) * 0.9 + 2)),
        gridspec_kw={"width_ratios": [3, 1]},
    )
    fig.suptitle(
        f"RetrievalProfile — {profiles[0].model}  ({profiles[0].total_layers} layers)\n"
        "Green = healthy mechanism  ·  Red = brittle or contested",
        fontsize=13, y=1.01,
    )

    # ── Left: heatmap ──────────────────────────────────────────────
    ax_heat: plt.Axes = axes[0]
    cmap = plt.cm.RdYlGn        # red (0) → yellow (0.5) → green (1)
    im = ax_heat.imshow(matrix, aspect="auto", cmap=cmap, vmin=0, vmax=1)

    ax_heat.set_xticks(range(len(dim_labels)))
    ax_heat.set_xticklabels(dim_labels, fontsize=9)
    ax_heat.set_yticks(range(len(mech_labels)))
    ax_heat.set_yticklabels(mech_labels, fontsize=10)
    ax_heat.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)

    # Annotate each cell with its numeric value
    for row_i, p in enumerate(profiles):
        for col_j, val in enumerate(to_row(p)):
            text_color = "white" if val < 0.35 or val > 0.85 else "black"
            ax_heat.text(col_j, row_i, f"{val:.2f}",
                         ha="center", va="center",
                         fontsize=9, color=text_color, fontweight="bold")

    plt.colorbar(im, ax=ax_heat, fraction=0.03, pad=0.02,
                 label="Score  (1 = healthy, 0 = brittle/contested)")

    # ── Right: epistemic class badges ──────────────────────────────
    ax_cls: plt.Axes = axes[1]
    ax_cls.set_xlim(0, 1)
    ax_cls.set_ylim(-0.5, len(profiles) - 0.5)
    ax_cls.axis("off")
    ax_cls.set_title("Class", fontsize=10, pad=8)

    for row_i, p in enumerate(profiles):
        color = class_colors[p.epistemic_class]
        y     = len(profiles) - 1 - row_i   # flip to match heatmap order
        ax_cls.add_patch(plt.Rectangle(
            (0.05, y - 0.35), 0.90, 0.70,
            color=color, alpha=0.85, linewidth=0,
        ))
        ax_cls.text(0.50, y,
                    p.epistemic_class.value.upper(),
                    ha="center", va="center",
                    fontsize=9, color="white", fontweight="bold")

    # Flip heatmap y-axis to match badge order
    ax_heat.invert_yaxis()

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out_path}")


# =============================================================================
# Main
# =============================================================================

def run(model_dir: str) -> None:
    novis_root = RESULTS_ROOT / "causalToM_novis" / model_dir
    vis_root   = RESULTS_ROOT / "causalToM_vis"   / model_dir

    if not novis_root.exists():
        print(f"No data found for model: {model_dir}")
        return

    # Infer total layers from available files
    sample_path = novis_root / "answer_lookback" / "payload"
    if sample_path.exists():
        files = os.listdir(sample_path)
        total_layers = max(int(f.replace(".json", "")) for f in files) + 1
    else:
        total_layers = 80  # fallback

    mechanisms = [
        "binding_address_payload",
        "binding_char_oi",
        "binding_obj_oi",
        "answer_pointer",
        "answer_payload",
    ]
    if vis_root.exists():
        mechanisms += ["vis_source", "vis_addr_ptr", "vis_payload"]

    profiles: list[RetrievalProfile] = []
    for mech in mechanisms:
        p = compute_profile(mech, model_dir, total_layers, novis_root,
                            vis_root if vis_root.exists() else None)
        profiles.append(p)

    print("=" * 65)
    print(f"RETRIEVAL PROFILE — {model_dir} ({total_layers}L)")
    print("=" * 65)
    print()

    for p in profiles:
        print(p.summary())
        print()

    # Visualise
    out_path = OUT_DIR / f"profile_{model_dir.replace('/', '_')}.png"
    visualise_profiles(profiles, out_path)

    # Summary table
    print("=" * 65)
    print("EPISTEMIC CLASSIFICATION SUMMARY")
    print("=" * 65)
    print(f"  {'Mechanism':<28} {'Class':<15} {'Peak IIA':>9} {'Gap':>6}")
    print("-" * 65)
    for p in profiles:
        cls = p.epistemic_class.value
        print(f"  {p.mechanism:<28} {cls:<15} {p.oid_coherence:>9.3f} "
              f"{p.gap_width:>6}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute RetrievalProfile from IIA result data"
    )
    parser.add_argument(
        "--model",
        default="Meta-Llama-3-70B-Instruct",
        help="Model directory name under results/causalToM_novis/"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run for all three paper models"
    )
    args = parser.parse_args()

    if args.all:
        for model in [
            "Meta-Llama-3-70B-Instruct",
            "Meta-Llama-3.1-405B-Instruct-8bit",
            "Qwen2.5-14B-Instruct",
        ]:
            print(f"\n{'='*65}")
            run(model)
    else:
        run(args.model)


if __name__ == "__main__":
    main()
