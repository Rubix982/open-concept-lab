# Engineer Tickets — edit-slice

### E-001 · SPIKE: do rigid-relation edits have mined grounds?

**Status:** closed
**Type:** spike
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10
**Estimated:** 3h (time-boxed — Protocol §3; if Spent > 6h, split or re-scope)
**Spent:** ~45m — stopped at first failure, as designed.

**Description:**
The design.md §0 gate. Opens as a spike, not an implementation: R-001 is medium
confidence and §0 has no data.

R-003 established that 35.4% of CounterFact (7,770 edits) uses a time-rigid
relation, so rigid edits are plentiful. But rigidity is **necessary, not
sufficient**: a rigid relation with no mined grounds in the KG yields no kernel
and therefore no probe. This spike answers whether §0 method (e) — mined Horn
rules read backwards — can actually produce grounds for the edits we care about.

Three questions, cheapest first, stop at the first failure:

1. **Head coverage.** In the AMIE rules shipped with `dice-group/Benchmarking-KE`,
   do any rules have a HEAD predicate corresponding to one of our 11 rigid
   Wikidata relations (P19, P20, P103, P495, P740, P364, P407, P178, P138, P449,
   P30)? Their rules are over DBpedia predicates, so this requires a
   Wikidata->DBpedia predicate mapping. If no rigid relation appears as a head,
   method (e) is dead for our purposes and we fall back to (c).
2. **Body plausibility.** For rules that do have a rigid head, are the bodies
   recognisable as *grounds* (premises) rather than co-occurrence artifacts?
   Read by hand, ~20 rules.
3. **Agreement.** Hand-label grounds for ~20 CounterFact edits with rigid
   relations. Do mined rule bodies agree above chance?

**Falsification (from design.md §0):** if mined bodies do not agree with
hand-labelled grounds above chance, (e) fails -> fall back to (c) as discovery,
then (b), then a non-reusable v1. Second check: the fraction of mined bodies
passing the directed intervention test.

**Blockers:** none

**Result: NEGATIVE.** Question 1 (head coverage) fails decisively; questions 2
and 3 are moot because there are no substantive rigid-head rules to inspect.
Of 913 usable rules, 66.5% are alias tautologies (`fact + alias => fact`), 21.2%
are alias-headed, 2.3% substantive. All 32 rigid-head rules are alias
tautologies. The pathology is DBpedia's redundant naming predicates plus AMIE,
so it is a property of the KG and not of the entity set — re-running over
CounterFact subjects is not expected to help.

**Artifacts:**
- agents/shared/findings.md -> "[E-001] §0 method (e) FAILS — alias tautologies"

**Closed:** 2026-09-10

---

### E-002 · SPIKE: does Wikidata support grounds where DBpedia did not?

**Status:** closed
**Type:** spike
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10
**Estimated:** 3h (time-boxed; if Spent > 6h, split or re-scope)
**Spent:** —

**Description:**
Split from E-001, which killed method (e) over DBpedia. This is a genuinely
different proposition rather than a retry: CounterFact is Wikidata-native
(relations are P-codes, objects carry Q-ids), and Wikidata stores labels as
labels rather than as statements — so the alias-predicate explosion that produced
E-001's tautologies largely does not exist there.

Cheapest-first, stop at the first failure:

1. **Entity coverage.** Sample rigid-relation CounterFact edits stratified across
   the 11 rigid relations. Entity-link subjects to QIDs. Measure: link success
   rate, statements per subject, and whether Wikidata actually asserts the
   `target_true` the edit is overwriting. If subjects are sparse, there are no
   grounds to find regardless of any mining step.
2. **Ground plausibility.** For subjects with adequate statements, do the
   co-present properties look like *premises* for the edited relation
   (e.g. P19 birth place and P27 citizenship as grounds for P103 native
   language)? Read by hand.
3. **Rule mining.** Only if 1 and 2 pass. Mine over the Wikidata slice and check
   whether the alias pathology recurs in another form (e.g. via P31/P279 chains).

**Falsification:** if Wikidata subjects are sparse, or co-present properties are
not plausibly justificatory, method (e) is dead outright and we fall back to
method (c) as discovery per design.md §0.

**Blockers:** none
**Artifacts:**
- agents/shared/findings.md -> "[E-005] possession re-measured"
- agents/engineer/workspace/possession_lift.py, run_e005.sh, lift/*.json
- src/remote.py — score_pairs, adaptive OOM halving, transport classification

**Closed:** 2026-09-11

---

### E-003 · Possession check — does the model hold what we intend to edit?

**Status:** closed — superseded by E-005
**Type:** spike
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10
**Estimated:** 3h (time-boxed)
**Spent:** ~3h. Head possession done; ground possession split to E-004.

**Result (head possession):** gpt2-medium 61% / gpt2-large 62% / Llama-3.1-70B
**93%** top-1 by constrained rank, 165 items. [T-039] confirmed, [O-004]
vindicated. Falsification did NOT trigger: head possession is *not* already high
at gpt2-medium under a valid measure — it only looked high (75%) under the
literature's two-way test, which this ticket shows overstates possession.
Remaining: GPT-J-6B, the intended *edit* target, still sweeping.

**Description:**
Executes [T-039]. A ground the model never held cannot be orphaned, so between
"the oracle lists these grounds" and "the edit orphaned them" sits a missing step
this ticket supplies.

Two layers, head first because it is free:

1. **Head possession.** Does the model hold the fact we intend to edit? For each
   CounterFact rigid-relation edit, teacher-force `target_true` and `target_new`
   given the prompt and compare. The standard pre-edit condition is
   P(target_true) > P(target_new). If a model fails this, editing that fact is
   meaningless and any orphan measured on it is an artifact.
2. **Ground possession.** Same test against grounds. Needs prompt templates for
   ground properties (P119 burial, P123 publisher, ...), which CounterFact does
   not supply. Deferred to E-004.

**Why it also settles [O-004] empirically.** The charter was amended to GPT-J on
the *argument* that GPT2-medium is too thin to hold grounds. Running possession
across gpt2-medium and gpt2-large — both already cached — converts that argument
into a measurement and gives a scaling trend before committing NDIF time. GPT-J
weights are NOT cached locally (7.3MB of config only) and 6B fp16 will not fit
16GB RAM, so GPT-J genuinely requires NDIF.

**Falsification:** if head possession is already high at gpt2-medium, the
possession argument for scaling weakens and O-004 rests on ground possession
alone — which then must be measured before the model choice is justified.

**Blockers:** none
**Artifacts:** src/probing.py; agents/engineer/workspace/; agents/shared/findings.md
**Closed:** —

---

### E-004 · Ground possession — does the model hold the GROUNDS, not just the heads?

**Status:** closed
**Type:** spike
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10
**Estimated:** 4h (time-boxed; if Spent > 8h, split or re-scope)
**Spent:** ~2h

**Result:** joint possession **69%** (61/89), above the ~50% collapse threshold —
the pilot has a pool. Ground possession 82% top-1, but **grain-confounded** and at
ceiling on top-3, so it may not be reported as "grounds are better known than
heads" [T-048]. Attrition is template-driven, not availability-driven: 165 -> 89
subjects, the opposite of what this ticket predicted.

**Artifacts:**
- agents/shared/findings.md -> "[E-004] joint possession is 69%"
- probes/ground_templates.md, src/ground_templates.py — 26 contestable templates
- agents/engineer/workspace/ground_possession.py, extend_snapshot.py

**Description:**
E-003 measured possession of the **edited head** — the fact CounterFact intends to
overwrite — and found 93% on Llama-3.1-70B. That number is an **optimistic ceiling
for grounds**, and the pilot's validity depends on the gap between them.

Two reasons the gap should be expected to be large:

1. **CounterFact is curated.** Its 34 relations were selected as facts models tend
   to know. Grounds are whatever Wikidata happens to assert about the subject —
   P119 place of burial, P123 publisher, P287 designed by, P931 place served — and
   nobody filtered those for model familiarity.
2. **Grounds are more obscure than heads by construction.** "Where was X born" is
   a common question; "where is X buried" is not.

If ground possession is materially below head possession, the measurable contested
set is the **intersection** of (head held) and (grounds held), which could be much
smaller than either. That number bounds the whole pilot and must be known before
any orphan rate is reported [T-039].

**Method (mirrors E-003 so results are comparable):**

1. From the pinned Wikidata snapshot `data/wikidata/2026-09-10/`, take the
   item-valued statements of the E-002 subjects (`src.wikidata.item_statements` —
   the `wikibase-item` datatype filter that excludes identifiers and media).
2. **Hand-write a prompt template per ground property.** CounterFact supplies
   templates only for its own 34 relations; ground properties have none. Expect
   ~20-40 templates. Follow CounterFact's cloze style, and **avoid its known
   ambiguity bug** — templates must be unambiguous between temporal and locative
   readings ("died at" invited "the age of 90"; see T-044).
3. Distractors: other values attested for the **same ground property**, so
   candidates are type-matched exactly as in E-003.
4. Score constrained rank on **GPT-J-6B** via `src/remote.py` — corrected
   2026-09-10 from Llama-3.1-70B. [E-003b] established the audit model must BE the
   edited model, and GPT-J is the pilot's subject. Carry Llama-70B as a ceiling
   column only. Report top-1/top-3 per ground property and the head-vs-ground gap.
5. Report the **joint** figure: fraction of edits where the head AND at least one
   ground are both held. That is the pilot's usable pool.

**Falsification / decision rule:** if joint possession is below ~50%, the pilot's
effective n collapses and either the edit set must be re-selected for
ground-density, or the domain changes.

**Note on templates.** Hand-written templates are a judgement call in the same
species as `probes/relation_modality.md`. Publish them as a contestable artifact
under `probes/`, not buried in a script [T-027].

**Blockers:** none. Independent of T-045 (which concerns the *edit* target); this
concerns whether grounds exist to be orphaned at all.

**Artifacts:** probes/ground_templates.md; agents/engineer/workspace/;
agents/shared/findings.md
**Closed:** —

---

### E-005 · Possession, re-measured against hard negatives

**Status:** closed
**Type:** spike
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-11
**Estimated:** 4h (time-boxed)
**Spent:** ~5h (over, largely on NDIF batching and three transport/memory fixes)

**Result:** possession 56% / 74% / 79% / 85% across 6B / 8B / 70B / 405B, n=165
each. Monotonic, decelerating, not saturated. Scale buys only the hard relations;
those already known at 6B stay flat. P19 place of birth tops out at 53% even at
405B and GPT-J holds 13%, which reopens [E-003b].

**RCA CORRECTION (2026-09-11):** the RCA below blamed surface-cue contamination
and prescribed the lift control. Measured, naive and possessed differ by only 3-5
points — the prior subtraction corrects almost nothing. The inflation came
overwhelmingly from **10 candidates being too few**, not from base rates. Both
defects were real; the causal story was wrong. The lift control is kept on its
merits (it shows the 4-5% prior baseline is weak, so results are not
template-guessable), not as the fix it was billed as.

**RCA (re-open of E-003/E-003b/E-004, 2026-09-10):**

> E-003 and E-004 measured possession by ranking the true answer against
> distractors sampled at random from the relation's value pool. That design cannot
> separate stored knowledge from surface plausibility: "Darrieux" looks French and
> "Yakuza" looks Japanese, so a model holding no entity knowledge scores well from
> morphology and base rates. E-004 exposed it — top-3 hit 100% on every ground
> property, and a test everything passes separates nothing — but the same defect
> was present in E-003 and I reported that ordering as high confidence anyway. What
> was misunderstood: I treated type-matching (candidates are all places) as
> sufficient control, when the operative confound is *cue-matching* (candidates
> must be equally suggested by the subject's surface form). CLAUDE.md already
> requires a control condition and none was run.

**Description:**
Re-measure head and ground possession with a design that subtracts the prior.

1. **Hard negatives from the model's own prior.** For each item, run the
   **subject-free** prompt (`"___ was born in the city of"`) and take the model's
   top-k predictions as distractors. Ranking the true answer first then requires
   knowledge that beats the model's own base rate — surface morphology and
   frequency are subtracted out by construction, with no hand-curation.
2. **Report lift, not accuracy.** The subject-free ranking is a reported column.
   Possession = improvement the subject provides over no subject at all.
3. **Surface-cue probe.** Substitute a surface-matched entity with a different true
   answer (another French-looking name whose language is not French). Unchanged
   ranking implies the model is reading morphology, not the entity.
4. **25-50 distractors**, so top-3 stops saturating. Report by answer-space size so
   grain is visible rather than confounded [T-048].

Run on gpt2-medium, gpt2-large, gpt-j-6b, Llama-3.1-70B for heads (to re-establish
or refute the scale curve) and on gpt-j-6b for grounds and joint possession.

**What survives from the superseded work and must not be re-derived:**
- The **measurement critique** [T-044] — 75%/61%/12% on identical items, and
  CounterFact's temporal/locative template ambiguity. Compares measures, not
  distractor quality.
- The **attrition analysis** — template coverage, not ground availability, throttles
  the sample (165 -> 89 subjects, median 8 grounds each).
- The **decision** that the audit model must be the edited model [E-003b].

**Falsification:** if lift over the subject-free prior is near zero, the models are
scoring on surface cues and possession as we have defined it is not measurable this
way — which would invalidate the possession gate itself, not merely its numbers.

**Blockers:** none
**Artifacts:**
- agents/shared/findings.md -> "[E-005] possession re-measured"
- agents/engineer/workspace/possession_lift.py, run_e005.sh, lift/*.json
- src/remote.py — score_pairs, adaptive OOM halving, transport classification

**Closed:** 2026-09-11

---

### E-006 · SPIKE: is ROME on Llama-3.1-8B feasible via NDIF?

**Status:** closed
**Type:** spike
**Priority:** high
**Created:** 2026-09-11
**Updated:** 2026-09-11
**Estimated:** 4h (time-boxed)
**Spent:** —

**Description:**
Executes [T-050] option 1. E-005 showed GPT-J holds 13% of P19 and 56% overall,
against Llama-3.1-8B's 40% and 74% — and P19/P20 carry the richest grounds, so the
edit target must move or the pilot probes relations that cannot orphan.

Three unknowns, cheapest first, stop at the first that fails:

1. **Can a weight edit be applied at all on a SHARED, REMOTE model?** NDIF hosts
   one copy of Llama-3.1-8B for all users; we cannot persist a weight change.
   ROME's update is rank-one on an MLP output projection, so its effect is
   expressible as an activation intervention: add `(dW) @ act` at the target layer
   on every forward pass. nnsight supports interventions remotely, and `.edit()`
   for persistent ones. **If this does not work, option 1 is dead and T-050 falls
   back to option 2** (re-select toward GPT-J's strong relations).
2. **Where do the second-moment statistics come from?** ROME needs the covariance
   of MLP keys at the target layer to whiten the update. rome-neighbors has
   `data/stats/gpt2/wikipedia_stats/...mom2_3000.npz` for GPT-2, so the estimate
   was over ~3000 samples. For Llama-3.1-8B: published (EasyEdit and similar ship
   Llama hparams), or computed by us over a Wikipedia sample. Computing remotely
   costs many NDIF calls; locally, 8B in fp16 is ~16GB against 16GB of RAM.
3. **Do layer/hyperparameter choices exist for Llama-3.1-8B specifically?**
   EasyEdit ships configs for llama-7b and llama-2-7b; 3.1-8B has a different
   architecture (GQA, different MLP dims) and may need its own.

**Falsification:** if (1) fails, or if (2) requires compute we do not have, option 1
is not available and T-050 resolves to option 2 with the ground-poverty limitation
reported explicitly.

**Note on scope.** Applying an existing editing method is not "proposing or tuning
an editing method" — the charter bans the latter. We are not improving ROME; we
are using it as the perturbation whose effects we audit.

**Result: FEASIBLE.** Intervention lands (" Paris" -> "acons" perturbing
layers[5].mlp.down_proj) and remote gradients work (norm 17.875), so ROME's
rank-one delta can be applied without persisting a weight change and v* can be
fitted through the frozen remote model. Covariance is 0.82 GB held locally, built
from chunked key collection (0.29 GB for 10k tokens). Layer choice undetermined
but not blocking. Unexpected gain: the edit is re-applied per pass rather than
persisted, giving paired pre/post against identical hosted weights.

**Blockers:** none
**Artifacts:**
- agents/shared/findings.md -> "[E-006] ROME on Llama-3.1-8B via NDIF is feasible"
- agents/engineer/workspace/rome_feasibility.py — the two primitive tests
- agents/engineer/workspace/ndif_health.py — connectivity check

**Closed:** 2026-09-11

---

### E-007 · Package the possession filter

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-13
**Updated:** 2026-09-13
**Estimated:** 4h

**Description:**
The deliverable [T-046, design.md v0.9 lens 9]. A tool run *before* an editing
experiment that reports what fraction of the edit set the model actually holds.

Every component exists — `src/probing.py` (local scoring, constrained rank),
`src/remote.py` (NDIF, batched), `src/typematch.py` (set-level type validation),
`src/data.py` (pinned CounterFact) — so this composes them into something a second
person can run without reading the research.

**Requirements:**

1. **Input is an arbitrary edit set**, not just CounterFact. An `Edit` is
   (prompt, subject, true_answer, relation_id). Ship a CounterFact loader and a
   JSONL path so anyone can bring their own.
2. **Possession = constrained rank + lift** [E-005]: the true answer ranks first
   among N type-matched candidates AND ranks higher with the real subject than
   with the subject replaced by a placeholder. Both arms, per item.
3. **Type-matched candidates** drawn from values attested for the same relation,
   with the set-level coordination diagnostic reported [T-055] — separation only,
   per-candidate flagging is advisory and must be labelled as such.
4. **Config in a file, not argv defaults** (CLAUDE.md). Model, N candidates, seed,
   placeholder, backend. Written to disk *with* the results.
5. **Resumable** — cache per (model, case_id), as the E-005 sweeps do. Three
   separate debugging cycles were cheap only because of this.
6. **Report**: headline held-rate, per-relation breakdown, and the config. Record
   the candidate-set size alongside every number, since absolute levels depend on
   it and only the ordering is robust [E-005 caveats].

**Falsification / done condition:** a second person, given only this repo, can run
the filter on their own edit set and get a held-rate with the config that produced
it. If it only works on CounterFact, it is not the deliverable.

**Explicitly NOT in scope:** orphan rate, propagation, discretion triage. Those
are the parked arc.

**Result:** done condition met — a JSONL edit set with its own relations runs
end-to-end and produces a held-rate with the config beside it. Verified on both
paths: CounterFact (40 items, 52% held, 100% coverage — consistent with E-005's
56%) and bring-your-own (8 capitals, 88% held). Rerun hits cache with no network.

Found by running rather than reading: candidates derived from the edit set scored
12/40 and returned 92%, a 40-point inflation from a silent denominator change —
the exact artifact class this filter detects. Fixed via an explicit reference
vocabulary plus reported coverage. Two further collisions fixed: cache keyed on
model alone would serve a 50-candidate result to an 8-candidate run, and per-model
output names let configs overwrite each other.

**Blockers:** none
**Artifacts:**
- src/possession.py — the filter; src/run_filter.py — CLI
- configs/possession_gptj.json, configs/possession_byo.json
- examples/my_edits.jsonl — bring-your-own format
- README.md — usage and the honest-reading caveats
- agents/shared/decisions.md -> "[E-007] candidates come from a reference vocabulary"

**Closed:** 2026-09-13

---

### E-008 · Mine transitive containment chains

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-14
**Updated:** 2026-09-14
**Estimated:** 4h

**Description:**
Executes [T-058]. Build the deductive ground sets T-041 needs.

A chain is three facts where two entail the third by transitivity of containment:

    inner-1   X  P131  Y      "X is located in Y"
    inner-2   Y  P131  Z      "Y is located in Z"
    outer     X   in   Z      entailed

Editing the outer to Z' contradicts the conjunction of the inners. A coherent model
must retract one. That is a strict contradiction rather than an implausibility —
the first in this project — which is the whole point of choosing this family.

**Method:**
1. Seed from CounterFact subjects whose relation is P131 or P17 (~1,600 records);
   those subjects are places and therefore have containment chains. People and
   works do not.
2. Link to Wikidata via the existing snapshot (read-through, dated, checksummed).
3. Walk P131 twice: X -> Y -> Z. Require X != Y != Z and all three labelled.
4. Emit chains with labels and QIDs, plus prompts for all three facts.
5. Record how many seeds yield a chain, and why the rest fail — attrition is a
   reported quantity here as elsewhere.

**Possession is a gate, not an afterthought [T-058 open point].** A chain where the
model does not hold inner-2 cannot test contraction — there is nothing to retract.
Every chain must pass the possession filter on ALL THREE facts before it enters the
experiment, and the shrinkage is itself worth reporting.

**Deliverable:** probes/containment_chains.md (contestable, with attrition) and the
machine-readable set. NOT the experiment — that is E-009.

**Standing constraint [O-004]:** these license an EXISTENCE claim only. No rate.

**Blockers:** none
**Artifacts:** src/chains.py; probes/containment_chains.md
**Result.** Chains mined: 136 from 200 P19 seeds (68%), attrition recorded. Superseded in use by the gated sets.
**Closed:** 2026-09-20

---

### E-009 · Possession-gate the entailment chains

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 3h

**Description:**
TODO item 4, and the last gate before the experiment. A chain can only test
contraction if the model holds **all three** of its facts:

    inner-1  X born-in Y     — if unheld, nothing to retract
    inner-2  Y in country Z  — if unheld, the entailment is not the model's
    outer    X born-in Z     — if unheld, the edit is meaningless

Any chain failing any of the three is unusable, and dropping them silently would
repeat exactly the denominator bug E-007 shipped and had to fix.

**Method:** reuse `src/possession.py` unchanged — constrained rank against
type-matched candidates plus the subject-free prior arm. Candidate pools come from
the chain set itself per fact position (birth cities for inner-1 and the outer's
subject; countries for inner-2 and the outer's answer), which is a legitimate
reference vocabulary here because all 136 chains share a relation.

**Expect heavy attrition.** GPT-J holds 13% of P19 [E-005], so a P19-anchored
family will lose most chains on inner-1 alone. **If it loses too much that is
itself the finding**, and the edit target moves to Llama-3.1-8B per [O-004] — which
[E-006] already established is editable via NDIF.

Report per-fact-position possession, not just the joint number, so it is visible
*which* leg fails and whether the loss is inner-1 (person obscurity) or inner-2
(city-country, expected to be easy).

**Blockers:** none
**Result (2026-09-15).** Llama-3.1-70B: inner_1 84%, inner_2 92%, outer 57%,
**74/136 = 54% usable** (GPT-J: 35/61/21, 20/136 = 15%). `outer` is the worst leg
at both scales, so the deficit is candidate-pool concentration, not small-model
thinness. The three legs are NOT independent — joint is 3.27x the independence
prediction at GPT-J, 1.25x at 70B, ordered by shared subject. Full write-up in
agents/shared/decisions.md [E-009].

**Artifacts:** agents/engineer/workspace/gate_chains.py;
probes/chains_gated_meta-llama_Llama-3.1-70B.json;
probes/chains_gated_EleutherAI_gpt-j-6b.json;
logs/gate_chains-llama-3.1-70b-2026-09-15.log;
agents/shared/decisions.md -> "[E-009] Result"

**Closed:** 2026-09-15


---

### E-010 · Adversary — check a claim against our own record

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 4h

**Description:**
The measured failure mode of this project: **every error was already refuted by an
artifact we had written and not read.** `probes/relation_modality.md` predicted the
containment failure; [T-044] predicted the template bug; `definitions.md`
declaration 4 predicted the star/chain confusion. The record was accurate and went
unconsulted.

The cost of that falls on the human, who currently has to sit and dry-run every
claim by hand. This makes that pass cheap.

**What it is:** a retriever with an opinionated index over the project's own
artifacts. Given a claim, it surfaces prior statements that bear on it, with where
they live and what authority they carry.

**What it is NOT: a judge.** It does not decide whether a claim is wrong. It puts
the relevant prior statement in front of a person, which is the same discipline the
project applies to models — *show the structure, never the ranking* [T-034].

**Design:**
1. Index claim-bearing statements only — findings entries, `**Decision:**` lines,
   numbered declarations, probe-table rows, thread `**Answer:**` fields — not every
   line of prose.
2. Carry **authority**: `definitions.md` is binding; `decisions.md` records
   commitments; `probes/*.md` are contestable data; findings carry confidence.
3. Carry **superseded** state. Three findings entries are marked SUPERSEDED; a
   naive grep would resurface withdrawn claims as authoritative.
4. Expand query terms through `agents/shared/glossary.md` — which the agentic
   template specifies and this project never created. "containment" must reach
   `P131` or the containment miss is not catchable.
5. Run over a whole file (`--file draft.md`) as well as a single claim, so a
   write-up can be checked in one pass.

**Falsification — it must catch all three documented misses:**
- "containment gives a strict contradiction" -> P131 is mutable
- "outer template asks for the country" -> the T-044 ambiguity finding
- "the graph gives us grounds" -> declaration 4 / the star-not-chain thread

If it misses any, the retrieval is not good enough to reduce anyone's reading.

**Result: falsification criterion met** — all three documented misses are caught.

    "containment gives us a strict contradiction"
      -> definitions.md:92  "Never write 'contradiction' where 'implausibility'
                             is meant"  [BINDING, rank 1]
    "the graph gives us grounds"
      -> definitions.md:31  declaration 4, the graph is a normative audit spec
                            [BINDING, rank 1]
    "the outer template asks for the country"
      -> probes/ground_templates.md:12  "No temporal/locative ambiguity"
                            [MEASURED, rank 4]

**Five bugs found by testing against those cases rather than by reading:**
1. Glossary entries wrap across lines, so the `_aliases:` trailer sat on a
   continuation line the parser skipped — it loaded 16 terms and expanded nothing.
2. Expanding both query and document double-counted: one concept match credited
   six shared tokens, so every probe-table row tied and ranking fell back to
   authority. Fixed by collapsing aliases to concepts before comparing.
3. Rule-based depluralisation returned "templat" for "templates" (the `es` rule
   fires first). Fixed by generating candidates and testing each against the map.
4. Twenty near-identical probe rows filled every slot. Fixed by capping hits per
   source — a tool meant to save reading must not spend slots on duplicates.
5. Excluding all tension words from matching hid the binding rule about
   "contradiction". Split into POLARITY (boost only) and LOADED (boost + match).

**Known limitations, not fixed:**
- The template case lands at rank 4, not rank 1. Single-concept claims tie easily
  and the tie-break is weak.
- `--file` mode flagged 33 claims on a 1,200-word draft at `--min-score 2.0`.
  Usable as a checklist, too noisy to read end-to-end. Needs a better floor.
- Retrieval is lexical. A claim that contradicts the record in different
  vocabulary will be missed, and the glossary is the only bridge.

**Artifacts:**
- src/adversary.py — indexer, glossary expansion, concept collapsing, scorer
- agents/shared/glossary.md — 16 terms; the template specified this file and the
  project had never created it

**Closed:** 2026-09-15

---

### E-011 · Is the `outer` deficit answer surface form, or real?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 1h

**Description:**
[E-009b] established that the `outer` possession deficit is two strings — United
States 6/40 and United Kingdom 2/14 held, against France 13/13, India 5/5, Japan
4/4. Grouped, article-taking names hold at 15% (n=54) and bare names at 84%
(n=82). The leading explanation is that `"X was born in the country of"` followed
by `" United States"` is ungrammatical where `" France"` is fine — i.e. we score a
Wikidata label rather than a natural continuation. That is a hypothesis, not a
finding, and this ticket decides it.

**Method.** Re-run the possession gate on the same 136 `outer` items, same model
(Llama-3.1-70B), same seed, same 28-country pool, changing exactly one thing: how
every candidate in the pool is rendered.

- Condition **bare** — Wikidata labels verbatim. This is the [E-009] baseline, 57%.
- Condition **natural** — the same countries in the form a sentence would use:
  `the United States`, `the United Kingdom`, `the Netherlands`, `the Philippines`,
  `the Czech Republic`, `China` for `People's Republic of China`. Every other
  label is unchanged, so 23 of 28 candidates are byte-identical across conditions
  and the contrast is isolated to the five that are not.

Rendering is applied to the WHOLE pool, never to the true answer alone — scoring
`" the United States"` against bare-form distractors would advantage it for a
reason that has nothing to do with the hypothesis.

**Confound, and why the existing measure controls it.** Prefixing `" the"` adds a
high-probability token, and `score_pairs` returns mean log-prob per continuation
token, so the natural form could win for reasons of length normalisation rather
than knowledge. The `held` criterion already guards this: it requires the true
answer to rank first with the real subject AND to rank higher than it does with
the placeholder. A form that wins on prior alone drives `rank_prior` to 1 and
fails the lift test. No new control is needed; state this in the result.

**Falsification, pre-stated.**
- *Confirm:* `natural` recovers US/UK to roughly the bare-name rate (~84%), and
  bare-name countries are unchanged. Template defect; cheap to fix; usable chains
  rise toward the 102/136 ceiling computed in [E-009b].
- *Deny:* US/UK stay low under `natural`. The model genuinely does not hold these,
  which is the more interesting result and needs its own explanation — the
  candidates are then Canada (60%) and Germany (25%), which take no article and
  which the surface-form story never explained.
- *Null:* both conditions move together, indicating the re-run is not measuring
  what the labels say. Treat as a bug, not a result.

**Deliverable.** One table: held rate by condition × answer-string class
(article-taking vs bare), plus the recomputed usable-chain count.

**Result (2026-09-15).** Deny on the headline, and the rank data reframes it.
`natural` moves rank-1-with-subject on article-taking names from 21% to 69% — the
surface-form effect is real and large — but the placeholder ranks the same answer
first at the identical 69%, so 31 of those 40 items fail the lift test. The two
criteria have no common operating point for a modal answer. Full entry in
agents/shared/decisions.md [E-011]. Opens E-012 (paired-subject control).

**Blockers:** none
**Artifacts:** agents/engineer/workspace/surface_forms.py;
results/E-011-surface-forms-meta-llama_Llama-3.1-70B.json;
agents/shared/decisions.md -> "[E-011] Result"
**Closed:** 2026-09-15

---

### E-012 · Paired-subject control: does the model track WHICH subject?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 3h

**Description:**
[E-011] showed the possession measure has no operating point for an answer that is
the modal answer for its relation. The placeholder control asks *"does the subject
matter at all"*, and a modal answer defeats that by construction: under a natural
rendering, `"[X] was born in the country of the United States"` is the top
completion whether or not `[X]` means anything, so the lift test rejects 31 of 40
items the model demonstrably ranks correctly.

The replacement asks the discriminating question instead: **does the answer prefer
THIS subject over other real subjects whose answer differs?**

**Design — WHY.** Without this, `possession.py` silently reports "not possessed" for
the most common answer in every relation, and every rate it produces is biased by
however concentrated that relation's answer distribution happens to be. That is a
defect in the deliverable, not in an experiment.

**Design — WHAT.** The measure becomes two criteria over one score matrix:

- **row test (unchanged):** `a_i` ranks first among candidates `C_i` under prompt
  `p_i`. "Given this subject, is the true answer the best candidate?"
- **column test (new):** among foil prompts `p_j` where `a_j != a_i`, the fraction
  with `s(a_i | p_i) > s(a_i | p_j)`. "Given this answer, is this the right
  subject?" This is an AUROC over (true pair vs false pair) and is reported graded,
  never only thresholded — consistent with declaration 6 on graded `orphan`.

A modal answer scores high under every prompt, so the row test passes and the old
lift test fails. The column test is indifferent to the answer's overall level and
asks only whether it is *higher where it should be*. That is what makes it defined
where the old control is not.

**Design — HOW, and the cost.** `run()` already computes the full score vector over
candidates for the subject arm and collapses it to a rank. Persisting the vector
makes the column test cost **zero additional remote calls**. The matrix is dense
wherever the pool is smaller than `n_candidates` — true for `outer` and `inner_2`
(28 countries), where every prompt scores every candidate. For `inner_1` (78 cities,
50 sampled) it is ~64% dense; report per-item foil coverage and treat an item with
too few foils the way `skipped` is already treated, never by silently averaging over
fewer.

**Confound.** Foil prompts differ from `p_i` in subject *and* in sentence length,
token count, and subject frequency. Restricting foils to the same relation and the
same template controls template and length; subject frequency is not controlled and
must be stated as a known threat, with [T-061]'s prominence numbers as the handle
for checking it later.

**Baseline to beat.** Chance is 0.5. The dumbest explanation for a high column score
is that the answer is simply rare — so report the column statistic broken out by
answer frequency class, the same split that exposed [E-009b].

**Falsification, pre-stated.**
- *Confirm:* modal answers (US, UK) show column scores well above 0.5 at 8B, so the
  model does track which subject, and [E-011]'s rejected items are recovered.
- *Deny:* modal answers sit at ~0.5. The model genuinely does not discriminate, the
  old measure was right to reject them for the wrong reason, and the chain set is
  smaller than [O-006] assumed.
- *Null:* column scores are high for everything including foils by construction —
  indicates the foil set is wrong, not a result.

**Scope.** v1 is the measure plus a report at 8B on the existing 136 chains.
DEFERRED: retrofitting published numbers, any frequency claim, and the paired
2x2 symmetric variant.

**Cache compatibility.** `ItemResult` gains fields, so old cache records cannot be
read into the new shape. Add a schema version to `FilterConfig.fingerprint`. The
project has already shipped two cache-collision bugs ([E-007], and the fixed-path
gate output); a shape change that reuses a key would be the third.

**Deliverable.** One table: row-test pass rate, column-test mean, and combined held
rate, by answer-frequency class, at 8B.

**Result (2026-09-15).** Confirm, with an interaction nobody predicted. Usable
chains over the 2x2 at 8B: bare+placeholder 58, bare+paired 59, natural+placeholder
59, natural+paired **78**. Neither fix alone moves anything; together +20. On `outer`
modal answers row goes 25% -> 68%. 78/136 at 8B beats the 74/136 that 70B gave under
the old instrument. Full entry in agents/shared/decisions.md [E-012].

**Blockers:** none
**Artifacts:** src/possession.py; src/discrimination.py;
agents/engineer/workspace/{run_e012,test_discrimination}.py;
results/E-012-discrimination-{bare,natural}-meta-llama_Llama-3.1-8B.json;
agents/shared/decisions.md -> "[E-012] Result"
**Closed:** 2026-09-15

---

### E-013 · The edit — does editing a conclusion ever retract its grounds?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 12h

**Description:**
The experiment this project is named for. Every prior ticket was a gate on it.

**The setup.** For each of the 78 chains usable at Llama-3.1-8B ([O-006], [E-012]):

    inner_1   X was born in the city of Y      (P19, rigid)
    inner_2   Y is located in the country of Z (P17)
    ------------------------------------------------- entails
    outer     X was born in the country of Z

Edit `outer` so the model asserts `Z'` instead of `Z`. Both premises still entail
`Z`. Unlike [E-002]'s evidential grounds, this family admits **no satisfying world**:
birth is rigid, so the model must give up `inner_1` or `inner_2`, or hold a set that
is jointly inconsistent. The question is not how often. It is **whether contraction
occurs at all** — an EXISTENCE claim, per the standing constraint in [O-004].

**Gate 0 — the covariance, now costed rather than assumed.** ROME's update needs
`C⁻¹k*` where `C` is the second-moment matrix of keys at the edited layer. Measured
from the model configs, not recalled: Llama-3.1-8B `d_mlp` = **14336**, so `C` is
**0.82 GB fp32** (70B would be 28672 → 3.29 GB, matching [O-005]). Resolve in this
order and record which was used:
1. A published precomputed statistic for this model. Do not assume one exists —
   ROME's distributed stats cover GPT-2 and GPT-J.
2. Accumulate `kkᵀ` remotely and transfer in column blocks (14336 × 1024 ≈ 59 MB per
   block, 14 blocks) rather than one 0.82 GB download. Cache to disk; it is a
   one-time cost and the edit is re-run many times against it.
3. **`C = I`** — the unwhitened rank-one update.

**RESOLVED 2026-09-15 → path 3, and it is not a fallback.** All 14 of EasyEdit's
shipped ROME configs set `mom2_adjustment: false`, including the ROME paper's own
gpt2-xl and gpt-j-6B, and the code path makes that exactly `C = I`. We run what the
reference toolkit runs, and we call it *"ROME as configured by EasyEdit"* rather than
*"ROME"*. Full entry in agents/shared/decisions.md [E-013] Gate 0. The 0.82 GB
collection is not needed. The confound below is unchanged and the control edit stays
mandatory.

**The confound that could fake the whole result.** A diffuse editor moves the grounds
by collateral damage, which looks exactly like contraction.

**AMENDED 2026-09-15 after the n=1 smoke test — the mandated control is not enough.**
The smoke test moved `inner_1` (shares the subject) hard and left `inner_2` (does not)
completely inert, which is what subject-keyed leakage looks like, and the post-edit
top-1 for *"born in the city of"* was `' Germany'` — a type error, not a revision.
A different-subject control cannot catch this, because an edit on another subject
never touches our subject's key direction. Three controls, all required:

1. **Same-subject control** — edit an unrelated property of the SAME subject to
   comparable magnitude. Only `inner_1` movement in EXCESS of this is a candidate.
   This is now the load-bearing control.
2. **Different-subject control** — as mandated by CLAUDE.md, for generic instability.
3. **Type-coherence read** — is the post-edit top-1 for `inner_1` a city or a country?
   A type error is leakage; a type-correct city in the new country is the signal.

See agents/shared/decisions.md [E-013] smoke test. A result reported without all three
is not a result.

**Metrics** — as fixed in CLAUDE.md, no new ones:
- KL pre→post over the next-token distribution at the final position.
- log-prob of the pre-edit correct answer (sign-free: did it give up *anything*
  where coherence demanded it give up *something*).
- log-prob of the injected object (rising where it should not = leakage).
- entropy change (rising = confusion, not reassignment).
- Multi-token answers teacher-forced, summed. Never position one alone.

**Falsification, stated in advance:**
- *Confirm:* on some chains, a premise's log-prob falls under our edit and not under
  the control. Contraction occurs. The existence claim lands.
- *Deny:* premises are unmoved beyond the null across all 78. Editors expand and
  never contract — which is [E-002]'s "editors expand; they never contract" promoted
  from a reading to a measurement, and is a publishable negative.
- *Null:* premises move as much under the control as under ours. Generic instability;
  the instrument is not sensitive enough at this edit magnitude, and that is a
  statement about the method, not the model.

**Deliverable.** The two-panel figure named in CLAUDE.md and one number: how many of
78 chains show a premise retraction exceeding the control's high percentile.

**Scope.** IN: 78 chains, 8B, ROME (or the stated fallback), both controls, single
phrasing. DEFERRED: multi-phrasing measurement (Part II), 70B, any rate claim,
sequential edits.

**Blockers:** none
**Artifacts:** src/edit.py; agents/engineer/workspace/run_e013.py; results/E-013-*.json
**Result.** The editor was built and the smoke test reshaped the control design. Result in decisions.md [E-013] gate 0 and [E-013] smoke test.
**Closed:** 2026-09-20

---

### E-014 · Scaled edit: where does the probability go, across countries and cities?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 6h

**Description:**
[E-013]'s pilot (n=12) found that log-prob drop on `inner_1` is the WRONG statistic:
the real edit and the same-subject control drop the old answer by comparable amounts
(mean 8.50 vs 6.82 nats), but the real edit sends the mass to a city *in the target
country* — Edinburgh→Hamburg for Germany, Paris→Santiago for Chile — while the control
sends it somewhere incoherent (Glasgow, "Ha", "The"). **Destination, not magnitude, is
the measurement.**

Two defects in the pilot's readout must be fixed before scaling, not after:

1. **Truncation.** Top-1 was first-token argmax, so "Mad", "G", "New" are unreadable.
   Rank FULL city names from a type-matched pool instead.
2. **Unverified membership.** "Hamburg is in Germany" was my inspection, not a lookup.
   Verify with Wikidata `P17` for every city in the pool.

**Pool coverage is the subtle one.** The `inner_1` candidate pool is the 78 cities that
appear as chain answers. If the coherent destination for a target country is not in
that pool, the model cannot express it and we would score a coherent relocation as a
failure — the [E-011] mistake exactly. The pool is therefore the chain cities UNION the
capital (`P36`) of every country in the target pool.

**Design.**
- N = all 77 usable chains that carry an occupation, covering ~28 target countries.
- Per chain: real edit (`outer` → counterfactual country) and same-subject control
  (occupation), both as in [E-013].
- Readout per condition: rank the full city pool at `inner_1`; record top-1, and
  whether `P17(top-1) == target country`.
- **Data controls, which is what makes this more than an anecdote:**
  - **Capital bias.** Santiago, Helsinki, Stockholm, Bern and London are all capitals.
    If the model simply emits the target country's capital, the relocation is coherent
    but shallower than "chose a plausible birth city". Report the capital rate.
  - **Placebo country.** For each chain, also test membership against a RANDOM other
    country. That is the null rate for "lands in country X" and it is what makes the
    real rate interpretable.
  - **Per-country breakdown.** The effect must not be carried by two or three
    countries. Report the rate by target country, the split that caught [E-009b].
  - **Original-country retention.** Does `inner_2` stay inert at scale (pilot: −0.02)?

**Falsification, pre-stated.**
- *Confirm:* real-edit `inner_1` lands in the target country at a rate far above both
  the control and the placebo. Coherent revision of the defeasible premise.
- *Deny:* real and control land in the target country at similar rates. The pilot's
  pattern was a small-n artifact.
- *Null:* neither lands in the target country once full names are ranked — the pilot's
  apparent coherence was an artifact of first-token argmax.

**Resumability is a requirement, not a nicety.** 154 edits x 25 steps is ~2h of remote
work and three runs were killed by memory pressure today. `v*` deltas cache to disk
keyed by case_id and config; a kill must cost wall-clock only.

**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e014.py; results/E-014-*.json;
data/wikidata/<date>/snapshot.json.gz (city P17, country P36)
**Result.** 67% into the target country against 5% baseline and control. Result in decisions.md [E-014].
**Closed:** 2026-09-20

---

### E-015 · Does relocation require an inference, or only country-flavoured content?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 3h

**Description:**
Resolves the dispute in agents/shared/disputes.md [E-014]. [E-013] found `inner_1`
relocating to a city in the edited country and I read it as the model revising the
defeasible premise. A cheaper account predicts the same data: `v*` makes `k*`-keyed
inputs emit a country-valued vector, `inner_1` shares the subject so its key is
similar, and a Germany-valued residual stream promotes Germany-associated tokens —
German cities among them. No inference.

**The discriminating variable is the RELATION, holding subject and target fixed.**

| edit | licenses "born in a German city"? | content |
| --- | --- | --- |
| `X was born in the country of` → Germany | **yes**, deductively | Germany |
| `X works in the country of` → Germany | **no** | Germany |

Work country is independent of birth city — nobody infers a birthplace from an
employer's country — while the *value vector's content* is the same country in both
arms. That is exactly the confound isolated.

Chosen over `"X died in the country of"`, which was the first idea: place of death is
only natural for dead subjects and the chain set mixes living and dead, so the probe
would be malformed for a subset — the [E-014] "born in the city of Wisconsin" defect
in a new costume.

**Method.** Same 71 clean chains. Target countries read from
`results/E-014-destination-*.json` rather than redrawn, so the two arms are matched
per chain and no RNG drift can desynchronise them. Same `v*` procedure, same clamp,
same readout: rank the 75-city pool at `inner_1`, record top-1 and whether
`P17(top-1) == target country`.

**Falsification, pre-stated.**
- *Deny the revision reading:* the work-country edit relocates `inner_1` into the
  target country at a rate statistically indistinguishable from the birth-country
  edit. Then relocation is country-content leaking into any same-subject probe, the
  "coherent revision" reading dies, and the honest result is a clean mechanistic one
  about what rank-one edits do.
- *Support it:* birth-country relocation materially exceeds work-country relocation.
  Something relation-specific survives, and the AGM-entrenchment framing in
  `definitions.md` declaration 6 becomes measurable rather than assumed.
- *Null:* neither relocates. Contradicts [E-013]; treat as a bug in E-015, not a
  result.

**Report the difference, not two rates.** The quantity is the paired per-chain gap
between arms; reporting the arms separately invites reading a difference that the
pairing does not support.

**Blockers:** E-014 (supplies the matched target countries)
**Artifacts:** agents/engineer/workspace/run_e015.py; results/E-015-*.json
**Result.** DENY — paired gap +0.0 pp, McNemar p = 1.000. Result in decisions.md [E-015].
**Closed:** 2026-09-20

---

### E-016 · The whitened editor — does a targeted update produce a non-zero gap?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-18
**Updated:** 2026-09-18
**Estimated:** 8h

**Description:**
[E-015] returned a paired gap of **+0.0 pp** — a work-country edit relocates the
birthplace exactly as often as a birth-country edit, so the relocation carries no
inference. Everything in [E-013]–[E-015] used `C = I`, which [E-013] measured as a
destructive regime (≈8 nat drops on unrelated same-subject facts). A more targeted
editor is the one place a genuine inference effect could still hide, and the ROME paper's
method section is built on the `C⁻¹` term that EasyEdit's fourteen configs disable.

**GATE — measure anisotropy before building anything.** ROME's update uses
`u = C⁻¹k*`. If the key distribution at layer 5 is near-isotropic then `C⁻¹ ∝ I`, `u ∝ k*`,
and whitening is a no-op — in which case [E-015]'s null is not an artifact of `C = I` and
this ticket closes without an experiment. Collect ~2k key vectors, take the spectrum, and
report the condition number and the participation ratio. Cheap, and it can kill the ticket.

**Feasibility, costed rather than assumed.** `C` is 14336² = **0.82 GB fp32** against 16 GB
of RAM, and forming plus inverting it is the naive route. Avoid it: with a sample matrix
`K` (N × d) and ridge `λ`, Woodbury gives

    (λI + KᵀK/N)⁻¹ k*  =  (1/λ)[ k* − Kᵀ (λN I + KKᵀ)⁻¹ K k* ]

so only `KKᵀ` (N × N) is ever formed. At N = 4096 that is 67 MB, not 820 MB, and the
14336² matrix never exists. Download cost is `K` itself at fp16: N × 14336 × 2 bytes,
≈ 117 MB at N = 4096, chunked and cached to disk.

**Corpus, and a deliberate divergence.** ROME collects `mom2` over Wikipedia. We collect
over the CounterFact prompt distribution already on disk. That is *domain-conditional* and
arguably better matched to what we edit, but it is **not** what ROME does, and any artifact
must say so. Record the corpus and N alongside every number, as with `k` and out-degree.

**Method, if the gate clears.** Re-run [E-015] unchanged with `u = C⁻¹k*` in place of
`u = k*`. Same 42 chains, same targets, same pool, same paired readout.

**Falsification, pre-stated.**
- *Confirm:* the whitened editor produces a materially non-zero paired gap. [E-015]'s null
  was an artifact of the unwhitened update, and the inference reading returns — for the
  whitened editor only.
- *Deny:* the gap stays at zero. The null is robust to the editor's targeting, which is a
  much stronger negative than [E-015] alone, and it says the displacement mechanism is not
  a consequence of a blunt update.
- *Null (gate):* the spectrum is near-isotropic, whitening is arithmetically a no-op, and
  the question dissolves.

**Result (2026-09-18).** DENY, and the null turns out to be analytic. Paired gap +0.0 pp
at the primary λ and 42/42 identical destinations, despite the whitened update being ~20x
more selective on held-out keys. Cause: ROME's `u·k*` normalisation pins the coefficient
to exactly 1 at the subject's last token, and any probe sharing that prefix has an
identical key there under causal attention — so the full delta lands regardless of `C`.
No choice of covariance could have changed [E-015]. Full entry in
agents/shared/decisions.md [E-016].

**Blockers:** none
**Artifacts:** src/whiten.py; agents/engineer/workspace/{collect_keys,run_e016,
why_whitening_null,scale_invariance,coeff_profile}.py;
results/E-016-whitened-meta-llama_Llama-3.1-8B.json;
agents/shared/decisions.md -> "[E-016] Result"
**Closed:** 2026-09-18

---

### E-017 · Is the leakage a property of the subject, or of prompt FORM?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-19
**Updated:** 2026-09-19
**Estimated:** 3h

**Description:**
Tests [T-074], the one threat [E-016] left standing. [E-016] established that ROME's
`u·k*` normalisation pins the update coefficient to **exactly 1** at the subject's last
token, and that any probe sharing the edit prompt's prefix has an identical key there
under causal attention — so the full delta lands regardless of `C`.

Our probes share that prefix **by construction**: both *"X was born in the country of"*
and *"X was born in the city of"* begin with the subject. A probe where the subject
appears LATER has a different key at its subject-last token, because that key depends on
the preceding context. So nothing is pinned, and the theory predicts less displacement.

| form | subject position | prefix shared with edit prompt? | predicted |
| --- | --- | --- | --- |
| **early** (current) `{} was born in the city of` | token 1 | yes | pinned at 1.0 → full delta |
| **late** `The city where {} was born is` | after 3 tokens | no | not pinned → attenuated |

**The control that makes this interpretable.** Changing phrasing changes expressibility
([E-011]: rank-1 on modal answers moved 21% → 69% on spelling alone). A late-subject probe
that simply fails would look exactly like "no leakage". So **baseline possession on the
late form is measured first, and the comparison is restricted to chains where BOTH forms
rank the true city first pre-edit.** Without that restriction this experiment cannot
distinguish its own hypothesis from a broken probe.

**Method.** Same 42 chains, same cached `v*` deltas and `k*` from [E-014] — no new
optimisation, the edit is unchanged and only the probe's form varies.
1. Baseline-rank both forms over the 75-city pool; keep chains where both hold.
2. Coefficient profile on the late form: is any position pinned at 1.0?
3. Post-edit readout on both forms; report the **paired** per-chain difference.

**Falsification, pre-stated.**
- *Confirm:* the late form shows no pinned coefficient and materially less relocation into
  the target country. The leakage is a property of prompt FORM, not of the subject, and
  [E-016]'s analytic account is validated on a case it did not construct.
- *Deny:* the late form relocates as strongly. The pinned coefficient is not the mechanism,
  [E-016]'s explanation is wrong, and the displacement travels some other way.
- *Null:* too few chains hold the true city at baseline on the late form. Report the
  coverage and treat the experiment as unrun rather than as a negative.

**Result (2026-09-19).** The relocation half hit the pre-stated NULL — the late probe
holds the true city in only 8/42 chains at baseline against 29/42 for the early form, so
the comparison is UNRUN rather than negative. The coefficient half answers T-074 anyway
and refutes the hypothesis: moving the subject later attenuates the coefficient by ~7%
(mean 0.93), not the order of magnitude predicted, while a DIFFERENT RELATION sharing the
prefix scores exactly 1.000. Same-subject leakage is structural. Full entry in
agents/shared/decisions.md [E-017].

**Blockers:** none
**Artifacts:** agents/engineer/workspace/{run_e017,coeff_forms}.py;
results/E-017-form-meta-llama_Llama-3.1-8B.json;
agents/shared/decisions.md -> "[E-017] Result"
**Closed:** 2026-09-19

---

### E-018 · The different-subject floor — does [E-017]'s claim survive its missing control?

**Status:** closed
**Type:** implement
**Priority:** **highest** — it can retract a published claim
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 1h

**Description:**
Tests [T-076], surfaced while designing [T-075] (see design.md Part IV).

[E-017] claims: *any prompt containing the subject receives 93–100% of the edit
vector at the subject's last token.* Every control behind it is a **same-subject**
control — different relation, late clause, possessive, long preamble, all at
0.93–1.00. The project's only non-subject datum is `inner_2` (*"Paris is located
in…"*), a different entity type answering a different question, not a matched
control.

**Nothing has measured a different person, same relation, same form.** Until it is,
"any prompt *containing the subject*" is not separated from "any prompt".

**Why this is not a formality.** [E-016] measured the layer-5 key second moment at
participation ratio **26.5 of 2048** — the keys occupy an effectively
~26-dimensional manifold. Vectors confined to a narrow subspace have substantial
cosine **by construction**, so the different-subject floor may be high for reasons
having nothing to do with the subject. [E-016] is also this project's standing
demonstration that an argument about key geometry can be confidently wrong.

**Implementation.** A variant of `agents/engineer/workspace/coeff_forms.py`, which
already computes exactly the right quantity — `(k @ kstar) / (kstar @ kstar)` at
`subject_last_index`. One form is added:

- `different subject`: the **early (edit form)** template
  `"{} was born in the city of"`, filled with the subject of a *different* chain,
  scored against **this** chain's `k*`.

Pair subjects by rotation (`subjects[(i + 1) % n]`) so every chain contributes once
and no chain is scored against itself. Assert `other_subj != subj` per chain and
fail loudly if it collides.

Keep the five [E-017] forms unchanged in the same run — layer 5 must reproduce the
published means (1.000 / 1.000 / 0.935 / 0.934 / 0.925) or the harness is wrong and
the new number means nothing. **That reproduction is the correctness gate; check it
before reading the control.**

Same 16 chains, same `E014_kstar_L5_s1538.pt` cache, `LAYER` unchanged.

**Outcomes, stated before the run:**

- **Confirm** — different-subject mean is low (≲0.3) and well separated from every
  same-subject form. [E-017] stands as published; the floor is now measured rather
  than assumed.
- **Deny** — different-subject mean is high (≳0.7). [E-017]'s claim, the E-016
  section of `web/blog/2026-09-15-five-days.mdx`, and that post's standfirst are
  **wrong rather than narrow**, and the correction is a retraction. The pinning
  would not be subject-keyed at all.
- **Null** — intermediate (0.3–0.7). The claim narrows to a graded one: subject
  match raises the coefficient but does not solely determine it, and the published
  wording needs replacing with the measured gap.

**Do not re-run a failure and read the second outcome as a diagnosis** — per
[O-007], NDIF rejects roughly half of all traces node-dependently. Go through
`retrying()`. One completed run is the result.

**Blockers:** —

**Artifacts:**

- agents/engineer/workspace/coeff_other_subject.py
- logs/coeff_other_subject-2026-09-20-103132.log
- agents/shared/decisions.md → "[E-018] Result: the different-subject floor is 0.082"

**Closed:** 2026-09-20 — **CONFIRM.** Different-subject mean 0.082 against 0.958
same-subject, gap 0.877, distributions non-overlapping (max 0.153 < min 0.483). Gate
passed: all five [E-017] forms reproduced to within 0.001. [E-017] stands with its
floor measured rather than assumed. The anisotropy prediction that motivated the
ticket was wrong, and is recorded as such.

---

### E-019 · The layer sweep — is the pinning a layer-5 fact or a ROME fact?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 1h

**Description:**
Runs [T-075] per design.md Part IV, whose first job was discharged early by [E-018].

[E-017]/[E-018] establish that at **layer 5** any prompt containing the subject
receives 93–100% of the edit vector while a different subject receives 8%. Layer 5
is what EasyEdit's `llama3-8b` ROME config edits. If the subject key becomes
context-sensitive deeper in the network, an editor targeting a later layer would
leak less across probe forms, and "structural" narrows to "structural at the layer
this config happens to edit".

**Method.** No cache needed, and no edit. For each layer `L`, `k*(L)` is the key at
the subject's last token of the **edit-form** prompt at `L` — which is one of the
six probes already in the batch. So the early form is 1.000 by construction at every
layer, and every other form is read against it. One trace per chain saving
`down_proj.input` at all eight layers; the coefficient is
`(k @ kstar) / (kstar @ kstar)` as in [E-017]/[E-018].

**Layers:** 0, 3, 5, 8, 12, 16, 24, 31 of 32. Denser early where ROME configs
cluster, two deep anchors. A shape test, not a per-layer claim.

**Forms:** the five from [E-017] plus [E-018]'s different-subject control, which is
retained as a **per-layer floor** rather than as the point of the run.

**Gate.** Layer 5 must reproduce [E-018]: same-subject forms near
0.999/0.935/0.934/0.924/0.999 and different-subject near 0.082. `k*(5)` is computed
fresh here rather than loaded from `E014_kstar_L5_s1538.pt`, so agreement also
validates that substitution. Check before reading any other layer.

**Outcomes, stated before the run.** Let `c_form(L)` be the mean over the four
non-trivial same-subject forms and `c_other(L)` the different-subject floor.

- **Confirm** — `c_form ≥ 0.9` at every layer with `c_other` low throughout. The
  structural claim generalises and ROME's layer choice is incidental to it.
- **Deny** — `c_form` falls below ~0.7 at deeper layers while `c_other` stays low.
  The claim narrows to early layers, and that is a fact about where an editor leaks
  less. Useful either way.
- **Null** — `c_form` falls **and `c_other` rises toward it**. The measure is losing
  discrimination with depth rather than the key becoming context-sensitive. This is
  why the floor is carried at every layer.

**This measures delivery, never effect.** A coefficient is how much of the edit
vector arrives, not whether it changes the answer — [E-016] showed those come apart.
Nothing here licenses a claim about what editing at layer 24 would do.

Per [O-007], go through `retrying()`; do not re-run a failure and read the second
outcome as a diagnosis.

**Blockers:** —

**Artifacts:**

- agents/engineer/workspace/layer_sweep_t075.py
- logs/layer_sweep_t075-2026-09-20-104950.log
- agents/shared/decisions.md → "[E-019] Result", "[O-008] Correction to a correction"
- web/blog/2026-09-15-five-days.mdx — published claim corrected

**Closed:** 2026-09-20 — **DENY at depth, NULL at 31.** Gate passed: layer 5
reproduces [E-018] to ±0.001 from a freshly computed `k*`. The claim splits — the
prefix-sharing case is 1.000 at all eight layers (algebra, layer-invariant), while
reformulated probes decay 0.98 → 0.52 from layer 0 to 24, so [E-017]'s form-robustness
is an early-layer fact. Layer 31 is unreadable: `c_other` 0.669 against `c_form` 0.699.
Surfaced [O-008], which partially reinstates a constraint [O-007] over-retracted.

---

### E-020 · Is the depth decay a direction change or a magnitude change?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 1h

**Description:**
Runs [T-077]. [E-019] measured the decay — reformulated probes fall 0.98 → 0.52
from layer 0 to 24 — and explains nothing about it.

**The decomposition is the whole experiment.** The coefficient is not a cosine:

    c = (k · k*) / (k* · k*) = (|k| / |k*|) · cos(k, k*)

So `c` can fall two ways, and they are different claims about the network:

- **cos falls** — the subject-position key *points somewhere else* at depth. The
  representation at that position is no longer determined by the subject tokens
  alone. Consistent with context being mixed in progressively.
- **norm ratio falls** — the key still points the same way, but is smaller relative
  to `k*`. A magnitude effect, and it would mean the direction survives while the
  delivered amount does not.

Both may fall. Pre-stating the split is the point.

**This distinguishes direction from magnitude, which is one level below mechanism.**
A falling cosine rules out a pure magnitude account; it does not *demonstrate*
attention mixing, which would need the attention patterns themselves. Say so in the
write-up rather than letting "cos fell" become "context is mixed in".

**Method.** Re-run [E-019]'s sweep — same 16 chains, same 8 layers, same 6 forms,
saves unrolled per [O-008] — logging three numbers per (chain, layer, form) instead
of one: `c`, `cos(k, k*)`, and `|k| / |k*|`. Assert
`abs(c - cos * norm_ratio) < 1e-4` per cell; the identity is algebra, so a
violation means the harness is wrong.

**Gate.** `c` must reproduce [E-019] — layer 5 at 0.935 / 0.934 / 0.924 / 0.082,
layer 24 at 0.524 / 0.564 / 0.444. Check before reading any decomposition.

**The different-subject probe carries information here too.** Its rise at layer 31
(0.082 → 0.669) is currently unexplained. If that rise is **cos** rising, distinct
subjects are converging on a shared direction near the output — a representational
collapse, and a better account of why layer 31 lost discrimination than "noise". If
it is the **norm ratio**, it is a scaling artifact. Pre-stated because it is the
kind of result that is easy to reframe after the fact.

**Outcomes:**

- **Direction** — cos falls materially (≲0.7 by layer 24) while the norm ratio stays
  near 1. The subject key genuinely reorients with depth.
- **Magnitude** — cos stays high (≳0.9) while the norm ratio falls. The direction
  survives; only the delivered size does not.
- **Both** — each contributes. Report the share of the decay attributable to each,
  since `log c = log(norm ratio) + log cos` makes that additive.

**Blockers:** —

**Artifacts:**

- agents/engineer/workspace/decompose_t077.py
- logs/decompose_t077-2026-09-20-*.log
- agents/shared/decisions.md → "[E-020] Result"

**Closed:** 2026-09-20 — **DIRECTION.** cos falls 0.984 → 0.471 from layer 0 to 24
while `|k|/|k*|` never leaves 0.97–1.24, so magnitude carries none of the decay and
in fact drifts against it. Gate passed; the identity held in all 768 cells. Layer
31's different-subject rise is cosine (0.660 with ratio 1.009) — representational
convergence, not a scaling artifact, which upgrades [E-019]'s "noise". Spawns
[T-078]: a falling cosine rules out magnitude but does not demonstrate attention
mixing.

---

### E-021 · Is the subject-token delta necessary and sufficient for the relocation?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 4h

**Description:**
Runs [T-067], the largest methodological hole in this project and the one §6 of the paper
names first. Everything from [E-013] to [E-020] is **behavioural**: we vary an input and
read an output. We can say the model *behaves as if* the subject-token delta drives the
relocation. We cannot say it *causes* it.

[E-016] established analytically that the coefficient at the subject's last token is
exactly 1, and [E-019]/[E-020] measured its decay elsewhere. Neither shows that position
is where the work happens — a coefficient of 1 at a position that contributes nothing
would produce the same numbers.

**The intervention.** The edit is applied as `Δout[t] = c(t) · δ`, where `c(t)` is the
coefficient at position `t`. Mask `c` by position and re-read the destination:

| arm | positions receiving δ | tests |
| --- | --- | --- |
| **A · full** | all | reproduces [E-014]: 67% into the target country |
| **B · only** | the subject's last token alone | **sufficiency** |
| **C · except** | every position *but* the subject's last | **necessity** |
| **D · none** | — | baseline, 5% |

This is causal in the sense available here: we intervene on the mechanism, not on the
input, and ask what the outcome depends on.

**Falsification, pre-stated.**
- *Confirm:* **B ≈ A** and **C ≈ D**. The subject-token delta is sufficient on its own and
  necessary — removing it alone destroys the relocation. The [E-016] account is causal,
  not merely consistent.
- *Deny necessity:* **C ≈ A**. Other positions carry the relocation; the pinned
  coefficient is real but not where the work happens, and §4.1 of the paper overstates.
- *Deny sufficiency:* **B ≈ D**. The subject token alone does nothing; the effect is
  distributed and the single-position story is wrong.
- *Null:* both B and C sit between A and D with no separation. The effect is genuinely
  distributed, no position is privileged, and the honest report is that the analytic
  result does not localise.

**Gate before reading the result.** Arm A must reproduce [E-014]'s 67% on the same 42
chains. A masking implementation that silently changes the full-edit result invalidates
the other three arms, and the difference would be invisible without the check.

**Method.** Same cached `v*` and `k*`; only the application mask varies. One scoring call
per arm per chain, 75-city pool, `P17` membership as in [E-014]. No new optimisation.

**Confound.** The subject's last token is also the position where `c` is largest, so
removing it removes the most mass. Report total masked coefficient mass per arm so a
"necessity" result can be read against how much was removed — otherwise C ≈ D is
unsurprising for the wrong reason.

**Result (2026-09-20).** Both. Gate passed (A = 67%, matching E-014). Sufficiency: B = 69%
against A = 67%, p = 1.000. Necessity: arm E, with the removed magnitude restored to the
surviving positions, reaches 12% against a 5% baseline. The decisive comparison is B vs E —
less mass at the right position beats more mass everywhere else, 29 vs 5, 24 discordant
pairs and none reversed, p < 0.0001. Full entry in agents/shared/decisions.md [E-021].

**Blockers:** none
**Artifacts:** src/remote.py; agents/engineer/workspace/run_e021.py;
results/E-021-positions-meta-llama_Llama-3.1-8B.json;
agents/shared/decisions.md -> "[E-021] Result"
**Closed:** 2026-09-20

---

### E-022 · Does the possession cell survive rephrasing? (T-062 and T-064)

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 4h

**Description:**
Runs [T-062] and [T-064] in one pass — they are the same measurement read two ways.

`notes/definitions.md` declaration 1 is **binding**: *a fact is a behavioral unit defined
by its probe set.* Every possession number in this repo was measured with **|probe set| =
1**, and [E-011] showed one template's surface form moved the usable-chain count further
than an order of magnitude of model scale did. So what we have called possession of a fact
is possession of a (fact, template) pair.

**Templates come from ParaRel, not from us.** <Cite> `arXiv:2102.01017` covers `P19` with 13
patterns. **Seven are usable**; the other six place `[Y]` prenominally — *"[X] was a
[Y]-born person"* — and this project's scorer appends the answer as a continuation, so a
mid-sentence slot cannot be scored without changing the measure. Excluded on that ground
alone, decided before any scoring. Our own published form is carried as an eighth so the
existing numbers have a referent inside the set.

**Method.** 60 `inner_1` facts × 8 templates. Per pair, the [E-012] measure: row test
(true answer ranks first) and column test (AUROC against foil prompts **at the same
template**, so template is held fixed inside each comparison). Cell = HELD / PRIOR / MUTE /
ABSENT.

**T-062 — the reading that decides whether a fact-level statistic exists.** Per fact, the
distribution of its 8 cells. Report the **modal-cell share**: 1.0 means the label is a
property of the fact; 0.125 means it is noise over templates.

**T-064 — MUTE.** Its rate over all 480 cells, and whether it tracks answer frequency as
the label-form account predicts.

**Falsification, pre-stated.**
- *Confirm a fact-level predicate:* modal-cell share concentrates high (≥0.75 for most
  facts). Possession is a property of the fact, single-template probing is a noisy
  estimator of it, and the existing numbers are biased but not meaningless.
- *Deny:* the share sits near chance. **No fact-level predicate exists**, every
  per-fact possession number in this project and in the editing literature is a
  template-level quantity reported under a fact-level name, and that is the more important
  result.
- *Null:* too few facts hold under *any* template for the distribution to be read. Report
  coverage and treat as unrun.

**Confound.** Templates differ in difficulty as well as in phrasing, so a fact that is
ABSENT under seven and HELD under one may be a template effect, not fact instability.
Report the per-template cell distribution alongside the per-fact one; a template that is
ABSENT for nearly everything is a bad probe, not evidence about facts.

**Result (2026-09-20).** T-062 CONFIRM: modal-cell share mean 0.923, median 1.000, 65% of
facts identical across all eight templates, chance 0.125. A fact-level predicate exists.
T-064: MUTE 27% of cells but tracking RARITY (35% rare vs 5% common), the opposite of the
surface-form account — both causes are real and pool concentration decides which appears.
Full entry in agents/shared/decisions.md [E-022].

**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e022.py; results/E-022-cells.json;
agents/shared/decisions.md -> "[E-022] Result"
**Closed:** 2026-09-20

---

### E-023 · Does the closed pool hide what the model would actually say? (T-066)

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 4h

**Description:**
Runs [T-066], and it is aimed at this project's own headline. Every number here comes from
**ranking a closed, type-matched pool**. That is what makes the measure controlled, and it
is also a choice: an answer outside the pool is invisible by construction rather than by
evidence.

[E-014] reports that an edit relocates the birth city into the target country **67%** of
the time. That was measured by ranking 75 cities. If the edited model, left to generate
freely, says something else — a city outside the pool, or not a city at all — then part of
that 67% is the pool forcing a choice the model would not have made.

**Method.** Greedy-decode four tokens from the `inner_1` prompt, baseline and under the
real edit, and compare against the ranked answer. `.all()` is unavailable in this nnsight
build, so the edit is applied per decoding step in its own trace — a verified mechanism
rather than a new one.

**Three quantities.**
1. **Pool coverage** — does the free generation begin with a pool city at all?
2. **Rank/generate agreement** — does the pool's argmax match what the model generates?
3. **The headline under generation** — does the edited model *generate* a city in the
   target country, and at what rate against the ranked 67%?

**Falsification, pre-stated.**
- *Confirm the pool:* generation lands in-pool for most facts and agrees with the ranked
  answer. The closed pool is a faithful proxy and [E-014]'s 67% stands as reported.
- *Deny:* generation frequently leaves the pool, or disagrees with the rank. The measure
  forces choices the model would not make, and every rate in this project — including the
  67% — describes behaviour under constraint rather than behaviour.
- *Null:* generations are degenerate under both conditions (punctuation, repetition), so
  the comparison has nothing to bite on. Report and treat as unrun.

**Confound.** Greedy decoding is itself a choice, and a model can rank an answer first
while sampling something else. This measures greedy generation against rank, not "what the
model would say" in general — say so rather than generalising.

**Result (2026-09-20).** DENY the pool's faithfulness. Free generation relocates into the
target country 30/30 against ranking's 67%. The pool cannot express most of the model's
answers, so ranking falls back to the highest-prior item — which is E-014's Washington
attractor. Paired results (E-015, E-016, E-021) are unaffected because both arms share the
pool. Full entry in agents/shared/decisions.md [E-023].

**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e023.py; results/E-023-generation.json;
agents/shared/decisions.md -> "[E-023] Result"
**Closed:** 2026-09-20

---

### E-024 · Does editing one attribute of a subject disturb its unrelated attributes?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 3h

**Description:**
The experiment that would turn a reframe into a result. [E-016] and [E-021] established
that the update reaches every prompt beginning with the edited subject, by arithmetic and
causally. If that is right, then what an edit reaches is a **subject**, and the relation
`v*` targeted is incidental — "editing a fact" would be a user-level description the
mechanism does not honour.

One prior datum points this way and was never followed: [E-013]'s smoke test found that
editing Vlaminck's **occupation** dropped his **birth-city** probe by ~8 nats. This runs
the reverse direction and adds a control.

**Design — a relatedness gradient, not a single contrast.**

| probe | relation to a birthplace edit |
| --- | --- |
| `By profession, X is a` → occupation | **unrelated**. No inference runs from birth country to profession. |
| `X is a citizen of` → citizenship | **plausibly related**. Birth country is evidence for citizenship. |

Same two probes on a **different, unedited subject** are the control.

**Measure: paired log-probability, no pool.** [E-023] showed that ranking a closed pool
undercounts badly and that only paired contrasts survive it. So the quantity here is
teacher-forced log P(true answer) on the same probe with and without the edit — same item,
same string, differenced. No candidate set, nothing to exclude.

**Falsification, pre-stated.**
- *Confirm "edits reach subjects":* both attributes of the edited subject fall
  substantially; the control subject's do not. The unit the editor operates on is the
  subject, and relation-selectivity is not a property of the update.
- *Deny:* the edited subject's unrelated attributes are unmoved. The update is
  relation-selective after all, [E-021]'s result is about birthplace probes specifically,
  and the reframe collapses.
- *Graded:* citizenship falls materially more than occupation. The update is partly
  selective — the strongest single result available here, because it would mean semantic
  relatedness modulates an effect the arithmetic says should be uniform.
- *Null:* the control subject also falls. The edit is not subject-keyed at all and
  something upstream is wrong; treat as a bug, not a finding.

**Confound.** Occupation and citizenship differ in how strongly the model holds them, so a
larger absolute drop may reflect a higher starting point. Report the baseline log-prob
beside every delta, and prefer the **control-differenced** drop over the raw one.

**Result (2026-09-20).** GRADED. Control-differenced drop: occupation +1.60 nats,
citizenship +6.58, control 0.03/0.05. An unrelated attribute of the edited subject does
fall, so the edit reaches the subject — but citizenship falls 4x harder, so the damage is
not uniform while E-021 showed the reach is. Confound flagged: type overlap and semantic
relatedness are entangled in these two probes. Full entry in agents/shared/decisions.md
[E-024].

**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e024.py; results/E-024-attributes.json;
agents/shared/decisions.md -> "[E-024] Result"
**Closed:** 2026-09-20


---

### E-025 · Type overlap or semantic relatedness? The language probe

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 2h

**Description:**
[E-024] found a birthplace edit damages citizenship 4x harder than occupation, and two
different accounts fit those two points:

- **type overlap** — the injected value is a country, so country-valued probes compete
  with it and others do not;
- **semantic relatedness** — citizenship is *about* origin, so it is disturbed.

They are entangled because citizenship is both. **Language separates them.** `P1412` is
semantically related to country of origin — where you were born predicts what you speak —
but its answers are *languages*, not countries.

| probe | type-matched to the edit? | semantically related? |
| --- | --- | --- |
| citizenship | **yes** (country) | yes |
| **language** | **no** (language) | **yes** |
| occupation | no (profession) | no |

**Prediction under each account.**
- *Type overlap:* language patterns with **occupation** (≈1.6 nats).
- *Semantic relatedness:* language patterns with **citizenship** (≈6.6 nats).
- *Both contribute:* language lands between them, and the gap sizes the two effects.

**Method.** Identical to [E-024] — same 37 subjects where labelled, same paired log-prob
with no candidate pool, same different-subject control, with a language probe added.
`P1412` labels are unfetched and must be pulled into a dated snapshot first.

**Confound.** Language answers are far lower-entropy than occupation answers (most of these
subjects speak one of a handful of languages), so a floor effect could suppress the drop.
Report the baseline beside the delta and treat a language baseline near zero as
uninterpretable rather than as a null.

**Result (2026-09-20).** TYPE OVERLAP, on endpoints. Occupation and language finish 0.04
nats apart (−6.16, −6.20) after starting 3.65 apart; citizenship finishes 2.95 below the
floor at −9.10. Two effects: uniform suppression of everything about the subject, plus
extra displacement only where the answer type matches the injected value. The run's own
drop-based headline said "semantic relatedness" and was wrong — retracted in the entry.
Full entry in agents/shared/decisions.md [E-025].

**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e025.py; results/E-025-language.json;
agents/shared/decisions.md -> "[E-025] Result"
**Closed:** 2026-09-20

---

### E-026 · Does the delivered coefficient predict displacement, or only bound it?

**Status:** split
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 6h
**Thread:** T-079

**Description:**

Every result from [E-016] to [E-021] measures **delivery** — what fraction of the edit
vector arrives at a position. None measures whether delivery predicts **effect**. [T-075]
named this gap in its own scope paragraph and [E-016]'s scale test is the reason it cannot
be assumed: the mapping from coefficient to destination is not linear.

It is also the one dimension never varied. **An edit has been applied at layer 5 and
nowhere else in the entire record** — [E-019] varied the layer for *coefficients* only.

**The prediction, and why it is a dissociation rather than a level shift.**

From [T-075]'s measured table:

| probe form | coefficient at L5 | coefficient at L20 |
| --- | ---: | ---: |
| subject-initial (shares the edit prefix) | 1.000 | **1.000** (analytic) |
| possessive (subject moved later) | 0.962 | **0.615** |

If the coefficient governs effect, editing at L20 instead of L5 must damage
subject-initial probes **identically** and possessive probes **measurably less**. No other
account on the table predicts that pattern: a "deep edits are weaker" account predicts a
uniform reduction, and a "coefficient is delivery only" account predicts no systematic
difference at all. The interaction is the claim; neither main effect is.

**Design — 2 (edit layer) × 2 (probe form), within subject.**

- Edit layer: **5** (EasyEdit's `llama3-8b.yaml`, and the whole existing record) and
  **20**. L20 is taken from [E-019]'s already-published table, which was run before this
  ticket existed — record that, because "you picked the layer with the lowest coefficient"
  is the first thing a hostile reader says.
- Probe form: `"{} was born in the city of"` (subject-initial) and
  `"The birthplace of {} is the city of"` (possessive). **Possessive, not late clause** —
  [E-017] found the late clause fails at baseline in 34 of 42 chains, and an unanswerable
  probe cannot show a drop.
- Subjects: the [E-014] set, same 37-ish chains [E-024]/[E-025] used, so results are
  comparable to the existing entries.
- Control: a different subject, same probes, same edit — as in [E-025].

**Measure.** Teacher-forced `log P(true city)`, same probe with and without the edit,
differenced, then control-differenced. **No candidate pool** — [E-023] showed ranking a
closed pool undercounts badly and only paired contrasts survive it.

**Pre-stated outcomes.** Let `D[form, layer]` be the control-differenced drop.

- **CONFIRM** — the coefficient predicts effect: `D[possessive, L20]` is at least **40%
  smaller** than `D[possessive, L5]` (the coefficient ratio 0.615/0.962 = 0.64 predicts
  ~36%), *while* `D[initial, L20]` and `D[initial, L5]` differ by **less than 20%**.
- **DENY** — the coefficient bounds delivery and does not predict effect:
  `D[possessive, L20]` and `D[possessive, L5]` differ by less than 20%. Every claim from
  [E-016] onward then becomes a claim about delivery only, and the paper must say so.
- **UNIFORM** — not a null, a different finding: both forms drop by a similar *proportion*
  at L20. That is "a deep edit is weaker", it refutes the dissociation, and it must be
  reported as refutation rather than dressed up as partial support.
- **INFEASIBLE** — if the L20 edit does not take at all (see the efficacy gate below), the
  run is uninterpretable and is reported as a feasibility result. Do not read it as DENY.

**Efficacy gate, mandatory, run first on 4 chains before the full batch.** Compute `v*` at
L20 for four subjects, apply, and check `log P(injected target)` on the edit prompt itself
rises comparably to L5. If the L20 edit moves the target by less than half of what L5 does,
stop and report INFEASIBLE — a failed edit cannot dissociate anything. Log the gate result
at `INFO` either way.

**Confounds and controls.**

1. *Edit efficacy differs by layer.* The subject-initial arm **is** the normaliser: it is
   pinned at exactly 1.000 at both layers by [T-075]'s analytic result, so equal damage
   there is the evidence the two edits are matched. Unequal damage there is itself a
   result — it would mean a coefficient of 1 does not guarantee equal effect.
2. *`v*` differs between layers.* `compute_v_batch` re-optimises per layer, so the deltas
   are not the same vector. Report `RankOneEdit.norm_ratio` (‖Δv‖/‖k*‖) per layer beside
   every number. A large norm difference is a live alternative explanation and must be
   stated, not buried.
3. *Probe forms have different baselines.* **Report endpoints, not only drops.** This is
   the [E-025] lesson at full force: that run's drop-based headline was wrong and had to be
   retracted, and the confound had been named in its own ticket while the code still
   computed on drops. Naming a confound is not controlling for it — the reporting code must
   print post-edit levels first.

**Baseline (lens 7).** The dumbest explanation that produces a smaller possessive drop at
L20 is that the L20 edit is weaker at everything. That is defeated *only* by confound
control 1, and by nothing else in this design. If the subject-initial arm also weakens,
there is no result here regardless of what the possessive arm does.

**Scope.** IN: 2 layers, 2 forms, one model, one relation, delivery *and* effect measured
on the same subjects. DEFERRED: intermediate layers (T-079 does not need a curve to answer
yes/no), other relations (T-081), other models (T-080), and any statement about which layer
an editor should target.

**Out of scope, explicitly.** This ticket asks whether the coefficient is a predictor. It
does **not** recommend an edit layer. [T-075] already recorded "a deeper edit layer would
leak less to reformulated probes" as a method-design observation and declined to chase it;
CLAUDE.md scopes this project to measuring what existing editors do. No artifact from this
ticket may recommend a layer, and the write-up must carry that sentence.

**Deliverable.** One 2×2 table of control-differenced drops with post-edit endpoints
alongside, and one number: the interaction contrast
`(D[poss,L5] − D[poss,L20]) − (D[init,L5] − D[init,L20])`.

**Method notes.** `compute_v_batch(m, specs, layer=20)` already takes the layer — no new
optimiser code. `score_pairs(..., edit=(layer, k_star, denom, delta_v))` already takes the
layer. Cache `v*` and `k*` at L20 under `E026_deltas_L20_s{seed}.pt` / `E026_kstar_L20_*`
so a stall resumes. Logging per the standing rule: `logging` with levels, a `FileHandler`
under `logs/`, config on line one, never piped through `tail`/`head`.

**Result (2026-09-20).** The experiment FAILED and its own pre-registration caught it.
The subject-initial arm moved 92%, far outside the 20% matching band, so the two edits were
not matched and the design cannot speak to its question. [T-079] is unanswered.

**A headline was stated and withdrawn.** The table invited "identical delivery, 13x
difference in effect, therefore the coefficient does not predict effect". [E-026b] then
scored both continuations on the edit prompt and showed the layer-20 edit does ~87% of the
target promotion and only ~19% of the belief displacement (true-answer drop 1.81 vs 9.70).
There is no held-fixed delivery to reason from; the lens-7 baseline this ticket wrote down
("the dumbest explanation is that the L20 edit is weaker at everything") won.

**RCA — the mandatory gate measured the wrong quantity.** It gated on *lift on the injected
target* and passed at 0.98. That criterion cannot distinguish an edit from a logit nudge: a
real edit raises the target AND suppresses the true answer, since they compete for one
slot. The gate should have gated on belief displacement. It was also too small — at n=4 it
reported +9.37/+9.52 where n=42 gives +6.16/+7.09.

**Surviving EXISTENCE claim.** ROME's own Efficacy Score is 76.2% at layer 20 (100% at
layer 5, 0% at baseline), and **24 of 42 layer-20 edits pass ES while leaving the true
answer within 3 nats of where it started** — versus 8/42 at layer 5. An edit the field's
standard metric reports as working can leave the belief essentially intact. Per [O-004]:
existence, never a rate.

**Confound stated, not buried.** EasyEdit's 25 steps / lr 0.5 are *layer-5*
hyperparameters, used unchanged at layer 20. The weak displacement is plausibly
under-optimisation rather than anything about depth. This blocks every depth claim and does
not touch the existence claim.

**Status:** split
**Split into:** E-028
**Reason:** the design was sound and its gate was not; the question survives the failure and
needs edits matched on belief displacement rather than target lift.
**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e026.py, run_e026b.py; results/E-026-gate.json,
E-026-depth.json, E-026b-edit-prompt.json; logs/run_e026-2026-09-20-182859.log;
agents/shared/decisions.md -> "[E-026] Result"
**Closed:** 2026-09-20 (split)

---

### E-028 · Re-run the depth comparison with edits matched on BELIEF DISPLACEMENT

**Status:** split
**Split into:** E-028a, E-028b, E-028c, E-028d
**Reason:** Recorded 2026-10-15, late. The question needed a step sweep, a budget match, a
matched-propagation run and a budget control before it could be answered; each became its
own ticket with its own pre-stated outcomes and its own result file, and §4.4 is written
from [E-028d]. The parent was left `open` for three weeks while its children closed, which
made the ledger report finished work as outstanding.

**And only two of the four children have tickets.** [E-028b] and [E-028d] do;
`E-028a-step-sweep.json` and `E-028c-matched-propagation.json` exist with no ticket behind
them, which is Discipline Rule 7 broken twice — work begun and a ticket never written.
Recorded here rather than repaired by back-dating two tickets, because a ticket written
after its result is a ticket that cannot have pre-stated anything, and the whole value of
the format is that the outcomes were fixed first. The runs are real and their numbers are
in `results/`; what is missing is the evidence that their outcomes were pre-registered, and
that evidence cannot be manufactured now.
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 5h
**Thread:** T-079, T-084

**Description:**

[E-026]'s question is untouched: does the delivered coefficient predict displacement, or
only bound it? Its design failed for one recorded reason — it matched the two edits on
*target lift*, which a logit nudge also achieves. Everything else in that ticket stands and
should be reused verbatim: the 2x2, the probe forms, the control subject, the paired
no-pool measure, the endpoints-before-drops reporting.

**The one change.** Match on **belief displacement** before comparing propagation.

- Gate criterion becomes: the deep edit must suppress `log P(true answer)` on the edit
  prompt to within 30% of what the shallow edit achieves (measured 9.70 nats at layer 5).
  Target lift is reported but decides nothing.
- Gate n rises from 4 to **12**. The n=4 gate overstated both arms by ~2.5 nats.

**Two routes to a matched deep edit; try them in this order.**

1. **Optimise harder at depth.** EasyEdit's 25 steps / lr 0.5 are layer-5 hyperparameters.
   Sweep steps in {25, 50, 100} at layer 20 on 6 subjects and plot true-answer suppression
   against step count. If 100 steps reaches layer 5's 9.70, the deep edit was merely
   under-optimised and the comparison becomes runnable. **Report the step count beside
   every number** — "ROME at layer 20" and "ROME's layer-5 config at layer 20" are
   different claims and this ticket must never conflate them.
2. **Match by selection, if optimisation will not close the gap.** Keep only subjects whose
   deep edit clears the displacement bar, and take the *same* subjects at layer 5. This
   loses n and sacrifices nothing else; per [O-004] the claim was existence-shaped anyway.

**Pre-stated outcomes.** Unchanged from [E-026], and now reachable:
CONFIRM if possessive weakens >=40% while subject-initial holds within 20%;
DENY if possessive moves <20%; UNIFORM if both weaken similarly (refutation, not partial
support); INFEASIBLE if no route produces a matched deep edit — which would itself be
worth reporting, since "ROME cannot be matched at depth" is a fact about the method.

**Falsification of route 1 specifically.** If suppression is flat in step count, the deep
edit is not under-optimised and the depth story is real rather than a hyperparameter
artifact. State that outcome; do not quietly move to route 2.

**Adversary.** "You kept tuning until the answer came out." Pre-empted by fixing the
displacement bar (30% of 9.70) and the step grid ({25,50,100}) **before the sweep runs**,
and by reporting every cell of the grid rather than the one that cleared the bar.

**Deliverable.** [E-026]'s 2x2 table plus a matching column showing each arm's belief
displacement on the edit prompt, so a reader can verify the arms are matched rather than
take it on trust.

**Blockers:** none
**Artifacts:** _(on close)_
**Closed:** split 2026-10-15 — children carry the artifacts

---

### E-027 · Is the pinning a ROME fact or a Llama-3.1-8B fact?

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 2h
**Thread:** T-080

**Description:**

Every coefficient in this project is measured on `meta-llama/Llama-3.1-8B`. The paper's
central claim — *any probe beginning with the edited subject receives the full,
unattenuated edit vector at the subject position, at every layer, for any `C`* — is derived
from ROME's `u·k*` normalisation and causal attention, neither of which is
architecture-specific. It should therefore reproduce on any decoder-only transformer, and a
reader will ask why we never checked.

This is **confirmatory by design and cheap by design**, and worth running for exactly that
reason: one measurement on a different architecture converts an assumed generality into a
measured one. It is not a place to spend more than the stated budget.

**Method.** [E-019]'s harness (`layer_one.py` / `layer_sweep_t075.py`) pointed at a second
model. Coefficient only — **no edits, no `v*` optimisation, no NDIF write path**. Read `k`
at the subject's last token for each probe form, and `k*` from the edit form, and report
`c = (k·k*)/(k*·k*)` per form per layer.

- Second model: GPT-J-6B, which is the model CLAUDE.md names as the working target and the
  model ROME's own paper reports. Different tokenizer, different `d_mlp`, different depth —
  all of which the derivation says should not matter.
- Same five probe forms as [E-019], same different-subject floor probe, same subject set
  where the names exist in both.
- Layers chosen proportionally to depth, not by absolute index — GPT-J has 28 layers to
  Llama's 32, so compare fractions of depth, and say so in the table header.

**Pre-stated outcomes.**

- **CONFIRM:** prefix-sharing probes return exactly 1.000 (within float tolerance, |c−1| <
  1e-4) at every layer measured. This is the analytic half and admits no partial credit —
  anything else means the derivation or the implementation is wrong, and that is the more
  interesting outcome.
- **The empirical half is genuinely open.** The reordered-probe decay (0.95 → 0.58 with
  depth) is *not* derived, and there is no reason it must transfer. A different decay
  profile is a finding, not a failure, and narrows [E-019] the way [E-019] narrowed
  [E-017]. State the Llama profile beside the new one rather than asking whether it
  "replicates".
- **Different-subject floor:** [E-018] measured 0.082 at layer 5. Report the second model's
  floor without a threshold — a high floor would mean the anisotropy argument that
  motivated [T-076] is model-dependent, which is worth knowing.

**Confounds.**

1. *Tokenisation.* `subject_last_index` re-tokenises the truncated prompt rather than
   assuming a position, so it transfers — but verify on three subjects by logging the
   decoded token at the computed index before trusting a single coefficient. A silent
   off-by-one here produces plausible wrong numbers, which is the dangerous kind.
2. *Layer indexing.* GPT-J's block attribute path differs from Llama's
   (`transformer.h[i].mlp.fc_out` rather than `model.layers[i].mlp.down_proj`). Resolve it
   once, assert the read tensor's shape against the config's `d_mlp`, and fail loudly on
   mismatch rather than reading the wrong module.
3. *Subject familiarity.* A subject GPT-J does not know may have a degenerate key. Restrict
   to subjects that pass a possession check on the second model, or report the coefficient
   without a possession filter and say which — do not mix.

**Scope.** IN: one second model, coefficient only. DEFERRED: any edit on the second model,
any behavioural readout, any third model.

**Deliverable.** One table, the [E-019] table's shape, with a second model's rows beneath
the first's — and one sentence saying whether the analytic claim is a ROME claim.

**Result (2026-09-20).** CONFIRM on the analytic half, exactly: worst deviation from
1.000 across all 216 prefix-sharing cells is 0.00e+00 on GPT-J-6B. The pinning is a claim
about ROME's normalisation and causal attention, not about Llama.

Two things the headline would have hidden, both read from the components:

- **The empirical half also transfers**, which was not expected and is worth more than the
  confirm. Compared at matched depth fraction, both models decay from 1.0 at the input to
  ~0.5 by two-thirds depth and flatten. The decay is not derived; two architectures on the
  same relative schedule is a stronger statement than either alone.
- **The different-subject floor does NOT transfer.** [E-018]'s 0.082 becomes 0.155 at the
  edit layer and never drops below it, reaching 0.524 at the final layer — *above* that
  layer's late-clause coefficient, so the coefficient stops discriminating subjects
  altogether. "Different subjects are near-orthogonal" is a Llama statement. The margin at
  the layer ROME actually edits is clean on both (0.87 vs 0.71), so the headline claim is
  untouched; only its generality across depth is model-dependent.

**Confound not controlled, stated rather than mixed:** the subjects were possession-gated
on *Llama* and run here with no GPT-J filter. Unfamiliar names could share a generic
direction and inflate the floor by construction, so the floor finding is PLAUSIBLE, not
CONFIRMED. Spawns [T-082]. It does not touch the analytic result — 1.000 is exact whether
or not the model knows the subject. Also spawns [T-083] (both floors are non-monotonic
with a minimum near the edit layer).

**Status:** closed
**Blockers:** none — independent of [E-026] and runnable concurrently.
**Artifacts:** agents/engineer/workspace/run_e027.py; results/E-027-second-model.json;
logs/run_e027-2026-09-20-182210.log; agents/shared/decisions.md -> "[E-027] Result"
**Closed:** 2026-09-20

---

### E-029 · Does ROME's Efficacy Score predict propagation at the STANDARD edit layer?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 1h
**Thread:** T-085

**Description:**

[E-026] failed as a depth experiment and left one observation its failure does not touch:
**24 of 42 layer-20 edits pass ROME's Efficacy Score while leaving the true answer within
3 nats of where it started**, and propagate to nothing. That was filed as a depth
observation, which is the weaker and more confounded form.

The same cell already exists at **layer 5**, in data on disk: **8 of 42**. Layer 5 is
EasyEdit's shipped configuration — the edit the field actually runs. If the relationship
holds there, the finding stops being about depth entirely and becomes a general caveat on
ES, which is both more defensible and the form that belongs in §6 of the write-up.

**No new measurement.** Joins two existing artifacts over the same 42 subjects:
`results/E-026b-edit-prompt.json` (belief displacement and ES margin on the edit prompt)
and `results/E-026-depth.json` (propagation to the two city probes). Zero NDIF cost, which
is why it runs now, while [E-028a] holds the remote budget.

**The sharp test — two predictors, one outcome.** Per subject, at layer 5:

- outcome: **propagation** = control-differenced drop on the subject-initial city probe
- predictor A: **belief displacement** = drop in `log P(true answer)` on the edit prompt
- predictor B: **ES margin** = `log P(target) − log P(true)` on the edit prompt

ES is a *threshold* on predictor B. The claim is not that ES is arbitrary — it is that B
and A come apart while A and the outcome do not.

**Pre-stated outcomes.**
- **CONFIRM** — ES is a poor proxy for propagation: displacement correlates with
  propagation at Spearman rho >= 0.6 **while** ES margin correlates at rho < 0.3. The two
  predictors must be compared on the same subjects; a strong displacement correlation alone
  says nothing about ES.
- **DENY** — both correlate comparably (within 0.2 of each other). ES then carries the same
  information as displacement and there is no caveat to report; the layer-20 observation
  was about depth after all, and [T-085] closes.
- **NULL** — neither correlates (both rho < 0.3). Propagation is driven by something
  neither predictor captures, which is a different and larger finding about [E-021]'s
  mechanism and would need its own ticket.

**Confounds and controls.**
1. *Subject-level strength.* A well-known subject might yield both a stronger edit and more
   propagation, inflating every correlation. **Control:** compute the same two correlations
   with baseline `log P(true answer)` partialled out, and report the partial alongside the
   raw. If the raw survives and the partial does not, the finding is about familiarity.
2. *Shared measurement.* Displacement and propagation both measure "the true answer went
   down" under the same edit, on different prompts. A correlation between them is expected
   and is not the claim — **the claim is the CONTRAST between predictors A and B.** Report
   both correlations or neither.
3. *Range restriction.* At layer 5 ES is 100% and the margin has a narrow spread (+2.29
   minimum). A weak rho for B may be restriction of range rather than absence of
   information. **Report the margin's spread beside its correlation**, and treat a narrow
   spread as a limit on what can be concluded rather than as evidence for the claim. This
   is the adversary's best attack and it must be answered in the entry, not waved at.

**Deliverable.** One scatter with two panels sharing a y-axis (propagation), x = each
predictor, with the ES threshold drawn as a vertical line; and one sentence naming which
predictor a practitioner should read.

**Scope.** Layer 5 only, 42 subjects, one relation, one model. Existence per [O-004] — no
rate is claimed about ROME as normally run.

**Result (2026-09-20).** DENY, cleanly. Belief displacement and ES margin correlate with
propagation at **0.419 and 0.425** — a gap of 0.006 against a pre-stated Deny band of 0.2.
ES carries the same information displacement does, so there is no ES caveat at layer 5.
The joint cell exists (8/42) and is inert: those edits propagate 8.86 nats against 10.51
for the rest.

Familiarity was controlled and does nothing (partials move <0.015). The range-restriction
worry this ticket called "the adversary's best attack" **did not materialise** — the ES
margin spans 22.15 nats — and that mis-prediction is recorded rather than dropped.

**Consequence, and it costs a claim rather than a number.** [E-026]'s 24/42 observation
stays a statement about weak or deep edits and must NOT be promoted to a general critique
of ES. It was headed for §6 in the more general form; this says that form is unsupported.
An hour of joining existing files killed a line that would have cost days.

Opens [T-086]: at rho ~0.42 neither predictor explains most of propagation's variance, and
nothing in the record says what does.

**Status:** closed
**Blockers:** none.
**Artifacts:** agents/engineer/workspace/run_e029.py; results/E-029-es-vs-propagation.json;
logs/run_e029-2026-09-20-215433.log; agents/shared/decisions.md -> "[E-029] Result"
**Closed:** 2026-09-20


---

### E-028b · Match layer 20 to layer 5 by BUDGET, then run the propagation comparison

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 3h
**Thread:** T-079, T-084

**Description:**

[E-028a] showed matching by *saturation* is the wrong target: neither layer had saturated
at 100 steps, and layer 5 gained as much as layer 20 over the grid, so the control refused
the verdict. Matching by **budget** needs neither layer to saturate and is what [E-028]
actually requires — two edits with **equal belief displacement**, whatever step count each
needs to get there.

**Step 1 — find the matching budget.** Layer 5 at 25 steps displaces **6.26 nats** on the
six-subject set. Layer 20 reaches 4.47 at 100 steps and gains ~0.93 nats per doubling, so
the crossing is near 400. Run layer 20 at **{200, 400}** and interpolate. The norm clamp is
not binding at either layer ([E-028a]: 33% of ceiling at L20, 0/6 at cap), so nothing
blocks the larger budgets.

- **Stop condition:** if layer 20 has not reached 6.26 by 400 steps, do NOT extend again
  without re-opening this ticket. An unbounded search for a budget that produces the
  desired match is the thing pre-registration exists to prevent.
- **If it cannot be matched at 400,** that is the reportable outcome: ROME's update at
  layer 20 cannot be brought to layer-5 displacement within an 16x budget, which is a
  fact about the method and answers [T-084] in the DEPTH direction.

**Step 2 — the propagation comparison, at matched displacement.** [E-026]'s 2x2, unchanged:
subject-initial and possessive city probes, control subject, paired no-pool measure,
endpoints before drops. The only change is that the layer-20 arm uses the matched budget.

**Pre-stated outcomes**, unchanged from [E-026] and now reachable because the arms are
matched on the quantity that matters:
- **CONFIRM** the coefficient predicts effect: possessive weakens >=40% at depth while
  subject-initial holds within 20%.
- **DENY**: possessive moves <20%.
- **UNIFORM**: both weaken similarly — refutation, not partial support.

**Naming, and it is not cosmetic.** A 400-step layer-20 edit is **not** "ROME as configured
by EasyEdit". Every artifact must call the arms `ROME/EasyEdit L5 (25 steps)` and
`ROME's update rule at L20 (N steps, displacement-matched)`. [E-013] gate 0 established the
project's convention of naming the configuration rather than the method, and this is the
first run where the two genuinely diverge.

**Confounds.**
1. *Matching on displacement does not match ‖Δv‖.* [E-028a] found L5 improves by turning
   the vector (‖Δv‖ flat at 7.2) and L20 partly by growing it (5.77 -> 6.90). At matched
   displacement the two deltas will differ in norm; report both norms beside every number
   and treat a large gap as a live alternative account rather than a footnote.
2. *Six subjects.* [E-028a]'s set is an unlucky draw (layer-5 displacement 6.25 against the
   full set's 9.70). The matched budget found on these six may not transfer. **Verify the
   match on a held-out 6 before running step 2**, and report the verification.
3. *Displacement is measured on the edit prompt only.* It is the right matching quantity
   precisely because it is measured where both edits were optimised, but it is not itself
   the outcome. Do not let the matching variable leak into the outcome reporting.

**Deliverable.** [E-026]'s 2x2 with a matching column showing each arm's displacement, so a
reader verifies the arms are matched rather than taking it on trust.

**Blockers:** none
**Artifacts:** _(on close)_
**Closed:** —

---

### E-028d · Is it the layer, or the step budget? The collinearity control

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-21
**Updated:** 2026-09-21
**Estimated:** 2h
**Thread:** T-079

**Description:**

[E-028c] found that two edits matched on belief displacement (6.97 vs 7.26), on delta norm
(7.52 vs 7.27) and on delivered coefficient (exactly 1.000, analytic) still differ **63%**
in how far they travel to a prompt sharing the edit's prefix. That is the dissociation
[E-026] claimed without earning.

**One alternative explanation remains, and it is built into the design.** Displacement was
matched by giving the deep arm a **16x step budget**, so *layer 20* and *400 steps* are
perfectly collinear. A heavily optimised rank-one update may simply be more specific to the
prompt it was optimised on — more steps, a solution fitted more tightly to that
continuation — with depth contributing nothing.

**The control is one cell: layer 5 at 400 steps.**

- Optimise `v*` at layer 5, 400 steps, same 12 subjects, same harness as [E-028b].
- Score the same 2x2 as [E-028c]: subject-initial and possessive city probes, control
  subject, paired no-pool measure, endpoints before drops.

**Pre-stated outcomes.** Let `P(layer, steps)` be the control-differenced drop on the
subject-initial probe. Known: `P(5, 25) = 9.66`, `P(20, 400) = 3.59`.

- **LAYER** — `P(5, 400)` stays within 20% of `P(5, 25)`, i.e. >= 7.7 nats. Budget does not
  drive propagation, the collinearity is broken in favour of depth, and [E-028c]'s
  dissociation stands as a layer effect.
- **BUDGET** — `P(5, 400)` falls to within 20% of `P(20, 400)`, i.e. <= 4.3 nats. The
  effect is optimisation budget, not depth; [E-028c]'s finding is about **how hard an edit
  was optimised**, which is a different and still interesting claim, and every depth
  statement in [E-028b/c] is withdrawn.
- **BOTH** — `P(5, 400)` lands between 4.3 and 7.7. Budget explains part; report the split
  and claim neither cleanly.

**Note that BUDGET is not a null.** "More optimisation makes an edit more local" would be a
finding about ROME's own hyperparameter — the one [E-028a] already showed is under-set at
25 steps — and it would connect directly to the field's generalisation/specificity
tradeoff. It must be reported with the same weight as LAYER, not as a failed experiment.

**Confounds.**
1. *Displacement will not be matched in this cell.* L5@400 will displace MORE than L5@25
   ([E-028a]: 8.31 at 100 steps and rising). That is fine and is the point — the question
   is whether propagation falls while displacement rises. **Report both**, and note that a
   fall in propagation alongside a rise in displacement is a stronger result than a fall
   alone.
2. *Clamp.* [E-028a] measured L5 occupancy at 54% of the ceiling at 100 steps. At 400 it
   may bind, which would cap the comparison. **Check occupancy and report it**; if the
   clamp binds, say so rather than reading the number.

**Deliverable.** A 2x2 of (layer) x (step budget) on the subject-initial probe's
propagation, with displacement and ‖Δv‖ beside every cell. Three cells exist; this ticket
buys the fourth and makes the design a crossing rather than a confounded pair.

**Blockers:** none
**Artifacts:** _(on close)_
**Closed:** —


---

### E-028 arc · Closure record

**Closed:** 2026-09-21

[E-028b] matched the arms (layer 20 reaches layer 5's 6.26-nat displacement at ~353 steps,
a 16x budget; held-out gap 0.93). [E-028c] compared propagation at that match and returned
UNMATCHED on its own pre-registration — the subject-initial arm, pinned at coefficient
1.000 at both layers, moved 63%. [E-028d] bought the fourth cell and broke the
layer/budget collinearity in favour of LAYER, with the budget account failing on both the
band test and the direction of its own mechanism.

**Result:** the coefficient bounds delivery and does not predict effect — 1.22 nats of
reach per nat displaced at layer 5 against 0.41 at layer 20, a factor of 2.96 across a 16x
budget range. [T-079] answered, DENY.

**Artifacts:** run_e028a.py, run_e028b.py, run_e028c.py, run_e028d.py;
results/E-028a-step-sweep.json, E-028b-budget-match.json,
E-028c-matched-propagation.json, E-028d-budget-control.json;
agents/shared/decisions.md -> "[E-028a]", "[E-028b/c]", "[E-028d]"

**What the arc cost and what it bought.** [E-026] asserted this conclusion on a design
whose arms differed in edit strength, and it had to be withdrawn. Getting it honestly took
three further runs and about six hours of NDIF time, each removing exactly one alternative:
strength ([E-028b/c]), optimisation budget ([E-028d]), and the norm clamp (checked, never
binding). The conclusion is the same sentence. The difference is that it is now true.

---

### E-030 · Is GPT-J's higher different-subject floor real, or unfamiliarity?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27
**Estimated:** 2h
**Thread:** T-082

**Description:**

[E-027] measured GPT-J's different-subject coefficient floor at **0.155** at the edit
layer against Llama's **0.082**, rising to **0.524** at the final layer — above that
layer's same-subject value, where the measure stops telling subjects apart at all. On that
basis §4.3 of the paper narrows [E-018]'s "different subjects are near-orthogonal" to a
**Llama-3.1-8B statement**.

**That narrowing is currently flagged PLAUSIBLE, not confirmed, and it is in the packet.**
The subjects were possession-gated on *Llama* and run on GPT-J with no filter. GPT-J is 6B
and Pile-trained; if it does not know these people, their name tokens may share a generic
"unfamiliar person" direction and inflate the floor by construction. Resolving this before
the call either upgrades a published claim or retracts one, which is why it runs first.

**Method.** Split, not a rate.

1. Run the shipped possession filter on **GPT-J** over ~36 subjects drawn from the gated
   chains. `possession.Scorer` is `Callable[[pairs], list[float]]`, so `score_pairs`
   against a GPT-J handle satisfies it with no change to the module.
2. Partition into **HELD** and **NOT-HELD** on GPT-J.
3. For each group, measure the different-subject coefficient exactly as [E-027] did —
   chain *i*'s `k*` against chain *i+1*'s subject in the same template — at three depths
   (fractions ~0.15, ~0.63, 1.00).
4. Compare the two floors.

**Pre-stated outcomes.**

- **ARCHITECTURAL** — the two floors differ by **< 0.05** at the edit layer. The high floor
  is a property of GPT-J's representations, familiarity is not driving it, and §4.3's
  narrowing of [E-018] to a Llama fact is **confirmed**. The paper's flag is upgraded.
- **FAMILIARITY** — NOT-HELD exceeds HELD by **≥ 0.10** *and* the HELD floor sits near
  Llama's 0.082. The floor was unfamiliar names all along; §4.3's narrowing is
  **withdrawn** and the sentence about it comes out of the packet.
- **MIXED** — anything between. Report both groups and claim neither; the flag stays.

**Confounds.**

1. *Possession is scored against a candidate pool, and [E-023] showed pools undercount.*
   Tolerable here because the experiment needs a **split**, not a rate — but a pool that
   undercounts moves subjects from HELD into NOT-HELD, which **dilutes** the contrast
   rather than manufacturing one. So a FAMILIARITY verdict survives the objection and an
   ARCHITECTURAL verdict is weakened by it. State that asymmetry in the entry.
2. *Group sizes.* If either group has **fewer than 8** subjects the comparison is
   underpowered; report the counts and say so rather than reporting a difference.
3. *Something else differing between the groups.* Report the **same-subject** coefficient
   per group alongside the floor. If HELD subjects also differ there, the split is picking
   up something other than familiarity and neither verdict holds.

**Deliverable.** One table: floor and same-subject coefficient, by group, by depth, with n
per group. One sentence on whether §4.3's flag is upgraded, withdrawn, or stays.

**Scope.** One model, one relation family, coefficient only, no edits. Existence
per [O-004].

**Result (2026-09-27).** ARCHITECTURAL. The floors are **0.146 against 0.146** at the edit
layer — a gap of 0.000 against a pre-stated band of 0.05. §4.3's narrowing of [E-018] to a
Llama fact is CONFIRMED and the plausible-not-confirmed flag is removed from the packet.

Two components the headline does not carry. **Every gap has the wrong sign** — familiarity
predicts NOT-HELD above HELD and it is lower at all three depths (all within 1 SEM, so the
reversal is not itself a finding, but a hypothesis predicting positive and getting
consistently negative is unsupported rather than weakly supported). And **the premise was
shaky**: GPT-J holds 21 of 36 subjects outright, so "GPT-J may not know these people" was
already doubtful.

Confound 3 did not fire (same-subject 0.865 vs 0.846). The pool confound survives and
weakens this direction specifically — dilution also produces a zero gap — but it does not
explain a consistently negative one, nor the 58% possession rate.

**Status:** closed
**Blockers:** none
**Artifacts:** agents/engineer/workspace/run_e030.py; results/E-030-floor-by-possession.json;
logs/run_e030-2026-09-27-103338.log; agents/shared/decisions.md -> "[E-030] Result"
**Closed:** 2026-09-27

---

### E-031 · Is the floor's dip near the edit layer real, or two coincidences?

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-09-27
**Updated:** 2026-09-27
**Estimated:** 1h
**Thread:** T-083

**Description:**

[E-027] noticed, without looking for it, that **both** models' different-subject floors are
non-monotonic with a minimum near depth fraction 0.15 — Llama **0.082** at L5, GPT-J
**0.155** at L4 — rising through the middle and again near the output. That is
approximately where ROME edits in both.

The existing evidence is 4 points on Llama and 6 on GPT-J, at n = 12–16. That is too
coarse to tell a real dip from sampling noise, and the observation is exactly the kind
[T-083] was opened warning about: *too satisfying not to over-read*.

**Method.** Finer spacing where the claim lives, and cheap because saves unroll.
`compute` one trace per subject per model with **8 layers saved at once** — the [O-008]
idiom, saves unrolled explicitly because a loop inside a trace body silently returns
nothing. Layers chosen at depth fractions **0.00, 0.06, 0.10, 0.16, 0.23, 0.32, 0.55,
1.00**, so five points sit below 0.25 where [E-027] had two.

- Llama-3.1-8B → layers 0, 2, 3, 5, 7, 10, 17, 31
- GPT-J-6B → layers 0, 2, 3, 4, 6, 9, 15, 27
- n = 20 subjects, up from 12, for tighter bars. Coefficient only, no edits.

**Pre-stated outcomes.** Let the window be depth fraction 0.05–0.25.

- **DIP** — each model's floor has its minimum inside the window, *and* that minimum sits
  below both neighbouring points by more than **one standard error of the mean**, *and*
  the two minima are within **0.15** of each other in depth fraction. Only then is there a
  shared phenomenon to explain.
- **NO DIP** — on at least one model the floor is flat or monotone across the window, or
  the minimum is within one SEM of its neighbours. The [E-027] observation was sampling
  noise and the sentence is removed from §4.3's margin.
- **DIFFERENT LOCATION** — both dip, but at fractions more than 0.15 apart. Then each is a
  fact about its own model and the coincidence claim dies even though both curves are
  non-monotonic.

**What a DIP would and would not license — read this before writing the entry.**

It would license: *different subjects are maximally separated at the subject position at
roughly this depth, in two architectures.* That is a statement about representations and
it is worth having.

It would **not** license any claim about ROME's layer choice. ROME selects its layer by
causal tracing, on a criterion that has nothing to do with inter-subject separation. Two
quantities peaking at similar depths is a coincidence of location, not a mechanism. To
make the connection one would have to show the causal-tracing peak and the floor minimum
**move together** across models — which needs causal tracing run on both, which we have
not done and are not proposing here. **Any sentence connecting the dip to ROME's layer
selection is out of scope for this ticket and must not appear in its entry.**

**Confounds.**
1. *Different subject pairing.* The floor is chain *i* against chain *i+1*; a different
   pairing gives different numbers. Use the same pairing rule as [E-027] and [E-018] so
   the curves are comparable to what is published, and say that the pairing is fixed
   rather than averaged over.
2. *Depth fraction is not a physical alignment.* Matching by fraction assumes the two
   networks do comparable work at comparable relative depth, which is an assumption, not a
   measurement. It is the same assumption [E-027] already makes; note it, do not re-argue
   it.

**Deliverable.** One two-line chart — floor against depth fraction, both models, with SEM
bars — and one sentence: dip, no dip, or different locations.

**Result (2026-09-27).** NO DIP — and the observation dies for a better reason than the
test that reported it. The minima are at fraction **0.06** (Llama) and **0.11** (GPT-J),
not the same place; and Llama's edit layer sits at fraction 0.16 where the floor is
**0.095**, roughly twice its 0.048 minimum. "ROME edits where subjects are maximally
separated" is false on its own terms, before significance enters.

**Defect in this ticket's own criterion, recorded.** "Below both neighbours by >1 SEM"
is defeated by a flat-bottomed minimum spanning two adjacent samples, which is exactly
what finer spacing produces — GPT-J's 0.144 and 0.153 are within each other's error. The
test would have failed that way regardless of the world, and it was foreseeable before
the run.

What survives without any threshold: the floor is lowest in the first fifth of the network
and rises monotonically after, a 14x range on Llama. That replaces the dip sentence in
§4.3's margin.

**Status:** closed
**Artifacts:** agents/engineer/workspace/run_e031.py; results/E-031-floor-curve.json;
agents/shared/decisions.md -> "[E-031] Result"
**Closed:** 2026-09-27


---

### E-032 · Does the pinning hold at frontier scale? 8B → 70B → 405B

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27
**Thread:** T-080

**Description.** Coefficient measurement needs no gradients — one forward pass, save the
MLP input at the subject's last token. That is `basic_trace`, which every hosted model
supports, so the scale question costs ~24 traces where an *edit* at 405B would cost days.
Llama-3.1-70B is base and is the clean comparison; Llama-3.1-405B-Instruct is the only
405B hosted and is instruction-tuned, so that arm varies scale AND post-training together.

**Result (2026-09-27).**

- **ANALYTIC: CONFIRM at both**, worst deviation 0.0e+00. With [E-027] that is four models
  across a **68x parameter range**, two architectures, base and instruct.
- **DECAY: approximately scale-invariant** at matched depth — worst deviations 0.131 and
  0.144 against a pre-stated 0.15 band. A pass, close enough to the threshold that it is
  reported as *approximately* invariant rather than cleanly so.
- **FLOOR: not a scale law, and the tidy story is refused.** 405B-Instruct reaches **0.009**
  at fraction 0.10 (max across 12 subjects 0.042, so not outlier-driven) against a
  same-subject 0.992 — a **108x** contrast. But 70B (0.110) is *worse* than 8B (0.061), so
  the trend is non-monotone on four points, and the 405B arm confounds scale with
  instruction tuning. Floor magnitude is model-specific.

**Access note.** An early probe failed with `OSError: could not get source code` and looked
like a permissions problem. It was the harness: nnsight reads the source of the frame
entering `model.trace`, and the probe ran from a heredoc with no source file. Re-run from
a real file, all three models trace in 6–8s. Recorded because [O-007] is the standing
lesson — re-run the thing that worked before attributing a failure to access.

**Artifacts:** agents/engineer/workspace/run_e032.py; results/E-032-scale.json;
agents/shared/decisions.md -> "[E-032] Result"
**Closed:** 2026-09-27

---

### E-033 · The relation crossover — is floor-plus-type-displacement general?

**Status:** closed — all 6 arms; see decisions.md "[E-033] Final"
**Type:** implement
**Priority:** high
**Created:** 2026-09-27
**Updated:** 2026-09-27
**Estimated:** 4h
**Thread:** T-081, T-080

**Description:**

[E-025] found that a **birthplace** edit produces two effects: a **floor** — everything
about the subject suppressed to roughly the same level — plus **type-matched
displacement**, an extra penalty only where the probe's answer type matches the injected
value.

| probe | type-matched to a country? | post-edit level |
| --- | --- | ---: |
| occupation | no | −6.16 |
| language | no | −6.20 |
| citizenship | **yes** | **−9.10** |

**It is stated as a general mechanism and measured on one relation.** Edited relation is
the third of [T-065]'s never-varied dimensions, and the other two are now done ([E-028]
layer, [E-032] model). This is the test, not a verification: until it runs, "general" is
an assumption.

**The design is a crossover.** Edit **occupation** instead — inject a profession — and the
prediction inverts. Occupation becomes the type-matched probe and should take the extra
displacement; citizenship, previously the displaced one, should fall back to the floor
beside language.

**Edit prompt must be subject-initial.** `"{} works as a"` → a profession the subject does
not have. **Do not reuse [E-014]'s cached `|ctl` deltas**: their prompt is
`"By profession, {} is a"`, which (a) does not begin with the subject, so the coefficient
is not pinned the way every other edit in this record is, and (b) is *identical to
[E-025]'s occupation probe*, so scoring it would measure efficacy on the edit prompt rather
than displacement of a different probe.

**Probes** — [E-025]'s three, unchanged, so the two arms are directly comparable:
occupation `"By profession, {} is a"`, citizenship `"{} is a citizen of"`, language
`"The native language of {} is"`. Targets: [E-014]'s per-subject `target_occ`, a profession
drawn from the pool and not held by that subject.

**Scale.** Run at **Llama-3.1-8B and Llama-3.1-70B**. Editing at 70B became possible today
— `compute_v_batch` summed a term on the delta's device with terms from `lm_head`, which on
a sharded model is a different GPU, so it raised a device error at any size above one card
and could never fire at 8B. Fixed. A 2-step probe now runs in 21s at 70B and 24s at 405B,
against 19s at 8B: **round trips dominate, not compute**, so editing at 70B costs
approximately what it costs at 8B.

**Pre-stated outcomes.** Post-edit **levels**, never drops.

- **CROSSOVER** — the mechanism is general. Under an occupation edit the occupation probe
  finishes at least **1.5 nats below both** citizenship and language, **and** the
  citizenship−language gap collapses to under **1 nat** (both at the floor). Under the
  birthplace edit that gap was 2.90.
- **NO CROSSOVER** — citizenship remains the most displaced even when the injected value is
  a profession. The structure is then about countries or about birthplace specifically, and
  [E-025]'s "type overlap" reading is withdrawn in its general form.
- **NO FLOOR** — the two non-matched probes do not converge to within 1 nat of each other.
  The two-effect account fails in a third way and needs its own ticket.

**Confounds.**
1. *Baselines differ wildly between probes* — language starts at −0.71, occupation at
   −4.36. **Report post-edit levels first and drops second, or not at all.** [E-025]'s
   first headline was computed on drops, said "semantic relatedness", and was retracted.
   This is the same trap one relation over.
2. *Occupation is a harder prediction than citizenship.* Its baseline is 3.65 nats lower,
   so it has less room to fall before hitting the floor. If occupation cannot get 1.5 nats
   below the floor because it started near it, report that as **uninterpretable**, not as
   a failed crossover.
3. *Different edit, different magnitude.* Report `‖Δv‖` for both arms. A profession target
   may need a larger or smaller update than a country target, and a level difference that
   tracks ‖Δv‖ is not type matching.

**Deliverable.** One table, 3 probes × 2 edited relations × 2 models, post-edit levels,
with baselines and ‖Δv‖ beside them. One sentence: does the displaced probe follow the
injected value's type?

**Blockers:** none.
**Artifacts:** _(on close)_
**Closed:** —

---

### E-034 · An unattended runner, ported from the second project's pipeline

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-14
**Updated:** 2026-10-14

**Description:**

Runs here are launched by hand, watched by hand, and read by hand. That has cost this
project more than any wrong hypothesis:

| loss | hours | would a gate have caught it? |
| --- | ---: | --- |
| partial delta cache read as complete ([E-033]) | ~1 | **yes** — completeness assert |
| layer absent from the scores cache key ([E-033]) | ~0 (caught) | **yes** — fingerprint assert |
| `optimise()` reading a flaky node as an oversized batch | ~1 | **yes** — triage on the exception class |
| two NDIF jobs hung in `RECEIVED` | **~144** | **yes** — watchdog, now partly covered by `CALL_TIMEOUT_S` |
| §4.5 asserting a claim §5.1 had withdrawn | — | **yes** — claim audit |
| [E-026]'s gate measuring the wrong quantity | ~2 | **no** — conceptual, no gate catches it |

`a private production pipeline of mine` solves this shape already. Port the parts that transfer.

**In scope.**

1. **`preflight.py`** — escalating gates before any remote work, the second project's `batch.py` order:
   lint and import (seconds) → the run's own report path against known-answer data
   (seconds) → cache fingerprint completeness (seconds) → a 2-call remote smoke (one
   minute). Only then the real run. Refuses rather than warns.
2. **`triage.py`** — the second project's `ledger.py` for our logs. Every WARNING/ERROR matched to a
   known cause (flaky node, OOM split, cross-device sum, transport, hang, parked chunk).
   **Unsorted is the output that matters** — a failure class we have not seen before is
   the only thing worth a person's attention.
3. **`report.py`** — one self-contained page per experiment, built only from what the run
   left on disk, readable mid-run. Pre-stated bands first, then the verdict, then the
   confounds the ticket named and whether each was checked, then the evidence.
4. **`watch.py`** — the overnight loop: take a queue of pre-registered tickets, preflight
   each, run it, triage it, report it, move to the next. Notify on *unsorted* only.

**Out of scope, deliberately.** Janaan gives `claude -p` two judgement steps — designer and
critic. **We give it none that touch a verdict.** Our verdicts are pre-registered band
tests in the runner and they stay there; a model asked "is this result real?" would supply
the confirmation bias [E-025], [E-026] and [R-012] each cost us. A brief may audit
**process** — endpoints reported alongside drops, n stated, each pre-registered confound
actually tested — because that is where our errors have been.

**Falsification.** If the next three runs under this harness produce no caught defect and
no unsorted triage line, the harness is overhead and should be cut back to `preflight`
alone. Record that at the third run rather than letting it accrete.

**Result (2026-10-14).** All four pieces built and exercised. `triage` over every log this
project has written: 3,700+ warnings, **0 unsorted** — after the first pass returned 15 and
showed most were not failures but verdicts and [O-004] scope notes logged at WARNING, which
is our own misuse of the level. `preflight` verified by **reintroducing** [E-033]'s cache-key
bug and confirming it refuses. Dry-runs moved from the scratchpad into `tools/dryruns/` and
are now executed rather than checked for.

**Status:** closed
**Artifacts:** tools/preflight.py, triage.py, report.py, watch.py, queue.json,
dryruns/dryrun_e033.py, README.md; agents/shared/decisions.md -> "[E-034]"
**Closed:** 2026-10-14

---

### E-035 · What sets how far an edit travels? A pre-registered candidate sweep

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-14
**Updated:** 2026-10-14
**Thread:** T-086

**Description:**

[T-086] is the one question nothing in this record predicts. [E-029] measured belief
displacement and ROME's efficacy margin against propagation at Spearman **0.419 and
0.425** — about 18% of variance, and near-identical to each other, so they are one weak
view rather than two. The coefficient cannot help **by construction**: it is pinned at
exactly 1.000 across precisely the probes whose outcomes differ most, so it has zero
variance where the outcome varies. [R-012] then withdrew the only candidate explanation on
the table — Ravfogel et al. place typed attributes outside their setting, and their
per-relation block structure predicts the opposite of [E-033].

So the thread has no candidate. **This ticket does not invent one; it eliminates.** Seven
quantities are measured against the same 42 subjects' propagation, six of them from data
already on disk.

**Candidates**, with why each is plausible and what it would mean:

| # | candidate | why | source |
| --- | --- | --- | --- |
| 1 | `‖Δv‖` | a bigger update should move more | cached |
| 2 | `‖k*‖` | the key's magnitude scales the delivered vector | cached |
| 3 | `‖Δv‖ / ‖k*‖` | [E-028c] reported these per arm; never per subject | cached |
| 4 | baseline `log P(true)` | a confident belief may resist, or have further to fall | [E-029] |
| 5 | target prior `log P(target)` | an edit toward a likely answer may travel cheaply | [E-026b] |
| 6 | subject token count | longer names spread the key over more positions | tokenizer |
| 7 | residual-stream norm at the subject position, layer 5 | the delta competes against what is already there — the one candidate needing the network | 42 reads |

**Pre-stated outcomes.** Against [E-029]'s incumbent ρ = 0.425.

- **FOUND** — some candidate reaches **ρ ≥ 0.60** *and* beats the incumbent by **≥ 0.15**.
  [T-086] gets its first real candidate and a follow-up ticket designs the causal test.
- **NOTHING BEATS IT** — no candidate exceeds **ρ = 0.50**. Then propagation magnitude is
  set by something in none of: update size, key size, their ratio, the belief's strength,
  the target's prior, the subject's length, or the local residual norm. That is a sharper,
  more useful statement of [T-086] than it currently has, and it is the outcome to expect.
- **MULTICOLLINEAR** — two or more candidates exceed 0.50 but correlate with each other
  above **0.80**. Then they are one quantity wearing several names and the entry must say
  which, rather than reporting a winner.

**Confounds.**
1. *Seven tests on 42 subjects.* At ρ = 0.50, n = 42, a single test is around p = 0.001,
   but seven of them are not. **Report the Holm-adjusted threshold beside every ρ** and
   treat any candidate clearing only the unadjusted bar as not clearing it.
2. *The outcome is itself noisy.* Propagation is a control-differenced drop with its own
   spread. A ceiling on any achievable ρ follows, and it is not 1.0. **Report the
   outcome's own spread** so a modest ρ is read against what is reachable.
3. *Candidates 1–3 are algebraically related.* `‖Δv‖/‖k*‖` is a function of the other two,
   so it cannot be independent evidence. Report them as a group, and never count the ratio
   as a third hit.

**Deliverable.** One table: candidate, ρ, Holm threshold, whether it clears, and its
correlation with the incumbent. One sentence naming the verdict.

**Scope.** Layer 5, 42 subjects, one model, one relation — the [E-029] set, so the
incumbent is measured on exactly the same subjects. Correlational: nothing here is causal,
and a FOUND result licenses a follow-up design, never a claim.

**Result (2026-10-15).** **NOTHING BEATS IT** — the outcome this ticket named in advance
as the one to expect. No candidate clears rho 0.50 at its Holm threshold.

```
norm_delta_v     -0.423   p 6.16e-03   Holm 7.14e-03   CLEARS
ratio_dv_over_k  -0.349   p 2.73e-02   Holm 8.33e-03   no
target_prior     +0.337   p 3.32e-02   Holm 1.00e-02   no
residual_norm    -0.309   p 5.31e-02   Holm 1.25e-02   no
norm_k_star      -0.228                                no
baseline_true    +0.067                                no
subject_tokens   +0.042                                no
es_margin (incumbent) +0.425
```

Propagation magnitude is set by none of update size, key size, their ratio, the belief's
strength, the target's prior, the subject's length, or the local residual norm.

**Confound 1 earned its place:** `ratio_dv_over_k` and `target_prior` both clear an
unadjusted alpha and neither clears Holm. Two of seven would have been reported as hits.
**Confound 2 as required:** the outcome's own sd is 3.11 on a median of 10.52, so the
reachable ceiling is not 1.0.

**Three things the verdict does not say.** (a) `‖Δv‖` is the one candidate clearing its
Holm threshold while sitting *below* the effect-size floor — statistically reliable,
practically weak, and the ticket set its floor on rho rather than p for exactly this.
(b) **Its sign is negative: a bigger update travels less far**, against the rationale it
was listed with. Recorded, not explained. (c) It correlates with the incumbent at only
−0.276 while each tracks propagation at ~0.42 — two weak views of *different* things,
unlike [E-029]'s pair. A rank-sum of the two reaches 0.510, which is **exploratory, not
pre-registered, and claimed for nothing**; it is why [T-093] exists.

**Bug found and fixed before any number was produced:** the residual-norm trace read
`layers[L].output[0]`, slicing away the batch. It crashed only because 42 subjects exceeded
a 15-token sequence; with a longer prompt than batch it would have returned one subject's
activations for all of them, silently. A shape assertion now refuses to index a wrong read.

**Artifacts:** run_e035.py; tools/dryruns/dryrun_e035.py;
results/E-035-propagation-candidates.json; logs/run_e035-2026-10-15-084614.log;
agents/shared/decisions.md -> "[E-035] Result"
**Closed:** 2026-10-15

---

### E-036 · How much of a ROME update reaches RippleEdits' own test prompts?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-14
**Updated:** 2026-10-14
**Thread:** T-003 · follows [R-013]

**Description:**

[R-013] killed the priced week by killing its premise: RippleEdits is **already**
subject-final — 44 of 46,754 prompts begin with their subject. So there is nothing to
rewrite. What replaces it is smaller, sharper, and made entirely with the benchmark's own
materials.

**Take RippleEdits' own edits and its own test prompts, and measure what fraction of the
update each test prompt would receive.** No editing, no rewriting, no probes of ours.
`k*` is read from the entry's own edit prompt; the coefficient is
`(k·k*)/(k*·k*)` at the subject's last token of each test prompt. Layer 5, which is what
EasyEdit's `llama3-8b.yaml` edits.

**Their taxonomy is the control structure, which is why this is worth doing on their data
rather than ours.** The six criteria differ in exactly the way the mechanism cares about:

| criterion | what it varies | predicted coefficient |
| --- | --- | --- |
| Relation Specificity | same entity, different relation | **high** — the key is the subject's, not the relation's |
| Logical Generalization | same entity, inverse/symmetric relation | **high** |
| Forgetfulness | same entity, a negated relation | **high** |
| Subject Aliasing | **a different surface form of the same entity** | **lower** — the key is a string, and the string changed |
| Compositionality I / II | a **different entity**, reached by a hop | **at the floor** ([E-018]: 0.082) |

That gradient is a prediction with four distinguishable levels, and nothing about it was
designed by us.

**Pre-stated outcomes.** Median coefficient at layer 5, per criterion.

- **MECHANICAL** — Relation Specificity, Logical Generalization and Forgetfulness all sit
  **≥ 0.80**, *and* Compositionality sits **≤ 0.30**. Their same-entity tests receive most
  of the update by arithmetic while their different-entity tests do not, which is the
  shape the concern predicts and is reportable against their own taxonomy.
- **NOT MECHANICAL** — the same-entity criteria sit **below 0.50**. The concern does not
  apply to this benchmark, §7 item 2 is withdrawn entirely, and that is the most useful
  possible outcome because it closes the project's one outward-facing claim honestly.
- **UNDIFFERENTIATED** — every criterion within 0.15 of every other. Then the coefficient
  does not distinguish their test types and the measurement says nothing about them.

**Confounds.**
1. *Subject Aliasing is the built-in control and must be reported whichever way it goes.*
   An alias is the same entity under a different string. If the coefficient is a property
   of the **string**, aliases drop; if of the **entity**, they do not. We predict a drop,
   and a non-drop would be more interesting than the headline.
2. *Entries are usable only when a subject label can be recovered* from a materialised
   prompt — 279 of the first 400. **Report the attrition and the reason**; per [O-004]
   this licenses an existence claim about their prompts, never a rate over the benchmark.
3. *Compositionality's subject is a different entity, so `subject_last_index` must locate
   the ORIGINAL subject inside a longer phrase* ("the place of death of Leo Arons"). The
   coefficient is then read at a position that is genuinely in the prompt — which is the
   honest thing to measure, but it is not "the subject position" in their sense, and the
   entry must say so.
4. *Delivery, not effect.* [E-028d] established these come apart by 2.96×. This measures
   what **arrives**, and no sentence may imply it measures what moves.

**Deliverable.** One table: RippleEdits criterion × median coefficient at layer 5, with
the inter-quartile range and n per criterion. One sentence on whether their same-entity
tests are reached mechanically.

**Scope.** `recent.json`, layer 5, Llama-3.1-8B, coefficient only, no edits applied.
Existence per [O-004].

**Result (2026-10-14).** UNDIFFERENTIATED, in 19 minutes with zero retries, fully
unattended. **Three criteria hold:** same-entity prompts receive 0.966–1.000 of the update
at layer 5 (n=1,200), with Forgetfulness at exactly 1.000, IQR 0.000.

**One criterion could not have answered, and the correction on the other runs the other
way.** Subject Aliasing was selected against by the entry filter, which required the
canonical label to appear in the test prompt. That filter and the alias-recovering one are
near-disjoint: of the aliasing prompts in the 200 entries used, it kept 8 by canonical
substring and missed 7 whose surface form is a genuinely different string (`Royal Ontario
Museum` -> `ROM`, `Hamilton LRT` -> `B-Line`). The run's "keyed on the ENTITY, not the
string" line is **withdrawn**: it is the conclusion a sample of near-identical strings
manufactures.

*Corrected 2026-10-14.* This paragraph's first version also said Compositionality's 0.983
"measures the wrong position". That was wrong, and the correction is worse for us.
RippleEdits' compositional prompts **name the edited subject verbatim** — *"the name of the
head of government of the place of death of Leo Arons is"* — so reading the coefficient at
that token is the right position, and confound 3 fired on a prompt form that does not
exist here. The *prediction* of a floor was what failed. Their different-entity tests still
reach the edited subject's token and still receive essentially the whole update there.
E-036 therefore measured **no different-entity floor at all** — nothing in this run is a
control. [E-037] supplies one.

Every gate passed. A construct-validity error is invisible to all of them.

**Status:** closed
**Artifacts:** run_e036.py; results/E-036-ripple-coefficients.json; out/reports/E-036.html;
agents/shared/decisions.md -> "[E-036] Result"
**Closed:** 2026-10-14


### E-037 · A floor measured on RippleEdits' materials, and the aliasing arm E-036 never ran

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-14
**Updated:** 2026-10-14
**Thread:** T-003 · follows [E-036]

**Description:**

[E-036] reported three same-entity criteria at 0.966-1.000 and read that as mechanical
delivery. It has **one defect and one hole**, and the hole is the larger of the two.

**The hole: there was no control.** Every criterion E-036 measured — Compositionality
included — reads the coefficient at a token that is the edited subject, because
RippleEdits' compositional prompts name the edited subject verbatim (*"the name of the head
of government of the place of death of Leo Arons is"*). So 0.983 was not a different-entity
reading and nothing in that run bounds the measure from below. A coefficient of 0.97 is
only evidence if a mismatched pair scores much lower **on these same prompts**. [E-018]'s
0.082 was measured on our own probe set, in a different prompt register, and importing it
here is an assumption, not a floor.

**The defect: Subject Aliasing was selected against.** `usable()` keeps a test prompt only
when the canonical subject label appears in it, which is precisely the condition an alias
violates. In the 200 entries E-036 used, that filter kept 8 aliasing prompts by canonical
substring and missed 7 whose surface form is a genuinely different string. Measured on the
raw file, the alias actually used is recoverable from the prompt's own `" of X is"` tail in
52 of 52 cases.

**Two arms.**

*Arm A — the permuted floor.* For every test prompt, compute its coefficient a second time
against a **different entry's** `k*`, partner drawn by a fixed-seed permutation over
entries. Same prompts, same layer, same positions, same arithmetic; only the edit it is
measured against changes. This is [E-018]'s construction rebuilt from RippleEdits' own
materials, which is what makes it a control rather than a borrowed number. It costs **zero
additional remote calls** — the keys are already read inside each entry's single trace and
need only be persisted (float16, `results/cache/E037_keys_*.pt`).

*Arm B — aliasing, selected correctly.* Extract the alias from the test prompt itself with
the `ripple_forms` pattern set, and read `subject_last_index` at **that string**. `k*` is
unchanged — still the canonical subject's key from the entry's own edit prompt. The
comparison is then genuinely "same entity, different string", which is what the criterion
is for. Entries whose aliasing prompts were only kept by canonical substring are reported
separately, not merged.

**Pre-stated outcomes.** Median coefficient at layer 5, Llama-3.1-8B, `recent`, n=400
entries (double E-036's, for the aliasing arm's sake).

- **CONTROLLED** — the permuted floor sits **<= 0.30** while same-entity criteria stay
  **>= 0.80**. E-036's reading survives with a control behind it, and the separation is the
  number that carries the claim.
- **NO SEPARATION** — the permuted floor sits **>= 0.60**. Then RippleEdits' prompt forms
  are similar enough that the coefficient is near-1 for almost any pairing, **E-036's
  headline is withdrawn**, and the finding becomes a fact about the measure's resolution on
  formulaic corpora. This is a real possibility: their prompts are templated, and a
  template's keys may overlap heavily regardless of subject.
- **PARTIAL** — floor between 0.30 and 0.60. Report the separation in nats-free raw form
  and claim no band.

On Arm B, independently:
- **STRING-KEYED** — alias median falls **>= 0.15** below the same-entity median. The
  coefficient is a property of the surface form.
- **ENTITY-KEYED** — alias median within 0.15 of same-entity. Warrants a sentence only if
  n >= 30 alias prompts with a genuinely different surface form; below that, report n and
  claim nothing. E-036's version of this line was withdrawn for exactly this reason.

**Confounds.**
1. *Alias n is small and that is the binding constraint.* Pre-register the n threshold
   above rather than discovering it after the medians are in view. [O-004]: existence only.
2. *The permutation must not pair an entry with a near-duplicate subject.* Reject a partner
   whose subject string shares a token with the entry's own, and log how many were
   rejected.
3. *Prompt length differs between arms.* The floor is read at the same token index in the
   same prompt as the real coefficient, so length is held exactly — this confound is
   controlled by construction, and the entry should say so rather than leave it unnamed.
4. *Delivery, not effect* — [E-028d], 2.96x. Unchanged and still binding.

**Deliverable.** One table: criterion x (own `k*`, permuted `k*`) median coefficient, with
IQR and n. The claim is carried by the **gap between the two columns**, not by either one.

**Scope.** `recent.json`, layer 5, Llama-3.1-8B, coefficient only, no edits applied.
Deferred: the other two subsets, other layers, any effect measurement.

**Result (2026-10-14).** ARM A · **CONTROLLED**, in 40 minutes with zero retries, fully
unattended.

```
criterion                     n    own k*     IQR  permuted k*     IQR       gap
Logical_Generalization      208     0.970   0.058        0.069   0.037     0.901
Compositionality_I         1981     0.982   0.028        0.065   0.045     0.917
Compositionality_II           3     0.991   0.019        0.109   0.081     0.882
Subject_Aliasing             27     0.898   0.468        0.071   0.044     0.826
Relation_Specificity       1818     0.969   0.046        0.075   0.048     0.894
Forgetfulness               241     1.000   0.000        0.072   0.047     0.928
```

The permuted floor is **0.070**, tight (IQR 0.037-0.048), against same-entity 0.969-1.000 —
**separation 0.900**. The pre-stated NO SEPARATION outcome, which would have withdrawn
[E-036]'s headline, did not occur. Compositionality I at n=1,981 sits at 0.982 against that
floor: their different-entity tests receive essentially the whole update, now measured
against a control rather than observed about prompt strings.

**Arm B declined its conclusion.** Different-surface aliases 0.302, canonical-substring
1.000 — a 0.70 gap that looks string-keyed, at **n=9 against a threshold of 30 fixed before
the run**. Subject_Aliasing's IQR of 0.468, against 0.019-0.058 elsewhere, is that split
visible in the aggregate. No sentence drawn.

**Two defects found in this ticket's own tooling, both fixed.**
1. `triage.py` matched `UNDERPOWERED` only behind a literal `VERDICT: ` prefix, so this
   runner's `ARM B · UNDERPOWERED` went unsorted and the loop stopped the queue on a
   healthy run. The verdict words are now matched on their own.
2. `dryrun_e037.py` cleaned up `results/E-037-ripple-floor.json` — which became the real
   run's output once the runner started naming files by subset, and the dry-run deleted a
   40-minute result. Recovered in 22s from the key cache, identical numbers. The cleanup
   now names only the path it writes and asserts `dry` is in it.

**Artifacts:** run_e037.py; tools/dryruns/dryrun_e037.py;
results/E-037-ripple-floor-recent.json; logs/run_e037-2026-10-14-133426.log;
agents/shared/decisions.md -> "[E-037] Result"
**Closed:** 2026-10-14

### E-038 · Is the coefficient keyed on the entity or on the string? At a power that can answer it

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-10-14
**Updated:** 2026-10-14
**Thread:** T-003 · follows [E-037]

**Description:**

[E-037] Arm B produced the gap and refused the conclusion: aliases with a genuinely
different surface form sit at **0.302**, prompts merely containing the canonical label at
**1.000**, at **n=9** against a threshold of 30 fixed before the run. This ticket is that
arm alone, at a power that can answer it.

**The n=9 was the 400-entry cap, not the corpus.** Counted over all three released subsets
with [E-037]'s own `usable()`:

```
recent     1,948 entries   1,303 usable    37 aliases with a different surface
random     1,922 entries     779 usable   314
popular      885 entries     496 usable    20
ALL        4,755 entries   2,578 usable   371
```

371 against a threshold of 30. `random` alone clears it eleven times over, and the
imbalance across subsets is itself worth reporting rather than pooling away.

**Arm A is not re-run.** A floor of 0.070 with an IQR under 0.05 across more than 4,000
readings is not going to move, and re-measuring it is the inward work [T-065] names. It
comes along for free — the same pass computes it — but no claim rests on repeating it.

**Method.** `run_e037.py --subset recent,random,popular --n 2600 --seed 1538`. One pass over
the union, so a single permutation spans all three and the floors pool legitimately. Key
cache and output are named by the subset list, so this cannot read [E-037]'s `recent`-only
cache and call it complete.

**Pre-stated outcomes.** Median coefficient of different-surface aliases against the
same-entity median, layer 5, Llama-3.1-8B, at n >= 30.

- **STRING-KEYED** — aliases fall **>= 0.15** below the same-entity median. The coefficient
  is a property of the surface form, which means a benchmark that renames its subject is
  measuring a different key, and [E-037]'s 0.302 was real rather than a small-sample
  artifact.
- **ENTITY-KEYED** — aliases within 0.15 of same-entity. Then [E-037]'s 0.302 was nine
  prompts behaving unlike their population, and **the direction [E-036] originally claimed
  is right for the wrong reason** — worth saying plainly, since this ticket exists because
  that claim was withdrawn.
- **SPLIT BY SUBSET** — the three subsets disagree by more than 0.15. Report per subset and
  pool nothing; `random` supplying 314 of 371 means a pooled median is mostly one subset's.

**Confounds.**
1. *`random` dominates the pooled n (314 of 371).* **Report the median per subset before
   the pooled one**, and let the pooled figure stand only if the three agree. This is the
   confound most likely to produce a confident wrong number here.
2. *"Genuinely different surface form" is a string test, not a semantic one.* `Rob Tennent`
   vs `Robert Tennent` differs by three characters; `B-Line` vs `Hamilton LRT` shares none.
   Both count as different. Record the edit-distance distribution alongside the median so a
   reader can see what the population is, and claim no graded effect this run cannot
   separate.
3. *The floor is pooled across subsets.* Verify it per subset too; a floor that differs by
   subset would mean prompt form varies in a way Arm A's single number hides.
4. *Delivery, not effect* — [E-028d], 2.96x. Unchanged and binding.

**Deliverable.** One table: subset x (different-surface alias median, canonical-substring
median, same-entity median, permuted floor, n). The claim is carried by the first column
against the third, per subset.

**Scope.** All three subsets, layer 5, Llama-3.1-8B, coefficient only, no edit applied.
~2,578 entries at [E-037]'s observed rate is roughly 4.5 hours. Deferred: other layers,
other models, any effect measurement.

**Blockers:** none. The per-subset table (confound 1) and the surface-distance
distribution (confound 2) were added to `report()` on 2026-10-14 and exercised by
`dryrun_e037.py`, including a SPLIT BY SUBSET case and a no-false-split case. Re-running
[E-037] from its key cache shows them on real data: 3 of 9 aliases are near-variants
(ratio >= 0.8, `Robert Tennent` -> `Rob Tennent`) and the rest are acronyms or alternate
names (`Royal Ontario Museum` -> `ROM`, 0.261), which is the population confound 2 said a
reader must be able to see.

**Result (2026-10-15).** Arm A **CONTROLLED** and unmoved at 6x [E-037]'s n: floor
**0.069**, same-entity 0.968-1.000, separation **0.902** over 23,505 readings.
Compositionality I is n=7,856 at 0.982.

**Arm B cleared its threshold and its own confound then forbade the headline.** n=370
different-surface aliases, pooled at **0.304** against same-entity 0.972 — which the runner
called STRING-KEYED. Confound 1 says a pooled median stands only if the subsets agree, and
they span **0.408**: popular 0.587 (n=19), random 0.301 (n=314), recent 0.179 (n=37), with
`random` supplying 314 of 370. **What is licensed: aliases sit below same-entity in all
three subsets — by 0.38, 0.67 and 0.79. Direction robust, magnitude not quotable.** That
settles the question: [E-036]'s withdrawn "keyed on the ENTITY, not the string" is
affirmatively refuted, independently in each subset.

**Three attempts.** The run died twice at ~1,300 entries on a malformed NDIF payload that
`retrying` did not classify as transport, and `watch.py` reported the first death as ok.
See [E-039]'s entry and the commits of 2026-10-14/15.

**Artifacts:** run_e037.py; results/E-037-ripple-floor-recent+random+popular.json;
logs/run_e037-2026-10-14-222439.log; logs/e-038-stderr.log;
agents/shared/decisions.md -> "[E-038] Result"
**Closed:** 2026-10-15

### E-039 · The within-benchmark control: MQuAKE hop-1 against hop-2+ questions

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-14
**Updated:** 2026-10-14
**Thread:** T-088 · follows [R-014], [E-037]

**Description:**

[E-037] measured 0.982 on RippleEdits' *different-entity* tests and the reason was that
their prompts name the edited subject verbatim. [E-037]'s own control — a permuted `k*` —
is a **synthetic** floor: it answers "would a stranger's edit reach this prompt" and not
"does a real different-entity test escape its own edit". [R-014] found a benchmark that
supplies the second control without anyone constructing it.

**MQuAKE names the edited subject iff the edit is on hop 1**: 6,861 of 6,861 at hop 1,
**0 of 16,506** at hops 2-4, exact in both directions, because it phrases a chain from its
head and a hop-2 edit targets an entity the question never mentions.

> chain: *Michael Feinstein → country of citizenship → **United States of America** →
> capital → Washington, D.C.*; edit on hop 2; question: *"What is the capital city of the
> country that Michael Feinstein is a citizen of?"*

**So the two arms live in one dataset, one prompt register, one edit set, one relation
distribution, differing in the single property under test.** The cross-benchmark confound
that would make "compare RippleEdits to MQuAKE" unreadable is gone by construction, and
nothing about the split was designed by us — it is read off `orig.triples_labeled`.

**Method.** [E-036]'s measurement, unchanged: `k*` at the subject's last token of
`requested_rewrite`'s prompt; coefficient at the subject's last token of the test prompt.
Layer 5, Llama-3.1-8B. Single-edit instances only, so the hop attribution is unambiguous.

**The position problem is the design question, and it must be settled before running.** A
hop-2+ question does not contain the edited subject, so there is no "subject's last token"
to read. Three candidate positions, and the ticket must pick one and say why:
1. **Final token of the prompt.** What the model actually answers from. Defensible, and
   not comparable to the hop-1 arm, which is read at the subject.
2. **Final token in BOTH arms.** Comparable, and discards the pinning this project is
   about.
3. **Subject position where one exists, final token where it does not.** What a
   benchmark's own scoring does, and the honest description of what a practitioner gets.

**Pre-registered: run 2 as the headline and 3 alongside.** Arm 2 is the only one where a
difference between hops cannot be an artifact of reading different positions; arm 3 is what
anybody actually experiences. Arm 1 is dropped and recorded as dropped.

**Pre-stated outcomes.** Median coefficient, hop-1 vs hop-2+, at the final token.

- **ESCAPES** — hop-2+ sits **<= 0.30** while hop-1 sits **>= 0.70**. A genuine
  different-entity test does escape the update, RippleEdits' 0.982 is a property of *its
  construction* rather than of multi-hop testing, and §4.6 must say so prominently.
- **NO ESCAPE** — hop-2+ sits **>= 0.70**. Then naming the subject is not what delivers the
  update, [E-037]'s explanation of Table 11 is wrong, and the whole §4.6 reading needs
  rewriting. **This is the outcome that costs us the most and it is live**: the final token
  of *"...that Michael Feinstein is a citizen of?"* shares no prefix with the edit prompt,
  but [E-019] measured 0.95 for subject-late probes at layer 5, so prefix-sharing is not
  the only route to a high coefficient.
- **BETWEEN** — report both medians and the gap; claim no band.

**Confounds.**
1. *Question form differs with hop depth.* A hop-4 question is longer and more clausal than
   a hop-1 one. **Control by restricting the headline to 2-hop chains**, where hop-1 and
   hop-2 edits produce questions of near-identical shape, and report 3- and 4-hop
   separately.
2. *MQuAKE's edits are not ROME edits.* We read `requested_rewrite` and compute `k*`
   ourselves; no MQuAKE-reported number is used or comparable. Say so.
3. *Hop-1 and hop-2 edits differ in relation distribution* — hop-2 subjects are
   disproportionately countries. Report the relation breakdown; a country-heavy arm may
   differ for reasons unrelated to hop.
4. *Delivery, not effect* — [E-028d], 2.96x. Binding.

**Deliverable.** One table: hop depth x (hop-1 edit, hop-2+ edit) median coefficient at the
final token, with IQR, n, and the 2-hop-only row as the controlled comparison.

**Scope.** MQuAKE-CF-3k, single-edit instances, layer 5, Llama-3.1-8B, coefficient only, no
edit applied. Deferred: MQuAKE-CF's full 27,654, MQuAKE-T, other layers, any effect
measurement.

**A relation-matched sub-comparison exists and the ticket did not anticipate it.**
Confound 3 said the arms' relation mixes differ, and they do — hop-1 is dominated by P27
(104 of 213 two-hop instances), hop-2 by P495/P37/P35/P112/P36. But **P495 appears in both
arms** (34 hop-1, 58 hop-2), so a relation-matched row is available for free. The runner
reports every relation spanning both arms, and **says UNCONTROLLED out loud when none
does** rather than printing an empty table that reads as a clean control.

**Sizing, counted before writing the runner.** MQuAKE-CF-3k single-edit two-hop instances:
**213 hop-1, 300 hop-2**, three questions each.

**Built 2026-10-14, ahead of the budget.** `run_e039.py`, `tools/dryruns/dryrun_e039.py`
(7 cases: three verdict bands, both confound tables, the disjoint-relation warning, and an
empty 2-hop row), all six preflight gates pass. Queued behind [E-038] so the loop starts it
when the budget frees; if [E-038] escalates the queue stops and this does not run, which is
the intended behaviour and not a bug.

**Result (2026-10-15).** VERDICT: **BETWEEN** — and the pre-registered headline arm was
uninformative, for a reason this ticket should have caught at design time.

```
arm                          n     FINAL     IQR     NATURAL     IQR
hop 1 (names the subject)  639     0.027   0.015       0.933   0.072
hop 2+ (does not)          900     0.055   0.039       0.055   0.039
```

FINAL was chosen as the headline because it is the only reading immune to a positional
artifact. True, and incomplete: **at the final token of a multi-hop question neither arm
receives anything** — 0.027 and 0.055, at or below [E-038]'s 0.069 floor. A comparison with
no variance in it cannot discriminate, and nothing in the ten lenses asked whether the
chosen measure *varies* before it was fixed. Confound 3 agrees: P27 reads 0.024 against
0.024 at n=312 and n=51.

**The finding is in the secondary arm, and is reported as a measurement rather than a band**
— promoting NATURAL to headline after seeing the numbers is the move pre-registration
exists to prevent. hop-1 questions receive **0.933** at the edited subject's token; hop-2+
questions receive **0.055** at every position they have. Within one prompt the subject token
and the final token are a factor of **35** apart.

**The consequence for §4.6 is larger than the result.** Table 11's 0.982 is read at the
subject's token, and this run shows the final token of such a prompt sits near the floor —
so the coefficient is a property of **a token**, not of a prompt, and the answer position is
not that token. It does *not* follow that the edit fails to reach the answer: the measure
sees direct layer-5 delivery only, and the path through attention at layers 6+ is invisible
to it. §4.4's delivery-versus-effect gap, in its positional form.

**Unplanned corroboration.** [E-038]'s floor is a permuted `k*` on RippleEdits (0.069);
this one is a different token on MQuAKE (0.027–0.055). Different corpus, different
construction — same range.

**Artifacts:** run_e039.py; tools/dryruns/dryrun_e039.py;
results/E-039-mquake-hops-MQuAKE-CF-3k.json; logs/run_e039-2026-10-15-010314.log;
agents/shared/decisions.md -> "[E-039] Result"
**Closed:** 2026-10-15

### E-040 · Is the alias drop graded by surface distance, and does that explain E-038's subset split?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-087 · follows [E-038]

**Description:**

[E-038] established that renaming a subject reduces delivery in all three RippleEdits
subsets, and that the **magnitude is not quotable** because the subsets span 0.408 — popular
0.587, random 0.301, recent 0.179. That span was reported as a confound. This ticket asks
whether it is instead a **consequence**: if the drop is graded by how different the alias
string is, and the subsets differ in what kind of aliases they contain, then one mechanism
explains both the drop and the disagreement.

No compute. The 370 alias coefficients and their SequenceMatcher ratios are already in
`results/E-037-ripple-floor-recent+random+popular.json`, written in the same loop iteration
and therefore index-aligned by construction (verified: 370 and 370).

**DISCLOSURE — this ticket is not fully pre-registered, and saying so is the point.**
While verifying that alignment I computed two bucket medians and saw them: ratio < 0.5
gives **0.105** (n=140), ratio >= 0.8 gives **0.837** (n=124). **No outcome below is stated
about those two buckets**, because a band written after seeing the number it judges is
decoration. What is pre-registered is everything that quantity does not determine — the
functional form, the subset decomposition, and the token-length control — none of which has
been computed.

**Pre-stated outcomes**, on quantities not yet seen.

1. **Functional form.**
   - **GRADED** — Spearman rho between surface ratio and coefficient is `>= 0.5` in
     magnitude, **and** a linear fit leaves less unexplained variance than a step function
     at its best-fitting threshold. The key is a continuous function of the token sequence.
   - **THRESHOLD** — a step beats the line. There is a surface-similarity boundary rather
     than a slope, and where it sits is the number worth reporting.
   - **NEITHER** — rho below 0.5. The bucket contrast is driven by something other than
     string distance and this ticket's premise is wrong.

2. **Does it explain [E-038]'s split?** Stratify each subset's aliases by ratio and compare
   within strata.
   - **EXPLAINS** — within strata, the three subsets' medians come within **0.15** of each
     other. Then the span is composition, not disagreement, and **[E-038]'s "magnitude not
     quotable" is lifted**: the quotable quantity is the slope, not the median.
   - **DOES NOT EXPLAIN** — the subsets still differ by more than 0.15 within strata.
     Something about the subsets beyond their alias composition is doing the work, and the
     [E-038] caution stands as written.

**Confounds.**
1. *Surface ratio correlates with token-count difference, and `subject_last_index` reads a
   token position.* A shorter alias is fewer tokens, so "different string" and "different
   position" are entangled. **Control: report rho partialled on the token-length
   difference, and report that difference's own rho alongside.** If length does the work,
   this is a fact about tokenisation and must be said that way.
2. *Acronyms are their own population.* `John Greif II Airport` -> `SPR` scores 0.000 and is
   not merely "a bit different". Report the acronym-like cases separately (alias is short,
   mostly uppercase, and a subsequence of the canonical initials).
3. *`random` supplies 314 of 370.* Any pooled fit is mostly one subset's. Report per-subset
   slopes before the pooled one, exactly as [E-038] learned to.
4. *This is delivery.* [E-028d], 2.96x.

**Deliverable.** One number — the Spearman rho — and one table: ratio stratum x subset x
median coefficient, with n per cell, showing whether the subsets converge within strata.

**Scope.** The 370 different-surface aliases already measured. No model, no new runs.
Existence per [O-004].

**Result (2026-10-15).** **GRADED.** rho **+0.778** (n=370), slope **+0.847**, intercept
−0.058 — a line beats the best step (RSS 18.29 vs 20.60). **Delivery to a renamed subject is
approximately the string similarity between the new name and the old one.** Confound 1 is
controlled: token-count difference correlates −0.335 and partialling it out moves rho only
to +0.746, so this is about the string rather than the read position. 58 acronym-like
aliases sit at 0.080, consistent with the slope.

**Subset question: SPLIT NOT EXPLAINED as pre-registered, and that verdict rests on
`popular`'s 5/5/9-alias cells** — an `n >= 3` inclusion threshold I set too low. Restricted
post-hoc to `n >= 10`, `random` and `recent` agree to **0.017** and **0.033**, far inside
the 0.15 band: composition explains the difference where the data can carry it. `popular`
has 19 aliases total and is unresolvable, and it is the subset at the top of [E-038]'s span
— so **[E-038]'s caution stands, for a reason now precisely located.**

**Artifacts:** run_e040.py; results/E-040-alias-gradient.json;
logs/run_e040-2026-10-15-080318.log; agents/shared/decisions.md -> "[E-040] Result"
**Closed:** 2026-10-15

### E-041 · Attention or MLP? Decomposing what reorients the subject key with depth

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-078 · follows [E-020]/[T-077]

**Description:**

[T-077] established that the subject key reorients by **direction**, not magnitude: cosine
to the edit-form key falls **0.984 → 0.471** across depth while the norm ratio never leaves
0.97–1.24 and drifts slightly *up*. Its answer explicitly refuses the next step — *"a
falling cosine is consistent with attention mixing, with MLP writes at the subject
position, and with anything else that reorients the residual stream."* [T-078] is that step.

**This ticket does not run the test [T-078] proposed, and the reason is the point.**
[T-078] says to compare attention *patterns* at the subject's last token between the edit
form and a reformulated one, and read a difference as evidence of context mixing. **That
test largely confirms itself.** The edit form is `"{} was born in the city of"` — the
subject sits at the start with almost nothing before it — while `"The city where {} was
born is"` places three tokens before the subject. Their attention patterns at that position
*must* differ, because one position has context available and the other does not. A
difference would be read as mechanism when it is a property of the prompts.

**What this measures instead.** The residual stream at the subject's last token is a sum:

    h(L) = embed + Σ_{l<L} [ attn_out(l) + mlp_out(l) ]

so the divergence between two forms' keys accumulates term by term, and each term is
readable. At every probed layer, for every form, read `self_attn.output` and `mlp.output`
at the subject's last token and accumulate

    D_attn(L) = ‖ Σ_{l<L} (attn_out_form(l) − attn_out_edit(l)) ‖
    D_mlp(L)  = ‖ Σ_{l<L} (mlp_out_form(l)  − mlp_out_edit(l))  ‖

**Which module writes the divergence is then a number rather than a candidate.**

**Pre-stated outcomes.** Compared at the layers where [E-020]'s cosine falls fastest.

- **ATTENTION WRITES IT** — `D_attn` exceeds `D_mlp` by **>= 2x**. Context mixing is the
  mechanism, [T-077]'s leading candidate is confirmed, and "structural at layer 5" has a
  cause rather than a correlation.
- **MLP WRITES IT** — `D_mlp` exceeds `D_attn` by **>= 2x**. The reorientation is written
  by the MLP at that position, the attention account named in [E-020] is **wrong**, and
  this is the more interesting outcome because nothing in the record predicts it.
- **BOTH** — within 2x of each other. Then the decomposition does not separate them and the
  ablation in confound 1 becomes the necessary follow-up rather than an optional one.

**Confounds.**
1. *The MLP's input depends on attention, so attention can drive `D_mlp` indirectly.*
   **This decomposition attributes DIRECT WRITES and not ultimate causation**, and no
   sentence in the entry may say otherwise. The causal version is an ablation — zero
   attention from the subject's last token to every preceding non-subject token and ask
   whether the key still reorients — and it is **deferred to a follow-up**, named here so
   the limit is on the record rather than discovered by a reviewer.
2. *The forms differ in how many tokens precede the subject, which is exactly what makes
   [T-078]'s own test circular.* **Control: a filler-padded edit form** — the edit form
   with semantically inert tokens prepended so the subject sits at the same index as in the
   late-clause form. If padding alone reproduces the late clause's divergence, the effect is
   about **position**; if it behaves like the unpadded edit form, it is about **content**.
   This is the arm that decides whether anything here is about context at all.
3. *Sixteen subjects, one relation, one model.* [E-033] found a 6/6 effect and a 1/6 effect
   in the same run. Existence per [O-004]; no rate, and no claim beyond this relation.
4. *Delivery, not effect* — [E-028d], 2.96x. Binding as everywhere.

**Deliverable.** One table: layer x (D_attn, D_mlp, their ratio, and [E-020]'s cosine at
that layer), so the accumulation can be read against the thing it is meant to explain.

**Method.** Reuse `decompose_t077.py`'s subjects, forms and layer set so the cosines are the
same numbers [E-020] reported. Saves must be **unrolled** — [O-008]: a loop inside a trace
body raises nothing and returns zero saves.

**Scope.** Llama-3.1-8B, 16 subjects, the [E-020] forms plus the padded control, layers
[0, 3, 5, 8, 12, 16, 24, 31], read-only. Deferred: the attention ablation (confound 1),
other relations, other models.

**Result (2026-10-15).** **VERDICT: BOTH** — deeper-half ratio **0.81**, inside the
pre-stated [0.5, 2.0], so the decomposition does not separate them at the fixed threshold.

**The band is not the finding.** Across three forms and eight layers — 24 cells —
**attention never writes more of the divergence than the MLP anywhere**; the highest ratio
in the table is **1.03**. The MLP leads ~2x early, draws level at 12-16, and leads ~3x at
layer 31, where the cosine has fallen furthest. So the attention-mixing account [E-020]
named as leading is **directionally contradicted at every depth**, while MLP WRITES IT is
not claimed because 0.81 does not meet the 2x bar set in advance.

**A design error caught by reading the output, not the gates.** The first run's five forms
collapsed to **three distinct prefixes**: under causal attention only the tokens up to and
including the subject matter, so `"{} died in the city of"` is bit-identical to the edit
form (exact zeros, ratio `inf`) and the padded control was bit-identical to the late
clause. Confound 2's control was a duplicate of what it controlled for, and the verdict was
computed over a duplicate plus an infinity. Forms are now keyed by prefix and asserted
distinct before the run proceeds. The error is this project's own central mechanism
appearing as a mistake in its design.

**Confound 2, properly run.** A matched-length unrelated prefix produces about **half** the
divergence of a related one through the middle layers (filler/late = 0.49-0.66 at L8-16)
and **converges to 0.90 by L31**. Position alone reorients substantially; related content
roughly doubles it where the network does relational work, and the advantage washes out
near the output.

**The BOTH verdict makes confound 1's ablation necessary rather than optional** — [T-095].

**Artifacts:** run_e041.py; tools/dryruns/dryrun_e041.py;
results/E-041-reorientation.json; agents/shared/decisions.md -> "[E-041] Result"
**Closed:** 2026-10-15

### E-042 · Does the negative ‖Δv‖ sign survive a different relation, model, layer and probe?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-094 · follows [E-035]

**Description:**

[E-035]'s strongest association is `‖Δv‖` against propagation at **−0.423**: *a bigger
update travels less far*, which is the opposite of the rationale the candidate was listed
with. [T-094] says the first move is **not a theory but a check on whether the sign
survives**, because [E-033] found a 6/6 effect and a 1/6 effect sitting side by side in one
run.

**That check costs nothing.** [E-033] left six result files, each carrying `‖Δv‖` per
subject alongside pre- and post-edit log-probabilities for three probes with their own
controls. Six cells: **2 models × 2 relations × 2 layers**, n=29 each.

**Method.** Per cell, per subject, the same control-differenced outcome [E-029] used:
`(base[self|p] − edit[self|p]) − (base[control|p] − edit[control|p])` on that cell's
**type-matched** probe, correlated with `‖Δv‖` by Spearman. No model, no network.

**Pre-stated outcomes.**

- **SIGN HOLDS** — the correlation is negative in **>= 5 of 6** cells. The [E-035]
  observation is not specific to one relation, model or layer, and [T-094] becomes a
  question about mechanism rather than about replication.
- **SIGN DOES NOT HOLD** — negative in **<= 2 of 6**. [E-035]'s −0.423 is a fact about that
  one configuration and must be written as one, which would also weaken [R-015]'s reopening
  of [T-085].
- **MIXED** — 3 or 4 of 6. No general statement; report the table and say which cells
  differ.

**Confounds.**
1. **All 29 subjects in every cell are a subset of [E-035]'s 42.** These are **not
   independent replications**: they vary model, relation, layer and probe while holding the
   *people* fixed. A consistent sign therefore shows the effect is not specific to the
   relation/model/layer/probe, and says **nothing** about whether it is specific to these
   29 subjects. No sentence may call this a generalisation across subjects.
2. *The six cells are not independent of each other either* — they share a pipeline, a
   subject pool and an optimiser configuration. Counting 5-of-6 is a consistency check, not
   six trials, and no p-value over the six is computed because it would imply independence
   this design does not have.
3. *`‖Δv‖` depends on how hard the target was to install.* Within a cell the relation and
   injected type are fixed, which controls it partly; across cells it is uncontrolled and is
   a candidate explanation for any sign that does flip.
4. *Delivery, not effect* — [E-028d], 2.96×. The outcome here is a measured drop, so this
   one is about **effect**, unlike most of the record. Say so rather than inherit the
   standard caveat wrongly.

**Deliverable.** One table: cell (model × relation × layer) × ρ(‖Δv‖, propagation), n, and
the matched probe. One line on how many of six are negative.

**Scope.** The six [E-033] files already on disk. No new measurement. Existence per
[O-004].

**Result (2026-10-15).** **SIGN HOLDS** by the pre-registered band — 5 of 6 negative —
**and the magnitudes say something narrower.**

```
8B    birthplace  L5   -0.364   substantial
70B   birthplace  L5   -0.131   near-zero
70B   occupation  L13  -0.116   near-zero
70B   occupation  L5   -0.073   near-zero
70B   birthplace  L13  -0.063   near-zero
8B    occupation  L5   +0.087   near-zero
```

Five of six are |rho| < 0.2, median −0.095, and the one substantial cell is the same model
and relation as [E-035]'s −0.423. A sign test on 5-of-6 gives p = 0.219 *granting* an
independence confound 2 denies. **The honest statement is "substantial in 8B/birthplace, a
weak consistent lean elsewhere", not "the sign generalises"** — the band counted signs and
cannot see magnitude, which is a defect in the band I wrote.

Narrows [R-015]: `‖Δv‖` as something ES margin cannot see may be specific to one
configuration. [T-085]'s amendment now carries that caveat.

**Artifacts:** run_e042.py; results/E-042-dv-sign.json;
logs/run_e042-2026-10-15-102445.log; agents/shared/decisions.md -> "[E-042] Result"
**Closed:** 2026-10-15

### E-043 · Is `popular`'s retained delivery about familiarity, or still about composition?

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-092 · follows [E-038]/[E-040]

**Description:**

[E-038] found alias medians of **popular 0.587, random 0.301, recent 0.179** — a 0.408 span
that made the pooled figure unquotable. [E-040] showed the drop is **graded by surface
similarity** (ρ = +0.778, slope +0.847) and that, within similarity strata, `random` and
`recent` agree to 0.017–0.033. **Composition explains those two.** `popular` has 19 aliases
in cells of 5, 5 and 9 and could not be tested, and it is the subset at the top of the span.

[T-092] names two accounts that predict opposite things: **familiarity** — a well-known
entity's alias is itself well-represented, so it keys closer to the canonical form and
survives stratification — against **composition**, which [E-040] would have caught with n.

**The thread assumed this needs new measurement. It does not.** The 370 alias coefficients
already exist, all 288 of their canonical subjects map to Wikidata QIDs in the released
files, and **sitelink count** — how many Wikipedia language editions carry the entity — is a
standard popularity proxy available from the same API this project already uses. So the
question becomes: **does popularity predict delivery after surface similarity is partialled
out?** No model, no edits, no NDIF.

**Pre-stated outcomes.** Partial Spearman of coefficient on sitelink count, controlling for
SequenceMatcher ratio, over n=370.

- **FAMILIARITY** — partial ρ **>= +0.20**. A well-known entity retains delivery under
  renaming beyond what string similarity explains, [T-092] has its answer, and [E-038]'s
  subset span becomes a popularity effect rather than an unexplained one.
- **NOT FAMILIARITY** — |partial ρ| **< 0.20**. How well known the entity is does not
  predict delivery once the string is accounted for; the `popular` subset's behaviour needs
  a different account and [E-038]'s caution stands undisturbed.
- **INVERTED** — partial ρ **<= −0.20**. Well-known entities lose *more* delivery under
  renaming, which no account on the table predicts and would be the most interesting result.

**Confounds.**
1. *Sitelink count is a proxy for popularity, not popularity.* **Validity check, reported
   first:** sitelink count must separate RippleEdits' own `popular` subset from `recent`,
   or the proxy does not measure what the subsets encode and no outcome below is readable.
2. *370 aliases come from 288 subjects*, so they are not independent — a subject with
   several aliases contributes several rows. **Report the per-subject aggregate alongside
   the per-alias figure**; if they disagree, the per-subject one governs.
3. *Sitelink count is heavily skewed.* Spearman throughout, never Pearson.
4. *Surface similarity is the thing being controlled for, and [E-040] showed it is strong*
   (ρ = +0.778). A partial correlation against a dominant covariate is unstable where the
   covariate's range is narrow; **report the stratified table as well as the partial**, so
   the answer does not rest on one estimator.
5. *Delivery, not effect* — [E-028d], 2.96×.

**Deliverable.** One number — the partial ρ — and one table: similarity stratum × sitelink
tertile × median coefficient, with n per cell.

**Scope.** The 370 aliases from [E-038], their 288 QIDs, and one Wikidata fetch. Existence
per [O-004] — this is a claim about these entities, never a rate.

**Result (2026-10-15).** **NOT FAMILIARITY**, and composition explains all three subsets.

Proxy gate passed first: sitelink medians are popular **50.0**, recent **4.0**, random
**0.0** — decisive and correctly ordered. Partial rho of coefficient on sitelinks
controlling for similarity: **+0.043** per alias, **+0.046** per subject, both inside the
pre-stated band. The stratified table agrees across estimators.

What does explain it, on two independent composition measures that rank-order exactly with
the coefficient:

```
subset       n   median ratio   median coef   near-variants
popular     19          0.769         0.587      47%
random     314          0.615         0.301      34%
recent      37          0.533         0.179      19%
```

`popular`'s aliases are simply more similar strings, which is what [E-040]'s +0.847 slope
predicts. **[E-038]'s 0.408 span is composition**, and its "magnitude not quotable" resolves
to: the median is not quotable, the slope is.

**Limit:** `popular`'s within-stratum test is still underpowered at n=19. This is two
aggregate composition measures plus the independent elimination of the alternative, not a
direct within-stratum replication for that subset.

**Artifacts:** fetch_sitelinks.py; run_e043.py; results/E-043-popularity.json;
data/wikidata/sitelinks.json; agents/shared/decisions.md -> "[E-043] Result"
**Closed:** 2026-10-15

### E-044 · Does the subject key still reorient when context cannot reach it?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-095 · follows [E-041]

**Description:**

[E-041] decomposed the key's divergence into direct writes and found the MLP term larger
than the attention term at every depth — but **the MLP's input depends on attention**, so an
attention-driven reorientation routed through the MLP is indistinguishable from a local one
in that measurement. It said so before running. [T-095] is the causal version.

**[T-095]'s design note ruled out two implementations.** Zeroing `self_attn.output` deletes
RoPE along with context, collapsing both forms to the same embedding and returning
"attention necessary" for a reason unrelated to context. Truncation ablates nothing.

**The third is expressible with documented model inputs and was probed before this ticket
was written.** Pass `attention_mask` with the non-subject prefix zeroed, together with
**explicit `position_ids`** so RoPE cannot shift when the mask does. Verified on the remote
model: position 0 is bit-identical, the masked span and everything after it changes. No
internals touched.

**Method.** For each form, mask positions `[1, subject_start)` — the prefix, keeping BOS,
which is an attention sink and whose removal would destabilise the forward pass for reasons
unrelated to the question. Read the key at the subject's last token at [E-020]'s layers and
recompute the cosine to the edit form's key, which is the same quantity [T-077] measured
falling 0.984 → 0.471.

**Because `position_ids` are pinned, the subject still sits at its own index in each form.**
So any divergence surviving the mask is **positional** — RoPE — and not contextual. That is
the decomposition this ticket buys.

**CORRECTNESS GATE, and the ticket does not run without it.** The edit form has **no**
non-subject prefix, so its mask is empty and its numbers must reproduce [E-041]'s
**exactly**. Rule 4 of `LOOP.md` exists because seven harness defects in two days each
returned a plausible value; an intervention whose failure mode is "silently masks nothing"
or "silently shifts RoPE" is precisely that shape. **The run aborts if the edit form moves.**

**Pre-stated outcomes.** Median cosine between each form and the edit form, at depth
(layers 16–31), under the mask.

- **CONTEXT NECESSARY** — cosine rises to **>= 0.95** at every layer. Cutting attention to
  the prefix removes the reorientation, so context mixing is what does it and [E-041]'s
  direct-write reading was the wrong frame.
- **CONTEXT NOT NECESSARY** — cosine stays **<= 0.75** at depth. The reorientation survives
  with context unreachable, so it is positional, and [E-020]'s attention account is wrong in
  a second independent way.
- **PARTIAL** — in between. Report **the fraction of [E-041]'s divergence the mask removes**,
  which is the informative quantity and is what [E-041]'s matched-filler arm predicts: a
  same-length unrelated prefix produced ~60% of a related one's divergence, so masking
  content should remove roughly 40%.

**Confounds.**
1. *Masking changes the forward pass for every position, not only the subject's.* We read
   only the subject's last token, and the gate confirms the unmasked case is untouched.
2. *BOS is kept.* Masking an attention sink is a different intervention with its own
   literature; keeping it is a choice and is recorded as one.
3. *A masked token still computes* — it attends to unmasked predecessors and is simply not
   attended **to**. The claim is about what reaches the subject position, not about deleting
   tokens.
4. *Delivery, not effect* — [E-028d], 2.96×.

**Deliverable.** One table: layer × form × (cosine unmasked, cosine masked, fraction of
divergence removed), with [E-020]'s original cosine as the anchor column.

**Scope.** Llama-3.1-8B, [E-041]'s 16 subjects and forms, layers [0,3,5,8,12,16,24,31].
Existence per [O-004].

**Result (2026-10-15). The runner printed CONTEXT NOT NECESSARY and the record REJECTS
the verdict.** The gate passed exactly — the edit form moved **0.00e+00** under a mask that
masks nothing — so the intervention is **faithful**. It is also **invalid**.

Three signatures: (a) masking makes divergence *worse*, 0.961 → 0.485 at L5, so the band's
premise is inverted; (b) masking 5 prefix tokens instead of 4 changes the cosine by
**6.85e-03**, so one position of RoPE offset is worth 0.007 against a 0.476 gap — it is not
positional; (c) the same positions filled with **real innocuous tokens** read **0.983**
where masked they read 0.485, so the gap is about masking, not position. Per-subject masked
values run 0.075–0.822, the instability of an input the model has no distribution for.

**The methodological result is the valuable one: a correctness gate proves an intervention
is FAITHFUL, not that it is VALID.** `LOOP.md` rule 4 extended accordingly.

[T-095] is answered from [E-041]'s existing in-distribution data instead — position with an
innocuous prefix carries most of the deep divergence (0.265 of 0.370) and related content
adds the rest.

**Artifacts:** run_e044.py; tools/dryruns/dryrun_e044.py;
results/E-044-context-ablation.json; logs/run_e044-2026-10-15-213307.log;
agents/shared/decisions.md -> "[E-044] Result"
**Closed:** 2026-10-15

### E-045 · Does the model hold typeshed signature facts at a CounterFact-comparable rate?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-098 · the gate on claim 3

**Description:**

Claim 3 is *"code as domain for weight edits."* [T-099] established what a decidable oracle
does and does not buy: [T-058] built genuinely deductive grounds and [E-015] found the
editor indifferent, so a formal domain **does not make editing cleaner** — it makes the
**audit** decidable. That is still worth having, and it is claim 2.

**But the whole direction has one precondition and it has never been checked.** Declaration
1 binds a fact to its probe set; [E-005] measured possession at **56/74/79/85%** at
6B/8B/70B/405B for ordinary CounterFact claims. **An invented notation would have
possession near zero** — deriving a synthetic formal corpus would install strings rather
than edit beliefs. Python's stdlib with typeshed escapes that: the model has seen
`os.path.join` ten thousand times, and the stub is a machine-checkable ground truth.

**The facts are machine-derived, not hand-picked**, which matters for the §5 circularity
objection. Parsed from `python/typeshed@main` with `ast`: every module-level public
function carrying a return annotation, excluding typevars and private aliases (stub
machinery, not facts), and excluding `Any`/`object`/`Incomplete` — **those record what the
stub author left unspecified, not a property of Python.** 666 functions survive.
`probes/typeshed_return_types.jsonl`.

**Method.** `src/possession.py` **unchanged**. Prompt: *"In Python, the function
`{name}` returns a value of type"*; true answer the annotation; candidates the 50 most
common annotations, so **N = 50 exactly as [E-005] used** — the module's own docstring warns
that *"absolute levels depend on N"*, and a comparison at a different N would be worthless.

**Pre-stated outcomes.** Possession on Llama-3.1-8B, against [E-005]'s **74%** for
CounterFact at that model and that N.

- **HELD** — possession **>= 60%**. The model holds stub-level signature facts about as
  densely as it holds encyclopaedic ones, and claim 3 is executable with the instrument
  already built. The code domain becomes a real project.
- **THIN** — possession **<= 30%**. It does not, and a formal-domain audit would be
  measuring facts the model never had. Claim 3 needs a different fact type, or it is a
  wish — learned in a day rather than after a corpus build.
- **BETWEEN** — 30–60%. Report which kinds of function hold; the answer is then about
  *which* code facts rather than whether.

**Confounds.**
1. **The answer distribution is skewed** — `None` is 183 of 666, `str` 124. A model could
   score by type frequency rather than knowledge. The filter's second arm already tests
   lift against a subject-free prompt, but **the rank-1-only rate must be reported beside
   the possession rate** so the gap that the lift arm removes is visible rather than
   implied.
2. *The prompt phrasing is ours and untested.* A low rate could be phrasing rather than
   ignorance. **Control: report possession by answer type.** If `str` holds and `None` does
   not, that is informative; if nothing holds, phrasing is a live alternative and the
   THIN verdict must say so.
3. *Teacher-forced* — measures whether the knowledge is **present**, not whether the model
   would emit it. Same caveat [E-005] carries; inherited, not re-litigated.
4. **Possession is not editability.** A held fact may still resist editing. This ticket
   gates the direction and licenses nothing about whether code facts edit cleanly.

**Deliverable.** One number — possession at N=50 on Llama-3.1-8B — beside [E-005]'s 74%.
One table: answer type × possession × n.

**Scope.** 200 facts sampled with a fixed seed from the 666 (cost), one model, one prompt
form. Existence per [O-004].

**Result (2026-10-15). BETWEEN at 49.5%** against [E-005]'s 74%, with template-alone
baselines of 9% and 4% — so the comparison is fair and the possession is real, just thinner.

**One row is an artifact and it is ours.** `int` scores 0/18 while the model ranks `int`
first for 15 of them: **all 18 have `rank_prior == 1`**, because the bare template already
predicts `int`. Lift is ≤ 0 by construction. **A fact whose answer is the template's own
prior cannot be scored by this measure** and should be reported unscoreable rather than
not-held — excluding them, possession is **54.4%**. Confound 1 asked for the rank-1 row,
which would not have shown this; the prior row, which did, was not asked for.

**What holds is characterisable**, which beats a single rate: `float` 100%, `complex` 89%,
`str` 85%, `bool` 67%, `bytes` 57% — against `None` 28%, `str | None` 0/4, `tuple[...]`
0/4. The model holds a return type where the function's purpose **determines** it and fails
where the stub author chose among plausible alternatives.

**Confound 2 answered:** a 100%-to-0% spread on one prompt form rules out phrasing as the
explanation for the low cells.

**For claim 3:** viable on a subset, not wholesale. An audit on typeshed must restrict to
determined return types or accept that half its facts were never held — a design constraint
bought for one 6-minute run instead of a corpus build. Spawns [T-100].

**Artifacts:** run_e045.py; tools/dryruns/dryrun_e045.py;
probes/typeshed_return_types.jsonl; results/E-045-typeshed-possession.json;
agents/shared/decisions.md -> "[E-045] Result" _(unratified)_
**Closed:** 2026-10-15

### E-046 · After an unrelated edit, what does the model say the attribute IS?

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-10-24
**Updated:** 2026-10-24

**Description:**
[E-024] and [E-033] measured only log P(*correct* answer) on the occupation and
citizenship probes. They record what the model **gave up**, never what it now
**believes instead**. Saif raised the objection that makes this load-bearing: if
Vlaminck is now born in Chile, falling confidence in "French citizen" may be
*coherent revision* rather than damage, and §4.5's claim is explicitly about the
answer's **type** — a claim about what an answer becomes, tested so far only by
what it stopped being.

Read the top-K vocabulary distribution at the first answer token, base and edited,
for both probes, over the same 37 subjects as [E-024]. One remote call per
(subject, probe, condition) — no greedy decode, no new edits; deltas and k* load
from the [E-014] cache.

Classify each top-1 against two pools built mechanically from the Wikidata
snapshot already in the repo (every P106 label and every P27 label seen across the
chain subjects), so the categories are not hand-enumerated.

**Pre-stated outcomes:**
- **CONFIRM (displacement):** edited top-1 leaves the occupation pool, and/or moves
  toward the injected country's type. §4.5 strengthened; the coherent-revision
  reading is refuted on its own ground.
- **DENY (coherent revision):** edited top-1 stays inside the occupation pool in
  most cases — a within-type reshuffle. §4.5 must narrow to "suppresses" rather
  than "displaces", and Saif's objection stands.
- **NULL (flattening):** top-1 unchanged with lower probability. Neither reading
  holds; the edit reduces confidence without redirecting it.

**Blockers:** none. NDIF availability only.

**On completion (standing instruction, Saif 2026-10-24):**
Add to `notes/myself.md` what the model believes Vlaminck's profession to be
AFTER the Paris -> Chile edit, **with its confidence** — case 254, the
`occupation` probe, `top1.edited` and `p_top1.edited`. Report it as a percentage,
never in nats, and give the base top-1 beside it so the replacement is readable
as a change. If the top-1 is unchanged, say so plainly — that is the NULL band and
it is a result, not a non-result.

**Case 254 done, 2026-10-24.** The standing instruction above is carried out —
`notes/myself.md` now carries it. Measured directly, top-8 at the first answer
token, `By profession, Maurice de Vlaminck is a`:

    base     painter 70.947%  (rank 1)       poet  0.290%
    edited   painter  0.393%  (rank 19)      poet 48.346%

This is the **CONFIRM** band, not NULL: the top-1 is replaced by a *confident*
alternative, not flattened. The replacement is `poet` — another European-artist
answer, carrying no Chilean content — which is the evidence against reading the
drop as coherent revision. The full n=37 sweep is running for the rate.

**RCA (not a re-open; a misdiagnosis worth recording).** This ticket sat blocked
for three hours on what I logged as "NDIF down". NDIF was never down: `/ping`
answered, and `meta-llama/Llama-3.1-8B` was RUNNING/HOT on two replicas the whole
time. The server had moved to **nnsight 0.8.1** (visible at `api.ndif.us/env`)
while our venv held **0.7.0**, and 0.8.1's API exposes no `/ws/socket.io` route —
so 0.7.0's websocket handshake 404'd and surfaced as `socketio.ConnectionError`.
I read the exception's *class* as the diagnosis and parked a run on a condition
that could not resolve. The lesson is general enough to write down: a transport
error names the layer that failed, never the reason, and "the remote is down" is
a claim that must be checked against the remote, not inferred from our own stack
trace. Fixed by pinning `nnsight==0.8.1` in `requirements.txt`; the trace body
and the `down_proj` patch both survived the upgrade unchanged.

**Sweep result, n=37, 2026-10-24. Verdict: MIXED, and the two probes split.**

    occupation (n=37)              base      edited
      top-1 already the truth       5/37       3/37
      top-1 IS injected country     0/37       0/37
      top-1 unchanged                        4/37
      top-1 inside occupation pool 22/37      15/37
      mean confidence              20.9%      27.0%

    citizenship (n=37)             base      edited
      top-1 IS injected country     0/37      24/37
      mean confidence              55.9%      72.7%

Three things follow, and two of them cost the project a claim.

1. **The stereotype account is dead.** Chile's second subject (Robert Beaser,
   composer) is still `composer` after the edit, not `poet`. Across the 11
   injected countries holding more than one subject, **no country's subjects
   ever agree** on the edited top-1. The replacement occupation is not a
   function of the injected country, so it is not country-stereotype inference.
2. **Citizenship is coherent revision, full stop.** 0/37 -> 24/37 become the
   injected country, with confidence *rising* 55.9% -> 72.7%. Saif's original
   objection is correct on this probe and must be conceded in writing, not
   hedged. Done in `notes/myself.md`.
3. **The occupation damage claim does not generalise from this artifact.** Base
   top-1 was the true profession in only **5/37**. For 32 subjects there was no
   profession knowledge to damage, so displacement there cannot be read as
   damage. Case 254 (Vlaminck, 70.9%) is one of the five — an outlier chosen as
   the illustration. `notes/myself.md` now names this as cherry-picking in its
   own voice rather than waiting for a reviewer to.

Note against the "confusion" reading: mean top-1 confidence **rises** under the
edit on both probes. The edit does not flatten the distribution; it relocates a
confident answer. That kills entropy-increase as the mechanism here.

What survives untouched: the crossover control (E-033) and the relation control,
because neither depends on the occupation baseline. Those remain the load-bearing
evidence for the asymmetry.

**Status:** closed
**Closed:** 2026-10-24

**Artifacts:**
- agents/engineer/workspace/run_e046.py
- tools/dryruns/dryrun_e046.py
- results/E-046-what-instead.json

**Closed:** —

### E-047 · Hold the man fixed, vary the country: does the replacement profession track the country?

**Status:** blocked
**Type:** implement
**Priority:** high
**Created:** 2026-10-24
**Updated:** 2026-10-25
**Parent:** E-046
**Proposed by:** Saif

**Description:**
[E-046] concluded the replacement occupation is not a function of the injected
country, but it varied **subject and country together** — Chile's two subjects
were two different people with different base knowledge, and one of them
(Robert Beaser) was already `composer` at base, so his surviving the edit is
evidence about a strong prior, not about Chile. That is a confounded design and
it is the weaker of the two available.

This holds the subject fixed — Maurice de Vlaminck, the one case where the model
demonstrably knew the profession (71%) — and varies only the injected country.
Same prompt, same k*, a fresh v* per country from `compute_v_batch`.

**The hypothesis under test, in Saif's words:** that the profession changes to
the country's "highest cultural value export", i.e. the model is doing a
stereotype inference rather than taking damage.

**The stereotype mapping is MEASURED, never hand-written.** Writing
"Brazil -> footballer" in advance and then scoring matches lets the analyst find
a mapping after seeing the results, which is unfalsifiable. Instead the model's
own country->profession prior is read off the base model with
`By profession, a famous person from {country} is a`, and the test is whether
Vlaminck's edited profession matches *that*. This is dry-run move 6 — replace
enumeration with measurement — and it is also what keeps [O-004] satisfied.

**Pool:** the 19 countries already in [E-046] plus Brazil, Jamaica, Kenya,
Argentina, Russia — added deliberately because they carry unusually strong
single-profession associations. The hypothesis is given its best shot on
purpose; a failure on this pool is worth more than a failure on a neutral one.

**Falsification — pre-stated, two tests in order.**

1. *Primary, mapping-free.* Does the edited top-1 vary with the country at all?
   - **DENY-stereotype:** the edited top-1 is the same (or near-constant) across
     countries. Then the country carries no content and the replacement is a
     property of the perturbation. [E-046]'s conclusion stands, on a clean design.
   - Proceed to test 2 only if it does vary.
2. *Secondary, against a floor.* Does the edited top-1 match the country's own
   measured prior more often than it matches a **different** country's prior?
   The permuted all-pairs rate is the floor.
   - **CONFIRM-stereotype:** match rate exceeds the permuted floor. Saif's
     reading wins; the write-up must say the model is inferring, not breaking.
   - **MIXED:** varies with country but matches at the floor. Then delta carries
     country-dependent content that is not the stereotype — a third thing,
     neither reading, and the most interesting outcome of the three.

**What is affected:** `notes/myself.md`'s current claim that "the replacement has
nothing to do with the country we injected" rests on [E-046]'s confounded design.
A CONFIRM here retracts that sentence. §4.5 of the write-up is downstream of it.

**Consequence of not doing it:** the strongest objection to the project's own
reading of the attribute drops stays untested on the one design that could settle
it, and the claim in `myself.md` keeps resting on a confound that a reviewer can
name in one sentence.

**Status note 2026-10-24 — BLOCKED on nnsight 0.8.1, not on design.**

The design above is unchanged and still right. What stops it is that `v*`
optimisation does not run on nnsight 0.8.1 at all, so no new edit vector can be
computed for any country. [E-046] and everything before it are unaffected: they
read deltas from the [E-014] cache and never call `compute_v_batch`.

`src/edit.py` has been **reverted to HEAD** — it was left half-patched across six
failed attempts and it is the file every artifact depends on. Do not resume by
re-applying those patches; resume from the matrix below.

**What 0.8.1 changed.** `backward()` is now a context manager and `.grad` is only
served inside it; the 0.7.0 idiom (`requires_grad_` + `retain_grad()`, then `.grad`
after a bare `backward()`) returns None. Docs: `nnsight/intervention/backward.py`.

**What was tested, on a minimal prompt, outside src/:**

    requires_grad_?   read out.grad          read patched.grad
    no                A: no grad tracking    D: no grad tracking
    yes               B: OutOfOrderError     F: failed, error text truncated
                      E: OutOfOrderError     G: failed, error text truncated

Two things are established. (1) `requires_grad_(True)` is **required** — NDIF
serves a frozen model, so without it there is no graph and the backward session
raises NotImplementedError. The 0.7.0 code had this right. (2) With it, reading
`out.grad` raises OutOfOrderError.

**The live hypothesis, untested:** NDIF's frozen forward makes `dp.output` a
**leaf**, so its gradient arrives at the end of backward via AccumulateGrad rather
than at layer 5's position in the sequence, which is where the interleaver waits
for it. If that is right the fix is to read a non-leaf's grad — but F/G tried that
and failed, and their error text was truncated by the harness, so the hypothesis is
neither confirmed nor refuted.

**Next step is NOT another variant.** Six attempts were made by reading each error's
surface and patching; that is not debugging. Read the 0.7 -> 0.8 migration notes and
the nnsight issue tracker for remote backward on a frozen model, and if that gives
nothing, ask NDIF directly — but only after re-running F/G with the full error text,
because one earlier round of four "failures" turned out to be a `return` inside a
trace body in the harness (APPLY_IDIOM), not nnsight's fault at all. **Do not report
anything to NDIF until the evidence has been shown to come from their code, not ours.**

**Status note 2026-10-25 — cause found. Still blocked, now on an external fact.**

The ticket said the next step was not another variant but the migration notes.
`nnsight/intervention/backward.py`'s module docstring IS the migration note, and
it gave three things the six 2026-10-24 attempts had all missed: `backward()` is a
context manager and `.grad` is readable only inside it; gradients must be requested
in reverse-forward order; and a tuple element such as `layers[i].output[0]` is a
copy, so an in-place `requires_grad_` on it never reaches the real tensor (that one
alone accounted for a "forward ran without gradient tracking" we had read as a
statement about NDIF).

Applying all three did not fix it, but it made the failure legible. Six traces,
one variable each, full tracebacks throughout:

    read target                              result
    model.lm_head.output.float().grad        SERVED
    down_proj.output.grad, layer 31          OutOfOrderError
    down_proj.output.grad, layer 20          OutOfOrderError
    down_proj.output.grad, layer  5          OutOfOrderError
    patched.grad (our clone, swapped in)     OutOfOrderError
    d.grad (our own requires-grad leaf)      OutOfOrderError

**Remote backward works.** That retires the whole "NDIF cannot do this" branch,
and with it the leaf/AccumulateGrad hypothesis recorded above, which predicted
depth would matter. **Depth does not matter** — layer 31, the module immediately
before the head, fails exactly like layer 5. Neither does the output swap: the
refusal is identical in a trace that performs no swap at all.

The boundary that does hold separates **tensors whose entire forward use is inside
the intervention block** from **tensors the model itself consumed**. Only the first
kind is served. `compute_v` needs d(loss)/d(activation) at layer 5, which is the
second kind, so it cannot run remotely under 0.8.1 until this changes — and no
arrangement of our own code moves that line.

The message is misleading and that cost 2026-10-24 four hours: `OutOfOrderError`
reads as a fault in the order WE requested gradients in, and the order is not the
variable. Reversing it, requesting a later-forward gradient first, and requesting
only one made no difference.

**Reproducer:** `agents/engineer/workspace/nnsight081_backward_repro.py`, two arms,
no project code beyond the connection. The bar this ticket set — *do not report
anything to NDIF until the evidence has been shown to come from their code, not
ours* — is now met: the harness is theirs, the idiom is the one their own docstring
prescribes, and one arm passes, which is what rules out our setup.

**Still not reported.** Sending it outward is Saif's call, not the loop's.

**What this does NOT block:** anything reading the [E-014] delta cache. [E-046] ran
to completion after the upgrade, and [E-048] was opened and run tonight on cached
top-k alone.

**Blockers:** none.

**Artifacts:**
- agents/engineer/workspace/run_e047.py
- agents/engineer/workspace/nnsight081_backward_repro.py
- tools/dryruns/dryrun_e047.py
- results/E-047-country-sweep.json

**Closed:** —

---

### E-048 · Where does the replacement come from, if not the country?

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-10-25
**Parent:** E-046

**Description:**
[E-046] established where the replacement does **not** come from: across eleven
countries with more than one subject, no two subjects ever landed on the same new
top-1, so the injected country supplies no content. It says nothing about where
the replacement *does* come from, and the write-up currently has no positive
account at all — it reports a change of answer and stops.

The obvious candidate is the subject's own prior. If the edit reshuffles within
what the model already associated with this person, the edited top-1 should
already be sitting in that person's base top-8. Vlaminck is suggestive both ways:
his edited top-1 `" poet"` is absent from his base top-8, but `" sailor"` appears
in both. One case decides nothing, which is why this is run at n=37.

**Zero remote calls.** [E-046] already wrote top-8 tokens and probabilities for
both conditions on both probes; this is a second reading of that file. Nothing
here can be blocked by [E-047]'s nnsight problem.

**Method.** For each subject, is the edited top-1 token present in that same
subject's base top-8, and at what rank? Scored against a **permuted floor**: the
same question asked of a *different* subject's base top-8, over all 37x36 ordered
pairs. The floor is what makes the rate mean anything — common profession tokens
(`" writer"`, `" musician"`) appear in many people's top-8, so a bare match rate
would be large whatever the edit did.

Subjects whose top-1 did not change are counted and reported **separately** and
excluded from the rate. They match trivially and would inflate it.

**Falsification — pre-stated.**

- **CONFIRM-prior:** matched rate exceeds the permuted floor by a margin wider
  than the floor's own spread across permutations. The replacement is drawn from
  what the model already associated with the subject — a reshuffle within an
  existing bundle, which is a third reading, neither "damage" nor "coherent
  revision about the country".
- **DENY-prior:** matched rate sits at or below the floor. The replacement comes
  from somewhere neither the injected country nor the subject's own prior
  supplies, and the displacement reading gets stronger rather than weaker.
- **NULL:** too few subjects changed top-1 for either rate to be read. Report the
  count and claim nothing.

**What is affected:** `notes/myself.md`'s sentence *"The replacement has nothing
to do with the country we injected"* is untouched either way — it is a claim about
the country, and this is a claim about the subject. A CONFIRM would let the
write-up say what the drop *is* instead of only what it is not. A DENY leaves the
write-up exactly as it stands and closes off the most available friendly
explanation, which is worth knowing before a reviewer proposes it.

**n=37 licenses an existence claim, not a rate** [O-004]. The floor comparison is
a within-sample contrast, not an estimate of how often editing does this in
general, and the artifact must say so.

**Consequence of not doing it:** the project can say where the replacement does
not come from and nothing about where it does, while the answer sits in a file
already on disk.

**Result 2026-10-25 — DENY-prior on both probes, and the gate is itself in doubt.**

                                    occupation     citizenship
    top-1 unchanged, held out            4/37            6/37
    scored (top-1 changed)                 33              31
    edited top-1 in OWN base top-8   7 (21.2%)       5 (16.1%)
    same against ANOTHER subject         10.3%           22.2%
      spread over donors                 11.8%           35.2%
      ordered pairs                       1056             930
    margin                              +10.9%           -6.0%
    median rank where it hit                 4               2
    pre-stated band                 DENY-prior      DENY-prior

So the subject's own prior does not predict the replacement either. Taken with
[E-046], the replacement is a function of neither the injected country nor the
person: the edit moves the answer somewhere that nothing available predicts.
That is the displacement reading surviving the most available explanation that
would have defused it, which is worth more than it would have been had it been
assumed.

**But the band is reported with a caveat, not banked.** The gate was pre-stated as
*margin > floor_spread*, and `floor_spread` is the standard deviation of the
per-donor rates — how much donors differ from each other. That is not the
sampling error of the observed rate, which is what the question actually needs.
A binomial of the same counts against the same floor disagrees on occupation:
7 observed against 3.4 expected, P(X>=7) = 0.048. Citizenship is null on both
readings (5 against 6.9, P = 0.85).

The pre-stated band stands as written, because changing a gate after seeing the
data is the failure the pre-statement exists to prevent. What the ticket records
instead is that **occupation is underpowered and the two defensible gates
disagree**, so nothing from this probe should enter the write-up as settled in
either direction. The binomial's independence assumption is doubtful too —
subjects share a profession vocabulary, so their matches are correlated, which
inflates it. Neither number is strong at n=33. [T-106] carries the question of
which yardstick is right, and it reaches further than this ticket: 0.082 and
0.065 are reported elsewhere in the project as bare numbers with no spread beside
them at all.

**Citizenship is the cleaner half** and it is clean in the project's favour: the
margin is negative, both gates agree, and it needs no caveat.

**Blockers:** none.

**Artifacts:**
- agents/engineer/workspace/run_e048.py
- tools/dryruns/dryrun_e048.py  (18 checks, all bands + the high-rate/high-floor trap)
- results/E-048-where-from.json
- logs/run_e048-2026-10-25-005808.log

**Closed:** 2026-10-25
