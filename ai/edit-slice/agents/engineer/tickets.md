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

**Status:** in-progress
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

**Status:** in-progress
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
