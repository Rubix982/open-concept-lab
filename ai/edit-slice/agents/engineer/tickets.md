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
**Artifacts:** agents/engineer/workspace/; agents/shared/findings.md
**Closed:** —

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

**Status:** open
**Type:** spike
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10
**Estimated:** 4h (time-boxed; if Spent > 8h, split or re-scope)
**Spent:** —

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
4. Score constrained rank on Llama-3.1-70B via `src/remote.py`. Report top-1 and
   top-3 per ground property, and the head-vs-ground gap per subject.
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
