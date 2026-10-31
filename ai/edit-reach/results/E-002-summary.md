# [E-002] The different-subject arm

_2026-10-31 · Llama-3.1-8B · layer 5 · 495 probes · 42 subjects · seed 1538_

## The question

[E-001] edited two properties of the same person and could not tell whether a probe moves because of **what the edit said** or because of **whose key it touched** — both arms touched the same key. This adds the arm that separates them: subject B's cached edit applied while probing subject A, with B chosen as the nearest edit magnitude to A's.

## The answer

```
real  -  same-subject      +0.0009   95% CI (+0.0004, +0.0024)
same-subject - diff-subj   +0.0583   95% CI (+0.0472, +0.0732)
real  -  diff-subject      +0.0842   95% CI (+0.0667, +0.0974)
```

Paired median differences, bootstrap 10,000. **Changing whose key the edit touches is worth about 65 times more than changing what the edit says.** Both intervals exclude zero, so content is not irrelevant — it is detectable and small.

```
median movement by arm
family             real   same-subj   diff-subj
ALL              0.0977      0.0625      0.0016
alias            0.0065      0.0020      0.0001
discrimination   0.0223      0.0114      0.0067
exposure         0.0489      0.0217     -0.0005
position         0.0900      0.0659      0.0037
repetition       0.3373      0.2656     -0.0076
semantics        0.1795      0.1767      0.0070
```

Donor edits were magnitude-matched: median |difference| 0.0255 over a range of 2.627. The different-subject arm is not merely weaker.

## A statistic that nearly misled

The per-arm medians above make `real` look 56% above the same-subject control (0.0977 vs 0.0625). That is a difference **of medians** over skewed distributions. The arms share their probes, so the paired median **of differences** is the right estimator, and it is **+0.0009** — about sixtyfold smaller. For a paired design, report paired quantities.

## What it settles

A probe moves because an edit happened to its subject, almost regardless of what the edit said. **Direct exposure is demonstrable in behaviour, not only by counting prompt strings** — which is what `notes/email-3-direct-exposure.md` previously had to rest on alone.

[E-001] stands: the coefficient still fails to predict a particular edit's effect, and now has a reason — there is very little specific effect to predict.
