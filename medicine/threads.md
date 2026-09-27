# Threads — medicine explainers

_Open questions. Parallel to `plan.md` (work) — a thread is an open question,
a ticket is a unit of work._

---

### T-001 · What is the organising spine of the flow piece?

**Status:** answered
**Parent:** —
**Opened:** 2026-09-27
**Question:** The bay piece is ordered by physiology (how fast each thing
kills). Flow cannot use that. What orders it?
**Answer:** One constraint — a blocked output — with every term read off it
as a downstream consequence. See `design-e002-flow.md` §0.

### T-002 · Is the causal spine actually defensible, or just tidy?

**Status:** open
**Parent:** T-001
**Opened:** 2026-09-27
**Question:** "Crowding is an output problem" is well supported in the
literature, but the piece states it flatly. Is there a defensible reading in
which input growth or throughput inefficiency dominates in some settings —
and if so, does the claim need a scope condition ("in systems with inpatient
occupancy above X") rather than being stated universally?
**Answer:** —

### T-003 · One file or two — and on what hinge?

**Status:** answered
**Parent:** —
**Opened:** 2026-09-27
**Question:** The user wants a merge. The two halves have different
organising logics. Does the merged piece need a third structure that contains
both (e.g. "two clocks a shift runs on" — the patient's clock and the
department's), or does it become one document with a visible seam, which may
be honest rather than a defect?
**Answer:** One file, on the time-to-harm ruler. A-B-C was never a claim about
anatomy — it ranks failures by how fast they kill, and the department is the
slow end of the same ranking. See `design-merge.md`.

### T-004 · Does the merge break the bay piece's ordering claim?

**Status:** answered
**Parent:** T-003
**Opened:** 2026-09-27
**Question:** The bay piece's first takeaway is "the order is physiology, not
ritual." Placing it inside a document whose other half argues that the real
order is set by bed availability may undercut or may sharpen it. Which?
**Answer:** Sharpens. The claim generalises from "the order is physiology" to
"the order is time-to-harm"; physiology was the fast special case.

### T-005 · Is nine sections already past what one page carries?

**Status:** answered
**Parent:** T-003
**Opened:** 2026-09-27
**Question:** The bay piece is already at nine sections and 265 KB. A merge
roughly doubles it. Is there a length past which a single-file explainer
stops being read and starts being scrolled — and if so, does the merge need
a collapsed-by-default second half, or a genuine split with cross-links?
**Answer:** Resolved by a change of purpose, not by measurement. The document
is now a personal reference to return to and learn from, not a one-sitting
read. Length stops being the risk; thinness is. Depth becomes a second axis
(progressive disclosure inside each section) while the time-to-harm ruler
still orders them. See T-008.

### T-006 · Does the drama tie generalise, or is it Pittsburgh-specific?

**Status:** answered
**Parent:** T-001
**Opened:** 2026-09-27
**Question:** The flow vocabulary is strongly US-specific — EMTALA,
observation status, the two-midnight rule, insurance-driven dispo. The bay
vocabulary is close to universal. A merged piece would be half universal and
half one country's billing system. Worth marking explicitly in the piece?
**Answer:** Resolved as a feature, and stated in the piece: fast failures are
the same everywhere because they are physics; slow ones differ by country
because they are design choices.

### T-007 · Is the vocabulary asymmetry evidence, or decoration?

**Status:** open
**Parent:** T-003
**Opened:** 2026-09-27
**Question:** The merge argument leans on a claim that the ED is perceptually
tuned to fast failures. One observation offered in support: the bay half has
~34 precise terms, the board half has ~10, several of them administrative
rather than clinical. Counting terms is a weak instrument and the sampling is
mine, so this may be a frame generating its own confirmation (dry-run rule 8,
the reflexive case). Either find a check someone else could run that could
come back negative, or demote it from argument to aside.
**Answer:** —

### T-008 · What does the engineer framing actually license?

**Status:** active
**Parent:** T-005
**Opened:** 2026-09-27
**Question:** The reader is a software engineer learning medicine. The shared
structure is real — sensitivity/specificity are recall and TNR over one
confusion matrix; pre-test probability plus a likelihood ratio is a Bayesian
update; ACLS is a state machine; compensated shock is reserve masking an
error until saturation. Where does the analogy stop being load-bearing and
start being a costume? The dry-run's rule 6 says these frames govern method,
not claims — so which translations are structural identity (Bayes really is
Bayes) and which are merely suggestive (the body is not a distributed system)?
**Answer:** — (working rule: identities get stated as identities, resemblances
get marked as resemblances and never used to license a medical inference)

### T-009 · Citation integrity at volume

**Status:** open
**Parent:** T-005
**Opened:** 2026-09-27
**Question:** A reference apparatus is the part of this document most likely
to be quietly wrong, because plausible-looking citations are cheap to produce
and expensive to check. What is the standing rule — every numeric claim
carries a source that was actually fetched, and anything unverified is marked
as such rather than omitted?
**Answer:** —
