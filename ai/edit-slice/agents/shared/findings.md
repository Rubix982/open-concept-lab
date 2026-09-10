# Findings — edit-slice

_Owned by: Researcher. Append-only._

---

## [R-001] Finding: RippleEdits' Logical Generalization is NOT a backward probe — but claim 1 must be narrowed

_Date: 2026-09-10_

**Verified metadata (session note §9 required this).** Cohen, Biran, Yoran,
Globerson, Geva, "Evaluating the Ripple Effects of Knowledge Editing in Language
Models," **TACL 2024**, arXiv **2307.12976** (v1 Jul 2023, v2 Dec 2023).
CLAUDE.md's "TACL 2024" is correct. `rome-neighbors/readings/ripple-effects/notes.md`
says "EMNLP 2023" — **that note is wrong and should be corrected.**

**What LG actually is.** Section 3.1 defines six criteria. Logical
Generalization: "Relations in a knowledge graph satisfy certain logical
constraints. For example, the relation Sibling is symmetric and therefore if
(e,Sibling,o) is true then (o,Sibling,e) is also true." Transitive relations
(e.g. Location) are checked likewise. The logical properties are manually
specified per relation.

**The verdict.** LG probes the *logical closure of the edited triple*. It does
not probe grounds. Two cases:

- *Symmetric/inverse* — edit (Eiffel, located-in, Rome), probe (Rome, contains,
  Eiffel). This swaps the arguments of the **same triple**. It is "backward" in
  argument order, not in justification. The probed fact is not a premise of the
  edit; it is the edit restated.
- *Transitive* — (Eiffel, located-in, Rome) + (Rome, located-in, Italy) =>
  (Eiffel, located-in, Italy). This *consumes* a second fact as a premise but
  probes only the **conclusion**. Whether the premise survived is never asked.

Neither reaches the orphan case: "the Eiffel Tower was built for the 1889 Paris
Exposition" is a distinct fact about a distinct entity that made the original
location fact hold. No RippleEdits criterion probes it. Preservation and
Relation Specificity are non-interference checks on the edited subject, not
grounds checks either.

**Consequence — claim 1 is narrowed, not killed.** The defensible form is:

> Existing ripple evaluation probes the *logical closure* of the edited triple,
> forward and lateral. Inverse/symmetric probes exist (RippleEdits LG) and are
> backward in **argument order**. No benchmark probes backward in
> **justification order** — the distinct facts whose truth was a premise for the
> edited fact.

The phrase "backward probing is unexplored," unqualified, is now indefensible
and must not appear in anything Natalie or Arnab reads. This is exactly the
counterexample §9 predicted Arnab would find.

**Unresolved.** Sources disagree on the sixth criterion: ar5iv gives
Preservation (PV) and states Forgetfulness is not defined; secondary sources
list Forgetfulness (FF) and omit PV. Likely an arXiv-v1 -> TACL rename. Does not
affect the verdict (neither is a grounds probe). TODO(verify) against the TACL
version of record before publication.

**Confidence: medium.** LG's definition is confirmed by two independent sources
and the verdict follows directly from it. Downgraded from high because the raw
PDF would not extract (image-heavy) — definitions came via ar5iv, not the TACL
version of record — and the PV/FF discrepancy is open.

---

## [R-002] Finding: Lens 2 clears — not scooped, but must be repositioned against knowledge-conflict and deferral

_Date: 2026-09-10_

**Verdict: PROCEED.** No existing work partitions an edit's affected knowledge by
*whether logic determines the outcome* and surfaces the underdetermined part for
human decision. But two neighbours are closer than design.md assumed, and the
positioning sentence must change.

### What was checked

**1. Backward direction — reconfirmed by a second independent source.**
*Benchmarking Knowledge Editing using Logical Rules*, Moteu Ngoli, Kouagou,
Zahera, Ngonga Ngomo — arXiv **2606.10554**, ISWC 2025 (LNCS 16141). Extracts
logical rules from a KG for an edit, generates multi-hop questions, finds ROME
and FT show up to a **24% gap** between directly edited and *entailed* knowledge.
Entirely forward: "logical consequences", "entailed knowledge". No premises, no
grounds. Independent of Cohen et al., same conclusion — [R-001] holds.

**2. Knowledge-conflict literature — nearest neighbour, different construct.**
*Knowledge Conflicts for LLMs: A Survey*, arXiv **2403.08319**, EMNLP 2024.
Taxonomy: context-memory, inter-context, **intra-memory**. Intra-memory is where
an orphan would live, and **knowledge editing is explicitly named as a cause** of
it. But the definition is:

> "a condition where LLMs exhibit unpredictable behaviors and generate differing
> responses to inputs that are semantically equivalent but syntactically distinct"

That is **paraphrase inconsistency**, not justification contradiction. Our orphan
is not a model giving two answers to one question; it is a model giving one
answer while retaining a coherent set of beliefs entailing its negation. Distinct
construct. Confirmed absent from the survey: (a) no method identifies which facts
conflict after an edit, (b) no method distinguishes conflicts logic can resolve
from ones it cannot, (c) no human routing appears anywhere. Mitigations are
fine-tuning, plugins, output ensembles, contrastive decoding.

**3. Abstention / deferral — the differentiator is the trigger.**
Existing deferral (selective prediction, learning-to-defer, ReDAct arXiv
2604.07036) triggers on **model uncertainty**: confidence below a calibrated
threshold routes to a human or a larger model. Ours triggers on **logical
underdetermination** — the model may be perfectly confident and still be in a
position where coherence demands a choice logic cannot make. Different signal,
different cause.

> **This is exactly what design.md lens 7 baseline 1 tests.** If pre-edit
> confidence and entropy predict the contested set as well as kernel structure
> does, we have reinvented uncertainty-based deferral. Our own baseline is the
> test of whether we are distinct from this literature. That is a good position.

**4. AGM → LLM transfer — unclaimed.** *From Doyle to AGM: A Survey and an
Implementation Roadmap for Belief Change*, Almeida & Casals, arXiv **2608.14567**.
Traces Doyle & London 1980 through AGM to contemporary approaches. **Purely
symbolic** — no mention of LLMs, neural networks, or model editing anywhere.
Useful as the citation for the formalism import; not a competitor.

**5. Unexpected support for T-011.** *One Mask to Rule Them All: On Hidden Facts
after Editing and How to Find Them*, Holmov, Youssef, Schoots, Seifert — arXiv
**2605.28839** (Apr 2026). Trains a binary mask over edited weights that reverses
>70% of edits on held-out data. Key line:

> "Our finding that edits **suppress rather than overwrite** knowledge explains
> why ROME and MEMIT fail to propagate changes to related facts."

This is mechanistic evidence for our structural claim: an expansion operator that
suppresses rather than retracts is exactly what leaves grounds intact. Converges
with *Forgetting is Not Erasure* (2606.02860) on accessibility-vs-destruction.
**Cite it; do not re-derive it.**

### Consequence — the positioning sentence changes

Was: *existing work measures whether an edit propagates; this measures whether an
edit left a decision unmade.* Still true but no longer sufficient, because
intra-memory conflict is adjacent. Now:

> Prior work measures **whether** an edit produced an inconsistency — forward
> entailment gaps (2606.10554), paraphrase inconsistency (2403.08319) — or defers
> on **model uncertainty** (selective prediction). None asks whether the
> inconsistency is one **logic can resolve**, and none surfaces the
> irreducibly-underdetermined remainder for a human. The contribution is the
> partition and the queue, not the detection.

### Unresolved / not checked

- **EasyEdit** and other editing toolkits not inspected directly for a partition
  or discretion signal. Remaining scoop surface.
- **T-003** (RippleBench distance-function swap) still unchecked.
- **Metadata inconsistencies to verify before citing:** 2606.10554 lists ISWC
  **2025** with a June **2026** arXiv date; 2608.14567 carries an Aug-2026 arXiv
  ID but reports "submitted 29 May 2026". Per session-2026-09-08 §9, resolve both
  against arXiv before either enters a document that leaves the repo.

**Confidence: medium-high.** Four abstracts and one survey section read directly,
two independent confirmations of the backward gap. Downgraded from high because
the sweep was search-driven rather than a systematic venue pass, and EasyEdit was
not inspected.
