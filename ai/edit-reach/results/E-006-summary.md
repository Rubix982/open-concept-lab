# [E-006] The two values partition by GPU. The GPU explains 1.4% of the drift.

_2026-11-01 · Llama-3.1-8B · layer 5 · nnsight 0.8.1 · 126 prompts per reading · 16 fresh connections_

## The question

[E-005] found readings of the same batch differing between NDIF connections on 93.94% of elements, deterministic within a connection, with only **two** distinct values across six readings. That is the shape of routing, and routing was never tested. nnsight surfaces `tracer.backend.meta`, which carries `max_mem_by_gpu` — a GPU index.

## The answer: it is routing, and it partitions perfectly

16 readings through fresh connections, same batch, same positions:

```
value               readings   served by
edd2b2b152de2098           8   GPU 0
54a1755349e607dc           8   GPU 2

GPU 0    8 readings   1 distinct value
GPU 2    8 readings   1 distinct value
```

Clean in both directions: each value came from one GPU, each GPU returned one value. Runtimes separate too — GPU 0 around 2.56s, GPU 2 around 2.6–3.2s. The connections alternated between devices rather than arriving in blocks, so it is per-connection routing.

## The tolerance, which is the number this card owed

Two derived quantities, and they differ in the one way that matters:

- **The anchor coefficient reads `k` and `k*` in the same trace.** Whatever the device does cancels in the ratio: **0.000e+00** deviation from 1.000 on every one of the 16 readings, both devices. This is why every anchor gate in this repo has survived without anyone noticing any of this — and it is a property of the gate's design, not foresight.
- **The floor reads against a cached `k*`**, so nothing cancels. It is [E-001]'s published number.

```
floor median      within a GPU    0.000e+00
                  across GPUs     3.110e-06
```

## And the device is not the whole story

Four floor medians have now been observed for the same 42 probes:

```
[E-001]  2026-10-31          0.08087725
[E-005]  first reading       0.08094215
[E-006]  GPU 0               0.08109000
[E-006]  GPU 2               0.08109313
```

Observed range **2.16e-04**. The device accounts for 3.11e-06 of it — about **1.4%**.

Two further sources were tested and priced:

- **Batch composition: zero.** The floor probes read alone (42 rows) and inside a 126-row batch, on one connection, are bit-identical.
- **Where the arithmetic runs: 5.06e-06 at the median, 2.98e-03 per item.** `coefficient_for` takes the dot product inside the trace on the GPU; `keys_at` brings the keys back and takes it on the CPU over 14336 channels. Individual coefficients move by up to 3e-3 between the two. The median barely moves, which is luck of the statistic.

The rest — roughly 2e-04, the gap between October 31 and today — is **not attributed**. Logged as **T-009**.

## What to do with this

- **A cross-session gate needs a tolerance of at least 2.2e-04 on a quantity of this kind**, not the 3.1e-06 device spread. [E-004]'s ±0.02 reproduction gate is comfortably above it and was right for a reason it did not know.
- **No artifact should assert bit-identity across readings.** [E-005]'s pre-stated `torch.equal` was unsatisfiable for exactly this reason.
- **Prefer a ratio read inside one trace** wherever the question allows it. The anchor gate is immune to everything measured here; the floor is not.
- **Record the device.** `keys_at(..., meta_out=d)` returns it. New runs should capture it; existing results are not retrofitted, because the device is 1.4% of the drift and relabelling them would imply more precision than we have.

## Limits

- 16 readings, one model, one layer, one batch. Two devices were seen; a third is not ruled out, and a value appearing at low rate would probably be missed.
- The GPU index is what the server reports as having held memory. It is a good proxy for "which replica" and it is not a host identifier.
- The unexplained 2e-04 is a two-day gap with one observation at each end. It is a range, not an estimate of anything.
