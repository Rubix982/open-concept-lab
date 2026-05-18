/*
 * bench.c — Cache Locality Benchmark (C implementation)
 * =======================================================
 * No BLAS. No NumPy. No abstractions.
 * Just malloc, float*, pointer arithmetic, and clock_gettime.
 *
 * What this measures and why it matters
 * ──────────────────────────────────────
 * Modern CPUs are fast at arithmetic. The bottleneck is almost always
 * memory — how quickly you can feed data to the ALUs. The hierarchy is:
 *
 *   Registers  ~0.3 ns  (handful of values, lives in the CPU itself)
 *   L1 cache   ~1 ns    (32–192 KB, one per core)
 *   L2 cache   ~5 ns    (256 KB – 12 MB, one per core or cluster)
 *   L3 cache   ~20 ns   (4–64 MB, shared across cores)
 *   RAM        ~80 ns   (GBs, off-chip)
 *   SSD        ~100 µs  (TBs, off-machine)
 *
 * The CPU fetches memory in 64-byte chunks called cache lines.
 * If you read 8 doubles sequentially, you pay ONE cache miss and get all 8.
 * If you read 8 doubles with stride=2048, you pay EIGHT cache misses.
 * This benchmark makes that cost observable and measurable.
 *
 * Papers referenced
 * ──────────────────
 * [1] Dao et al., FlashAttention, NeurIPS 2022.           arXiv:2205.14135
 * [2] Martinez et al., Cache-aware GEMM, Cluster Comput.  doi:10.1007/s10586-025-05426-6
 * [3] Yuan et al., LLM Inference Roofline, 2024.          arXiv:2402.16363
 * [4] Deshmukh et al., Batched MatMul, ACM TOMS 2023.     arXiv:2311.07602
 *
 * Compile:
 *   make          ->  -O3 -march=native -ffast-math  (optimised)
 *   make debug    ->  -O0 -g                          (no optimisation)
 */

#include <math.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef __APPLE__
#  include <sys/sysctl.h>   /* sysctl: CPU brand, cache sizes on macOS */
#endif

/* ─────────────────────────────────────────────────────────────────────────────
 * Output: print to stdout AND an optional log file simultaneously.
 * Every printf in this file goes through P() so results are always captured.
 * ───────────────────────────────────────────────────────────────────────────*/

static FILE *g_log = NULL;   /* set by --out or auto-generated filename */

static void P(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt); vprintf(fmt, ap);        va_end(ap);
    if (g_log) {
    va_start(ap, fmt); vfprintf(g_log, fmt, ap); va_end(ap);
    }
}

/* ─────────────────────────────────────────────────────────────────────────────
 * Architecture detection
 *
 * We record the CPU model and cache sizes so a results file saved on one
 * machine can be compared meaningfully against a run on another.
 * Cache sizes determine the "right" tile size for Part 2 — what fits in L2
 * on an M2 is different from what fits in L2 on an Intel Xeon.
 * ───────────────────────────────────────────────────────────────────────────*/

typedef struct {
    char     cpu_brand[256];   /* e.g. "Apple M2"                       */
    uint64_t l1d_bytes;        /* L1 data cache size in bytes            */
    uint64_t l2_bytes;         /* L2 cache size in bytes                 */
    uint64_t l3_bytes;         /* L3 cache size (0 if absent/unified)    */
    uint64_t logical_cores;    /* logical CPU count                      */
} ArchInfo;

static ArchInfo detect_arch(void)
{
    ArchInfo a;
    memset(&a, 0, sizeof(a));
    strcpy(a.cpu_brand, "unknown");

#ifdef __APPLE__
    size_t len;

    len = sizeof(a.cpu_brand);
    sysctlbyname("machdep.cpu.brand_string", a.cpu_brand, &len, NULL, 0);

    /* Apple Silicon reports hw.l1dcachesize per-cluster; Intel reports per-core */
    len = sizeof(a.l1d_bytes);
    sysctlbyname("hw.l1dcachesize", &a.l1d_bytes, &len, NULL, 0);

    len = sizeof(a.l2_bytes);
    sysctlbyname("hw.l2cachesize", &a.l2_bytes, &len, NULL, 0);

    len = sizeof(a.l3_bytes);
    sysctlbyname("hw.l3cachesize", &a.l3_bytes, &len, NULL, 0);

    len = sizeof(a.logical_cores);
    sysctlbyname("hw.logicalcpu", &a.logical_cores, &len, NULL, 0);
#else
    /* Linux: read from /proc/cpuinfo for brand, sysfs for cache sizes.
     * Left as an exercise — add #elif defined(__linux__) block here.    */
    strcpy(a.cpu_brand, "Linux CPU (detection not implemented)");
    a.logical_cores = 1;
#endif

    return a;
}

/* Build a filename-safe version of the CPU brand for the results file.
 * "Apple M2 Pro" -> "Apple_M2_Pro"                                       */
static void cpu_to_slug(const char *brand, char *slug, size_t maxlen)
{
    size_t j = 0;
    for (size_t i = 0; brand[i] && j < maxlen - 1; i++) {
        char c = brand[i];
        /* keep alphanumeric, replace everything else with underscore */
        slug[j++] = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                    (c >= '0' && c <= '9')  ? c : '_';
    }
    slug[j] = '\0';
}

static void print_arch(const ArchInfo *a)
{
    P("  CPU            : %s\n",   a->cpu_brand);
    P("  Logical cores  : %llu\n", (unsigned long long)a->logical_cores);
    P("  L1D cache      : %llu KB\n", (unsigned long long)(a->l1d_bytes  / 1024));
    P("  L2 cache       : %llu KB\n", (unsigned long long)(a->l2_bytes   / 1024));
    if (a->l3_bytes > 0)
        P("  L3 cache       : %llu KB\n", (unsigned long long)(a->l3_bytes / 1024));
    else
        P("  L3 cache       : N/A (Apple Silicon has unified L2 per cluster)\n");
}

/* ─────────────────────────────────────────────────────────────────────────────
 * Timing
 *
 * clock_gettime(CLOCK_MONOTONIC) gives wall-clock time that is:
 *   - monotonic: never goes backwards (unlike gettimeofday)
 *   - nanosecond resolution on Linux/macOS
 * We return seconds as a double; 1e-9 precision is enough for µs benchmarks.
 * ───────────────────────────────────────────────────────────────────────────*/

static double now_s(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * Aligned allocation
 *
 * posix_memalign(ptr, alignment, size) guarantees the returned pointer is
 * a multiple of `alignment` bytes. We use CACHE_LINE (64) so our arrays
 * start on a cache-line boundary.
 *
 * Why does alignment matter?
 * A cache line is 64 bytes. If an array starts at address 0x38 (56), the
 * first 8 bytes of data share a cache line with whatever came before it.
 * Accessing A[0] fetches that shared line; accessing A[1] (offset 8) is
 * fine; but A[0] was "split" — two potential cache lines for one logical
 * start. With alignment=64, A[0] is guaranteed to be the *first* element
 * in its cache line. Cleaner prefetch, no false sharing on the first fetch.
 * ───────────────────────────────────────────────────────────────────────────*/

#define CACHE_LINE 64   /* bytes — true for x86_64 and ARM64 */

static double *alloc_d(size_t n)
{
    void *p = NULL;
    if (posix_memalign(&p, CACHE_LINE, n * sizeof(double)) != 0) {
        perror("posix_memalign"); exit(1);
    }
    return memset(p, 0, n * sizeof(double));
}

static float *alloc_f(size_t n)
{
    void *p = NULL;
    if (posix_memalign(&p, CACHE_LINE, n * sizeof(float)) != 0) {
        perror("posix_memalign"); exit(1);
    }
    return memset(p, 0, n * sizeof(float));
}

static void fill_rand_d(double *A, size_t n)
{
    for (size_t i = 0; i < n; i++)
        A[i] = (double)rand() / (double)RAND_MAX;
}

static void fill_rand_f(float *A, size_t n)
{
    for (size_t i = 0; i < n; i++)
        A[i] = (float)rand() / (float)RAND_MAX;
}

/* ─────────────────────────────────────────────────────────────────────────────
 * Formatting helpers
 * ───────────────────────────────────────────────────────────────────────────*/

static void section(const char *title)
{
    P("\n────────────────────────────────────────────────────────────────\n");
    P("  %s\n", title);
    P("────────────────────────────────────────────────────────────────\n");
}

static void print_row(const char *label, double ms, double ref_ms)
{
    if (ref_ms <= 0.0) {
        P("  %-46s %8.2f ms\n", label, ms);
        return;
    }
    double ratio = ms / ref_ms;
    if (ratio < 1.0)
        P("  %-46s %8.2f ms   %5.1f×\n",        label, ms, 1.0 / ratio);
    else
        P("  %-46s %8.2f ms   %5.1f× slower\n", label, ms, ratio);
}

/* ═════════════════════════════════════════════════════════════════════════════
 * PART 1 — Memory Layout: row-major vs column-major traversal
 *
 * The problem
 * ───────────
 * You have an N×N matrix of doubles in memory. You want to sum every element.
 * There are two obvious ways to write the nested loop. They produce the same
 * answer. They do not take the same time.
 *
 * Why they differ: cache lines
 * ────────────────────────────
 * The CPU fetches memory in 64-byte blocks called cache lines.
 * One cache line = 64 / 8 = 8 doubles.
 *
 * Row-major (C default): A[i*N + j]
 *   A[i][0], A[i][1], ..., A[i][7] are contiguous in memory.
 *   Reading A[i][0] fetches a cache line containing A[i][0..7].
 *   The next 7 reads are free — data already in L1.
 *   Cost: N² / 8 cache misses total.
 *
 * Column-major: A[j*N + i]
 *   A[0][j], A[1][j], ..., A[N-1][j] are N*8 bytes apart.
 *   For N=2048: stride = 2048 * 8 = 16,384 bytes = 256 cache lines.
 *   Reading A[0][j] fetches a cache line. Reading A[1][j] is 256 lines away
 *   — that first line has already been evicted from L1/L2 long before we
 *   need it again. Almost every access is a fresh cache miss.
 *   Cost: N² cache misses total — 8× the theoretical minimum.
 *
 * Connection to FlashAttention [1]
 * ─────────────────────────────────
 * This same argument applies at GPU scale. The Q, K, V matrices in attention
 * live in HBM (GPU's "RAM", ~2 TB/s). The score matrix QKᵀ is N×N and at
 * seq=2048 is 16 MB — does not fit in on-chip SRAM (~20 MB shared across all
 * SMs). Every pass over it is a slow HBM fetch. FlashAttention tiles the
 * computation so the score matrix never leaves SRAM. Same insight, bigger gap.
 * ═════════════════════════════════════════════════════════════════════════════*/

/*
 * sum_row_major: walks A[0..N-1][0..N-1] in storage order.
 * Memory access pattern: A[0], A[1], A[2], ... — perfectly sequential.
 * Hardware prefetcher detects the stride=1 pattern immediately and begins
 * fetching the next cache line before we ask for it.
 */
static double sum_row_major(const double *A, size_t N)
{
    double acc = 0.0;
    for (size_t i = 0; i < N; i++)
        for (size_t j = 0; j < N; j++)
            acc += A[i * N + j];    /* stride 1 — hardware prefetcher loves this */
    return acc;
}

/*
 * sum_col_major: same matrix, same elements, different index order.
 * Memory access pattern: A[0], A[N], A[2N], ... — stride = N doubles.
 * For N=2048: each access is 16 KB apart. L1 is 64–192 KB (fits ~4–12 rows).
 * By the time we come back around to the same cache line, it is long gone.
 * The prefetcher cannot help with an irregular-looking large stride.
 */
static double sum_col_major(const double *A, size_t N)
{
    double acc = 0.0;
    for (size_t i = 0; i < N; i++)
        for (size_t j = 0; j < N; j++)
            acc += A[j * N + i];    /* stride N — cache miss likely every access */
    return acc;
}

static void bench_layout(size_t N)
{
    char title[128];
    snprintf(title, sizeof(title),
        "Part 1 · Memory Layout  (N=%zu  matrix=%.0f KB per array)",
        N, (double)(N * N * sizeof(double)) / 1024.0);
    section(title);

    /* How many cache lines separate adjacent column elements? */
    size_t col_stride_bytes   = N * sizeof(double);
    size_t col_stride_lines   = col_stride_bytes / CACHE_LINE;
    /* Of the 8 doubles fetched per cache line, only 1 is useful in col-major */
    double useful_pct_col     = 100.0 / (double)(CACHE_LINE / sizeof(double));

    P("  Cache line             : %d bytes = %zu doubles\n",
      CACHE_LINE, (size_t)(CACHE_LINE / sizeof(double)));
    P("  Col-major stride       : %zu bytes = %zu cache lines between elements\n",
      col_stride_bytes, col_stride_lines);
    P("  Useful bytes per fetch : row=100%%  col=%.0f%%\n\n", useful_pct_col);

    double *A = alloc_d(N * N);
    fill_rand_d(A, N * N);

    /* Warm-up pass: bring data into whatever cache level it fits in.
     * Without this, the first timed run pays cold-start penalties that
     * aren't representative of steady-state performance.               */
    volatile double warmup = sum_row_major(A, N);
    (void)warmup;

    double t0, t1;

    t0 = now_s();
    volatile double s_row = sum_row_major(A, N);
    t1 = now_s();
    double ms_row = (t1 - t0) * 1e3;

    t0 = now_s();
    volatile double s_col = sum_col_major(A, N);
    t1 = now_s();
    double ms_col = (t1 - t0) * 1e3;

    /* volatile sinks prevent the compiler from proving the results are
     * unused and eliminating the loops entirely under -O3.             */
    (void)s_row; (void)s_col;

    double bytes = (double)(N * N * sizeof(double));
    print_row("row-major  A[i*N + j]  (stride 1, sequential)", ms_row, -1.0);
    print_row("col-major  A[j*N + i]  (stride N, cache-hostile)", ms_col, ms_row);

    P("\n  Effective bandwidth:\n");
    P("    row-major : %.1f GB/s  (close to measured DRAM bandwidth)\n",
      bytes / (ms_row * 1e-3) / 1e9);
    P("    col-major : %.1f GB/s  (bytes fetched >> bytes used)\n",
      bytes / (ms_col * 1e-3) / 1e9);
    P("  Cache-hostile penalty: %.1f×\n", ms_col / ms_row);
    P("  (Re-run with --n 4096 to push the matrix well past L3)\n");

    free(A);
}

/* ═════════════════════════════════════════════════════════════════════════════
 * PART 2 — GEMM: loop order and tiling
 *
 * Three C implementations of C += A × B for N×N double matrices.
 * Same algorithm. Same result. Different loop orders and blocking.
 * No BLAS. No SIMD. Every performance difference is purely cache behaviour.
 *
 * Why ijk is slow: B is accessed column-wise
 * ───────────────────────────────────────────
 *   for i: for j: for k:
 *     C[i][j] += A[i][k] * B[k][j]
 *
 *   In the inner k-loop:
 *     A[i*N+k]  — k increments → row access of A → sequential → GOOD
 *     B[k*N+j]  — k increments → column access of B → stride N → BAD
 *     C[i*N+j]  — i,j fixed in k-loop → scalar, lives in register → GOOD
 *
 *   Every inner-loop step advances B by N*8 bytes. For N=256: 2 KB stride.
 *   We bring in a cache line of B, use one double from it, then jump 2 KB.
 *   That cache line is likely evicted before we need it again.
 *
 * Why ikj is fast: one loop reorder, free speedup
 * ─────────────────────────────────────────────────
 *   for i: for k: for j:
 *     C[i][j] += A[i][k] * B[k][j]
 *
 *   In the inner j-loop:
 *     A[i*N+k]  — i,k fixed → scalar, hoisted to register → no memory
 *     B[k*N+j]  — j increments → row access of B → sequential → GOOD
 *     C[i*N+j]  — j increments → row access of C → sequential → GOOD
 *
 *   Both B and C are now accessed sequentially. The prefetcher handles both.
 *   Cost: 0 changed lines of math. Benefit: 5–10× speedup on cache-cold data.
 *
 * Why tiling goes further: the whole working set stays in cache
 * ─────────────────────────────────────────────────────────────
 *   Partition A, B, C into T×T blocks. The micro-kernel multiplies one
 *   (T×T) block of A by one (T×T) block of B and accumulates into C.
 *   Working set = 3 × T² × 8 bytes (three blocks, doubles).
 *
 *   If that fits in L2, all three blocks stay warm for the entire
 *   micro-kernel. No evictions mid-computation.
 *
 *   T=32  →  24 KB  → targets L1 (~64 KB)
 *   T=64  →  96 KB  → targets L2 (~256 KB – 4 MB depending on CPU)
 *   T=128 → 384 KB  → targets L3
 *
 *   This is exactly what BLAS does, plus SIMD register packing.
 *   Martínez et al. [2] derive the analytical optimal T; we sweep empirically.
 *
 * Operational intensity (Roofline model [3])
 * ───────────────────────────────────────────
 *   FLOPs = 2N³  (N² dot products, each N multiply-adds)
 *   Bytes ≥ 3N²×8  (minimum: load A, B once; store C once)
 *   OI = 2N³ / (24N²) = N/12  FLOP/byte
 *
 *   Below the ridge point (typically 10–50 FLOP/byte): memory-bound.
 *   Above: compute-bound, and SIMD/parallelism is what helps next.
 * ═════════════════════════════════════════════════════════════════════════════*/

/*
 * gemm_ijk: textbook triple loop, column-wise B access.
 * Exists only as a baseline to make the cache penalty visible.
 * Never use this ordering for real work.
 */
static void gemm_ijk(const double *A, const double *B, double *C, size_t N)
{
    for (size_t i = 0; i < N; i++)
        for (size_t j = 0; j < N; j++)
            for (size_t k = 0; k < N; k++)
                /* B[k*N+j]: k advances in this loop — column stride, cache-hostile */
                C[i*N+j] += A[i*N+k] * B[k*N+j];
}

/*
 * gemm_ikj: same formula, swapped j/k loop order.
 * A[i*N+k] is now constant in the j-loop — compiler hoists it to a register.
 * B[k*N+j] and C[i*N+j] both increment j — row access, sequential.
 * This is the minimum viable cache-friendly GEMM. Zero new ideas required.
 */
static void gemm_ikj(const double *A, const double *B, double *C, size_t N)
{
    for (size_t i = 0; i < N; i++)
        for (size_t k = 0; k < N; k++) {
            double a_ik = A[i*N+k];         /* hoisted: stays in a register     */
            for (size_t j = 0; j < N; j++)
                /* B[k*N+j]: j advances — row stride, sequential, prefetcher-friendly */
                C[i*N+j] += a_ik * B[k*N+j];
        }
}

/*
 * gemm_tiled: explicitly blocked GEMM.
 *
 * The ikj-order loop is already good but still accesses the *full* rows of B
 * and C per k-iteration. If N is large, those rows exceed L1 and get evicted
 * between k-steps. Tiling prevents this by processing in T×T sub-matrices
 * whose combined footprint fits in one cache level.
 *
 * Loop structure: outer tile loops (i,k,j) select the three blocks;
 * inner micro-kernel loops (ii,kk,jj) are the ikj pattern inside one block.
 * a_ik is hoisted identically — it's a scalar in the inner jj-loop.
 */
static void gemm_tiled(const double *A, const double *B, double *C,
                       size_t N, size_t T)
{
    for (size_t i = 0; i < N; i += T)                  /* i-tile */
    for (size_t k = 0; k < N; k += T)                  /* k-tile */
    for (size_t j = 0; j < N; j += T)                  /* j-tile */
    /* micro-kernel: one (T×T) × (T×T) block multiply */
    for (size_t ii = i, ie = i+T<N?i+T:N; ii < ie; ii++)
    for (size_t kk = k, ke = k+T<N?k+T:N; kk < ke; kk++) {
        double a_ik = A[ii*N+kk];           /* scalar in jj-loop — register */
        for (size_t jj = j, je = j+T<N?j+T:N; jj < je; jj++)
            C[ii*N+jj] += a_ik * B[kk*N+jj];   /* sequential in both B and C */
    }
}

static double run_gemm_fn(void (*fn)(const double*, const double*, double*, size_t),
                          size_t N)
{
    double *A = alloc_d(N * N);
    double *B = alloc_d(N * N);
    double *C = alloc_d(N * N);
    fill_rand_d(A, N * N); fill_rand_d(B, N * N);

    double t0 = now_s();
    fn(A, B, C, N);
    double ms = (now_s() - t0) * 1e3;

    /* Touch C so the compiler cannot prove it is dead and eliminate the call */
    volatile double sink = C[0] + C[N*N-1];
    (void)sink;

    free(A); free(B); free(C);
    return ms;
}

static double run_gemm_tiled(size_t N, size_t T)
{
    double *A = alloc_d(N * N);
    double *B = alloc_d(N * N);
    double *C = alloc_d(N * N);
    fill_rand_d(A, N * N); fill_rand_d(B, N * N);

    double t0 = now_s();
    gemm_tiled(A, B, C, N, T);
    double ms = (now_s() - t0) * 1e3;

    volatile double sink = C[0] + C[N*N-1];
    (void)sink;

    free(A); free(B); free(C);
    return ms;
}

static void bench_matmul(size_t N)
{
    char title[128];
    snprintf(title, sizeof(title),
        "Part 2 · GEMM  (N=%zu  OI≈%zu FLOP/byte  no BLAS no SIMD)",
        N, N / 12);
    section(title);

    double flops = 2.0 * (double)N * (double)N * (double)N;

    P("  %-46s %8s   %s\n", "kernel", "time", "GFLOP/s");
    P("  %s\n", "────────────────────────────────────────────────────────────");

    /* ijk: baseline — exists only to show the cache penalty */
    double ms_ijk = run_gemm_fn(gemm_ijk, N);
    P("  %-46s %8.2f ms   %.3f\n",
      "ijk  (B column-access — cache hostile)",
      ms_ijk, flops / (ms_ijk * 1e-3) / 1e9);

    /* ikj: free speedup from loop reorder only */
    double ms_ikj = run_gemm_fn(gemm_ikj, N);
    P("  %-46s %8.2f ms   %.3f   (%.1f× vs ijk)\n",
      "ikj  (B row-access — free loop reorder)",
      ms_ikj, flops / (ms_ikj * 1e-3) / 1e9, ms_ijk / ms_ikj);

    /* tiled: sweep three tile sizes to find the cache-level sweet spot */
    size_t tiles[] = {32, 64, 128};
    for (size_t t = 0; t < 3; t++) {
        size_t T      = tiles[t];
        size_t ws_kb  = 3 * T * T * sizeof(double) / 1024;   /* working set */
        char   label[64];
        snprintf(label, sizeof(label),
                 "tiled T=%-3zu  (%3zu KB working set)", T, ws_kb);
        double ms_t = run_gemm_tiled(N, T);
        P("  %-46s %8.2f ms   %.3f   (%.1f× vs ijk)\n",
          label, ms_t, flops / (ms_t * 1e-3) / 1e9, ms_ijk / ms_t);
    }

    P("\n  Every number above is raw C. No BLAS, no SIMD, no intrinsics.\n");
    P("  ijk→ikj: same 3 lines of math, different address arithmetic.\n");
    P("  Optimal tile T: largest value where 3T²×8 bytes < L2 size. [2]\n");
}

/* ═════════════════════════════════════════════════════════════════════════════
 * PART 3 — Attention IO analogy (FlashAttention without the GPU)
 *
 * What standard attention actually does to memory
 * ─────────────────────────────────────────────────
 * Scaled dot-product attention:
 *   S[i][j] = (Q[i] · K[j]) / sqrt(d)     step 1: seq×seq matrix → RAM
 *   S        = softmax_row(S)              step 2: read it back from RAM
 *   out[i]   = Σⱼ S[i][j] × V[j]          step 3: read it a third time
 *
 * S is a *temporary*. It is written once and read twice. It never needed
 * to persist. But in the standard implementation it is fully allocated,
 * and at seq=1024, float32: S = 1024² × 4 = 4 MB written + read twice.
 *
 * FlashAttention's core observation [1]
 * ──────────────────────────────────────
 * You do not need to materialise S if you maintain three running values
 * per query row: a running max m, a running normaliser l, and an
 * accumulated output vector acc.
 *
 * Online softmax update rule (per query row r, processing key tile j):
 *   s     = Q[r] · K[j] / sqrt(d)         (TILE×TILE partial scores)
 *   m_new = max(m_old, rowmax(s))
 *   acc   = acc × exp(m_old − m_new)       (rescale for new max)
 *         + exp(s − m_new) × V[j]
 *   l     = l   × exp(m_old − m_new)
 *         + rowsum(exp(s − m_new))
 *   m     = m_new
 * At the end: out[r] = acc / l
 *
 * Why the rescaling works: softmax is shift-invariant.
 *   softmax(x) = softmax(x − c) for any constant c.
 * We pick c = running max to keep exp() numerically stable (no overflow).
 * When the max changes, old exp values were computed with the wrong shift —
 * we correct them by multiplying by exp(old_max − new_max).
 *
 * Memory consequence:
 *   Standard:  alloc seq² floats, write, read, read → 3 × seq² × 4 bytes IO
 *   Tiled:     alloc TILE² floats (the s block), never more → tiny working set
 *
 * On this CPU the gap is modest — RAM is fast relative to compute.
 * On a GPU (A100: SRAM ~20 MB, HBM ~2 TB/s, SRAM BW ~10× faster):
 *   seq=2048, d=64: S = 16 MB > SRAM → every standard-path access is HBM.
 *   Tiled keeps score in SRAM. That is the entire speedup.
 * ═════════════════════════════════════════════════════════════════════════════*/

#define ATTN_TILE 64

/*
 * attention_standard: allocates the full seq×seq score matrix.
 * Three separate passes over the data — each a separate memory allocation
 * read. Clear, simple, correct. Pays full IO cost.
 */
static float *attention_standard(const float *Q, const float *K, const float *V,
                                  size_t seq, size_t d)
{
    float  scale = 1.0f / sqrtf((float)d);
    /* THE problematic allocation: seq² floats, written once, read twice */
    float *S   = alloc_f(seq * seq);
    float *out = alloc_f(seq * d);

    /* Pass 1: compute QKᵀ — writes every element of S to memory */
    for (size_t i = 0; i < seq; i++)
        for (size_t j = 0; j < seq; j++) {
            float dot = 0.0f;
            for (size_t dd = 0; dd < d; dd++)
                dot += Q[i*d+dd] * K[j*d+dd];
            S[i*seq+j] = dot * scale;   /* written to RAM — S is too big for cache */
        }

    /* Pass 2: row softmax — reads S back from RAM */
    for (size_t i = 0; i < seq; i++) {
        float mx = S[i*seq];
        for (size_t j = 1; j < seq; j++)
            if (S[i*seq+j] > mx) mx = S[i*seq+j];
        float sum = 0.0f;
        for (size_t j = 0; j < seq; j++) {
            S[i*seq+j] = expf(S[i*seq+j] - mx);    /* subtract max for stability */
            sum += S[i*seq+j];
        }
        for (size_t j = 0; j < seq; j++)
            S[i*seq+j] /= sum;
    }

    /* Pass 3: S × V — reads S from RAM a second time */
    for (size_t i = 0; i < seq; i++)
        for (size_t j = 0; j < seq; j++) {
            float s_ij = S[i*seq+j];
            for (size_t dd = 0; dd < d; dd++)
                out[i*d+dd] += s_ij * V[j*d+dd];
        }

    free(S);    /* S's entire lifetime: malloc → write → read → read → free */
    return out;
}

/*
 * attention_tiled: online softmax accumulation — S never allocated at full size.
 *
 * We process Q in ATTN_TILE-row chunks. For each chunk of queries, we
 * walk all key/value tiles and maintain per-row (m, l, acc).
 * The score block s is only ATTN_TILE × ATTN_TILE floats — fits in L1/L2.
 *
 * Working set at any point:
 *   q tile  : ATTN_TILE × d floats  = 64×64×4 = 16 KB
 *   k tile  : ATTN_TILE × d floats  = 16 KB
 *   v tile  : ATTN_TILE × d floats  = 16 KB
 *   s block : ATTN_TILE²   floats   = 16 KB
 *   acc,m,l : ATTN_TILE × (d+2)     ≈ 16 KB
 *   Total                           ≈ 80 KB  →  fits in L2
 *
 * Compare to standard path: seq=1024 → S = 4 MB  →  does not fit anywhere.
 */
static float *attention_tiled(const float *Q, const float *K, const float *V,
                               size_t seq, size_t d)
{
    float  scale = 1.0f / sqrtf((float)d);
    float *out   = alloc_f(seq * d);

    /* these four are the *entire* score-related allocation — no seq×seq */
    float *acc = alloc_f(ATTN_TILE * d);            /* accumulated output tile   */
    float *m   = alloc_f(ATTN_TILE);                /* per-row running max       */
    float *l   = alloc_f(ATTN_TILE);                /* per-row running normaliser*/
    float *s   = alloc_f(ATTN_TILE * ATTN_TILE);    /* TILE×TILE score block     */

    for (size_t i = 0; i < seq; i += ATTN_TILE) {
        /* how many query rows are in this tile (last tile may be smaller) */
        size_t qi = (i + ATTN_TILE <= seq) ? ATTN_TILE : seq - i;

        /* reset per-tile state: acc=0, m=-inf, l=0 */
        memset(acc, 0, qi * d * sizeof(float));
        for (size_t r = 0; r < qi; r++) { m[r] = -1e30f; l[r] = 0.0f; }

        for (size_t j = 0; j < seq; j += ATTN_TILE) {
            size_t kj = (j + ATTN_TILE <= seq) ? ATTN_TILE : seq - j;

            /* compute TILE×TILE partial scores: s[r][c] = Q[i+r]·K[j+c]/√d */
            for (size_t r = 0; r < qi; r++)
                for (size_t c = 0; c < kj; c++) {
                    float dot = 0.0f;
                    for (size_t dd = 0; dd < d; dd++)
                        dot += Q[(i+r)*d+dd] * K[(j+c)*d+dd];
                    s[r*ATTN_TILE+c] = dot * scale;
                    /* s lives in L1/L2 — it is TILE² floats, not seq² */
                }

            /* online softmax update per query row */
            for (size_t r = 0; r < qi; r++) {
                /* find new max across this score tile */
                float m_new = m[r];
                for (size_t c = 0; c < kj; c++)
                    if (s[r*ATTN_TILE+c] > m_new) m_new = s[r*ATTN_TILE+c];

                /* correction factor: old exp values used wrong shift */
                float exp_shift = expf(m[r] - m_new);

                /* exp(s − m_new) in-place — overwrites the score tile */
                for (size_t c = 0; c < kj; c++)
                    s[r*ATTN_TILE+c] = expf(s[r*ATTN_TILE+c] - m_new);

                /* rescale acc to account for the updated max */
                for (size_t dd = 0; dd < d; dd++)
                    acc[r*d+dd] *= exp_shift;

                /* accumulate new contribution: exp(s) × V tile */
                float l_new = l[r] * exp_shift;
                for (size_t c = 0; c < kj; c++) {
                    l_new += s[r*ATTN_TILE+c];
                    float s_rc = s[r*ATTN_TILE+c];
                    for (size_t dd = 0; dd < d; dd++)
                        acc[r*d+dd] += s_rc * V[(j+c)*d+dd];
                }

                m[r] = m_new;
                l[r] = l_new;
            }
        }

        /* normalise accumulated output and write to output matrix */
        for (size_t r = 0; r < qi; r++)
            for (size_t dd = 0; dd < d; dd++)
                out[(i+r)*d+dd] = acc[r*d+dd] / l[r];
    }

    free(acc); free(m); free(l); free(s);
    return out;
}

static float max_abs_err(const float *a, const float *b, size_t n)
{
    float err = 0.0f;
    for (size_t i = 0; i < n; i++) {
        float d = fabsf(a[i] - b[i]);
        if (d > err) err = d;
    }
    return err;
}

static void bench_attention(size_t seq, size_t d)
{
    size_t score_kb  = seq * seq * sizeof(float) / 1024;
    /* working set: q-tile + k-tile + s-block + acc (rough) */
    size_t tile_ws_kb = (2 * ATTN_TILE * d + ATTN_TILE * ATTN_TILE +
                         ATTN_TILE * (d + 2)) * sizeof(float) / 1024;
    char title[128];
    snprintf(title, sizeof(title),
        "Part 3 · Attention IO  (seq=%zu  d=%zu  score matrix=%zu KB)",
        seq, d, score_kb);
    section(title);

    float *Q = alloc_f(seq * d);
    float *K = alloc_f(seq * d);
    float *V = alloc_f(seq * d);
    fill_rand_f(Q, seq * d);
    fill_rand_f(K, seq * d);
    fill_rand_f(V, seq * d);

    double t0, t1;

    t0 = now_s();
    float *out_std = attention_standard(Q, K, V, seq, d);
    t1 = now_s();
    double ms_std = (t1 - t0) * 1e3;

    t0 = now_s();
    float *out_tiled = attention_tiled(Q, K, V, seq, d);
    t1 = now_s();
    double ms_tiled = (t1 - t0) * 1e3;

    /* verify correctness: both paths must agree to within float32 rounding */
    float err = max_abs_err(out_std, out_tiled, seq * d);

    P("  Score matrix    : %zu KB  (grows as seq²  —  quadratic in sequence length)\n",
      score_kb);
    P("  Tiled working   : ~%zu KB  (grows as seq  —  linear, fits in L2)\n",
      tile_ws_kb);
    P("  Max abs error   : %.2e  (numerical agreement; expect < 1e-4)\n\n",
      (double)err);

    print_row("standard  (allocate + write full seq×seq S)", ms_std,   -1.0);
    print_row("tiled     (online softmax, S never exists)  ", ms_tiled, ms_std);

    P("\n  Standard: S written to RAM once, read back twice = %zu KB × 3 = %zu KB IO\n",
      score_kb, score_kb * 3);
    P("  Tiled:    score block = %d × %d floats = %zu KB — never leaves L2\n",
      ATTN_TILE, ATTN_TILE, (size_t)(ATTN_TILE * ATTN_TILE * sizeof(float) / 1024));

    if (ms_tiled < ms_std)
        P("  Tiled wins: %.1f× — IO reduction beats inner-loop overhead.\n",
          ms_std / ms_tiled);
    else
        P("  Standard wins: %.1f× — inner loop overhead > IO saving at this size.\n"
          "  Try --seq 2048. On a GPU with HBM the tiled path always wins.\n",
          ms_tiled / ms_std);

    free(Q); free(K); free(V);
    free(out_std); free(out_tiled);
}

/* ─────────────────────────────────────────────────────────────────────────────
 * main
 * ───────────────────────────────────────────────────────────────────────────*/

int main(int argc, char *argv[])
{
    size_t layout_n  = 2048;
    size_t matmul_n  = 256;
    size_t attn_seq  = 512;
    size_t attn_d    = 64;
    char   out_path[512] = {0};   /* empty = auto-generate */

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--n")   && i+1 < argc) layout_n = (size_t)atoi(argv[++i]);
        if (!strcmp(argv[i], "--mm")  && i+1 < argc) matmul_n = (size_t)atoi(argv[++i]);
        if (!strcmp(argv[i], "--seq") && i+1 < argc) attn_seq = (size_t)atoi(argv[++i]);
        if (!strcmp(argv[i], "--d")   && i+1 < argc) attn_d   = (size_t)atoi(argv[++i]);
        if (!strcmp(argv[i], "--out") && i+1 < argc) {
            strncpy(out_path, argv[++i], sizeof(out_path) - 1);
        }
    }

    /* detect architecture before opening the log file so we can name it */
    ArchInfo arch = detect_arch();

    /* auto-generate results filename if not specified */
    if (out_path[0] == '\0') {
        time_t now = time(NULL);
        struct tm *tm_info = localtime(&now);
        char slug[128];
        cpu_to_slug(arch.cpu_brand, slug, sizeof(slug));
        /* strip trailing underscores from slug */
        for (int k = (int)strlen(slug)-1; k >= 0 && slug[k] == '_'; k--)
            slug[k] = '\0';
        strftime(out_path, sizeof(out_path), "../results/%Y-%m-%d_%H-%M-%S", tm_info);
        snprintf(out_path + strlen(out_path),
                 sizeof(out_path) - strlen(out_path),
                 "_%s.txt", slug);
    }

    g_log = fopen(out_path, "w");
    if (!g_log)
        fprintf(stderr, "warning: could not open %s for writing\n", out_path);
    else
        fprintf(stderr, "logging to: %s\n", out_path);

    /* ── header ── */
    P("\n════════════════════════════════════════════════════════════════\n");
    P("  Cache Locality Benchmark  (C)\n");
    P("  Compiled %s %s\n", __DATE__, __TIME__);
    P("════════════════════════════════════════════════════════════════\n\n");
    print_arch(&arch);
    P("\n  Parameters: --n %zu  --mm %zu  --seq %zu  --d %zu\n",
      layout_n, matmul_n, attn_seq, attn_d);

    srand(42);  /* fixed seed — reproducible random matrices across runs */

    bench_layout(layout_n);
    bench_matmul(matmul_n);
    bench_attention(attn_seq, attn_d);

    P("\n════════════════════════════════════════════════════════════════\n");
    P("  Takeaways\n");
    P("────────────────────────────────────────────────────────────────\n");
    P("  1. A[i*N+j] vs A[j*N+i]: same data, same math, different perf.\n");
    P("     The CPU has no idea which access pattern you intended.\n");
    P("  2. ijk→ikj: zero lines of algorithm changed. The loop order\n");
    P("     is the memory access pattern in row-major C.\n");
    P("  3. Tile size T is a hardware measurement, not algorithm choice.\n");
    P("     Optimal: largest T where 3T²×8 < L2 size.\n");
    P("  4. FlashAttention = 'S is a temporary that never needed to\n");
    P("     exist in RAM.' The rest is online softmax bookkeeping.\n");
    P("════════════════════════════════════════════════════════════════\n\n");

    if (g_log) fclose(g_log);
    return 0;
}
