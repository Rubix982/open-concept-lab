# [E-010] The conformance suite across depth — 2026-11-03

90 remote traces. Five layers on each of two models, six checks each.

```
Llama-3.1-8B (bfloat16)   L0        L5       L12       L24       L31
ratio_in_trace       0.00e+00  0.00e+00  0.00e+00  0.00e+00  0.00e+00
batch_rows (ratio)   0.00e+00  0.00e+00  0.00e+00  0.00e+00  0.00e+00
pad_content          0.00e+00  0.00e+00  0.00e+00  0.00e+00  0.00e+00
cached_reference     7.25e-03  7.30e-03  7.63e-03  7.58e-03  7.63e-03
batch_width abs      3.91e-03  4.30e-02  1.95e-02  4.69e-02  2.66e-01
  key magnitude          0.75      1.66      1.06      3.41     19.75
  AS % OF MAGNITUDE     0.52%     2.59%     1.84%     1.38%     1.34%
matmul_site          8.41e-07  5.32e-06  1.63e-05  2.66e-05  3.68e-05

GPT-J-6B (float32)        L0        L5       L12       L20       L27
batch_width % of mag     0.00%     0.92%     1.32%     1.27%     0.91%
matmul_site          1.49e-08  7.45e-09  7.45e-09  1.86e-09  7.45e-09
```

**Structure is depth-independent.** All three structural checks read exactly 0.000e+00 at all ten layer-model pairs.

**The shape effect does not grow with depth.** Its absolute size rises 68-fold over 31 layers; key magnitude rises 26-fold underneath it. Relative, it is flat and under 3% everywhere, on both architectures. Reporting the absolute figure alone would have supported "it gets much worse deep", which is false.

**The arithmetic-site effect does grow with depth, and only in bfloat16.** 44-fold over 31 layers on the 8B; flat at float32 epsilon on GPT-J across five layers. Accumulation, not depth.

**Unplanned consistency check.** On GPT-J, `cached_reference` is 0.000e+00 at exactly the layers where `batch_width` is. Caching costs nothing where shape costs nothing — the same effect seen twice. Nothing enforces this.

**Not swept.** `Llama-3.1-70B`, at any layer but 5. It has 80.
