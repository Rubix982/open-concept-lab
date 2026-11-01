# [E-005] The loaders are the same instrument. The serving session is not.

_2026-11-01 · Llama-3.1-8B · layer 5 · nnsight 0.8.1 · 42 anchor-prefix + 42 anchor-floor probes · 3 readings per loader_

## The question

nnsight 0.8.1 deprecates `LanguageModel` in favour of `TransformersModel`. Every number in this repo and in edit-slice came through the deprecated one, as did every cached tensor on disk. So the question was whether switching is an **upgrade** or a **re-baseline**.

## The answer

Module paths are identical — `llama`, 32 layers, `d_mlp` 14336, the same `Envoy` at `model.layers[5].mlp.down_proj`. `arch.py` needs no second mapping.

```
comparison                   pairs   worst |d|   max fraction of elements differing
WITHIN  language                 3   6.250e-01        0.9394
WITHIN  transformers             3   0.000e+00        0.0000
BETWEEN the two loaders          9   6.250e-01        0.9394
```

**Two readings taken through the same loader differ as much as two taken through different ones.** So the loader is not the variable, and the two are the same instrument at the reproducibility this platform offers.

The gates hold under both, across all six readings: the 42 analytic anchors pin at exactly **1.000** every time (worst deviation 0.000e+00), and the floor median lands within 2e-4 of [E-001]'s 0.0809.

## What the design had to change, and why that is the finding

The card pre-stated branch 1 as *"module paths match and activations are bit-identical"*, measured with `torch.equal`. **That criterion is unsatisfiable on this platform**, and it is recorded as a design error rather than quietly relaxed to `allclose` — which is precisely the move the dry-run was written to forbid.

What the first comparison actually found was two readings differing on 94% of elements with only 6% of them inside one bf16 ulp of their own value. Attributing that to the loader was tempting and wrong. Varying the loader *on its own* — several readings each — showed the same spread inside one loader.

This is the same control shape as [E-004]'s relation split, for the same reason: **a difference is attributable only once the thing it is being attributed to has been varied by itself.** Both cards would have published the opposite conclusion without that step, and in both the confound was found by asking what else varies, not by anything in the measurement.

## The thing that does vary, which is bigger than the question asked

Readings differ **between NDIF serving sessions**, on byte-identical inputs:

- 93.94% of elements differ, by up to 6.250e-01 at `lm_head` and 3.125e-02 at the layer-5 key site, against a median |key| of 1.135e-02.
- Only about 6% of differing elements sit within one bf16 ulp of their own value, so this is not rounding on the wire.
- Within a session it is **deterministic**: repeated reads agree bit-for-bit.
- The grouping follows contiguous runs of connections rather than the loader, which is consistent with routing to one of several replicas.

**Impact on recorded numbers is small but not zero.** Derived scalars barely move, because the quantities we report are ratios read inside a single trace:

```
anchor coefficients   1.000 exactly, all 6 readings, both loaders
floor median          language      0.080942 / 0.081093 / 0.081093
                      transformers  0.081093 / 0.081093 / 0.081093
                      [E-001] published 0.0809
```

[E-001]'s published 0.0809 is the **first-connection** value; later connections give 0.081093. The spread is 1.5e-4 on a quantity we quote to four decimals, so nothing published is wrong — but it is luck rather than design that it is not.

Logged as **T-008**.

## What was decided

The loaders are interchangeable, so the switch is safe. **It is not taken in this ticket.** Changing the loader every number was read through, on the same day the instrument was found to vary between sessions, would mean two changes at once with one of them unmeasured. `connect(loader=...)` stays switchable with `"language"` as the default, and the switch is a one-line change whenever it is wanted.

## Limits

- Two surfaces were compared: the edit layer's key site and `lm_head.output`. Generation, `score_pairs` teacher forcing and other layers were not.
- One model, one layer, 84 prompts, three readings per loader. Three readings are enough to show that within-loader spread exists; they do not estimate how often it occurs.
- Why sessions differ is **not established** here. The replica hypothesis fits the grouping and is not tested.
