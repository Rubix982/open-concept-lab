# A cheap pre-edit estimate of an edit's reach detects contamination, not propagation

_Draft. [D-005]. Structure and budgets are in `skeleton.md`._

---

## Abstract

A rank-one weight edit, as ROME applies it, divides its update by a fixed inner product, which means the fraction of that update arriving at any token is computable in one forward pass through the unedited model — before the edit exists, and for any prompt rather than for a list written in advance. We show this quantity is exactly 1 wherever the prompt opens with the edited subject, by a derivation rather than a fit, and confirm its premise on four models from 6B to 405B. We then show it is blind where edit propagation actually lives: for questions that never name the edited subject, an edit on a *stranger* sharing the question's relation reaches it as much as the real subject's edit does, to within +0.0002 against +0.8439 for the same control in the other regime. The quantity is therefore a contamination detector — it reports that a test item names the edited subject, not that an edit travelled — and one published benchmark has items that fail on exactly that ground, receiving a median 0.982 of an update they were built to test the propagation of. We report this as a negative result with a working control, and name what the control cost us to get right.

## 1 · The proposal, and why it is attractive

An evaluation of a weight edit can show that the edit broke something. It cannot show that the edit broke nothing. An item that was never written and a failure that never happened produce the same output — an empty result — and no amount of writing more items separates them, because a hand-written set measures the imagination of whoever wrote it rather than the extent of the damage.

The move that would fix this is to stop enumerating and start measuring: define a quantity for *any* prompt, so that an item can be scored without having been anticipated. ROME offers a natural candidate, because its update is rank-one and therefore scalar at every token. The fraction of the update landing on a token is a number, computable in one forward pass through the model as it was **before** the edit.

Be clear about what this buys. It removes the need to foresee which items matter. It does not remove the need to have items: the quantity is still evaluated on prompts we happen to hold, and a prompt nobody wrote is still unscored. What changes is that the set no longer has to be *right* in advance — only large.

This note asks whether that candidate quantity does the job, and finds that it does one job well and the intended job not at all.

## 2 · Related work, and what is not claimed

The nearest work we found is He et al. (2026), which reports both the depth phenomenon and a cosine decay with layer — 0.80 at layer 5 falling to 0.50 at 25, against 0.98 to 0.47 here — eight months earlier. What it does not carry is a control of the kind in §3: its reading of the effect as depth rests on edit success rates staying high across layers, which is a different quantity from the one that would separate a real effect from the measure's own behaviour.

**On novelty, plainly.** The mechanism in §3 is a line of algebra that any practitioner could derive, and several may assume without writing down. The claim here is **not** that it is unpublished. It is that we could not find it stated, on one web-search pass and one neighbouring paper read in full — which is enough to ask the question and not enough to answer it. If it is published, §3 becomes a replication and the contribution is §6.

Also cited: Meng et al. (2022) and Meng et al. (2023) for the edit rule; Cohen et al. (2024) for the benchmark scored in §6, read against its own test-type definitions rather than its abstract; Zhong et al. (2023) for the multi-hop benchmark used there.

## 3 · Method

ROME rewrites a single MLP output projection `W` at one layer so that a chosen key maps to a chosen value:

    W' = W + (v* − W k*) uᵀ / (uᵀ k*)

For any token whose key at that layer is `k`, the change this makes to the layer's output is `(v* − W k*)` scaled by

    c = (k · u) / (u · k*)

so `c` is the fraction of the update that token receives. It needs one forward pass through the unedited model, and nothing about the edit beyond `k*` and `u`.

**FIGURE 1** → `two-regimes.svg`

The figure is the argument, and the algebra under it is three steps. Under causal attention the hidden state at position *i* depends only on tokens at positions ≤ *i*. The key is read at the last token of the subject. So if two prompts agree on every token up to and including that one, their keys there are equal. A probe that opens with the edited subject agrees with the edit prompt on exactly that span. Therefore `k = k*`, and `c = (k*·u)/(u·k*) = 1` — for any `u`, any covariance, at any layer, whatever the probe goes on to ask.

This is analytic. It is not refuted by a measurement; it is refuted by an error in the three steps above, or by its premise failing. **The premise is the empirical part** — that the prompts really do share that span — and it is what §4 reports.

**The control is part of the measurement, not a check run afterwards.** A reading of 1.000 is consistent with the mechanism above and equally consistent with a pipeline that returns 1 by construction, and the two are indistinguishable from the reading alone. What makes 1.000 a claim is the floor: the same pipeline, the same prompts, scored against an edit on a different subject. In the implementation a reading without a baseline does not type-check. We mention this here rather than in a software appendix because it is the reason the numbers in §§4–6 can be believed, and because §6 is an account of a floor that was wrong.

## 4 · The near field: exact, and exact for an uninteresting reason

| | value |
| --- | --- |
| prompt opens with the edited subject | **1.000**, worst deviation 0.0e+00 |
| models, 6B to 405B | four, all exact |
| prompt names a different person | **0.082** mean, 0.081 median |
| overlap between the two groups | none — highest different-subject 0.153 sits below lowest same-subject 0.483 |
| the edited subject after a preamble | 0.93 at layer 5, 0.79 at 12, 0.52 at 24 |

The premise of §3 holds, and holds without slack. The separation is not a threshold we chose; the two distributions do not meet.

The consequence is the part worth carrying. A probe moving after an edit is not evidence that the model reasoned from the edit — if the probe names the edited subject, the whole update arrives there mechanically, and it would arrive whatever relation the probe asked about. Any argument that treats movement on such a probe as propagation has to supply something this measurement does not.

**What would show this wrong.** A prompt sharing the prefix whose coefficient is not 1.000, with the pipeline's anchor gate passing.

## 5 · What one update actually does

One rank-one edit has two effects and they are separable. Measured on 495 probes over 42 subjects, three arms, paired, bootstrapped at 10,000 resamples:

| | real − control | control − stranger |
| --- | --- | --- |
| **destination** — where the new answer goes | **+0.2828** (+0.2424, +0.3232) | +0.0000 (−0.0101, +0.0101) |
| **destruction** — what the old answer loses | +0.0009 (+0.0004, +0.0024) | **+0.0583** (+0.0472, +0.0732) |

The two halves separate in opposite directions on the same probes. Destruction follows *whose* key the edit touched and barely notices what the edit said — identity is worth about 65 times content. Destination is the other way round: it is specific to the content, and an edit on a different subject delivers nothing, landing in the injected country at the base rate.

**Stated against ourselves.** This says content that *can* answer the question is what arrives. It does not say every edit delivers its own content somewhere: the control edit injects an occupation while these probes ask for a city, so no arm-symmetric check exists here. A readout able to express the control's own content would settle it, and is not run.

## 6 · The far field: the measure is blind where propagation lives

The coefficient is exact where the prompt names the edited subject. That is the easy half, and it is easy for a reason given in §3: such a prompt shares the edit prompt's prefix, so the key is the same key and the arithmetic has nowhere else to go. The question this section answers is whether anything is left over — whether the measure says anything about a prompt that never names the subject at all.

It has to, to be useful. A question that names the edited subject can be answered by the update arriving at that mention directly, so a score on it cannot separate propagation from delivery. Propagation lives in the other case: the model is asked about some entity reached *through* the edited one, and the edited one is never mentioned. Call that the **far field**, and the case where the subject does appear the **near field**.

We measured on MQuAKE-CF-3k, a multi-hop editing benchmark whose items chain two relations, taking 513 instances that carry a single edit. No edit was applied. Each hop-2 question — the one about the entity at the end of the chain — was scored against its own instance's `k*`, and then against all 512 others. The 512 others are the control: an edit on a stranger, which by construction cannot have propagated anywhere near this question. If the measure sees propagation, a question's own edit must reach it more than a stranger's does.

**FIGURE 2** → `near-and-far-field.svg`

| | own `k*` | same-relation stranger | excess | 95% CI | n |
| --- | --- | --- | --- | --- | --- |
| **far field** — the question never names the subject | 0.0543 | 0.0481 | **+0.0002** | (+0.0001, +0.0004) | 900 |
| **near field** — the question names it | 0.9334 | 0.0506 | **+0.8439** | (+0.8379, +0.8500) | 639 |

A stranger's edit reaches a far-field question as much as the real subject's edit does, to within two ten-thousandths. The interval excludes zero, so the effect is there; it is also more than three orders of magnitude smaller than the same comparison in the near field, on the same instrument, on the same day. The near-field row is what the measure looks like when it is working. The far-field row is what it looks like when it is not.

So at layer 5 the coefficient has no subject-specific dynamic range in the far field. It is not that propagation fails to happen — nothing here says an edit does not reach a two-hop question. It says that this measure cannot tell whether it did.

### The floor that gave the opposite answer

The first version of this measurement scored each question against *all* donors rather than same-relation ones. That gives a far-field excess of +0.0232, with an interval excluding zero, which reads as real far-field signal and would have been reported as such.

Nearly every donor carries a different relation from the question being scored. So that floor was not a stranger-floor at all; it was the different-relation floor wearing another name, and the +0.0232 was the measure doing what §4 says it does — responding to the relation — rather than finding anything about the subject.

The confound did not come out of the measurement. It came from asking what else a hop-2 subject is: it is the middle entity of the chain, which the question is about indirectly, which means donors sharing its relation are not interchangeable with donors that do not. Nothing in the numbers would have flagged this. A tighter interval would have made it worse.

This is worth stating plainly because the same shape of error is available to anyone measuring against a floor, and a floor that is secretly a different comparison does not announce itself. The only defence we know of is the one in §3 — make the control part of the measurement, so that constructing a reading without one is impossible, and so that what the control holds fixed is written down where it can be disputed.

### What the measure does detect

Something, and it is worth having. The coefficient reliably detects two things: that a prompt names the edited subject, and which relation it asks about.

That first one is a property of benchmark items, and some benchmark items have it when they should not. RippleEdits, which evaluates whether an edit's consequences follow, includes a test type meant to check that an edit reaches a *different* entity arrived at through the edited one. Its prompts read like *"the name of the head of government of the place of death of **Leo Arons** is"* — with the edited subject sitting inside the prompt that is supposed to test travel away from it.

**FIGURE 3** → `direct-exposure.svg`

Those items receive a median **0.982** of the update, against a **0.065** floor built by scoring the same prompts against a stranger's edit. The update arrives at the queried token by arithmetic, before any question of the model composing two relations arises.

An editor could therefore score on that test while generalising nothing. What would show this wrong: the answers to those items moving under an edit that is delivered to the subject mention but whose content cannot answer the question — which would mean something other than direct delivery is doing the work.

This is not a property of multi-hop evaluation, and saying so would overstate it. MQuAKE names the edited subject when and only when the edit sits on the chain's first hop — 6,861 of 6,861 items, and 0 of 16,506. The same field that produced the problem also produced a benchmark without it, by construction rather than by design, which is what makes the failure diagnosable rather than something to complain about.

**What would show this section wrong.** A layer sweep finding far-field dynamic range at some depth other than 5. That would not rescue layer 5, which is where ROME and EasyEdit edit, but it would mean the measure is blind at one depth rather than blind.

---

## 7 · Whether a remote reading can be trusted at all

Every number above was read off a shared inference service, where the same request on two days need not return the same bytes. Two facts are what a reader needs, and the rest is in the repository.

**A ratio whose two terms are read inside one trace is exact** — deviation 0.000e+00 across three models, two architectures and depths 0 to 79, fifteen layer-model pairs. Every coefficient here is such a ratio, which is why §§4–6 carry no tolerance. **Nothing else is portable:** the same disagreement computed on the serving GPU against a local CPU reads 5.3e-06 on one model and 7.5e-09 on another served in float32, and readings partitioned by serving GPU on one day and not at all two days later. What varies is the deployment — dtype, sharding, tensor shape — not the model family, so a tolerance written into a gate is right in one place and wrong in the next.

One correction from that work belongs here and not only there: we reported that this disagreement grows with depth in bfloat16, and a sweep of a larger model withdrew it. The effect falls 53-fold to one layer and rises 298-fold to another; the direction was one model's artefact.

**What would show this wrong.** A derived ratio read with both terms inside one trace that is not 0.000e+00.

## 8 · Limits

Everything qualified is here; §§1–7 run without hedges.

1. **Delivery is not effect.** Every number is how much of the update arrives at a token. None is how far the model's answer moved. At a fixed coefficient, measured movement spans a factor of 2.96. This is the gap the work set out to close and did not close.
2. **The coefficient belongs to a token, not a prompt.** Within one prompt the subject position and the final position differ by a factor of 35, and the answer is produced at the final position.
3. **§6 is one model, one layer, two-hop chains.** The layer is the one ROME and EasyEdit edit at, which is why it was chosen, and it is still one layer.
4. **The 42 subjects of §5 are survivors, not a sample.** Computing a new edit against a remote model needs a backward pass the inference library refuses mid-trace, so the subjects are those whose edits were already cached. No magnitude in §5 generalises past that set.
5. **Mined and hand-built sets license existence claims, never rates.** Nothing here is a frequency.
6. **Magnitude matching in §5 is one scalar.** Two edits of equal norm can differ in direction relative to a probe's key. A directional control is the obvious refinement and is not run.
7. **Nothing here was read outside the project before this document.** Every result was produced and reviewed by the same two parties. The record of self-correction — §6's floor, §7's withdrawn claim — is evidence the process catches things, not evidence that what remains is right.
8. **How this may not be used.** §6 is a finding about a measure. It is not a screening method being offered, and no threshold is proposed, because setting one would need the delivery-to-effect link that item 1 says is missing.

## 9 · What this is, plainly

A negative result with a working control.

What makes it worth writing is not the denial. It is that the same control, on the same instrument, separates +0.8439 in one regime from +0.0002 in the other — so the denial is a measurement rather than a failure to find something, and a reader can tell the difference. The positive direction is blocked on a library that will not run a backward pass against a remote model, and that is named here so nobody has to guess whether it was tried.

## References

Cohen, R., Biran, E., Yoran, O., Globerson, A., & Geva, M. (2024). Evaluating the Ripple Effects of Knowledge Editing in Language Models. *Transactions of the Association for Computational Linguistics*, 12. https://arxiv.org/abs/2307.12976

He, Z., Chen, B., Xiong, T., Sun, Z., Zhu, M., & Chen, X. (2026). On the Limitations of Rank-One Model Editing in Answering Multi-hop Questions. *arXiv:2601.04600*. https://arxiv.org/abs/2601.04600

Meng, K., Bau, D., Andonian, A., & Belinkov, Y. (2022). Locating and Editing Factual Associations in GPT. *NeurIPS*. https://arxiv.org/abs/2202.05262

Meng, K., Sharma, A. S., Andonian, A., Belinkov, Y., & Bau, D. (2023). Mass-Editing Memory in a Transformer. *ICLR*. https://arxiv.org/abs/2210.07229

Zhong, Z., Wu, Z., Manning, C. D., Potts, C., & Chen, D. (2023). MQuAKE: Assessing Knowledge Editing in Language Models via Multi-Hop Questions. *EMNLP*. https://arxiv.org/abs/2305.14795

_Every entry is carried from `web/data/papers.yml`, where each is marked `verified: true` — title, authors, year and venue checked against the paper's own record rather than read off a search result._
