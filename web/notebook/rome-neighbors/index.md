---
title: rome-neighbors
sidebar_label: rome-neighbors
sidebar_position: 1
description: Does structured representational geometry predict whether a knowledge edit propagates to logically entailed neighbours?
---

# rome-neighbors

**Does structured representational geometry predict whether a knowledge edit
propagates to logically entailed neighbours?**

Raw representational *distance* does not. Measured across neighbour types it
comes out near-flat, around $0.6$, which is close enough to uninformative that
distance alone cannot be the predictor. The question this project asks is
whether *structured* geometry and *alignment* do better, resolved by entailment
hop and measured causally rather than behaviourally.

<Claim
  label="What is being tested"
  record={{
    Predictors: "Bilinear structure (Kim), alignment (Jeong / STEAM)",
    Metric: "Interchange intervention accuracy — causal, not behavioural",
    Resolution: "Per entailment hop, not pooled",
    Status: <Status kind="provisional">Experiments running</Status>,
  }}
>
  The first hop-resolved comparison of causal predictors for edit propagation on
  a decoder-only language model.
</Claim>

## Why hop resolution matters

Pooling hops hides the effect. A predictor can look useless averaged over
neighbours at every distance and still be sharp at one hop and absent at three —
and it is the shape of that decay, not its average, that says where an edit's
influence actually stops.

$$
\text{IIA}(h) = \frac{1}{|N_h|}\sum_{n \in N_h}
  \mathbb{1}\!\left[\, f_{\text{patched}}(n) = y_{\text{source}}(n) \,\right]
$$

Reporting $\text{IIA}$ as a function of hop $h$ gives a curve. Reporting it
pooled gives a number that can be right and say nothing.

## Layout

The library is the source of truth; experiments are thin runners over it.

```
ripplekit/     config, data, reps, predictors, analysis
experiments/   one reproducible runner per ticket
readings/      the vetted literature map
agents/        tickets and shared surfaces
```

## Threats being tracked

- **Confound** — neighbour types differ in token frequency as well as hop, so
  frequency has to be controlled before hop can be read as hop.
- **Baseline** — the dumbest explanation is raw distance. Any structured
  predictor has to beat it on the same edits, not on a friendlier set.
- **Construct validity** — behavioural accuracy after an edit is not the same as
  the edit having propagated. That is why the metric is interventional.
- **Localisation is not editability** <Cite id="hase2023localization" /> — the
  first objection a reviewer raises here, so the design answers it rather than
  waiting to be asked.

<References ids={["cohen2024ripple", "zhong2023mquake", "hase2023localization", "todd2024functionvectors", "fiottokaufman2025nnsight", "kim2025bilinear", "jeong2025steam"]} />
