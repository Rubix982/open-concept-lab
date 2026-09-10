# edit-slice

Research instrument for measuring **directional** propagation of weight-level
knowledge edits against a **decidable** dependency oracle.

Not a method. We do not propose better editing algorithms. We measure what
existing ones (ROME, MEMIT) do to knowledge they were not aimed at. Any
suggestion that drifts toward "and then we could fix it by..." is out of scope —
proposing a method means owning the burden of beating JNO (arXiv 2606.01610),
and that is not this project.

---

## Core claims (the thing being tested)

1. **Backward probing is unexplored.** All existing ripple evaluation probes
   forward: edited fact → consequences. Nobody probes the *grounds* that made
   the original fact hold. Edit "Eiffel Tower is in Rome" and the model still
   believes it was built for the 1889 Paris Exposition — a contradiction
   reachable only upstream.
2. **No decidable oracle exists.** Every benchmark uses approximate semantic
   distance (embedding cosine, RAG rank, LLM-generated MCQs). A compiler or type
   system gives a decidable relation instead.
3. **Code as domain for weight edits.** Dependency graphs drive planners
   (CodePlan) and retrieval; weight edits on code knowledge are scored with
   scalar accuracy. Nobody joined those ends.

This is a **transfer**, not a discovery. The symbolic literature solved it:
JTMS justification networks (Doyle 1979), AGM contraction, backward program
slicing (Weiser 1981). Frame it as importing a formalism into the subsymbolic
setting. Never frame it as "nobody thought of this."

---

## Definitions — treat as binding

- **Fact**: a behavioral unit defined by its probe set. Not a parameter-level
  object. Superposition explains why edges leak; it is not our ontology.
- **Dependency**: name which relation is meant — syntactic reference, type
  entailment, or semantic. The compiler gives a **decidable lower bound** on
  true dependency, never the full graph. Do not write code or docs implying
  completeness.
- **Scope**: propositional layer only (signatures, ownership, conventions,
  invariants). The procedural layer — capacity to write architecture-consistent
  code — is explicitly out of scope.
- **The graph is a normative audit spec**, not a model of the network. Its
  boundary is our choice. Coherence is bounded at **k hops**, forward and
  backward. `k` is always an explicit parameter, never a default buried in code.
- Three outcome categories, keep them distinct in every metric name and column:
  - `update` — a fact that should have been replaced was (correct)
  - `damage` — an unrelated dependent broke (harmful)
  - `orphan` — the edit left its own grounds standing, and the resulting belief
    state is jointly **implausible** (new). *Amended 2026-09-10:* previously
    "and now contradictory". Measured [E-002]: the grounds are evidential, so a
    satisfying world usually exists and the claim is implausibility, not
    inconsistency. Graded, never binary. See definitions.md declaration 6.

Banned word: **"inevitable."** Full world-model revision is undeliverable.

---

## Current task

**Backward-probe pilot.** ~50 CounterFact edits, **GPT-J-6B via NDIF**, ROME.
Two hand-built probe sets per edit: consequences (forward) and grounds
(backward). Hypothesis: forward looks respectable because that's what these
methods were tuned against; backward fails badly.

**Grounds are hand-built and deliberately deductive** for this pilot. E-002 found
that grounds *as expressed in Wikidata* are evidential, not deductive — but that
is a fact about Wikidata's property schema, not about knowledge. Hand-building
lets us ask the sharper question: **does contraction ever occur at all?**
Hand-picked sets are legitimate for an **existence** claim and illegitimate for
any **frequency** claim. Do not let this pilot's sets be reused to estimate a rate.

Deliverable is a two-panel figure and a number. Nothing else needs to exist yet.
Do not build the movement-sweep infrastructure until this asymmetry is
confirmed — it is a week of work and worthless if there's nothing there.

---

## Metrics and experimental hygiene

Primary signal is distributional movement, not accuracy.

- **KL** pre→post over next-token distribution at the final position. Unsigned
  magnitude; needs no reference answer.
- Carry three signed quantities alongside, always:
  - log-prob of pre-edit correct answer. *Amended 2026-09-10:* this previously
    read "for grounds probes this should **not** fall", which assumed grounds are
    bystanders. They are the thing under audit. Measurement is now **sign-free** —
    ask whether the model gave up *anything* where coherence demanded it give up
    *something* — and `orphan` is graded, per definitions.md declaration 6 and
    agents/shared/decisions.md [E-002].
  - log-prob of injected object token (rising where it shouldn't = leakage)
  - entropy change (rising = confusion, not reassignment)
- Multi-token answers: teacher-force and sum log-prob deltas. Never read
  position one alone.

**Controls are mandatory, not optional.** Every perturbation moves everything a
little, so raw KL rankings are dominated by fragile prompts.

1. Null distribution over unrelated prompts — significance means exceeding a
   high percentile, not being nonzero.
2. A *different* edit of comparable magnitude on the same base model, swept
   identically. Probes moving under both are generically unstable; only probes
   moving under ours are candidates.

Any script producing a ranking without both controls is incomplete. Say so
rather than shipping it.

**Caching.** The base model is fixed, so the pre-edit pass runs once. Persist
top-100 log-probs plus log-sum-exp of the tail per prompt, so new metrics never
require re-running the base model.

**Triage buckets** for significant movers, joined against edit metadata:
`shares_subject` (expected), `shares_relation` (relation-level leakage),
`shares_object` (attractor effect), `shares_nothing` (surprise). Only the last
gets read by hand; its size is itself a result.

**Reproducibility.** Out-degree is measured relative to the edge-type
vocabulary. Different vocabularies give different branching factors for the same
node. Every artifact reporting out-degree must record the vocabulary alongside
it. Same for `k`. Seeds fixed and logged.

---

## Probe generation

Hand-written probes are circular — they enumerate what we already believe
depends on the fact. Two escapes, both wanted eventually:

- **Read questions off the oracle.** A formal language has a closed edge-type
  set (calls, imports, type instantiation, subtyping, field access, module
  exports). Each templates a question mechanically. Probe discovery becomes
  edge-type enumeration: finite and inspectable. The graph is the *question
  generator*, not just the ground truth.
- **Invert for discovery.** Sweep a broad unrelated prompt bank, rank by
  movement, inspect top movers, then explain them. Measure-then-probe.

Templates give coverage; the sweep gives surprise. Enumeration for the code
domain is graph traversal — walk k hops, template per edge type.

Worth trying: ROME's update is low-rank at one layer, so its effect on an input
is governed by that input's key vector's overlap with the edit's key direction
under covariance whitening. That predicts blast radius **without a forward pass
through the edited model**. If predicted and measured rankings correlate, cheap
predictor plus mechanistic story. If they diverge, that divergence is the
finding.

---

## Stack and conventions

- Python for pipelines and analysis. No framework scaffolding; small,
  well-structured modules with real boundaries.
- Prefer stdlib and established libs. Justify every new dependency.
- Clean architecture, not scripts: loading, editing, probing, metrics, and
  reporting are separate modules with typed interfaces. A notebook is a
  consumer, never the source of truth.
- Deterministic seeds, configs in files not argv defaults, results written to
  disk with the config that produced them.
- Long runs must be resumable.
- Skip basics in explanations. Advanced, real-world application level.

```
edit-slice/
  notes/        session notes, definitions.md, meeting prep
  refs/         papers + bib
  probes/       probe sets, one file per edit batch
  src/          pipeline
  results/      raw outputs (gitignored except summaries)
```

`notes/definitions.md` is the most important file in the repo. Keep it under a
page. It should get harder to change over time.

---

## Literature — read before designing anything adjacent

- **KnowledgeSmith** (2510.02392) — already tested the out-degree hypothesis.
  Editing over-spreads, unlearning under-spreads; hierarchical branch structure
  imposes ceilings on update effectiveness; consistency-capacity tradeoff. Do
  not re-derive this.
- **JNO** (2606.01610) — desirable propagation and unintended perturbation as
  coupled pressures. Our correct/damage distinction, as a method.
- **RippleBench** (2512.04144) — distance-stratified propagation curves, and the
  distance function is pluggable including graph path length. **Check whether a
  code dependency graph can be swapped in.** Highest-leverage available move.
- **Forgetting is Not Erasure** (2606.02860) — apparent forgetting may be
  interface drift, recoverable by stitching. If so, "damage" is accessibility
  loss, not destruction, and the jenga framing is wrong in an interesting way.
- **AI Engram** (2606.14997, ICML 2026 oral) and its critique (2607.24805) on
  path dependence under sequential edits.
- **EditPropBench** (2605.02083) — dependency-labeled cascades, but manuscripts
  and LLM editors, not weights.
- **CodePlan** — Bairi et al., Proc. ACM Softw. Eng. 1 (FSE), 2024, arXiv
  2309.12499. Change may-impact analysis; the compiler is explicitly the oracle.
  Means claim 2 is "exists in SE, unused in editing," not "open."
- **Cohen et al.**, TACL 2024 (RippleEdits) — read the test-type definitions
  directly. Logical Generalization covers inverse and symmetric relations, which
  is arguably a weak backward probe and the likeliest counterexample to claim 1.

Citation IDs above came from search and are **unverified**. Verify against arXiv
before any of them enters a document that leaves the repo. Never generate a
citation from memory — look it up or leave a `TODO(cite)`.

---

## Out of scope / do not suggest

- Proposing or tuning an editing method.
- Self-reinforcing update mechanisms, backward-pass sync between chains.
- Biological neurogenesis analogies — they argue for unbounded parameter growth,
  which is the expensive option.
- Token-cost or inference-savings framing as headline. It is motivation at most.
  Leading with cost invites "RAG already solves this, cheaper."
- Scaling **for its own sake**, or to frontier scale for headline value. The
  discipline stands; the blanket size cap does not. *Amended 2026-09-10:* the
  model must be large enough to **hold the grounds it is audited against** — a
  model that never knew the justification cannot orphan it, so possession is a
  **construct requirement**, not ambition. GPT2-medium is too thin for that, so
  the working target is **GPT-J-6B via NDIF**. Choose the smallest model that
  demonstrably holds the grounds; "small and legible" still wins every tie.
- Any claim of novelty stronger than "unclaimed in this setting."
