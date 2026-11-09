# E-015 · How loose is the upper bound on an edit's reach?

_2026-11-09 · Llama-3.1-8B, layer 5 · 513 instances, 1,539 question-positions · offline over `results/cache/E004_keys.pt`, no NDIF · closes C-007 on branch 2_

## The bound

ROME adds `δ · c(k)` at the edited layer. `δ = v* − Wk*` is **fixed**; only the scalar

```
c(k) = (k* · k) / (k* · k*)
```

varies with the token. So `c` is the projection coefficient of `k` onto `k*`, and Cauchy–Schwarz bounds it for **every** prompt — no enumeration, no forward pass through the edited model:

```
|c(k)| ≤ ‖k‖ / ‖k*‖,   equality exactly when k ∥ k*
```

`C = I` throughout this project, so the norms are Euclidean. This part is analytic: it is refuted by an error in those three lines, or by the update ceasing to be rank-one with a fixed direction. No measurement refutes it.

## What was measured

Whether the bound is *informative*, which is a separate and empirical question. Looseness is `bound/|c|`. A bound never approached forbids nothing.

| regime | n | median &#124;c&#124; | median bound | median looseness | 95% CI | IQR | max |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| near field — the question names the edited subject, read at its last token | 639 | 0.9334 | 0.9881 | **1.05** | 1.05–1.06 | 1.04–1.09 | 10.6 |
| far field — the question never names it, read at the final token | 900 | 0.0544 | 1.1456 | **21.12** | 20.16–22.14 | 16.11–32.75 | 1715.3 |

Gate: 16 hop-2 coefficients recomputed from the cache against the published `E-004` values, worst deviation **2.390e-08**. All 1,539 items satisfy `|c| ≤ bound`. None dropped for a near-zero denominator.

## The result

**A universal upper bound on an edit's reach exists, costs one line, and forbids nothing that happens.**

The number that carries it is the far field's **median bound of 1.1456** against a median coefficient of **0.0544**. The bound permits a question that never names the edited subject to receive *more* than the near field actually receives. It therefore cannot distinguish a far-field question from the edited subject itself.

**The near field's 1.05 is not a second finding.** There `k ≈ k*`, which is the same prefix-sharing that pins the anchor coefficient at exactly 1.000, so Cauchy–Schwarz is near-equality by construction. It is reported because it confirms the implementation, not because it is news. Reading it as a positive result would be reporting the anchor a second time under a new name.

## A prediction that was right for the wrong reason

The dry-run that produced this card predicted the far-field bound would read ≈ 1 and forbid nothing. It reads 1.15 and forbids nothing. But the reason given was `E[‖k‖²_{C⁻¹}] = tr(C⁻¹C) = d`, which assumes `C` is the second moment of keys. `C = I` here, so that argument does not apply. The observed ≈ 1 comes from keys having comparable Euclidean norms — a different fact. The number generalises no further than this setting, because the derivation that would have carried it elsewhere was wrong.

## Limits

**Nothing here is about behaviour.** The bound is on the perturbation at one layer. Crossing to logits needs a Lipschitz constant for the rest of the network, which is unread (T-011).

**One model, one layer, one covariance.** `C = I`. The bound's form is unchanged under whitening but `‖k‖_{C⁻¹}` is a different quantity, and whitening is precisely the operation that could shrink the far-field bound.

**This is not a method.** It says what the quantity already in use cannot do; it does not propose a replacement.
