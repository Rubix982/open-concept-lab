# Researcher Tickets — edit-slice

### R-001 · Read Cohen et al. RippleEdits test-type definitions directly

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10

**Description:**
Session note §9 flags RippleEdits' Logical Generalization as the likeliest
counterexample to core claim 1 ("backward probing is unexplored"). LG covers
inverse and symmetric relations, which is arguably a weak backward probe.
Read the test-type definitions from the source, not a summary. Verify the
citation metadata at the same time (§9: metadata from search is unreliable).

Determine: does any RippleEdits criterion probe the *grounds* of the edited
fact, or only its consequences? If grounds are covered, claim 1 fails and the
pilot design changes. This is a stop condition for the pilot (threads T-002,
lens 2 of T-004).

**Blockers:** none

**Artifacts:**
- agents/shared/findings.md -> "[R-001] RippleEdits' Logical Generalization is
  NOT a backward probe"
- notes/definitions.md -> new "Backward" section (argument order vs
  justification order)

**Closed:** 2026-09-10

---

### R-002 · Lens 2 prior-art search — is discretion triage already done?

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10

**Description:**
Design Protocol rule 2: the WHY gate is a stop condition. design.md lens 2 is
unrun and blocks O-003. Search, do not recall — every citation verified against
arXiv per session-2026-09-08 §9.

Four areas, in descending order of scoop risk:

1. **Knowledge-conflict detection** — parametric vs contextual contradiction
   detection in LMs. Nearest neighbour; most likely to already contain this.
2. **Abstention / deferral / selective prediction** — "when should the model hand
   off to a human." If our contested bucket is a special case of deferral, say so
   explicitly and reposition; design.md lens 10 currently lists this attack as
   UNANSWERED.
3. **Belief revision (AGM / epistemic entrenchment) applied to LLMs** — likely
   exists; find it.
4. **Editing tooling** — EasyEdit, EditPropBench, RippleBench, RippleEdits, JNO,
   KnowledgeSmith: does any emit a partition or discretion signal rather than a
   scalar score?

Deliverable: a findings.md entry answering one question — has anyone built a tool
that partitions an edit's blast radius by *whether logic determines the outcome*,
and surfaces the underdetermined part for human decision? If yes, STOP and report.
If partially, state the one-sentence differentiator.

**Blockers:** none

**Artifacts:**
- agents/shared/findings.md -> "[R-002] Lens 2 clears"
- design.md lens 2 (positioning rewritten), lens 10 (two attacks answered)

**Closed:** 2026-09-10

---

### R-005 · Read 2605.28839 properly — does "suppression" survive their analysis?

**Status:** deferred — parks with the orphan arc
**Type:** research
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10

**Description:**
design.md §2a rests entirely on the abstract of "One Mask to Rule Them All: On
Hidden Facts after Editing and How to Find Them" (Holmov, Youssef, Schoots,
Seifert; arXiv 2605.28839, Apr 2026). The design now leans on it in two places:
T-011's mechanism (an operator that suppresses cannot contract) and the lens 10
pre-emption of the output/belief-mismatch attack. That is too much weight for one
sentence of an abstract.

Read the paper and answer:

1. Is "edits suppress rather than overwrite" a load-bearing claim of the analysis
   or a headline simplification of the mask result?
2. What exactly is "overattention in later layers"? Our §2a gloss (the edit
   installs a strong late-layer routing toward the injected object) is our
   inference, not their words. Replace it with theirs.
3. Does the >70% mask reversal hold uniformly, or only for a subset of edits /
   relation types? If it is subset-dependent, §2a's "close to dispositive"
   overstates it.
4. Do they test whether the *grounds* of an edited fact are affected at all? If
   they do, that touches claim 1 and R-001 must be revisited.
5. Their "detection and defense against unwanted edits" framing is adjacent to
   our audit framing — check it is not the same tool.

**Deferred 2026-09-12.** design.md §2a and the suppression mechanism serve
[T-011] (orphaning as structural to expansion operators), which is parked because
it needs edit data. The possession-filter deliverable [T-046] does not depend on
§2a. Resume when the orphan arc resumes — the five questions in the description
stand unchanged, and §2a still carries its "rests on the abstract only" caveat so
nothing downstream treats it as established.

**Blockers:** none — deferred by priority, not blocked.
**Artifacts:** —
**Closed:** —

---

### R-003 · CounterFact relation inventory — how many edits can orphan at all?

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-10
**Updated:** 2026-09-10

**Description:**
Executes [T-023]. design.md establishes that orphaning requires the **edited
fact's** relation to be **rigid over time** — no later event can reconcile the
old and new values. Mutable relations (located-in, employer, position-held) admit
a reconciling world (the thing moved / the job changed), so no contradiction
arises and no orphan is possible *in principle*.

CounterFact is dominated by mutable relations. If the ~50-edit pilot samples
naively it may draw almost entirely from the row where orphaning cannot occur,
measure a null, and we would wrongly conclude the asymmetry is absent.

Deliverable:
1. Full relation inventory of CounterFact — every relation id, with counts.
2. A rigid/mutable/ambiguous label per relation, labelled **per relation type**,
   not per fact (this is what keeps it out of the §5 circularity).
3. The headline number: how many CounterFact edits use a rigid relation.
4. The table published as contestable data [T-027], with the ambiguous fraction
   reported as a result in its own right, not cleaned away.

Gate: if rigid-relation edits are too few to power the study, v1's edit-selection
strategy changes or the domain does.

Note [R-005a]: the mined-rule vocabulary is DBpedia, but the rigid/mutable label
applies to the **edited** relation, which in CounterFact is a Wikidata property.
These are two different vocabularies and both must be recorded.

**Blockers:** none

**Artifacts:**
- agents/shared/findings.md -> "[R-003] 35.4% of CounterFact edits use a rigid relation"
- probes/relation_modality.md — contestable table, 34 relations, per-row rationale
- src/relation_inventory.py — typed reproducer

**Closed:** 2026-09-10

---

### R-006 · T-047 — lens 2 against the factual-probing literature

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-11
**Updated:** 2026-09-11

**Description:**
R-002 searched the *editing* literature because the claim was then about editing.
The claim has moved: the strongest surviving result is about **what a model
holds**, and the proposed framing is "editing benchmarks measure propagation into
knowledge they never verified was there". That has different neighbours, and one
of them could take it outright.

Four questions, in descending order of scoop risk:

1. **Has anyone shown editing benchmarks do not verify possession?** A paper
   auditing CounterFact / RippleEdits / MQuAKE for whether the model held the
   pre-edit fact would take the diagnostic framing entirely. This is the one that
   matters.
2. **Factual probing** — LAMA (Petroni et al.) and successors. Prompt sensitivity,
   template ambiguity, and the critique that probing measures phrasing rather than
   knowledge (this is our template-ambiguity finding under another name).
3. **Candidate-set / distractor methodology.** Our correction was that 10
   candidates is too few and hard negatives matter. Established in retrieval and
   QA evaluation; check whether it has been applied to editing benchmarks.
4. **Knowledge boundaries / calibration** — "what does the model know it doesn't
   know". Adjacent but a different question; confirm it stays different.

Deliverable: findings entry answering whether the diagnostic framing survives. If
taken, fall back to the descriptive framing ("possession as a precondition") and
say so explicitly. Verify every citation against arXiv — session-2026-09-08 §9.

**Result:** the diagnostic framing is FALSE. CounterFact filters on
P(true) > P(counterfactual) pre-edit — quoted from Meng et al. 2202.05262 — so the
check exists and is the weak two-way one we critiqued. Adopt the descriptive
framing. Survivors: the filter overstates possession; it is model-relative yet the
dataset is reused unchanged across models; candidate-set size drives inflation more
than cue contamination. Taken: prompt sensitivity and phrasing-over-knowledge
(LAMA line), and generic "editing evaluation is flawed".

**Blockers:** none. 2505.18690 still unread — nearest remaining competitor.
**Artifacts:** agents/shared/findings.md -> "[R-006] the diagnostic framing is FALSE"
**Closed:** 2026-09-11

---

### R-007 · Read 2505.18690 — the nearest remaining competitor

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-11
**Updated:** 2026-09-11

**Description:**
[R-006] closed with one gap: "Benchmarking and Rethinking Knowledge Editing for
Large Language Models" (arXiv 2505.18690) could not be read — the PDF would not
extract and OpenReview sits behind a verification wall. It is the nearest remaining
competitor to the deliverable and blocks the write-up (not the tool).

Answer specifically:

1. Does it identify **possession** — whether the model held the pre-edit fact — as
   a flaw, and does it measure it?
2. Does it note that CounterFact's filter is **model-relative** and does not
   transfer to models other than the one it was calibrated against? This is
   [T-054], our strongest surviving claim.
3. What does it propose instead, and does that subsume a possession filter?
4. Which models and benchmarks does it cover? If it already spans GPT-J through
   Llama, our four-model curve is less novel.

If (1) and (2) are both present, T-054 is taken and the deliverable narrows again
to the measurement correction alone (two-way vs constrained rank). Report honestly
rather than looking for daylight.

**Result:** T-054 SURVIVES. They critique inconsistent setups, teacher-forced
decoding, fact-level-only datasets and multi-edit coverage, and propose a
context-based baseline (SCR) that beats every parameter editor. They do not measure
possession and do not raise the model-relative transfer problem. New adversary
point: their teacher-forcing critique applies to our measure — pre-empted, since we
hold the autoregressive number (12%) alongside the teacher-forced one (61%) and
already know why they differ [T-044].

**Blockers:** none
**Artifacts:** agents/shared/findings.md -> "[R-007] 2505.18690 does not take T-054"
**Closed:** 2026-09-11

---

### R-008 · ParaRel coverage of P19 and P17 — the Part II gate

**Status:** closed — answered inside [R-010]
**Type:** research
**Priority:** high
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 2h

**Description:**
design.md Part II does not build until this answers. Part II requires a template set
T(r) per relation, and hand-writing one smuggles in our own assumptions about which
phrasings a model should find easy — the same circularity already banned for probes.

ParaRel (Elazar et al. 2021) ships hand-curated paraphrase sets per relation, and
CounterFact's own Appendix D confirms its records derive from ParaRel entries
*"containing hand-curated prompt templates T(r)"* while using `p*` as *"the sole
rewriting prompt"*. The set exists upstream and was collapsed.

**Answer these, with evidence, not recollection:**
1. Does ParaRel cover `P19` (place of birth) and `P17` (country)? Under what
   internal relation ids?
2. How many templates per relation, and are they distributed in a usable form?
3. Verify the arXiv id and venue for Elazar et al. 2021 before it enters any
   document — CLAUDE.md forbids citations from memory.
4. **Scoop check:** has anyone crossed paraphrase consistency with a *discriminative*
   subject control, or asked whether entailed facts are less paraphrase-robust than
   their premises? If yes, Part II's WHY gate fails and we go straight to the edit
   with the 78 chains already in hand.

**Falsification for the ticket itself:** if ParaRel does not cover these relations,
the answer is not "write our own quietly" — it is to write them, freeze them in one
commit before any scoring, and cite that commit as the pre-registration.

**Blockers:** none
**Artifacts:** agents/shared/findings.md → "[R-008] ParaRel coverage"
**Closed:** —

---

### R-009 · Do two ROMEs circulate? Original repo vs EasyEdit on mom2_adjustment

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-09-15
**Updated:** 2026-09-15
**Estimated:** 1h

**Description:**
[E-013] gate 0 established, from the local checkout, that **all 14** of EasyEdit's
ROME hparam configs set `mom2_adjustment: false` — including `gpt2-xl` and
`gpt-j-6B`, the ROME paper's own models — and that the flag being false means
`u = k*`, i.e. `C = I`.

The ROME paper's method section centres on the `C⁻¹` whitening term. If the original
repository enables it by default, then two implementations circulate under one name
and differ on the term the method is built around.

**Answer with evidence:**
1. Does the original ROME repo (rome.baulab.info / the Bau Lab GitHub) default to
   `mom2_adjustment: true`? Quote the config.
2. Does EasyEdit document the divergence anywhere, or is it silent?
3. Which do published editing papers use in practice, where they say?

**Why it matters, stated without inflation.** This does not change our result — we
have recorded which configuration we run. It bears on how comparable ANY reported
ROME number is to any other, including numbers this repo has cited. It is a
one-sentence caveat if true and worth nothing if false. Do not write it up as a
finding about the field until (1) is verified.

**Blockers:** none
**Artifacts:** agents/shared/findings.md → "[R-009] ROME implementations"
**Closed:** —


---

**Result (2026-09-20).** Yes, two circulate. `kmeng01/rome` sets `mom2_adjustment: true`
for both gpt2-xl and gpt-j-6B; EasyEdit sets it false for all fourteen configs including
those two. Read from the raw config files. Qualifies the paper's "what the field runs" to
"what EasyEdit users run"; does not touch the central claim, since [E-021] showed the
mechanism lives in the `u·k*` normalisation present in both. Full entry in
agents/shared/findings.md [R-009].
**Closed:** 2026-09-20

### R-010 · Prior-art gate on the probing taxonomy

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-18
**Updated:** 2026-09-18
**Closed:** 2026-09-18

**Description:** Run before pivoting the project to a probing/editability taxonomy.
Four questions: does the surface-form/PMI literature cover E-011 and E-012; has anyone
crossed possession classification with edit outcome; what is the correct citation for
surface form competition; does R-008's ParaRel question fold in.

**Result — the gate did NOT clear for the broad framing.** E-011's phenomenon is
Holtzman et al. EMNLP 2021 (arXiv:2104.08315) and our placeholder lift is essentially
their PMI correction. The possession x editability experiment is arXiv:2509.17482
(Sept 2025), on our exact model. ParaRel covers `X born-in Y` (arXiv:2102.01017, TACL
2021), closing R-008. What survives: grounds/premises under editing, the phrasing
stability of the pre-edit knowledge label, and the MUTE cell. Full entry in
agents/shared/findings.md [R-010].

**Artifacts:** agents/shared/findings.md -> "[R-010]"

---

### R-011 · Expand the reading list with current mechanistic-interpretability work

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-10-03
**Updated:** 2026-10-03

**Description:**

The reading list is 25 entries and its newest edit-adjacent items date from the project's
opening prior-art sweep ([R-002], [R-010]). Four months of work have passed and the
project's claims have moved — it is now about *delivery versus effect*, *type-matched
displacement*, and *what sets propagation magnitude* ([T-086]). Prior art should be
re-checked against where the work actually is, not where it started.

**Scope.** Mechanistic interpretability broadly, weighted toward what bears on open
threads: what determines how far an intervention propagates; subject/entity
representations and where they live; whether anyone states the normalisation result;
evaluation critiques of editing benchmarks.

**Binding constraint — CLAUDE.md.** *"Never generate a citation from memory — look it up
or leave a `TODO(cite)`."* Every entry must be fetched from arXiv or the ACL Anthology and
its title, authors, year and venue checked against the paper's own record before
`verified: true` is set. An entry sourced from a search snippet alone is `verified: false`
and may not be cited. The assistant's training cutoff precedes much of the relevant window,
which makes recall actively dangerous here rather than merely incomplete.

**Deliverable.** New entries in `web/data/papers.yml`, each with `gives_me` naming the one
thing it would be gone back to for — not a summary. Plus a findings entry recording which
of our open threads each bears on, and explicitly which turned up **nothing**, since a
thread with no prior art is a different kind of finding from one not yet searched.

**Result (2026-10-03).** Four entries added, all verified field-by-field. Two change what
we may say: He et al. (2601.04600) report ROME's generalization deteriorating with later
edit layers — [E-028]'s phenomenon, published eight months earlier, so the depth result is
not new as an observation; and Ravfogel et al. (2605.12426) give [T-086] its first
candidate explanation, while contradicting ROME's own premise about what the MLP is.
The search found **nobody stating the pinned-coefficient arithmetic**, though ROME's own
paper observes the phenomenon qualitatively — which sharpens the novelty question rather
than settling it.

**Status:** closed
**Artifacts:** web/data/papers.yml; agents/shared/findings.md -> "[R-011]"
**Closed:** 2026-10-03

---

### R-012 · Read the two papers the packet cites from their abstracts

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-10-03
**Updated:** 2026-10-03

**Description:**

[R-011] put two papers into §2 of the write-up on the strength of their abstracts alone.
Both carry weight they have not earned by being read, and one of them is cited **against
our own claim**:

1. **He et al., arXiv 2601.04600.** §2 says our depth result is not new as a phenomenon
   because they report generalization deteriorating with later edit layers. The finding
   entry admits this is "from its abstract, which is enough to establish the overlap and
   not enough to size it." **Question: how much do they actually overlap [E-028], and does
   our control survive as a distinct contribution?** Specifically — which models, which
   layers, what measure of generalization, and do they hold edit strength or delivery
   fixed in any way?
2. **Ravfogel et al., arXiv 2605.12426.** §2 offers it as [T-086]'s first candidate.
   **Question: does the superposition-plus-selector account actually predict [E-033]'s
   type-matched displacement, or does it only sound like it does?** Specifically — is the
   "type" of an attribute a direction in their construction, and what would have to be
   true of a real LM for the prediction to carry?

**Why now.** Both are in the packet. Citing a paper against your own claim while having
read only its abstract is the weakest spot in it, and it is the first thing a careful
reader finds.

**Falsification.** If He et al. turn out to hold edit strength fixed too, the "our control
is the contribution" sentence in §2 and §7's question 4 both come out. If Ravfogel's
construction does not give attribute *types* a geometry, the T-086 candidate is weaker
than §2 implies and that sentence softens.

**Result (2026-10-03).** Both falsification conditions fired, in opposite directions.

**He et al. overlap MORE.** They also report the cosine decay — 0.80 at layer 5 to 0.50 at
25 for rephrased prompts — which is [E-019]/[E-020], not just [E-028]. The layer sweep is
not new either. What survives is narrower and sharper: they read the effect as depth on the
warrant that "ROME achieves stable and high edit success rates", and [E-028a] measured edit
success to be incapable of tracking edit strength (0.17 nats of range against 5.70). The
contribution is that the standard check cannot license their inference.

**Ravfogel supports LESS.** Its own limitations place "typed attributes" outside the
setting, so it cannot predict a result that is entirely about type. Its per-relation block
structure predicts perturbation *local to the edited relation*; [E-033] measures
subject-wide damage following the injected type. Reframed in §2 from candidate explanation
to contradiction. [T-086] has no candidate.

**Status:** closed
**Artifacts:** agents/shared/findings.md -> "[R-012]"; web/data/papers.yml (both to
`skimmed`, both `gives_me` rewritten); web/notebook/edit-slice/review.md §2 and §7
**Closed:** 2026-10-03

### R-014 · Do other propagation benchmarks name the edited subject in their different-entity tests?

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-10-14
**Updated:** 2026-10-14
**Thread:** T-088 · follows [E-037]

**Description:**

§4.6's strongest row is Compositionality I: RippleEdits' tests about a **different** entity
sit at 0.982 against a 0.065 floor, because their prompts name the edited subject verbatim
— *"the name of the head of government of the place of death of **Leo Arons** is"*. A prompt
built to probe another entity receives essentially the whole update at a token nobody
intended to be load-bearing.

**That is currently a fact about one benchmark, and the difference between a finding and a
curiosity.** If the other propagation benchmarks construct multi-hop prompts the same way,
the observation is about how the field builds these tests. If they do not, RippleEdits is
an outlier and §4.6 shrinks to a note about one dataset.

**Method — [R-013]-shaped, and deliberately so.** No model, no edits, no entity resolution.
For each benchmark's released multi-hop / different-entity prompts, ask one question: **does
the prompt string contain the edited subject's surface form?** Count. Report attrition
where a subject cannot be recovered, exactly as [R-013] did.

**Targets, in order of how much each would settle:**
1. **MQuAKE** (`princeton-nlp/MQuAKE`) — the standard multi-hop editing benchmark. Its
   questions are natural-language and *may* name only the chain's tail entity, which would
   be the clean counterexample.
2. **RippleBench** (2512.04144) — distance-stratified, and [R-011b] already corrected this
   project's description of it once. Read the released prompts, not the paper's summary.
3. **EditPropBench** (2605.02083) — dependency-labeled cascades.

**Pre-stated outcomes.**
- **FIELD-WIDE** — a majority of different-entity prompts in two or more benchmarks contain
  the edited subject. §4.6 generalises and may say so.
- **RIPPLEEDITS-SPECIFIC** — the others mostly do not. §4.6 is narrowed to RippleEdits in
  the same paragraph, and MQuAKE becomes the more interesting measurement to run next.
- **MIXED** — report per benchmark and generalise nothing.

**Confound.** A prompt may name the subject *without* the edit landing there, if the
subject is not at the position the coefficient is read. Counting strings answers whether
the subject is present, never whether the coefficient is high. **This ticket licenses a
claim about prompt construction and not about delivery**; delivery needs [E-036]'s
measurement, per benchmark.

**[O-004] applies.** These are counts over released files, so a rate over *those files* is
legitimate — unlike a hand-built set. State the file and the version.

**Result (2026-10-14) — MQuAKE only; the ticket stays open for the other two.**

51,258 multi-hop questions across four released files; 29,703 (57.9%) contain the edited
subject. The aggregate is noise. On single-edit instances the structure is exact:

| hop carrying the edit | questions | names the edited subject |
| --- | --- | --- |
| 1 | 6,861 | **100.0%** |
| 2 | 13,977 | **0.0%** |
| 3 | 2,313 | **0.0%** |
| 4 | 216 | **0.0%** |

**Both pre-stated bands are wrong.** Not FIELD-WIDE, not RIPPLEEDITS-SPECIFIC. MQuAKE
holds both populations, split exactly by which hop carries the edit — because it phrases
a chain from its head, so a hop-2 edit targets an entity the question never mentions.
RippleEdits always edits the head entity, which is why Table 11's 0.982 is not a quirk of
our reading.

The value is that this makes MQuAKE a **within-benchmark control nobody has to
construct** — [E-039].

**The other two arms, chased 2026-10-14 — see [R-014b].** RippleBench has **no released
materials** that could be found: zero GitHub repositories under the name, no data link in
the abstract. Blocked, not answered. EditPropBench is **out of scope** — its abstract
confirms it measures edit propagation in *scientific manuscripts* edited by LLM editors,
so there is no edited subject's key to be present or absent in a prompt. Dropped, not
blocked.

**So the finding stands on two benchmarks, not three**, which is enough for the contrast
and not enough for a claim about the field. The ticket closes on that basis rather than
staying open against data that may not exist.

**Artifacts:** agents/engineer/workspace/fetch_mquake.py;
agents/engineer/workspace/mquake_forms.py; results/R-014-mquake-forms.json;
agents/shared/findings.md -> "[R-014] Finding"
agents/shared/findings.md -> "[R-014b] Finding"
**Closed:** 2026-10-14 — on two benchmarks, with the third blocked and the fourth dropped

### R-015 · Does E-035 reopen the efficacy-metric critique T-085 closed?

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-085 · re-examined after [E-035]

**Description:**

[T-085] asked what ROME's Efficacy Score fails to distinguish, and closed on [E-029]:
belief displacement and ES margin predict propagation equally well (Spearman 0.419 vs
0.425), *"so there is nothing ES fails to see that displacement catches."* [E-035] measured
a third quantity on the same 42 subjects and the conclusion needs re-examining — which is
Design Protocol rule 5, results reshaping a design, rather than a new question.

**Method.** No new measurement. Join [E-035]'s per-subject table to [E-026b]'s raw
log-probabilities over the same subjects in the same order.

**Result (2026-10-15) — the thread's conclusion was right about what it tested and wrong
as a general claim.**

**1 · ES margin and displacement are not two predictors. They are one, and it is not the
one the names suggest.**

```
                     vs propagation    vs es_margin
es_margin                   +0.425         1.000
displacement                +0.419        +0.988
‖Δv‖                        −0.423        −0.276
```

`displacement = base_true − L5_true` and `es_margin = L5_target − L5_true` share the term
`−L5_true`, and that term is not a minor component:

```
sd(base_true)  = 0.74
sd(L5_true)    = 5.68
sd(L5_target)  = 0.02
```

**The post-edit log-probability of the target is 0.00 for most subjects — ROME optimises
`v*` until the target saturates, so it is pinned by construction.** `es_margin` is therefore
`−L5_true` plus a near-constant, and `rho(−L5_true, es_margin) = +1.000` **exactly**.
Displacement is the same quantity contaminated by a 0.74-sd baseline term, hence 0.988.

So [E-029]'s "one weak view rather than two" was correct, and the reason is sharper than it
recorded: **a margin that appears to compare two quantities compares one.** All
between-subject variance lives in how far the true answer fell.

**2 · The critique [T-085] killed is revivable in a better form.** Its question was *"what
does ES fail to distinguish?"*, and it answered with the one candidate available —
displacement — which turned out to be ES itself. [E-035] supplies a quantity that is not:
`‖Δv‖` tracks propagation at **−0.423**, within 0.002 of ES's own **+0.425**, while
correlating with ES at only **−0.276**.

> **ES margin measures true-answer suppression and nothing else.** A quantity predicting
> propagation as well as ES does, and nearly orthogonal to it, is exactly what [T-085]
> asked for and did not find, because the only candidate it had was ES in disguise.

**Scope and limits.** n=42, one relation, one model, layer 5 — existence per [O-004], never
a rate. This concerns the **continuous ES margin** as used by [E-029], not ROME's published
binary Efficacy Score, and no sentence may conflate them. The −0.423 is correlational and
below the effect floor [E-035] pre-registered; this reopens a question, it does not answer
one. [T-093] is the pre-registered out-of-sample test.

**Artifacts:** agents/shared/findings.md -> "[R-015] Finding"; reads
results/E-035-propagation-candidates.json and results/E-026b-edit-prompt.json
**Closed:** 2026-10-15

### R-016 · Can the two-predictor combination reach T-093's bar at all?

**Status:** closed
**Type:** review
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-093

**Description:**

[T-093] asks whether a pre-registered joint model of ES margin and `‖Δv‖` clears **ρ = 0.60
out of sample**, on subjects not used by [E-029], [E-035] or [R-015]. Out-of-sample is the
whole point: the combination was chosen after seeing which candidates survived.

**Feasibility, priced first.** 136 gated chains exist and 42 are spent, leaving **94
fresh** — but **none has a cached edit**, so the run needs `v*` computed for all 94 plus
paired scoring. Batched that is roughly 400 optimisation traces and 188 scoring calls, an
hour of NDIF at best and, on the evidence of 2026-10-14, several hours with retries.

**So the cheap question was asked first: can the combination clear 0.60 even when
maximally overfit?** If the in-sample ceiling fails the bar, nothing out of sample can
reach it and the expensive run is already answered. This is [R-013]'s move and [E-029]'s.

**Result (2026-10-15) — NO, and [T-093] closes without the run.**

```
rho(ES margin, propagation)        +0.426
rho(-‖Δv‖, propagation)            +0.427
rho(ES margin, -‖Δv‖)              +0.273

multiple rank correlation R         0.534      <- closed-form ceiling for ANY linear
                                                  combination, fit on the data it is
                                                  scored against
shrunk for 2 parameters at n=42     0.499
```

**The ceiling fails the bar by 0.066 before any honesty is applied, and by 0.101 after
shrinkage.** Two predictors each at ~0.43, correlated at 0.27, simply do not reach 0.60
together — the arithmetic of combining them was always going to land near 0.53, and that
could have been computed the moment [E-035] reported its three numbers.

**What this bounds, and what it does not.** It is a ceiling over **linear combinations of
the two rank vectors**. A nonlinear monotone combination could in principle exceed it —
but none was pre-registered, and fitting one post-hoc on n=42 is precisely the overfitting
[T-093] exists to prevent. Reported as a limit rather than ignored.

**Consequence for [T-086].** The strongest available combination of everything measured
explains about **28%** of rank variance. [E-035] eliminated seven candidates individually;
this eliminates the best pairing of the two survivors. **"Nothing explains more than ~18%
alone or ~28% together" is now the statement**, and it rests on an exhaustive search of the
candidates the record contains rather than on not having looked.

**Artifacts:** agents/shared/findings.md -> "[R-016] Finding"; arithmetic over
results/E-035-propagation-candidates.json
**Closed:** 2026-10-15

### R-017 · Lens-2 prior art on the three claims being considered for outward use

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-097

**Description:**

Three claims are being weighed for an outward-facing note, and **none has had a prior-art
pass.** [R-002], [R-010] and [R-011] cleared earlier framings; the ES identity and the
screen framing are two days old and were searched by nobody.

`CLAUDE.md` permits no novelty claim stronger than *"unclaimed in this setting"*, and
"we did not find it" is its weakest form. This ticket is the difference between that and an
embarrassment in front of a mentor.

**The three:**

1. **The coefficient screen.** A propagation test can only measure propagation if its test
   prompt's key does not overlap the edit's key, and `(k·k*)/(k*·k*)` decides this *before*
   any edit is applied. **Searched as:** a pre-run or a-priori screen/criterion for
   propagation or ripple benchmarks; predicting edit locality from key overlap without a
   forward pass through the edited model.
2. **The ES-margin identity.** ROME's optimiser saturates its target, so the efficacy
   *margin* is rank-identical to true-answer suppression (ρ = 1.000, sd 0.02 against 5.68).
   **Searched as:** critiques of Efficacy Score / efficacy magnitude; the observation that
   the target's post-edit probability is pinned by the optimisation criterion.
3. **The benchmark construction finding.** RippleEdits' compositional tests name the edited
   subject verbatim and receive 0.982 of the update against a 0.070 floor; MQuAKE names it
   iff the edit is on hop 1. **Searched as:** critiques of RippleEdits/MQuAKE construction;
   subject leakage or surface overlap in multi-hop editing evaluation.

**Outcomes.** Per claim: **STATED** (someone has it — withdraw or reposition), **ADJACENT**
(close work exists, ours differs in one sentence), **UNFOUND** (no hit; the weakest
positive and the only one available).

**Scope.** Literature search only. No measurement. A result here changes what may be
written, never what was measured.

**Result (2026-10-15).** **Screen: UNFOUND. ES identity: UNFOUND. Benchmark finding:
ADJACENT**, with ChainEdit (2507.08427) as a named neighbour that must be cited and
distinguished — its compositional flaw is intermediate-knowledge misalignment with an
external KG, ours is the prompt naming the edited subject so the update arrives by
arithmetic. Different mechanism, different fix.

Nearest work on the screen inverts it: SUIT and SetKE treat key overlap as something an
*editor* should manage, not as a property of an *evaluation item* computable in advance.

**Confidence medium — abstracts only**, which [R-011b] established is not enough. ChainEdit
must be read before claim 3 leaves the repo. Eight identifiers unverified.

**Artifacts:** agents/shared/findings.md -> "[R-017] Finding"
**Closed:** 2026-10-15

### R-018 · Read ChainEdit properly — claim 3 depends on a distinction drawn from its abstract

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-10-15
**Updated:** 2026-10-15
**Thread:** T-097 · required by [R-017]

**Description:**

[R-017] found claim 3 **ADJACENT** to ChainEdit (2507.08427) and drew the distinction from
that paper's **abstract**. [R-011b] established what that is worth: *"a description read off
a search snippet is not a verified citation even when the identifier is correct"* — two of
this project's own literature entries were wrong after being summarised from search and then
reasoned from. Claim 3 is now the thing most likely to leave the repo, and it rests on
exactly that kind of reading.

**What must be settled, in order of how much damage each would do:**

1. **Does ChainEdit already make our observation?** Does it anywhere note that a
   compositional test prompt *contains the edited subject*, or that the edit reaches such a
   prompt mechanically rather than by reasoning? If yes, claim 3 is **STATED** and must be
   withdrawn or repositioned as a measurement of something they asserted.
2. **Is their flaw really intermediate-knowledge misalignment?** [R-017] says theirs is
   LLM-vs-KG disagreement about the middle fact. Confirm from the body, not the abstract.
3. **Does their fix dissolve our concern?** If realigning the dataset to the model's own
   beliefs also removes the subject from the prompt, their fix covers ours and the
   contribution shrinks to having measured it.
4. **Do they report anything we should cite as support** — e.g. evidence that editors
   score well on compositional tests without generalising?

**Outcomes.** **STATED** — withdraw or reposition. **ADJACENT-CONFIRMED** — the [R-017]
distinction survives a real reading and can be written in one sentence. **ADJACENT-REVISED**
— they are close in a way the abstract concealed, and the sentence must change.

**Scope.** One paper, read. Record the venue and identifier as verified or not, per the
standing citation rule.

**Result (2026-10-15). ADJACENT-CONFIRMED**, and the reading paid for itself.

1. **Do they make our observation?** No. Full-body search for `surface`, `lexical`,
   `overlap`, `verbatim`, `shortcut` returns **zero hits**; `subject` appears only in
   template grammar and path endpoints. They never note that a compositional prompt names
   the edited subject.
2. **Is their flaw intermediate-knowledge misalignment?** Yes, confirmed from the body:
   *"their reliance on external KGs for question formulation... they requires external
   knowledge beyond the edited content to correctly answer."* [R-017]'s abstract reading
   was right.
3. **Does their fix dissolve our concern?** **No — and their third variant sharpens it.**
   Filtered drops unverifiable questions, Replaced regenerates the middle fact from the
   model's state, and **In-Prompt "explicitly inject[s] intermediate knowledge into
   prompts"** — making the prompt *longer* while the edited subject remains. A repaired
   benchmark that still fails a coefficient screen is the best illustration we have of
   what the screen adds.
4. **Anything to cite as support?** They evaluate on RippleEdits **POPULAR** only, and
   merge CI and CII into one Reasoning metric following KnowEdit — so their results cannot
   separate the two compositional types [E-038] measured at 0.982 and 0.955.

**Citation:** title and authors verified against the arXiv record for **2507.08427**.
**Venue is NOT verified** — "ACL 2025" came from a search summary and must not be stated.

**Artifacts:** agents/shared/findings.md -> "[R-018] Finding"
**Closed:** 2026-10-15
