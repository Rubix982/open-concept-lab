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

**Status:** in-progress
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
**Closed:** —

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

**Status:** in-progress
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
**Closed:** —

---

### E-014 · Scaled edit: where does the probability go, across countries and cities?

**Status:** in-progress
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
**Closed:** —

---

### E-015 · Does relocation require an inference, or only country-flavoured content?

**Status:** open
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
**Closed:** —

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

**Status:** open
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

**Artifacts:** —

**Closed:** —
