# [E-001] Predicted reach against measured movement

_2026-10-31 · Llama-3.1-8B · layer 5 · 495 probes over 42 subjects · seed 1538_

Raw output is `E-001-predicted-vs-measured.json` (gitignored). This is the part that has to survive it.

## The number C-001 turned on

```
overall, raw      rho = 0.522   95% CI (0.450, 0.587)
overall, excess   rho = 0.085   95% CI (-0.003, 0.172)
```

`excess` is movement beyond what a **different edit on the same person** produces. The bar was 0.5, written before the run. **Denied.**

## Per family

```
family            n   coef med   move med    ctl med   excess med
alias            80      0.121      0.007      0.002        0.001
discrimination   37      0.096      0.022      0.011        0.003
exposure         42      0.958      0.049      0.022        0.031
position        210      0.958      0.090      0.066        0.001
repetition       84      0.981      0.337      0.266        0.000
semantics        42      0.980      0.180      0.177        0.000
```

The same-subject control accounts for about **72%** of the median movement (|movement| 0.1034, |control| 0.0740). What the coefficient tracks is that a probe is sensitive to an edit on this subject, not that this edit reaches it.

## Two things the run confirmed on the way

**The anchor gate.** 42 probes that begin with the edited subject must read exactly 1.000, because under causal attention `k = k*` and the ratio is arithmetic. Against a cached `k*` in bf16: worst deviation **6.382e-03**, 25 of 42 outside the band. With `k*` read in the same trace and the dot product in float32: **0.000e+00**. Both faults were mine; see [E-001] in `agents/shared/decisions.md`.

**An independent replication.** `anchor-floor` — same prompt shape, different person — returned a median coefficient of **0.0809** against [E-018]'s separately measured floor of **0.082**.

## What this does not touch

The direct-exposure critique of RippleEdits rests on counting whether the edited subject appears in a prompt, and on MQuAKE's 6,861/6,861 against 0/16,506. That is arithmetic over prompt strings. It needs no coefficient and is unaffected.
