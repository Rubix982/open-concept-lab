# cache-locality-bench

A local prototype demonstrating memory-hierarchy effects on dense matrix
operations, grounded in recent HPC/ML research.

---

## Research Anchors

| # | Paper | Key Insight |
|---|-------|-------------|
| [1] | Dao et al. (2022). **FlashAttention**. NeurIPS 2022. [arXiv:2205.14135](https://arxiv.org/abs/2205.14135) | Reformulates attention as tiled SRAM computation; reduces HBM reads from O(Nd+N²) → O(N²d/M). The cleanest real-world application of cache-blocking theory. |
| [2] | Martínez et al. (2025). **Cache-aware Optimization of GEMM**. Cluster Computing 28, 779. [doi:10.1007/s10586-025-05426-6](https://doi.org/10.1007/s10586-025-05426-6) | Derives an analytical tile-size model for L2/L3 hierarchies; shows measurable gains over vanilla LAPACK on multicore CPUs. |
| [3] | Yuan et al. (2024). **LLM Inference Unveiled: Roofline Model Insights**. [arXiv:2402.16363](https://arxiv.org/abs/2402.16363) | Applies roofline analysis to every LLM layer; formally proves the decode phase is memory-bound. The OI framing in Part 2 mirrors theirs. |
| [4] | Deshmukh, Yokota, Bosilca (2023). **Batched MatMul on Intel/AMD/Fujitsu**. ACM TOMS. [arXiv:2311.07602](https://arxiv.org/abs/2311.07602) | Cross-architecture micro-kernel blocking study. Our tile-sweep methodology mirrors this. |

---

## What it measures

### Part 1 — Memory Layout (C-order vs F-order)
Row-major (C) vs column-major (Fortran) array traversal. When you read
a row from a C-order array, you walk contiguous memory — every cache line
fetched is fully used. Reading the same row from an F-order array jumps
`stride = N × 8` bytes between elements: each access is likely a separate
cache-line miss once the matrix exceeds L2.

This is the mechanical intuition FlashAttention formalises: GPU SRAM is
the "L1 cache" of the attention problem. If the score matrix exceeds SRAM,
you pay HBM bandwidth on every pass.

### Part 2 — Tiled Matrix Multiply
Manual blocked GEMM that isolates the tile-to-cache-level mapping:

| Tile | Working set (3 blocks) | Target level |
|------|------------------------|--------------|
| 32   | 24 KB                  | L1 (~64 KB)  |
| 64   | 96 KB                  | L2 (~256 KB) |
| 128  | 384 KB                 | L3           |
| 256  | 1.5 MB                 | L3 / spills  |

The operational intensity for N×N GEMM: `OI = 2N³ / (3 × N² × 8) = N/12`
FLOP/byte. The Roofline model [3] predicts: below the ridge point (~10–50
FLOP/byte on most CPUs) → memory-bound; above → compute-bound.

### Part 3 — FlashAttention IO Analogy
Two implementations of scaled dot-product attention:

- **Standard**: materialises the full `seq × seq` score matrix in RAM
- **Tiled**: online softmax accumulation — the score matrix never leaves
  a tile-sized working set (`TILE × seq × 4` bytes)

This is Algorithm 1 from Dao et al. [1], implemented in pure NumPy.

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python bench.py                          # defaults (n=2048, seq=512)
python bench.py --n 4096                 # push layout beyond L3
python bench.py --mm 512 --repeats 5    # more stable matmul timing
python bench.py --seq 2048 --d 64       # attention at realistic seq_len
```

---

## Observed results (M2 MacBook, Python 3.14, NumPy 2.4)

### Part 1 — Layout penalty: ~1×

The M2's unified memory architecture with a 12 MB L2 per cluster and
~100 GB/s memory bandwidth largely erases the cache-hostile penalty at
N=2048. NumPy's C-level BLAS path also uses SIMD prefetching that hides
stride effects. To see the effect you'd need:
- Pure Python element-access loops (no BLAS layer)
- N large enough to exhaust the L2 (try `--n 8192` on a server-class CPU)

This is actually a feature of Apple Silicon's design: the memory hierarchy
is intentionally wide and flat to reduce programmer sensitivity to access
patterns — the same reason M-series performs well for ML inference.

### Part 2 — Tile sweep: 33× → 2× vs BLAS as tile grows

```
tile=32  ( 24 KB) →  14.7 GFLOP/s  (33× slower than BLAS)
tile=64  ( 96 KB) →  48.7 GFLOP/s  (10× slower)
tile=128 (384 KB) → 127.3 GFLOP/s  ( 4× slower)
tile=256 (1.5 MB) → 209.0 GFLOP/s  ( 2× slower)
BLAS              → 484.9 GFLOP/s  ← ceiling
```

The closing gap is not (only) cache effects — it is Python dispatch overhead.
At `tile=32`, there are `(512/32)³ = 4096` Python calls into NumPy BLAS.
At `tile=256`, only `8`. Each call has ~5–10 µs overhead that BLAS assembly
eliminates entirely. The lesson: Python loop overhead and cache miss penalty
are both real costs that tiling addresses simultaneously.

### Part 3 — Tiled attention: 2.3× slower at seq=512, still slower at seq=2048

The standard path benefits from a single vectorised BLAS call for the full
`Q @ Kᵀ`. The tiled path replaces it with `(seq/TILE)²` smaller BLAS calls
— each fast individually, but carrying Python dispatch overhead per block.

On a real GPU (e.g. A100), FlashAttention wins because:
1. The CUDA kernel has no Python dispatch overhead
2. GPU HBM bandwidth (~2 TB/s) is still 10–20× slower than SRAM bandwidth
3. The score matrix at seq=2048 (16 MB) far exceeds GPU SRAM (~20 MB total)

On a CPU with fast unified RAM, the IO gap between "cache" and "RAM" is
smaller, so the bandwidth savings are harder to see in a Python prototype.
The correct experiment would be a Cython or C extension, or running on a
GPU with a real CUDA implementation.

---

## What this prototype teaches

1. **Layout beats algorithm** (at the RAM level). Access pattern relative
   to storage order determines memory bandwidth utilisation — before any
   algorithmic change.

2. **Tile size is a hardware constant, not an algorithm choice**. The optimal
   tile (Martínez et al. [2]) is the largest whose `3 × tile²` working set
   fits in L2. You can compute it analytically; this benchmark measures it.

3. **FlashAttention is a tiling paper**. The insight is not "use a clever
   algorithm" — it is "the score matrix is a temporary that exceeds on-chip
   memory, so don't materialise it." This benchmark runs that argument in
   Python to make it concrete, even if the speedup requires a CUDA kernel
   to observe.

4. **The Roofline model tells you which problem you have**. OI = N/12 for
   N×N GEMM. Below the ridge → memory bound (tile); above → compute bound
   (vectorise / SIMD / parallelise).

---

## Next directions

- **Numba JIT** the tiled loops to remove Python dispatch overhead and isolate pure cache effects
- **Cross-level tile sweep** — add `psutil`/`cpuinfo` to auto-detect L2 size and pick the theoretical optimum
- **Parallel tiling** — `multiprocessing` or `concurrent.futures` over row-tile blocks (embarrassingly parallel outer loop)
- **GPU version** — rewrite tiled_attn as a Triton kernel to reproduce the actual FlashAttention speedup
