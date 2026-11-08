# Paper skeleton — [D-004]

_Written 2026-11-08. Structure, figure slots, tables and every number. **The prose is [D-005] and is deliberately not here.**_

## Shape — decided 2026-11-08

**A short note on arXiv, four to six pages.** Not a workshop submission: no venue is being targeted, so nothing here is shaped by a deadline or a page limit someone else set.

**Written for a general mechanistic-interpretability reader** — someone who knows transformers and does not know the editing benchmarks.

Those two choices pull against each other, and the pull is the main constraint on [D-005]. A reader who needs the benchmarks explained, in a document with no room to explain them, is how a short note becomes a long one. Three rules settle it, and a draft that breaks one of them has gone wrong:

1. **No benchmark primer.** §1 states the problem in terms the reader already holds — *you cannot measure what an edit did not break* — and names no benchmark. RippleEdits and MQuAKE first appear in §6, where they do work.
2. **Each benchmark is introduced in the sentence that uses it**, in one clause, never in a paragraph of its own.
3. **Figure 1 carries §3's explanation.** The derivation is four lines of algebra under a picture, not a page of prose building up to it. If §3's prose would still make sense with the figure removed, too much of it has been written.

Section budgets, in single-column page fractions. These are a check on the draft, not a target to fill:

| § | | budget |
| --- | --- | --- |
| 1 | The proposal | 0.5 |
| 2 | Related work | 0.3 |
| 3 | Method, with Figure 1 | 0.6 |
| 4 | The near field | 0.3 |
| 5 | Destruction and destination | 0.3 |
| 6 | **The far field — the denial**, with Figures 2 and 3 | 1.4 |
| 7 | Reproducibility | 0.2 + a pointer |
| 8 | Limits | 0.4 |
| 9 | What this is | 0.15 |

§6 gets more than §§1–5 together. That is the point of the document.

**§7 shrinks to a paragraph and a pointer.** It is half the tickets and none of the central claim, and the reference it comes from is already written and stands on its own. The paragraph says what a reader must know to believe §§4–6 — that a ratio read inside one trace is exact, and that no magnitude is portable — and sends them to the repository for the rest.

**Figures 4 and 5 come out.** `same-number-twice.svg` goes with §7 to the notebook page; `delivery-is-not-effect.svg` is replaced in §8 by one sentence, because a limit does not need a picture in a four-page note. Both stay on the web page, where there is room.

---

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

**One paragraph and a pointer.** Budget 0.2 of a page. The reader needs exactly two facts to believe §§4–6, and the rest belongs in the reference, which is already written.

**Fact one, which licenses every number above.** A ratio whose two terms are read inside a single trace came back at **0.000e+00** — three models, two architectures, depths 0 to 79, all fifteen layer-model pairs. Every coefficient in this note is such a ratio. [E-007]–[E-011].

**Fact two, which stops a reader generalising the magnitudes.** Nothing else is portable. The disagreement between two arithmetic sites reads 5.3e-06 on Llama-3.1-8B and 7.5e-09 on GPT-J, which NDIF serves in float32 rather than bfloat16; readings partitioned perfectly by serving GPU on one day and not at all two days later. What varies is the **deployment** — dtype, sharding, tensor shape — not the model family. A tolerance written into a gate is therefore wrong somewhere else, and has to be measured where it runs.

**Then the pointer**, with a sentence on what is there: the full reference, the conformance suite, and the four corrections the suite forced on the reference. Also, in one clause, that [E-010]'s "grows with depth" was withdrawn by [E-011] — because a reader who later finds that in the repository should find it acknowledged here first, not discovered.

**Falsifier.** A derived ratio read with both terms in one trace that is not 0.000e+00.

## 8 · Limits

All qualification lives here; §§1–7 run unhedged.

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

## What still has to be decided

Shape and reader were settled on 2026-11-08 and are at the top of this file. One thing is left, and it does not block [D-005]:

**Format.** Typst or LaTeX. Every figure is an SVG, which Typst includes natively and LaTeX does not. Either way this machine has no toolchain, which is [D-006] and is Saif's call.
