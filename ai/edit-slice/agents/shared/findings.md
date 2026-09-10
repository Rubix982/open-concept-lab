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
