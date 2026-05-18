#!/usr/bin/env python3
"""
bench.py — Cache Locality Benchmark (Python / NumPy implementation)
=====================================================================
This is the *high-level* version of the same benchmark in bench.c.
NumPy's operations ultimately call the same C/BLAS/LAPACK code that
any HPC library would — but the Python layer hides the cost.

Use this file to understand the concepts.
Use bench.c to see the raw hardware numbers.

Key difference from the C version
───────────────────────────────────
In C, a loop like:
    for i: for j: acc += A[j*N + i]
is executed element-by-element in your process. Each cache miss is yours.

In Python, `A.sum(axis=1)` dispatches to a C function inside NumPy.
That C function uses SIMD, prefetching, and sometimes BLAS routines that
partially hide cache miss penalties. This is why Part 1 shows a much
smaller penalty here than in the C benchmark — NumPy's internals absorb it.

The tiled attention (Part 3) is the exception: even in Python, avoiding
the seq×seq allocation is observable, because the memory pressure
from malloc + write + read dominates even through NumPy's optimisations.

Research anchors
────────────────
[1] Dao et al. (2022). FlashAttention: Fast and Memory-Efficient Exact
    Attention with IO-Awareness. NeurIPS 2022. arXiv:2205.14135
    → Tiling GEMM to fit SRAM: reduces HBM reads O(Nd+N²) → O(N²d/M)

[2] Martinez et al. (2025). Cache-aware Optimization of Matrix Multiplication
    and Matrix Factorizations on Multicore Processors.
    Cluster Computing 28, 779. doi:10.1007/s10586-025-05426-6
    → Analytical tile-size model for L2/L3 hierarchy.

[3] Yuan et al. (2024). LLM Inference Unveiled: Survey and Roofline Model
    Insights. arXiv:2402.16363
    → Roofline analysis of LLM layers; proves decode is memory-bound.

[4] Deshmukh, Yokota, Bosilca (2023). Cache Optimization and Performance
    Modeling of Batched Matrix Multiplication. ACM TOMS. arXiv:2311.07602
    → Cross-architecture tile-sweep methodology (mirrors this benchmark).

Usage
─────
    python bench.py                        # defaults
    python bench.py --n 4096               # bigger layout matrix
    python bench.py --mm 512 --repeats 5   # more timing samples
    python bench.py --seq 2048 --d 64      # bigger attention problem
"""

import argparse
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from typing import Callable, Optional

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Output: mirror every print to stdout AND a results file
# ─────────────────────────────────────────────────────────────────────────────

_log_file = None   # set in main()


def P(text: str = "") -> None:
    """Print to stdout and the open log file simultaneously."""
    print(text)
    if _log_file:
        _log_file.write(text + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# Architecture detection
#
# We capture CPU brand and cache sizes so results files saved on different
# machines are self-describing and comparable.
# ─────────────────────────────────────────────────────────────────────────────

def detect_arch() -> dict:
    """Return a dict of CPU / cache info for the current machine."""
    info: dict = {
        "cpu":          "unknown",
        "logical_cores": os.cpu_count() or 1,
        "l1d_kb":       None,
        "l2_kb":        None,
        "l3_kb":        None,
        "os":           platform.system(),
        "os_version":   platform.release(),
    }

    if platform.system() == "Darwin":
        # macOS: sysctl is the authoritative source for cache sizes
        def sysctl(key: str) -> str:
            try:
                return subprocess.check_output(
                    ["sysctl", "-n", key], stderr=subprocess.DEVNULL
                ).decode().strip()
            except Exception:
                return ""

        brand = sysctl("machdep.cpu.brand_string")
        if not brand:
            # Apple Silicon doesn't expose brand_string the same way
            brand = sysctl("hw.model")
        info["cpu"] = brand or "Apple Silicon"

        for key, field in [
            ("hw.l1dcachesize", "l1d_kb"),
            ("hw.l2cachesize",  "l2_kb"),
            ("hw.l3cachesize",  "l3_kb"),
        ]:
            val = sysctl(key)
            if val:
                info[field] = int(val) // 1024

    elif platform.system() == "Linux":
        # Linux: /proc/cpuinfo for brand, lscpu for cache
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        info["cpu"] = line.split(":")[1].strip()
                        break
        except OSError:
            pass

    return info


def print_arch(info: dict) -> None:
    P(f"  CPU            : {info['cpu']}")
    P(f"  Logical cores  : {info['logical_cores']}")
    P(f"  OS             : {info['os']} {info['os_version']}")
    P(f"  Python         : {sys.version.split()[0]}")
    P(f"  NumPy          : {np.__version__}")
    if info["l1d_kb"]:
        P(f"  L1D cache      : {info['l1d_kb']} KB")
    if info["l2_kb"]:
        P(f"  L2 cache       : {info['l2_kb']} KB")
    if info["l3_kb"]:
        P(f"  L3 cache       : {info['l3_kb']} KB")
    else:
        P(f"  L3 cache       : N/A (Apple Silicon unified L2)")


def cpu_slug(info: dict) -> str:
    """CPU name with spaces replaced by underscores, for use in filenames."""
    name = info["cpu"].replace(" ", "_")
    return "".join(c if c.isalnum() or c == "_" else "" for c in name)


# ─────────────────────────────────────────────────────────────────────────────
# Timing
#
# time.perf_counter() is the highest-resolution clock available in Python.
# We take the *minimum* over multiple runs — minimum eliminates OS scheduling
# noise better than mean or median for short, repeatable microbenchmarks.
# ─────────────────────────────────────────────────────────────────────────────

def timed(fn: Callable, repeats: int = 3) -> float:
    """Return minimum wall-clock time in seconds over `repeats` calls."""
    best = float("inf")
    for _ in range(repeats):
        t = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - t
        if elapsed < best:
            best = elapsed
    return best


def fmt_time(s: float) -> str:
    if s < 1e-3:  return f"{s * 1e6:7.1f} µs"
    if s < 1.0:   return f"{s * 1e3:7.1f} ms"
    return              f"{s:7.3f}  s"


def print_row(label: str, t: float, baseline: Optional[float] = None) -> None:
    if baseline is None:
        P(f"  {label:<46} {fmt_time(t)}")
        return
    if t < baseline:
        P(f"  {label:<46} {fmt_time(t)}   {baseline/t:5.1f}×")
    else:
        P(f"  {label:<46} {fmt_time(t)}   {t/baseline:5.1f}× slower")


def section(title: str) -> None:
    w = 66
    P(f"\n{'─' * w}")
    P(f"  {title}")
    P(f"{'─' * w}")


# ═════════════════════════════════════════════════════════════════════════════
# PART 1 — Memory Layout: C-order vs F-order
#
# NumPy arrays are C-order (row-major) by default: A[i, j] and A[i, j+1]
# are sizeof(float64) = 8 bytes apart — they share a cache line.
#
# np.asfortranarray() produces an F-order (column-major) copy: A[i, j] and
# A[i+1, j] become adjacent in memory. Reading row-by-row from an F-order
# array is the Python equivalent of the col-major C loop — strided reads.
#
# Why the penalty is smaller here than in C
# ───────────────────────────────────────────
# `A.sum(axis=1)` dispatches to a compiled C function in NumPy. That function
# uses SIMD and the compiler's auto-vectorizer, which may reorder loads,
# use wider registers, and benefit from hardware prefetching. It partially
# hides the cache miss penalty that raw C loops expose directly.
#
# To see the raw penalty, run the C version.
# To understand the concept, this version is sufficient.
#
# Connection to FlashAttention [1]
# ──────────────────────────────────
# The same argument applies at GPU scale. GPU "SRAM" (shared memory / L1)
# is ~164 KB per streaming multiprocessor on A100. The score matrix QKᵀ
# for seq=2048 is 16 MB — 100× larger. Every pass over it hits HBM.
# Tiling keeps the working set in SRAM. Same physics, bigger gap.
# ═════════════════════════════════════════════════════════════════════════════

def bench_layout(N: int, repeats: int) -> None:
    matrix_kb = N * N * 8 // 1024
    section(f"Part 1 · Memory Layout  (N={N}×{N}  matrix={matrix_kb} KB per array)")

    col_stride_bytes = N * 8
    col_stride_lines = col_stride_bytes // 64    # cache lines between column elements
    useful_pct_col   = 100.0 / 8                 # 1 of 8 doubles per cache line used

    P(f"  Cache line             : 64 bytes = 8 doubles")
    P(f"  Col-major stride       : {col_stride_bytes} bytes = {col_stride_lines} cache lines")
    P(f"  Useful bytes per fetch : row=100%  col={useful_pct_col:.0f}%")
    P()

    # C-order: A[i, j] and A[i, j+1] are contiguous → sequential reads
    A_c = np.random.rand(N, N).astype(np.float64)

    # F-order: A[i, j] and A[i+1, j] are contiguous → reading rows is strided
    # np.asfortranarray makes a copy with column-major memory layout
    A_f = np.asfortranarray(A_c)

    tests = [
        ("row sum  C-order  [stride=1, sequential]", A_c, 1),
        ("row sum  F-order  [stride=N, cache-hostile]", A_f, 1),
        ("col sum  C-order  [stride=N, cache-hostile]", A_c, 0),
        ("col sum  F-order  [stride=1, sequential]", A_f, 0),
    ]

    results = {}
    for label, arr, axis in tests:
        # lambda with default args captures the current arr/axis values
        results[label] = timed(lambda a=arr, ax=axis: a.sum(axis=ax), repeats)

    baseline = results["row sum  C-order  [stride=1, sequential]"]
    for label, t in results.items():
        print_row(label, t, baseline)

    penalty = results["row sum  F-order  [stride=N, cache-hostile]"] / baseline
    bandwidth_row = (N * N * 8) / (baseline * 1e9)
    P()
    P(f"  Effective bandwidth (row-major) : {bandwidth_row:.1f} GB/s")
    P(f"  Cache-hostile penalty           : {penalty:.1f}×")
    P(f"  (NumPy's C internals absorb some penalty — C version shows the raw number)")


# ═════════════════════════════════════════════════════════════════════════════
# PART 2 — Tiled matrix multiply
#
# We implement three versions to show the progression:
#
#   np.dot (BLAS)  : vendor-optimised ceiling — SIMD + register blocking
#   tiled (Python) : manual T×T blocking, inner multiply via NumPy
#
# Tiled working set per micro-kernel = 3 × T² × 8 bytes
#   T=32  →  24 KB  → targets L1 (~64 KB)
#   T=64  →  96 KB  → targets L2 (~4 MB on M2)
#   T=128 → 384 KB  → targets L3 (or L2 on large-cache CPUs)
#   T=256 → 1.5 MB  → L3 or spills
#
# Why BLAS still wins here
# ─────────────────────────
# Even with optimal tiling, Python loop overhead is real. With T=64 and
# N=512, there are (512/64)³ = 512 Python calls into NumPy for the inner
# block multiply. Each call has ~2–5 µs overhead. BLAS makes ONE call with
# the full N×N problem and uses SIMD assembly throughout.
#
# The lesson: tiling is the right idea; BLAS also tiles internally plus
# adds SIMD register blocking. The gap between our tiled Python and BLAS
# is interpreter overhead, not a flaw in the tiling concept.
#
# Operational intensity (Roofline model [3])
# ───────────────────────────────────────────
# OI = 2N³ / (3 × N² × 8) = N / 12  FLOP/byte
# For N=512: OI ≈ 43 — at or above the ridge point → compute-bound.
# For N=64:  OI ≈  5 — below ridge → memory-bound; tiling helps more.
# ═════════════════════════════════════════════════════════════════════════════

def tiled_matmul(A: np.ndarray, B: np.ndarray, tile: int) -> np.ndarray:
    """
    Blocked GEMM: partition A, B, C into (tile × tile) sub-matrices.

    The outer three Python loops select which block triple (A_blk, B_blk, C_blk)
    to work on. The inner multiply `A_blk @ B_blk` is a NumPy call that
    dispatches to BLAS for that small sub-problem.

    The cache benefit: each block triple has working set = 3×tile²×8 bytes.
    If that fits in L2, all three blocks stay warm across the inner k-loop.
    The inner BLAS call sees hot data; less time waiting for memory.
    """
    N = A.shape[0]
    C = np.zeros((N, N), dtype=A.dtype)
    for i in range(0, N, tile):
        ie = min(i + tile, N)
        for k in range(0, N, tile):
            ke = min(k + tile, N)
            # A block: rows [i:ie], cols [k:ke] — kept warm across j-loop
            a_blk = A[i:ie, k:ke]
            for j in range(0, N, tile):
                je = min(j + tile, N)
                # inner call: (tile×tile) @ (tile×tile) — working set fits in L2
                C[i:ie, j:je] += a_blk @ B[k:ke, j:je]
    return C


def bench_matmul(N: int, repeats: int) -> None:
    oi = N // 12
    section(f"Part 2 · Matrix Multiply  (N={N}  OI≈{oi} FLOP/byte)")

    A = np.random.rand(N, N).astype(np.float64)
    B = np.random.rand(N, N).astype(np.float64)
    flops = 2 * N ** 3

    # BLAS baseline: single call, internally tiled + SIMD + multi-threaded
    t_blas = timed(lambda: A @ B, repeats)
    gflops = flops / t_blas / 1e9
    P(f"  {'NumPy BLAS  (vendor ceiling)':<46} {fmt_time(t_blas)}   {gflops:.1f} GFLOP/s ← ceiling")

    # Tile sweep: show how working set size relative to cache affects speed
    for tile in [32, 64, 128, 256]:
        n_blocks = (N // tile) ** 3   # number of Python dispatch calls
        if n_blocks < 1:
            continue
        ws_kb = 3 * tile * tile * 8 // 1024
        label = f"tiled  tile={tile}  ({ws_kb} KB working set)"

        t = timed(lambda b=tile: tiled_matmul(A, B, b), max(repeats - 1, 1))
        gflops_t = flops / t / 1e9
        ratio = t / t_blas
        P(f"  {label:<46} {fmt_time(t)}   {gflops_t:.2f} GFLOP/s  ({ratio:.0f}× vs BLAS)")

    P()
    P("  Gap to BLAS = Python dispatch overhead, not a flaw in tiling.")
    P("  As tile grows: fewer dispatches, each call is a larger BLAS problem.")
    P("  BLAS eliminates all dispatch overhead with a single SIMD kernel.")


# ═════════════════════════════════════════════════════════════════════════════
# PART 3 — FlashAttention IO analogy
#
# This is the conceptual heart of [1]. The question is not "can we compute
# attention faster" — it is "do we need to write this intermediate matrix
# to RAM at all?"
#
# Standard path (quadratic memory)
# ──────────────────────────────────
#   S = softmax(QKᵀ / √d) · V
#   Allocates: seq×seq float32 matrix S
#   For seq=2048: S = 4 MB, written once, read twice = 12 MB total IO
#
# Tiled path — online softmax (Algorithm 1, Dao et al. [1])
# ──────────────────────────────────────────────────────────
#   Process Q in TILE-row blocks. For each Q tile:
#     Walk all K/V tiles. Maintain per query-row: (m, l, acc).
#     m   = running max of scores seen so far
#     l   = running normaliser (sum of exp(s − m))
#     acc = running output accumulation
#
#   When a new score tile arrives with values larger than current max m:
#     Rescale acc and l by exp(m_old − m_new) to correct for the wrong shift.
#     Then add the new contribution normally.
#
#   Mathematical basis: softmax is shift-invariant.
#     softmax(x) = softmax(x − c) for any constant c.
#   We pick c = running max to keep exp() numerically stable (prevents
#   overflow: if x[i] is 100, exp(100) overflows float32; exp(100−100)=1).
#
# Memory consequence
# ───────────────────
#   Standard: allocs seq×seq floats → peak memory O(seq²)
#   Tiled:    allocs TILE×TILE scores → peak memory O(seq × TILE)  ← linear!
#
#   TILE=64, seq=2048:
#     Standard score matrix  : 16 MB
#     Tiled score block       : 16 KB  (fits in L1)
#
# On this CPU the speedup is modest (RAM is fast).
# On a GPU (HBM << SRAM bandwidth by 10-20×) tiling always wins.
# ═════════════════════════════════════════════════════════════════════════════

def bench_attention(seq: int, d: int, repeats: int) -> None:
    score_kb  = seq * seq * 4 // 1024
    tile      = 64
    tile_ws_kb = (2 * tile * d + tile * tile) * 4 // 1024

    section(f"Part 3 · Attention IO  (seq={seq}  d={d}  score={score_kb} KB)")

    Q = np.random.rand(seq, d).astype(np.float32)
    K = np.random.rand(seq, d).astype(np.float32)
    V = np.random.rand(seq, d).astype(np.float32)
    scale = float(d) ** -0.5

    # ── Standard: allocate full seq×seq score matrix ──────────────────────
    def standard_attn() -> np.ndarray:
        # Step 1: QKᵀ — the problematic seq×seq allocation
        S = (Q @ K.T) * scale           # shape (seq, seq) — written to RAM
        # Step 2: numerically stable softmax — reads S back
        S -= S.max(axis=1, keepdims=True)
        np.exp(S, out=S)
        S /= S.sum(axis=1, keepdims=True)
        # Step 3: weighted sum with V — reads S a third time
        return S @ V

    # ── Tiled: online softmax, no full S ever allocated ───────────────────
    TILE = 64

    def tiled_attn() -> np.ndarray:
        """
        Flash-style: process Q in TILE-row chunks. Score matrix S never
        allocated — only a (TILE×TILE) block exists at any point.

        For each Q tile q_i:
          acc = zeros(TILE, d)     # accumulated weighted sum
          l   = zeros(TILE, 1)     # running normaliser
          m   = -inf(TILE, 1)      # running max (for numerical stability)

          For each K/V tile k_j, v_j:
            s     = q_i @ k_jᵀ * scale          # (TILE, TILE) — stays in L1
            m_new = max(m, rowmax(s))
            acc   = acc * exp(m − m_new)        # rescale old contribution
                  + exp(s − m_new) @ v_j
            l     = l   * exp(m − m_new)
                  + rowsum(exp(s − m_new))
            m     = m_new

          out[i] = acc / l
        """
        out = np.zeros((seq, d), dtype=np.float32)

        for i in range(0, seq, TILE):
            q = Q[i : i + TILE]                         # (TILE, d) — "SRAM"
            acc = np.zeros((q.shape[0], d), dtype=np.float32)
            l   = np.zeros((q.shape[0], 1), dtype=np.float32)
            m   = np.full((q.shape[0], 1), -1e9, dtype=np.float32)

            for j in range(0, seq, TILE):
                s = (q @ K[j : j + TILE].T) * scale     # (TILE, TILE) — tiny block

                m_new     = np.maximum(m, s.max(axis=1, keepdims=True))
                exp_shift = np.exp(m - m_new)            # correction for old data
                exp_s     = np.exp(s - m_new)            # exp of new scores

                # rescale existing accumulator, add new weighted V contribution
                acc = acc * exp_shift + exp_s @ V[j : j + TILE]
                l   = l   * exp_shift + exp_s.sum(axis=1, keepdims=True)
                m   = m_new

            out[i : i + TILE] = acc / l    # normalise and flush to output
        return out

    # Warm up
    standard_attn(); tiled_attn()

    t_std   = timed(standard_attn, repeats)
    t_tiled = timed(tiled_attn,    repeats)

    # Correctness check — both paths should agree to within float32 rounding
    ref = standard_attn()
    got = tiled_attn()
    max_err = float(np.abs(ref - got).max())

    P(f"  Score matrix size  : {score_kb} KB  (grows as seq²  —  quadratic)")
    P(f"  Tiled working set  : ~{tile_ws_kb} KB  (grows as seq  —  linear)")
    P(f"  Max absolute error : {max_err:.2e}  (expect < 1e-4)")
    P()
    print_row("standard   (allocate full seq×seq S)",         t_std)
    print_row("tiled      (online softmax, no full S)",       t_tiled, t_std)

    P()
    if t_tiled < t_std:
        P(f"  Tiled wins: {t_std / t_tiled:.1f}× — IO reduction beats Python loop overhead.")
    else:
        P(f"  Standard wins: {t_tiled / t_std:.1f}× — Python loop overhead > IO saving here.")
        P(f"  The threshold inverts when score matrix exceeds L3 (~seq 2048+).")
        P(f"  On a GPU (HBM latency >> SRAM), tiled wins decisively at seq ≥ 512.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    global _log_file

    ap = argparse.ArgumentParser(
        description="Cache locality benchmark (Python/NumPy)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--n",       type=int, default=2048, help="Layout matrix N (default 2048)")
    ap.add_argument("--mm",      type=int, default=512,  help="Matmul matrix N (default 512)")
    ap.add_argument("--seq",     type=int, default=512,  help="Attention seq length (default 512)")
    ap.add_argument("--d",       type=int, default=64,   help="Attention head dim (default 64)")
    ap.add_argument("--repeats", type=int, default=3,    help="Timing repeats (default 3)")
    ap.add_argument("--out",     type=str, default=None, help="Output file (default: auto)")
    args = ap.parse_args()

    arch = detect_arch()

    # Auto-generate results filename
    out_path = args.out
    if out_path is None:
        ts   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        slug = cpu_slug(arch)
        out_path = os.path.join(
            os.path.dirname(__file__), "results", f"{ts}_{slug}_py.txt"
        )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    _log_file = open(out_path, "w")
    print(f"logging to: {out_path}", file=sys.stderr)

    # Header
    P(f"\n{'═' * 66}")
    P(f"  Cache Locality Benchmark  (Python / NumPy)")
    P(f"{'═' * 66}")
    print_arch(arch)
    P(f"  Parameters     : --n {args.n}  --mm {args.mm}  --seq {args.seq}  --d {args.d}")

    bench_layout(args.n, args.repeats)
    bench_matmul(args.mm, args.repeats)
    bench_attention(args.seq, args.d, args.repeats)

    P(f"\n{'═' * 66}")
    P("  Key takeaways")
    P(f"{'─' * 66}")
    P("  1. Memory layout drives performance before any algorithm change.")
    P("     F-order data + row-wise reads = cache miss per element.")
    P("     (NumPy hides this partially; raw C exposes the full penalty.)")
    P()
    P("  2. Tiling keeps the working set in fast cache. Tile size is a")
    P("     hardware parameter. Optimal T: 3T²×8 < L2 size. [2]")
    P()
    P("  3. FlashAttention's breakthrough was recognising attention as an")
    P("     IO problem, not a FLOPs problem. [1]  (Dao et al., NeurIPS 2022)")
    P()
    P("  4. The Roofline model tells you which bottleneck you have:")
    P("     OI = N/12 FLOP/byte. Below ridge → memory-bound (tile).")
    P("     Above ridge → compute-bound (SIMD / parallelism). [3]")
    P(f"{'═' * 66}")
    P()

    _log_file.close()


if __name__ == "__main__":
    main()
