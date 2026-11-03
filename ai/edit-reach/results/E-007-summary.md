# [E-007] Conformance run — 2026-11-03

`meta-llama/Llama-3.1-8B`, layer 5, 11 remote traces, 57s, one session.
Reference: `docs/ndif-reproducibility.md`. Raw: `results/E-007-conformance.json` (gitignored).

```
check               documented        yours  verdict
dtype_budget                 -    3.887e-03  recorded
ratio_in_trace       0.000e+00    0.000e+00  matches
cached_reference     6.382e-03    7.299e-03  matches
batch_rows           0.000e+00    0.000e+00  matches
batch_width                  -    4.297e-02  recorded
matmul_site          5.060e-06    5.319e-06  matches
session_partition            -    1.000e+00  recorded
trace_source                 -            -  recorded
```

**Everything with a reference matched.** `batch_rows` is the derived ratio; its raw keys moved 4.297e-02 (2.59% of magnitude) and are reported in the same row's detail.

**New, not previously measured.** `batch_width` — the same rows and the same content with eight extra pad tokens move the raw keys by 4.297e-02. Causally this cannot matter; it is kernel shape-dependence.

**Not reproduced.** Four fresh connections all landed on GPU 0 and returned one signature, so [E-006]'s GPU partition is consistent with this run and not demonstrated by it. The documented run used sixteen connections.

**Corrections this run forced**, in `docs/ndif-reproducibility.md` and `[E-007]` in decisions.md: the batch-composition claim narrowed to derived ratios; the arithmetic-site figure gated on the median rather than the per-item maximum, which is sample-dependent (6.31e-05 here against 2.98e-03 over the original 42 probes).
