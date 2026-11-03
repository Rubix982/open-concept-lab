# [E-011] Llama-3.1-70B across depth — 2026-11-03

45 remote traces, layers 0, 5, 20, 40, 79 of 80.

```
check                      L0        L5       L20       L40       L79
ratio_in_trace       0.000e+00 0.000e+00 0.000e+00 0.000e+00 0.000e+00
batch_rows (ratio)   0.000e+00 0.000e+00 0.000e+00 0.000e+00 0.000e+00
pad_content          0.000e+00 0.000e+00 0.000e+00 0.000e+00 0.000e+00
cached_reference     4.444e-03 6.211e-03 5.025e-03 6.289e-03 5.405e-03
batch_width abs      2.441e-04 1.953e-03 7.812e-03 1.172e-02 1.094e-01
  key magnitude          0.063     0.215     0.957     1.094     7.094
  AS % OF MAGNITUDE      0.38%     0.91%     0.82%     1.07%     1.54%
matmul_site          4.839e-06 4.969e-07 9.127e-08 2.719e-05 1.654e-05
```

**Structure: fifteen layer-model pairs, every one exactly zero.** Two architectures, three model sizes, depths 0 to 79.

**The batch-shape bound held on the deepest model.** 0.38%-1.54%, inside the sub-3% band. Its 448-fold absolute rise over 79 layers is fully accounted for by keys growing 113-fold — the same decomposition found on the 8B, now at 2.5x the depth.

**It refuted a claim one run old.** [E-010] saw the arithmetic-site median rise monotonically on the 8B and wrote "grows with depth in bfloat16". The 70B falls 53-fold to layer 20, then rises 298-fold to layer 40. The direction was an artefact of one model. What survives: two to three orders of magnitude of variation in bfloat16 with no predictable direction, and none in float32.

**The prediction written before the run** — "adds a row, breaks nothing" — was half wrong, and that half is the result.
