---
slug: the-check-that-was-never-there
title: "The check that was never there"
authors: [saif]
tags: [lab-notes, knowledge-editing, edit-slice, method]
date: 2026-09-14
standfirst: >
  I withdrew a claim because I thought a benchmark already handled it. Then I read
  the paper's appendix instead of its prose, and found the withdrawal was the
  mistake. CounterFact has no possession check — and a model's own numbers say so.
---

Four days ago I wrote about a claim of mine getting smaller. This is the sequel,
and it goes the other way.

<!-- truncate -->

The claim was that **knowledge-editing benchmarks measure propagation into
knowledge they never verified was there.** Edit a fact, check whether the change
ripples outward correctly — but if the model never held the fact you edited, a
"failed ripple" is an artifact of ignorance rather than a property of the editor.

I searched, found that CounterFact appeared to handle this, and withdrew the
claim. That was wrong, and I want to lay out both the evidence and how I got it
backwards, because the second part is the more useful half.

## What made me withdraw it

CounterFact opens its dataset section by citing exactly this concern:

> Hase et al. (2021) observed that standard model-editing benchmarks underestimate
> difficulty by often testing only proposals that the model previously scored as
> likely. We compile a set of more difficult false facts (s, r, o\*): these
> counterfactuals start with low scores compared to the correct facts (s, r, o_c).

Read at speed, that is a filter. The authors are aware of the problem, they say so,
and they say they compiled the set to avoid it. I concluded the check existed and
was merely weak, wrote that up, and moved on.

## What the appendix actually says

The construction appendix describes how records were built:

> Each record in CounterFact is derived from a corresponding entry in PARAREL …
> **Solely using the PARAREL entry**, we derive two elements … **o\* is drawn from
> a weighted sample of all PARAREL tuples with the predicate (r, ·)**.

The counterfactual target is obtained by sampling another object of the same
relation — a different city for a city-location prompt. Specificity prompts come
from a Wikidata SPARQL query. **No model is consulted at any point in
construction.**

So the sentence in §3.3 is a claim about what that sampling is expected to yield,
not a step that was performed with a model. The aspiration is real; the mechanism
is sampling. Those are different things, and the difference is the whole argument.

## The paper's own numbers agree

This does not rest on my reading of one appendix. Table 4 reports baselines for the
**unedited** model, and the Efficacy Score column is the fraction of records where
`P(false target) > P(true fact)`.

For unedited GPT-2-XL, the benchmark's own primary model: **ES = 22.2**.

Twenty-two percent of CounterFact records already favour the *false* answer before
anything is edited. If records had been selected so the model prefers the true
fact, that number would be near zero.

Turn it around: GPT-2-XL holds the true fact in **77.8%** of records. Which, for
what it is worth, is close to the 75% I measured on GPT-2-medium with the same
two-way test — exactly what you would expect if no model-specific selection ever
happened.

## So how bad is it, really?

`P(true) > P(false)` is a forced choice between two options. It asks whether the
model prefers the real answer to one specific fabricated alternative, which is a
much easier question than whether it holds the fact.

A harder test: does the true answer rank **first** among 50 type-matched
candidates, *and* does it rank higher with the real subject present than with the
subject replaced by a placeholder? The second condition matters — without it, a
model that has simply learned "mother-tongue prompts end in a language" scores
well on the template alone.

Measured that way, over 165 items per model:

| model | params | possession | template alone |
| --- | ---: | ---: | ---: |
| GPT-J | 6B | **56%** | 5% |
| Llama-3.1-8B | 8B | **74%** | 4% |
| Llama-3.1-70B | 70B | **79%** | 4% |
| Llama-3.1-405B | 405B | **85%** | 5% |

Monotonic, decelerating, and **not saturated at 405B**. Fifteen percent of a
curated factual benchmark is still not held by the largest model I could reach.

The shortfall on GPT-J is **44%** — twice what the benchmark's own two-way number
would suggest.

Scale buys the hard relations and leaves the easy ones alone. Native language sits
at 80% on a 6B model and flat at 93% above it. The movement is all in the
strugglers: original broadcaster **13% → 87%**, location of formation
**40% → 93%**, place of birth **13% → 53%**.

That last one deserves a pause. **Place of birth tops out at 53% even at 405B**,
and GPT-J holds 13%. It is among the relations with the richest surrounding
context — burial place, citizenship, family — so it is exactly where you would want
to look for knock-on effects, and it is the relation every model holds worst.

## This is not a criticism of the benchmark

CounterFact was built to make *insertion* hard, and it does that. Sampling a
plausible-but-wrong object of the same relation is a sound way to get difficult
targets. Possession of the fact being displaced is a different question, and it was
simply never the one being asked.

The problem is downstream. The fixed 21,919 records are now run against GPT-J,
Llama, Qwen, Mistral and everything since, and nothing in the standard pipeline
asks whether the model under test holds the facts being overwritten.

The fix is cheap: **report possession alongside efficacy, measured on your model.**

## How I got it wrong

Two separate literature passes and neither caught this, because both were searching
for *competing work* rather than re-reading the *primary source*. I had the ROME
paper open in a directory on my own machine the entire time. The appendix was three
pages from the sentence I misread.

The narrow lesson: when a claim turns on what a paper **did**, read its methods
appendix before concluding from its prose. Aspiration and mechanism live in
different sections and only one of them is binding.

## Honest limits

**Levels depend on the candidate count.** Fifty candidates is harder than ten; more
would be harder still. Ordering across models is robust, absolute levels are not,
and the config is recorded beside every number for that reason.

**Scoring is teacher-forced.** That measures whether knowledge is *present*, not
whether the model would spontaneously produce it. On identical items: two-way 75%,
constrained 61%, free generation 12% — and the last is depressed mostly by
ambiguous prompt templates, not ignorance. Constrained teacher-forcing is the right
instrument for possession; free generation bounds it from below.

**Prompt sensitivity is not my finding.** That models are brittle to phrasing, and
that probing can measure wording rather than knowledge, is well established in the
factual-probing literature. What is new here is locating it inside an editing
benchmark and pricing it.

**Rigid relations only** for the scale curve — 11 of CounterFact's 34, chosen
because the wider project needed time-stable facts. Whether mutable relations
behave the same is unmeasured.

**I have not run the constrained measure on GPT-2-XL.** The benchmark's own model
is characterised here by its reported ES alone. Placing it on the same axis as the
rest would be worth doing.

---

The tool is [edit-slice](https://github.com/Rubix982/open-concept-lab). It takes an
arbitrary edit set, reports what fraction the model holds, and reports coverage —
because a held-rate computed over a silently biased subset is worse than no
held-rate. I know that because an early version did exactly that, and inflated its
own number by forty points.
