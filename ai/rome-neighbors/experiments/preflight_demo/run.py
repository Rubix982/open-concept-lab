"""
E-011 — Consolidated predictor-comparison demo (the Monday demo).

The three-act arc on real RippleEdits data, in one run, on `ripplekit`:
  ACT 1 (E-007)  raw distance is a flat, weak baseline across neighbour types
  ACT 2 (E-008)  layer sweep — is the flatness a position/layer artifact?
  ACT 3 (E-009)  structured ALIGNMENT — does it separate types where distance didn't?

Outputs one figure (predictor_arc.png) + one table (predictor_arc.txt) telling the
arc, plus the `sep` metric (mean(propagate) − locality) per predictor per layer —
the number that says whether a predictor is informative. This is the seed of the
edit-propagation pre-flight diagnostic (the target tool).

Scope: PREDICTOR comparison only. Turning "separates types" into "predicts
PROPAGATION" needs the causal outcome (E-010, IIA on nnpatch) — presented as a
plan for Arnab's review, not built here.

Usage:
    pip install -e .          # from repo root, once
    export NNSIGHT_API_KEY=... ; export RIPPLEEDITS_FILE=...   # if not default
    python experiments/preflight_demo/run.py
"""

import time
from pathlib import Path

from ripplekit import analysis, config, data, predictors, reps

OUT = config.RESULTS_DIR
OUT.mkdir(parents=True, exist_ok=True)
HOW = "mean"   # mean-pool avoids the last-token attention sink (E-005/E-007)


def _fmt(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m}m{s:02d}s"


def _progress(done: int, total: int, t0: float, label: str) -> None:
    frac = done / max(total, 1)
    bar = "█" * int(frac * 24) + "░" * (24 - int(frac * 24))
    el = time.time() - t0
    eta = (el / max(done, 1)) * (total - done)
    print(f"  {label} [{bar}] {done}/{total} ({frac*100:.0f}%) "
          f"· elapsed {_fmt(el)} · eta {_fmt(eta)} · cached {reps.cache_size()}",
          flush=True)


# ── data ────────────────────────────────────────────────────────────────────────
pairs = data.load_pairs()
ans_idx = data.answer_index()
loaded = reps.load_disk_cache()
print(f"{len(pairs)} typed pairs · layers {config.SWEEP_LAYERS} · how={HOW} "
      f"· resumed {loaded} cached reps\n", flush=True)

# ── fetch: proven single-layer path, per (unique prompt × layer) ────────────────
# (multi-layer prewarm left unvalidated while NDIF is flaky — single-layer is proven.)
_prompts: set[str] = set()
for p in pairs:
    _prompts.add(p.base)
    _prompts.add(p.neighbour)
    for q in list(ans_idx.get(p.answer, set()))[: config.K_ANCHOR + 1]:
        _prompts.add(q)
prompts = sorted(_prompts)
total_fetches = len(prompts) * len(config.SWEEP_LAYERS)
print(f"fetching up to {total_fetches} reps ({len(prompts)} prompts × "
      f"{len(config.SWEEP_LAYERS)} layers), checkpointing to disk...", flush=True)

t0 = time.time()
for j, pr in enumerate(prompts):
    reps.prewarm(pr, config.SWEEP_LAYERS, HOW)   # ONE pass/trace → all layers
    if (j + 1) % 20 == 0 or j == len(prompts) - 1:
        reps.save_disk_cache()                   # periodic checkpoint
        _progress((j + 1) * len(config.SWEEP_LAYERS), total_fetches, t0, "fetch")
reps.save_disk_cache()
print(f"fetch complete in {_fmt(time.time()-t0)}\n", flush=True)

# ── compute raw distance + alignment, per layer ────────────────────────────────
# raw_by[layer]   : list[(type, cos(base, neighbour))]
# align_by[layer] : list[(type, cos(neighbour, anchor(answer)))]
raw_by: dict[int, list[tuple[str, float]]] = {L: [] for L in config.SWEEP_LAYERS}
align_by: dict[int, list[tuple[str, float]]] = {L: [] for L in config.SWEEP_LAYERS}

print("computing predictors from cached reps (no remote calls)...", flush=True)
tc = time.time()
for i, p in enumerate(pairs):
    refs = [q for q in ans_idx.get(p.answer, set()) if q != p.neighbour]
    for L in config.SWEEP_LAYERS:
        raw_by[L].append((p.type, predictors.raw_distance(p.base, p.neighbour, L, HOW)))
        phi = predictors.anchor(p.answer, refs, L, HOW)
        if phi is not None:
            align_by[L].append((p.type, predictors.alignment(p.neighbour, phi, L, HOW)))
    if i % 20 == 0 or i == len(pairs) - 1:
        _progress(i + 1, len(pairs), tc, "compute")

# ── sep per predictor per layer (the headline signal) ──────────────────────────
lines: list[str] = []
lines.append(f"{'layer':>5}  {'sep(raw)':>10}  {'sep(align)':>11}")
lines.append("─" * 30)
sep_raw, sep_align = [], []
for L in config.SWEEP_LAYERS:
    sr = analysis.sep(analysis.aggregate_by_type(raw_by[L]))
    sa = analysis.sep(analysis.aggregate_by_type(align_by[L]))
    sep_raw.append(sr); sep_align.append(sa)
    lines.append(f"{L:>5}  {sr:>10.3f}  {sa:>11.3f}")

# best layer per predictor (max separation)
best_raw_L = config.SWEEP_LAYERS[max(range(len(sep_raw)), key=lambda k: sep_raw[k])]
best_align_L = config.SWEEP_LAYERS[max(range(len(sep_align)), key=lambda k: sep_align[k])]

table = "\n".join(lines)
print("\n" + table)
print(f"\nbest sep(raw)   @ layer {best_raw_L}   = {max(sep_raw):+.3f}")
print(f"best sep(align) @ layer {best_align_L} = {max(sep_align):+.3f}")
print("\nRead: sep≈0 = predictor can't tell should-propagate from locality.")
print("If sep(align) >> sep(raw), structured geometry carries what distance missed.")

# per-type detail at each predictor's best layer
print("\n── by type @ best layers ──")
analysis.print_table(f"raw distance @ L{best_raw_L}",
                     analysis.aggregate_by_type(raw_by[best_raw_L]))
analysis.print_table(f"alignment @ L{best_align_L}",
                     analysis.aggregate_by_type(align_by[best_align_L]))

# ── artifacts ─────────────────────────────────────────────────────────────────
(OUT / "predictor_arc.txt").write_text(
    f"n_pairs={len(pairs)} how={HOW} layers={config.SWEEP_LAYERS}\n\n"
    + table
    + f"\n\nbest sep(raw) @L{best_raw_L}={max(sep_raw):+.3f} "
    + f"best sep(align) @L{best_align_L}={max(sep_align):+.3f}\n"
)

# figure 1: the arc — sep vs layer, both predictors
try:
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.5), facecolor="#0a0c0f")
    ax.set_facecolor("#0f1318")
    ax.plot(config.SWEEP_LAYERS, sep_raw, marker="o", color="#e57373",
            linewidth=2, label="raw distance (baseline)")
    ax.plot(config.SWEEP_LAYERS, sep_align, marker="s", color="#4fc3f7",
            linewidth=2, label="structured alignment")
    ax.axhline(0, color="#4a5568", linewidth=0.8, linestyle=":")
    ax.set_xlabel("layer", color="#4a5568")
    ax.set_ylabel("separation  =  mean(propagate) − locality", color="#4a5568")
    ax.tick_params(colors="#4a5568")
    for s in ax.spines.values():
        s.set_color("#1e2530")
    ax.set_title(f"Which predictor separates propagate-types? — GPT-J · RippleEdits "
                 f"(n={len(pairs)})", color="#c8d4e0", fontsize=11)
    ax.legend(facecolor="#0f1318", edgecolor="#1e2530", labelcolor="#c8d4e0")
    fig.savefig(OUT / "predictor_arc.png", dpi=150, bbox_inches="tight", facecolor="#0a0c0f")
    print(f"\nSaved → {OUT/'predictor_arc.png'}  and  {OUT/'predictor_arc.txt'}")

    # figure 2: by-type bars, raw vs alignment, at their best layers
    analysis.bar_by_type(
        {"raw distance": analysis.aggregate_by_type(raw_by[best_raw_L]),
         "alignment": analysis.aggregate_by_type(align_by[best_align_L])},
        title=f"Similarity by neighbour type — GPT-J (n={len(pairs)})",
        out=OUT / "by_type.png", ylabel="cosine similarity",
    )
except ImportError:
    print("\n(matplotlib unavailable — tables written, plot skipped)")
