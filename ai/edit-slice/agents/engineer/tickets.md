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
