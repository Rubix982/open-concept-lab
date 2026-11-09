# E-016 · Does a subject's prominence predict how hard an edit hits?

_2026-11-09 · 41 subjects, 495 probes, Llama-3.1-8B layer 5 · offline but for one cached Wikidata fetch · closes C-008 on branch 3_

## Why this and not more geometry

Seven candidates had been eliminated against a pre-registered floor and the published page says the absence *"is now evidence of having looked."* **Every one of them was a property of the activation geometry.** This is the first test of a property of the **subject**, and [R-003] established the same day that the nearest prior work ran neither arm of it.

Damage is the per-subject **median `excess`** — real movement minus same-subject control movement — because [E-002] measured generic subject-keyed instability at 65× the content effect, so raw movement would report the control's job rather than the subject's.

## The result: neither predictor moves

| relationship | ρ | 95% CI | excludes 0 |
| --- | ---: | --- | :---: |
| prominence vs damage | **+0.005** | −0.315, +0.314 | no |
| dependent count vs damage | **−0.053** | −0.366, +0.270 | no |
| total statements vs damage | −0.055 | −0.370, +0.259 | no |
| headroom (`p_base`) vs damage | −0.130 | −0.399, +0.171 | no |
| prominence \| dependent count | +0.059 | −0.228, +0.336 | no |
| dependent count \| prominence | −0.079 | −0.355, +0.211 | no |
| prominence \| dependent count, headroom | +0.038 | −0.266, +0.327 | no |
| dependent count \| prominence, headroom | −0.047 | −0.340, +0.264 | no |

Eight relationships, every interval spanning zero, every point estimate within 0.13 of it. **All eight are reported because six were computed and reporting one would be a cherry-pick.**

## The three confound controls, all reported

**Prominence and dependent count are correlated but not collinear**, ρ = **0.701** — below the 0.8 line the ticket set in advance, so the partial coefficients above are reportable rather than unstable.

**Headroom does not rescue either predictor.** A better-known subject has a higher pre-edit probability and more room to fall, so a prominence effect could be a headroom effect under another name. Controlling for median `p_base` moves prominence from +0.059 to +0.038. There was nothing there to explain away.

**Family composition does not carry it.** The six probe families are unevenly represented per subject. Recomputed over the four families every subject has — exposure, position, repetition, semantics — prominence reads **+0.015** and dependent count **−0.039**. The picture is unchanged.

## What this does and does not say

**It is no evidence of an effect, not evidence of no effect.** At n = 41 the widest interval runs −0.366 to +0.270, so what this run excludes is a monotone relationship of roughly **|ρ| > 0.37**. A real effect of 0.2 would sit comfortably inside every interval here and this study would not have seen it. Anyone reading a null off this table should read that sentence with it.

**The working heuristic is neither confirmed nor refuted.** *Edit facts with few dependents* survives as advice with no measurement behind it. What has been removed is the easiest way it could have been right.

**Prominence here is a proxy.** The falsifier in `edit-slice/threads.md` asks for **corpus frequency** of the subject string. Wikipedia language-edition count is the closest thing obtainable without a corpus, and it is a measure of an entity's documentation rather than of how often its name appears in text. Its range is real — 0 for a subject with no Wikipedia article at all, 67 for the most covered — so it is not a degenerate variable, but it is not the quantity the thread named.

**Scope.** 41 of 42 subjects; `Joey BadA$$` does not resolve by label against the cached snapshot and is excluded by name rather than silently. One relation family, one model, one layer. Each subject's label maps to exactly one QID in the snapshot, checked, so the predictors are not noisy from entity confusion.

**Half a gate.** The ticket asked the run to reproduce [E-002]'s paired medians, +0.0583 for identity against +0.0009 for content. The content figure reproduces exactly: median `excess` over all 495 probes is **0.0009**. The identity figure is a different contrast that this run does not recompute, so only one of the two numbers was actually checked — recorded because a gate that checks half of what it claims to check is the fault this project has already paid for three times.

## What it changes

The published sentence *"the absence is now evidence of having looked"* is strengthened and should be made specific: **two classes of variable have now been searched — the geometry of the key, and the identity of the subject — and neither carries the magnitude.** That is a better sentence than the one on the page, because a reader can tell what was not searched.
