# Decisions — edit-slice

_Owned by: Engineer. Append-only._

---

## [E-002] Decision: grounds are evidential, not deductive — AGM's ordering half, not its closure half

_Date: 2026-09-10_

**Decision:** Model the edit-to-grounds relation as **evidential support**, not
entailment. `orphan` becomes a **graded** quantity: the joint implausibility an
edit introduces, reported with the specific facts carrying it. Kernel contraction
and minimal hitting sets are dropped as machinery. AGM is retained as the account
of the *problem* — revision requires giving something up, logic does not say what —
with its **ordering** side (epistemic entrenchment, Grove spheres, Lewis-Stalnaker
closest-world) replacing its **closure** side (kernels, partial meet).

**Rationale:** E-002 measured it. None of five hand-read rigid-relation cases
produced a strict contradiction — died-Barcelona/buried-Baltimore, developer-IBM/
publisher-Sega, named-after-Hamburg/serves-London, native-Russian/born-Paris,
born-Milwaukee/citizen-Finland are all satisfiable. An earlier claim of ours was
wrong: time-rigidity blocks the *relocation* reconciliation only, and does not
establish contradiction. Strict cross-property contradiction is rare in this data,
so a deductive instrument would find almost nothing and would drift back into
RippleEdits' territory.

The change also strengthens the project's thesis rather than weakening it. If
grounds were deductive, a machine could compute the contraction and human
discretion would be a convenience. Because support is evidential, **logic cannot
adjudicate**, so the decision structurally belongs to a person — which is the
T-025 argument in its strongest form. The tool's output becomes "this edit made
these facts jointly improbable, confirm?" rather than the false claim
"contradiction detected".

**Alternatives rejected:**
- *Keep kernels, restrict to the deductive subset.* Small, mostly definitional,
  and converges on inverse/symmetric relations — which RippleEdits' Logical
  Generalization already covers [R-001].
- *Keep "contradiction" as loose vocabulary over evidential relations.* Rejected:
  a single satisfying world refutes it, and it is the fastest attack surface a
  reviewer has.

**Costs, accepted knowingly:**
- [T-008]'s termination argument weakens. "Kernels are finite so backward needs no
  `k`" presupposed entailment. Evidential support has no natural boundary and needs
  a threshold — a parameter, published contestable like
  `probes/relation_modality.md`. The forward/backward asymmetry we claimed on
  boundedness is partly given back.
- `orphan` is no longer crisp.
- [R-003]'s rigid/mutable table is **reinterpreted, not discarded**: rigidity is a
  plausibility *modifier*, not a contradiction test.

**Revisit if:** the graded measure proves unrankable in practice (no stable
threshold separating "materially implausible" from "slightly moved"), or if a
deductive subset large enough to power a study is found after all.

---

## [O-004] Decision: raise the model to GPT-J-6B via NDIF; hand-build deductive grounds for the pilot

_Date: 2026-09-10_

**Decision:** Amend `CLAUDE.md`'s blanket size cap. The pilot moves from
GPT2-medium to **GPT-J-6B via NDIF**, and the pilot's ground sets are
**hand-built and deliberately deductive** rather than discovered.

**Rationale — two independent reasons, neither of them ambition:**

1. **Possession is a construct requirement [T-039].** A model that never held a
   justification cannot orphan it. If GPT2-medium does not know Perec was born in
   Paris, the "ground" is not left standing — it was never there — and the
   phenomenon is unobservable regardless of whether it is real. The audited system
   must possess the beliefs being audited. NDIF removes the resource objection.
2. **Wikidata's schema is not knowledge's schema.** E-002 concluded grounds are
   evidential from what Wikidata expresses. Wikidata has `place of burial`; it
   cannot express "city-in-France ^ tower-in-city => tower-in-France". Letting a
   KG's property set decide whether deduction exists was a category error.
   Hand-building asks the sharper question directly: **does contraction ever
   occur, even where entailment is explicit?**

**Scope of the claim this licenses — binding.** Hand-picked ground sets support an
**existence** claim and never a **frequency** claim. "Contraction does not occur
even where entailment is explicit" is defensible; "contraction fails in N% of
edits" is not, and these sets may not be reused to estimate a rate. The
circularity of §5 is acceptable for existence and fatal for frequency.

**Alternatives rejected:**
- *Stay at GPT2-medium.* Risks measuring a null produced by ignorance rather than
  by the editor — the same trap T-023 raised for relation modality, one level up.
- *Continue with mined evidential grounds only (E-002's plan).* Deferred, not
  rejected: it answers frequency, and frequency is meaningless until existence is
  settled.

**What this does not overturn:** [E-002] stands. Grounds encountered in the wild
are evidential, `orphan` is graded, AGM's ordering half is still the formalism.
This decision adds a deductive *probe* to test a sharper case; it does not restore
kernels as machinery.

**Revisit if:** GPT-J also fails to hold hand-built grounds reliably (then
possession, not editing, is the bottleneck and the domain must change), or if
contraction *does* occur on deductive sets — which would make the frequency
question live again and reopen [E-002]'s deferred half.

---

## [E-007] Decision: candidates come from a reference vocabulary, not the edit set

_Date: 2026-09-13_

**Decision:** `candidate_pool` takes an explicit `reference` set, separate from the
edits being filtered, and every unscoreable item is reported in `skipped` with a
reason rather than dropped.

**Rationale — measured, on the first end-to-end run.** Deriving candidates from the
edit set itself scored only **12 of 40** items and returned **92%** held. The 28
missing items were relations with fewer than three attested answers, and what
survived were the two relations dense enough to be easy. With a reference
vocabulary: **100% coverage, 52% held** — consistent with E-005's 56% for the same
model.

A 40-point inflation produced by a silent denominator change is exactly the
selection artifact this filter exists to detect. Shipping it inside the detector
would have been the worst available outcome, and it was found by running the tool
rather than by reading it.

**Alternatives rejected:**
- *Warn and continue with edit-set candidates.* A warning does not fix a biased
  denominator, and the headline number would still be wrong.
- *Fail on sparse relations.* Too brittle; partial coverage is legitimate provided
  it is reported. Hence `coverage`, plus an explicit warning below 80%.

**Two collisions fixed alongside, both correctness rather than tidiness:**
- Cache keyed on model alone would serve a 50-candidate result to an 8-candidate
  run — same `case_id`, different number. Now keyed on a `fingerprint` over
  everything that changes a value (model, n_candidates, seed, placeholder); date
  excluded, since it records when rather than what.
- Output named per model would let two configs overwrite each other. Now named
  after the config.

**Revisit if:** a user's edit set has relations absent from any available reference
vocabulary. Currently that surfaces as 0% coverage with a clear reason, which is
correct but unhelpful; generating candidates from the relation's value type would
be the fix.


---

## [O-005] Decision: large models only — the size floor replaces the size ceiling

_Date: 2026-09-15_

**Decision:** work only with very large models. From NDIF's ungated set that is
**Llama-3.1-70B** (possession 79%) and **Llama-3.1-405B** (85%). GPT-J-6B and the
8B tier are out.

**Supersedes [O-004]'s rule**, which was *"choose the smallest model that
demonstrably holds the grounds; small and legible still wins every tie."* That rule
was derived to justify moving OFF GPT2-medium and was written as a ceiling-with-a-
floor. It is now a floor only.

**Rationale:** the gate result forced it. On GPT-J only **20 of 136** chains had all
three legs held (15%) — thin for an existence claim and fragile if a few fail the
edit. Possession is 56% on GPT-J against 79% at 70B, so the usable set should
roughly double. Directed by the user 2026-09-15.

**Consequence that is not yet paid for.** [E-003b] established the audit model must
BE the edited model, so gating on 70B commits the edit to 70B. [E-006] verified
editability — intervention plus remote gradients — on **Llama-3.1-8B**, not 70B.
ROME at 70B needs second-moment statistics over d_mlp 28672, roughly 3.3 GB fp32,
which has been neither collected nor costed. 405B is worse: d_mlp 53248, ~11 GB.

**Revisit if:** the covariance collection at 70B proves impractical, in which case
the honest options are to run the edit at a scale we can actually edit and report
the possession ceiling as a limitation, or to drop the edit arm entirely and ship
the audit instrument alone.
