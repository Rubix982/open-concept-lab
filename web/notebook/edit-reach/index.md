---
title: edit-reach
sidebar_label: Overview
sidebar_position: 1
description: Testing whether an edit's reach can be predicted before the edit is applied. It cannot — and what the measure does detect is worth saying precisely.
---

# edit-reach

[edit-slice](/notebook/edit-slice/) found that a ROME edit reaches everything sharing its subject by arithmetic rather than by inference. This project asked whether that finding could be turned into a tool: a number, computed in one forward pass through the **unedited** model, that says in advance how far an edit will travel.

The two are kept apart on purpose. edit-slice accumulates findings. This one was to produce a working screen or show that it cannot.

It showed that it cannot. What follows is where the line falls.

<Claim
  label="What the instrument is"
  superseded="The coefficient screens whether a benchmark item can test propagation, so it can be used as a pre-run gate on propagation evaluations."
  record={{
    "What replaced it": "It detects contamination — that a prompt names the edited subject, and which relation it asks about. It does not detect propagation.",
    "Why the first version failed": "C-001 (the coefficient does not predict measured movement) and E-004 (in the far field, a stranger's edit on the same relation reaches a question as much as the real subject's edit does).",
    Confidence: "High on the near field, which is analytic. The far-field result is one model, one layer, two-hop chains.",
  }}
>
  A contamination detector, not a propagation detector.
</Claim>

## What was proposed

A benchmark gives a lower bound on an edit's damage and never an upper bound. It can show that an edit broke something; it cannot show that an edit broke nothing, because an absent item and an absent failure look identical. Writing a larger item set does not fix this — a hand-written set measures the limits of whoever wrote it.

The alternative was to replace enumeration with measurement. ROME's update is rank-one, so for any token with key `k` the fraction of the edit that lands on it is

$$
c = \frac{k \cdot u}{u \cdot k^{*}}
$$

and this is computable without applying the edit at all. A quantity defined for *any* prompt rather than for a listed set means an item can be scored without having been anticipated.

That is the appeal, and it survives the result below. What does not survive is the claim that this quantity tells you about propagation.

## Where it works, and why that is not enough

Under causal attention, a prompt that begins with the edited subject has, at that subject's last token, exactly the same preceding text as the edit prompt did. So its key is identical to `k*`, and `c = 1` — for any covariance, at any layer, whatever relation the prompt goes on to ask about. This is a derivation, not a measurement. What was measured is its premise, and it held exactly: **1.000** across four models from 6B to 405B. A prompt naming a different person gets **0.082**.

<Figure
  src="/img/edit-reach/two-regimes.svg"
  alt="Three prompts drawn as strips. The edit prompt begins with Maurice de Vlaminck. A probe beginning with the same name shares every token the subject's last token can see under causal attention, so its key is identical and the coefficient is exactly 1.000. A probe beginning with a different person reads 0.082."
  caption="The whole account in one picture. The coefficient is read at the subject's last token, and under causal attention that token sees only what precedes it — so a probe that opens with the edited subject has the same key the edit had, whatever it goes on to ask."
  wide
  plain
/>

The near field is therefore real and sharp, and it is where the useful application lives. RippleEdits has a test type meant to check whether an edit propagates to a *different* entity reached through the edited one; its prompts read *"the name of the head of government of the place of death of **Leo Arons** is"*, with the edited subject sitting inside the prompt. Those items receive **0.982** of the update against a **0.065** floor built from a stranger's edit on the same prompts. MQuAKE names the edited subject when and only when the edit sits on the chain's first hop — **6,861 of 6,861**, and **0 of 16,506** — so the problem is diagnosable rather than universal.

<Figure
  src="/img/edit-reach/direct-exposure.svg"
  alt="The item is meant to test whether an edit on Leo Arons travels two hops, through his place of death to that place's head of government. But the prompt itself contains the string Leo Arons, so the edit reaches the queried token directly."
  caption="The item is built to ask whether an edit travels two hops. The edited subject is sitting in the prompt, so it does not have to."
  wide
  plain
/>

Detecting that is worth something. It is not what the project set out to do.

## Where it fails

**C-001 — does predicted reach predict measured movement? Denied**, 31 October 2026. 495 probes, 42 subjects, Llama-3.1-8B at layer 5.

The sharper version came a day later. Scored on MQuAKE-CF-3k, 513 single-edit two-hop instances with no edit applied, every hop-2 question against all 512 other instances' `k*`:

<Figure
  src="/img/edit-reach/near-and-far-field.svg"
  alt="One shared scale from 0 to 1. In the near field the subject's own edit reads 0.9334 against a stranger's 0.0506, an excess of plus 0.8439. In the far field they read 0.0543 and 0.0481, an excess of plus 0.0002, so close that the two marks sit almost on top of each other."
  caption="The same control, applied twice. In the near field it separates the real edit from a stranger's by 0.84. In the far field the two marks are one mark."
  wide
  plain
/>

| | own `k*` | same-relation stranger | excess | 95% CI |
| --- | --- | --- | --- | --- |
| **far field** (question never names the subject), n=900 | 0.0543 | 0.0481 | **+0.0002** | (+0.0001, +0.0004) |
| **near field** (question names it), n=639 | 0.9334 | 0.0506 | **+0.8439** | (+0.8379, +0.8500) |

A stranger's edit reaches a far-field question as much as the real subject's edit does, to within two ten-thousandths. The same control barely dents the near field. The far field is where multi-hop propagation lives, and at layer 5 this measure has no subject-specific dynamic range there at all.

**The first floor gave the opposite answer**, and it is recorded because of that. Scored against *all* donors, the far-field excess is +0.0232 with an interval excluding zero — which reads as real far-field signal. But nearly all donors carry a different relation, so that floor was the different-relation floor under another name. The confound was found by asking what else a hop-2 subject is — the chain's middle entity, which the question is about indirectly — and not by anything in the measurement.

## Whether any of it reproduces

Half the tickets here are not about editing at all. They ask whether a number read off a remote model is the same number tomorrow, because a result that cannot be read twice is not a result.

<Figure
  src="/img/edit-reach/same-number-twice.svg"
  alt="Three nested boxes. The outermost is the deployment — dtype, sharding and tensor shape — which sets the scale of disagreement. Inside it is routing, which replica served a request. Innermost is a single trace, where a derived ratio read with both terms inside that trace was exactly zero at all fifteen layer-model pairs tested."
  caption="Three things move a reading, and only the innermost one can be made to stop."
  wide
  plain
/>

What came out is narrower than expected and more useful. The structural claims hold exactly — a ratio whose two terms are read inside one trace came back at **0.000e+00** on every one of fifteen layer-model pairs, across three models, two architectures and depths 0 to 79. **No magnitude holds.** The same disagreement between two arithmetic sites reads 5.3e-06 on Llama-3.1-8B and 7.5e-09 on GPT-J, which NDIF serves in float32 rather than bfloat16.

So the thing that varies is the deployment, not the model family: the 8B and the 70B are the same family and disagree, while GPT-J differs because of how it is served. Any gate with a tolerance written into it is wrong somewhere else. The tolerance has to be measured on the deployment you are actually running. The full reference, with the conformance suite that found four errors in it, is [in the repository](https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/docs/ndif-reproducibility.md).

## What is in the package

`editreach` 0.1.0 — ten modules, about 1,900 lines. Two choices in it are claims rather than tidying:

- **The coefficient is an object, not an expression.** In edit-slice it was written inline in each run script. It is the thing being claimed, so it has a name and a type.
- **A reading without a control does not type-check.** edit-slice stated this as prose and relied on whoever wrote the next script having read it. Here it is `Unbaselined`, and the program stops. A coefficient of 1.000 means nothing without the floor that shows the pipeline was capable of returning something else — and a pipeline hardwired to return 1 looks identical without it.

What the package cannot do: compute a new edit against a remote model. `compute_v` needs a backward pass, which nnsight 0.8.1 refuses mid-trace. So the 42 subjects everything here rests on are the ones whose edits were already cached — survivors, not a free draw.

## Limits

<Figure
  src="/img/edit-reach/delivery-is-not-effect.svg"
  alt="An edit passes through two steps. Delivery is how much of the edit arrives at a token, and the coefficient measures it. Effect is how far the model's answer moves, and the coefficient does not measure it. At one fixed coefficient the measured movement still spans a factor of 2.96."
  caption="The gap this project existed to close, and did not."
  wide
  plain
/>

- **Delivery is not effect.** Every number here says how much of the edit vector arrives at a token. None says how far the model's answer moved. At a fixed coefficient, measured movement spans a factor of 2.96.
- **The coefficient belongs to a token, not a prompt.** Within one prompt the subject position and the final position differ by a factor of 35, and the answer is produced at the final position.
- **The far-field result is one model, one layer, two-hop chains.** A layer sweep could still find dynamic range at a depth other than 5. It would not rescue layer 5, which is where ROME and EasyEdit edit.
- **The 42 subjects are not a sample.** They are the cached survivors of a blocked path. Any magnitude here generalises no further than that set.
- **This is not an offer.** The scope above is a finding about a measure, not a method anyone should adopt. Nothing here proposes a better editor, and the project does not claim the mechanism is unpublished — only that it could not be found stated.

## What would change this

| | |
| --- | --- |
| a layer sweep finds far-field dynamic range at some depth other than 5 | the screen is alive again, at that depth, and the scope sentence narrows to layer 5 |
| a graded relation-similarity control shows the +0.0002 moving with relation distance | the categorical split is too coarse and the far field has structure this missed |
| the backward-pass block is lifted | the delivery-to-effect link can be tested on a free draw instead of 42 survivors |
