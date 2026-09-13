# A benchmark that outlived its calibration

_Draft — D-002, v2. Claim **strengthened and verified** 2026-09-14 against the ROME
paper's construction appendix and its own baseline table. The earlier "outlived its
calibration" framing was wrong in its mechanism: there was no calibration._

Every propagation result in knowledge editing is conditional on the model having
held the fact being edited. If it never did, a "failed ripple" is an artifact of
ignorance rather than a property of the editor.

That condition is never established. Not for your model, and not for the model the
benchmark was built with.

## What CounterFact actually does

CounterFact is not naive about the problem. Meng et al. open §3.3 by citing exactly
this concern:

> "Hase et al. (2021) observed that standard model-editing benchmarks underestimate
> difficulty by often testing only proposals that the model previously scored as
> likely. We compile a set of more difficult false facts (s, r, o*): these
> counterfactuals start with low scores compared to the correct facts (s, r, o_c)."

Read quickly, that sounds like a filter. It is not. The construction appendix says
how it was actually done:

> "Each record in CounterFact is derived from a corresponding entry in PARAREL ...
> **Solely using the PARAREL entry**, we derive two elements ... **o\* is drawn from
> a weighted sample of all PARAREL tuples with the predicate (r, ·)**."

The counterfactual target is obtained by sampling another object of the same
relation. Specificity prompts come from a Wikidata SPARQL query. **No model is
consulted at any point in construction.** The aspiration in §3.3 is about making
insertion *difficult*; it was implemented by how `o*` is sampled, not by checking
what any model believes about `o_c`.

And the paper's own numbers confirm it. Table 4's unedited GPT-2-XL baseline reports
**ES = 22.2** — the fraction of records where the model already prefers the *false*
target before any edit. Had records been selected so the model prefers the true
fact, that would be near zero. It isn't.

So on the benchmark's own primary model, **22% of records fail even the weakest
possession test on day one** — and nothing downstream re-checks. The fixed 21,919
records are now run against GPT-J, Llama, Qwen, Mistral and everything since.

This is not carelessness. The benchmark was built to make *insertion* hard, which it
does. Possession of the fact being displaced is simply a different question, and it
was never the one being asked.

## How much weaker is the check?

Three tests, same 165 items, same model (gpt2-medium), 10 candidates:

| test | result |
| --- | ---: |
| `P(true) > P(counterfactual)` — the field's filter | **75%** |
| true answer ranks first among 10 type-matched candidates | **61%** |
| free generation, unconstrained top-1 | **12%** |

The 12% is not ignorance. CounterFact's templates are ambiguous between temporal
and locative readings — *"Karolos Koun died at"* invites `" the age of 90"` — so a
model that knows the answer answers a different question and scores zero. Under
constraint, the same model ranks Koun/Athens **1st of 10**.

Prompt sensitivity and the worry that probing measures phrasing rather than
knowledge are long established in the factual-probing line (LAMA and its critiques).
What is new here is locating it inside an editing benchmark and showing what it
costs downstream.

## Possession across scale

Constrained rank against **50** type-matched candidates, plus a control arm: the
same candidates scored with the subject replaced by a placeholder, so a model
riding the template's base rate earns nothing. 165 rigid-relation items per model.

| model | params | possession | template alone |
| --- | ---: | ---: | ---: |
| gpt-j-6b | 6B | **56%** | 5% |
| Llama-3.1-8B | 8B | **74%** | 4% |
| Llama-3.1-70B | 70B | **79%** | 4% |
| Llama-3.1-405B | 405B | **85%** | 5% |

Monotonic, decelerating, **not saturated at 405B**. Fifteen percent of a *curated*
factual benchmark is still not held by the largest model tested.

Scale buys the hard relations and leaves the easy ones alone. `P103` native
language is 80% at 6B and flat at 93% above. The movement is concentrated:
`P449` original broadcaster **13% → 87%**, `P740` location of formation
**40% → 93%**, `P19` place of birth **13% → 53%**.

That last row is the one to sit with. **`P19` tops out at 53% even at 405B**, and
GPT-J holds 13%. Place of birth is among the relations with the richest surrounding
context — burial place, citizenship, family — so it is exactly where a propagation
study would want to look, and it is the relation every model holds worst.

## What this means if you are running these benchmarks

Report possession beside efficacy, measured on *your* model. There is no inherited
filter to rely on — not a weak one, not an outdated one, none.

Concretely: about **44%** of rigid-relation CounterFact edits on GPT-J target facts
the model does not hold under a constrained test. The benchmark's own two-way
number on its own model already flags 22%. Propagation failures measured on those
records are not evidence about the editor.

## Limits, stated rather than buried

**What we did not measure.** We report possession for GPT-J, Llama-3.1-8B, -70B and
-405B. GPT-2-XL, the benchmark's own primary model, is characterised here only by
the paper's reported ES = 22.2 — the weak two-way figure, not our constrained one.
Running the constrained measure on it would place the benchmark's original model on
the same axis as the rest, and would likely show a shortfall well above 22%. It is
not hosted on NDIF, so it needs a local run. Worth doing; not load-bearing, since
the construction appendix already settles that no filter exists.

**Levels depend on the candidate count.** Fifty candidates is harder than ten;
more would be harder still. Ordering across models is robust, absolute levels are
not, and the count is recorded beside every number for that reason.

**Scoring is teacher-forced.** That measures whether knowledge is present, not
whether the model would spontaneously produce it. Recent work criticises
teacher-forced evaluation for exactly this. The response here is to report all
three arms rather than pick the flattering one — and constrained teacher-forcing
is the right instrument for *possession*, with free generation bounding it below.

**The field was searched, not swept.** The nearest competitor
(arXiv 2505.18690) critiques inconsistent setups, teacher-forcing, dataset coverage
and multi-edit scope; it does not measure possession and does not raise the
transfer problem. That closes the nearest neighbour, not the literature.

**Rigid relations only** for the scale curve — 11 of CounterFact's 34, chosen
because the wider project needed time-stable facts. Whether mutable relations
behave the same is unmeasured.

## The tool

`edit-slice` ships the filter used here. It takes an arbitrary edit set, reports a
held-rate with the config that produced it, and reports coverage — because a
held-rate computed over a silently-biased subset is worse than no held-rate at all.
We know that because an early version of the filter did exactly that, and inflated
its own number by forty points.
