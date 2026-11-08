# Paper skeleton — [D-004]

_Written 2026-11-08. Structure, figure slots, tables and every number. **The prose is [D-005] and is deliberately not here.**_

Format is not decided yet. This file is format-agnostic on purpose: [D-006] chooses LaTeX or Typst and that choice should not be made by whatever was convenient to write in today. One input to it, found while drawing the figures — **every figure here is an SVG, Typst includes SVG natively and LaTeX does not.** With LaTeX each figure needs a conversion step and something has to own it.

Every number below carries the ticket it came from. A number that cannot be traced to `agents/shared/decisions.md` or `results/` does not go in. Where a claim is analytic it is marked `[A]` and ships its derivation; `[A]` claims are not refuted by observation, so the falsifier given is the **premise's**.

---

## Working title

_Placeholder:_ **A cheap pre-edit estimate of an edit's reach detects contamination, not propagation**

The title has to carry the negative. A title that says what the measure does, without saying where it stops, is the overclaim this whole document exists to avoid.

## Abstract

Five sentences, in this order. No sentence may be added before these five exist.

1. The proposal: ROME's update is rank-one, so the fraction of it arriving at any token is computable in one forward pass through the unedited model, with no edit applied and no item set written in advance.
2. It is exact where the prompt names the edited subject — 1.000, and that is a derivation, not a fit.
3. It is blind where propagation lives: in the far field a stranger's edit on the same relation reaches a question as much as the real subject's does, excess +0.0002.
4. So the measure is a contamination detector. It says that a benchmark item names the edited subject; it does not say an edit travelled.
5. That distinction is testable on published benchmarks today, and one of them fails it.

---

## 1 · The proposal, and why it is attractive

**Claim.** A benchmark gives a lower bound on an edit's damage and never an upper bound: an absent item and an absent failure are indistinguishable. Writing a bigger item set does not fix this, because a hand-written set measures the limits of whoever wrote it.

**The move.** Replace enumeration with measurement. A quantity defined for *any* prompt lets an item be scored without having been anticipated.

**What this buys and does not.** It removes the need to **foresee** which items matter. It does not remove the need to **have** items — the quantity is still evaluated on prompts we happen to hold. State this in §1, not in the limits, because a reader who meets it late will feel it was withheld.

**Falsifier.** If a published ripple benchmark reports, with its item set, an upper bound on unmeasured damage, the framing in this section is wrong.

## 2 · Related work, and what is not claimed

- **He et al., arXiv 2601.04600** — the nearest work. It has the depth phenomenon (§4.4) and the cosine decay (§4.3): 0.80 at layer 5 down to 0.50 at 25, against this project's 0.98 to 0.47. Eight months earlier. `TODO(cite)` — verify authors, venue and section numbers against the paper itself, not a search snippet.
- **Cohen et al., TACL 2024 (RippleEdits)** — the benchmark §6 scores. Read the test-type definitions directly.
- **MQuAKE** — `TODO(cite)`.
- ROME and MEMIT — `TODO(cite)`.

**The positioning sentence, which must appear verbatim somewhere in §2:** the mechanism in §3 is a line of algebra, and the claim here is **not** that it is unpublished — only that it could not be found stated, on one web-search pass and one neighbouring paper read in full. That is enough to ask the question and not enough to assert the answer.

**Falsifier.** A paper stating the pinned coefficient makes §3 a replication and moves the contribution to §6 and §7.

## 3 · Method

**3.1 The coefficient.** ROME rewrites one MLP output projection:

    W' = W + (v* − W k*) uᵀ / (uᵀ k*)

For a token whose key at that layer is `k`, the fraction of the update landing on it is

    c = (k · u) / (u · k*)

computable in one forward pass through the **unedited** model.

**3.2 Two regimes.** `[A]` Under causal attention, a prompt sharing the edit prompt's prefix up to the subject's last token has an identical key there, so `c = 1` — for any `u`, any covariance, at any layer, whatever relation the prompt goes on to ask. Derivation goes in the body, not an appendix; it is four lines.

> **Premise, which is the empirical part:** the prompts actually share that prefix. That is what [E-017] and [E-018] measured, and it is what a reader should attack.

**3.3 The control is part of the measurement.** A coefficient of 1.000 means nothing on its own, because a pipeline hardwired to return 1 produces exactly the same reading. The different-subject floor is what makes 1.000 a claim. In the implementation a reading without a baseline does not type-check (`Unbaselined`). Keep this in the method, not in a software appendix — it is why the numbers can be believed.

**FIGURE 1** → `two-regimes.svg`. Why one number is exact and the other is not.

## 4 · The near field: exact, and exact for an uninteresting reason

| | value | source |
| --- | --- | --- |
| prompt begins with the edited subject | **1.000**, worst deviation 0.0e+00 | [E-032] |
| models it held across | four, 6B → 405B | [E-032] |
| prompt names a different person | **0.082** mean, 0.081 median, 16 chains | [E-018] |
| overlap between the two groups | none — highest different-subject 0.153 < lowest same-subject 0.483, gap 0.877 | [E-018] |
| independent replication of the floor | 0.0809 against 0.082 | [E-001] |
| the edited subject after a preamble | 0.93 (L5), 0.79 (L12), 0.52 (L24) | edit-slice |

**The sentence this section exists for.** A probe moving after an edit is not evidence the model reasoned.

**Falsifier.** A prefix-sharing prompt whose coefficient is not 1.000, with the pipeline's anchor gate passing.

## 5 · What one update actually does

Two effects of one rank-one edit, separated on one probe set under one readout — 495 probes, 42 subjects, three arms, paired, bootstrap 10,000, seed 1538.

| | real − ctl | ctl − other | source |
| --- | --- | --- | --- |
| **destination** (where the new answer goes) | **+0.2828** (+0.2424, +0.3232) | +0.0000 (−0.0101, +0.0101) | [E-003] |
| **destruction** (what the old answer loses) | +0.0009 (+0.0004, +0.0024) | **+0.0583** (+0.0472, +0.0732) | [E-003], [E-002] |

The two halves separate in **opposite directions on the same probes**. Discordant pairs for destination, real against ctl: 142 to 2.

**So:** changing *whose* key the edit touches is worth about **65×** changing *what the edit says* — and that is destruction. Destination is the other way round, and is content-specific.

**Stated against ourselves:** this is "content that *can* answer the question is what arrives", not "every edit delivers its own content somewhere". The control injects an occupation and these probes ask for a city, so no arm-symmetric check exists here.

**Falsifier.** A readout that can express the control's own content, showing it delivering there.

## 6 · The far field: the measure is blind where propagation lives

**This is the section the paper is for.** MQuAKE-CF-3k, 513 single-edit two-hop instances, no edit applied, every hop-2 question scored against all 512 other instances' `k*`. [E-004].

**FIGURE 2** → `near-and-far-field.svg`. Goes **before** the table.

| | own `k*` | same-relation stranger | excess | 95% CI | n |
| --- | --- | --- | --- | --- | --- |
| **far field** — the question never names the subject | 0.0543 | 0.0481 | **+0.0002** | (+0.0001, +0.0004) | 900 |
| **near field** — it names it | 0.9334 | 0.0506 | **+0.8439** | (+0.8379, +0.8500) | 639 |

**6.1 The first floor gave the opposite answer, and that belongs in the body.** Against *all* donors the far-field excess is +0.0232 with an interval excluding zero — which reads as real far-field signal. Nearly all donors carry a different relation, so that floor was the different-relation floor under another name. It was found by asking what else a hop-2 subject is — the chain's middle entity, which the question is about indirectly — and not by anything in the measurement.

A reviewer will ask how many other floors in this literature are the wrong floor. The honest answer is that we do not know, and the method §3.3 describes is what would tell them.

**6.2 What the measure does detect, stated precisely.** That a prompt names the edited subject, and which relation it asks about.

**FIGURE 3** → `direct-exposure.svg`.

| | value | source |
| --- | --- | --- |
| RippleEdits Compositionality_I, median coefficient | **0.982** | [E-036] |
| stranger floor on those same prompts | **0.065** | [E-037] |
| the floor across all criteria, for comparison | 0.070, IQR under 0.05, n > 4,000 | [E-037], [E-038] |
| MQuAKE names the subject, edit on hop 1 | 6,861 / 6,861 | [R-014] |
| MQuAKE names the subject, later hops | 0 / 16,506 | [R-014] |

**The consequence, stated without inflation:** an editor could score on that RippleEdits test while generalising nothing. It is not an indictment of multi-hop evaluation — MQuAKE shows the problem is avoidable, in the field's own data, by construction rather than by design.

**Falsifier.** A layer sweep finding far-field dynamic range at a depth other than 5 — which would not rescue layer 5, where ROME and EasyEdit edit.

## 7 · Whether a remote reading can be trusted at all

Half the tickets. A result that cannot be read twice is not a result, and on shared inference infrastructure that is not automatic.

**FIGURE 4** → `same-number-twice.svg`.

| | value | source |
| --- | --- | --- |
| ratio with both terms inside one trace | **0.000e+00**, all 15 layer-model pairs | [E-007]–[E-011] |
| coverage | 3 models, 2 architectures, depths 0–79 | [E-008], [E-011] |
| same quantity, one term from an earlier session | worst deviation 6.382e-03, 25 of 42 outside a 1e-3 band | [E-007] |
| two arithmetic sites, median, Llama-3.1-8B | 5.3e-06 | [E-008] |
| the same, GPT-J-6B, served float32 | 7.5e-09 | [E-008] |
| serving GPUs, 16 fresh connections, 2026-11-01 | perfect partition, 3.11e-06 across | [E-006], [E-009] |
| the same, two days later | one GPU, no partition | [E-009] |
| the "drift" of 2.16e-04 | four exact replica values, within-device spread 0.000e+00 | [E-012] |

**The sentence:** what varies is the **deployment** — dtype, sharding, tensor shape — and not the model family. Two models of one family disagree; GPT-J differs because NDIF serves it in float32. **So a gate with a tolerance written into it is wrong somewhere else**, and the tolerance has to be measured on the deployment being run.

**A claim withdrawn mid-project, left in.** [E-010] saw the arithmetic-site effect rise monotonically on the 8B and wrote "grows with depth in bfloat16". [E-011] found the 70B falls 53-fold to layer 20 and then rises 298-fold to layer 40. The direction was one model's artefact. What survives: two to three orders of magnitude of variation in bfloat16 with no predictable direction, and none in float32.

**Falsifier.** A derived ratio read with both terms in one trace that is not 0.000e+00.

## 8 · Limits

All qualification lives here; §§1–7 run unhedged.

**FIGURE 5** → `delivery-is-not-effect.svg`.

1. **Delivery is not effect.** Every number is how much of the update arrives at a token. At a fixed coefficient, measured movement spans ×2.96 ([E-028d]).
2. **The coefficient belongs to a token, not a prompt.** Within one prompt, subject and final positions differ by 35×, and the answer is produced at the final position.
3. **The far-field result is one model, one layer, two-hop chains.**
4. **The 42 subjects are not a sample.** They are the cached survivors of a blocked path — [E-047] refuses remote `v*` on nnsight 0.8.1 — so no magnitude generalises past that set.
5. **Hand-built and mined sets license existence, never rate.**
6. **Magnitude matching is one scalar**, `‖Δv‖/‖k*‖`. Two edits of equal norm can differ in direction relative to the probe's key. A directional control is the obvious refinement and is not run.
7. **Nothing here was reviewed outside the project** until this document. The self-correction record is evidence the process works, not evidence the conclusions are right.
8. **How this may not be used.** The scope statement is a finding about a measure. It is not a method being offered, and no threshold on the coefficient is proposed, because setting one needs the delivery-to-effect link that §8.1 says is missing.

## 9 · What this is, plainly

A negative result with a working control.

The thing that makes it worth writing is not the denial — it is that the control separates +0.8439 from +0.0002 on the same instrument, so the denial is a measurement rather than a failure to find something. The positive direction is blocked on [E-047], and is named here so that nobody has to guess whether it was tried.

---

## What still has to be decided before [D-005] starts

1. **Venue, or none.** A workshop note and an arXiv-only report want different lengths and different amounts of §7.
2. **Whether §7 stays in.** It is half the tickets and none of the central claim. It may be an appendix, or its own short note — the reproducibility reference it comes from is already written and stands alone.
3. **Format**, per the note at the top: the SVG figures argue for Typst.
