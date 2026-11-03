# [E-008] The conformance suite across three models — 2026-11-03

36 remote traces. Layer 5. Suite unchanged between models; only `--model` differs.

```
check                Llama-3.1-8B   Llama-3.1-70B     GPT-J-6B
served dtype             bfloat16        bfloat16      float32
d_mlp                       14336           28672        16384

ratio_in_trace          0.000e+00       0.000e+00    0.000e+00   structure
batch_rows (ratio)      0.000e+00       0.000e+00    0.000e+00   structure
pad_content             0.000e+00       0.000e+00    0.000e+00   structure
trace_source       WithBlockNotFound  (same)          (same)     structure

cached_reference        7.299e-03       6.211e-03    7.353e-03   magnitude
batch_width (raw)       4.297e-02       1.953e-03    5.292e-02   magnitude
   as % of magnitude        2.59%           0.91%        0.92%
matmul_site (median)    5.319e-06       4.969e-07    7.451e-09   magnitude
```

Everything carrying a reference matched on every model, after the arithmetic-site reference was made per-model.

**Three things this run established.**

1. **The structure generalises across architectures.** GPT-J is not a Llama and behaves identically on every structural check.
2. **No magnitude generalises.** The arithmetic-site median spans three orders of magnitude. The 5.06e-06 this project had been quoting is a Llama-3.1-8B fact.
3. **The batch-shape effect is not bfloat16 and not a masking fault.** GPT-J is served in **float32** and shows it at the same relative size as the 70B; and filling the pad region with a different token leaves the keys bit-identical, so nothing is reading the padding.

**Not reproduced.** The GPU partition: four connections per model, each landing on one device.
