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

**Status:** open
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

**Blockers:** none

**Artifacts:** agents/shared/findings.md; design.md §2a to be revised or confirmed
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
