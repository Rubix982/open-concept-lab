# Definitions

_edit-slice · binding. Five declarations, then the outcome vocabulary._
_This page should get harder to change over time._
_Changed 2026-09-09 (D-001, first write) · 2026-09-10 (R-001, added declaration 5)._

---

**1 · A fact is a behavioral unit defined by its probe set.** Not a
parameter-level object. ROME/MEMIT imply discrete editable units; their own
mechanism sections imply superposition and shared parameters. We take the
behavioral horn: the dependency graph is over *behaviors*, and superposition is
the explanation for why edges leak, not the ontology edges are drawn in. A fact
therefore has no location, and no metric here presumes one.

**2 · Name the dependency relation; the compiler gives a decidable lower
bound.** Syntactic reference, type-level entailment, and semantic dependency are
three relations, currently conflated under "the compiler is the oracle" — every
artifact names which it means. The compiler reports edges that certainly exist
and is silent on edges that may; it is a lower bound, never the full graph. That
is the strength: a decidable subset is what makes the oracle usable, and claiming
completeness is what would make it indefensible.

**3 · Scope is the propositional layer.** In: signatures, ownership,
conventions, invariants — knowledge expressible as assertions, where the graph
stays decidable. Out, explicitly and permanently: the procedural layer, the
capacity to write architecture-consistent code. Bracketing it is clarity, not
retreat.

**4 · The graph is a normative audit spec, not a model of the network.** An LM is
not structured like a graph and that does not matter — the graph specifies what
is *required* of the network after an edit, not what the network is. Its boundary
is a choice we state, not a fact to discover; transitive closure reaches
everything, so a boundary that had to be discovered could never be found.
Coherence is bounded: **no contradiction reachable within k hops, forward or
backward, of the edited node.** `k` is an explicit parameter of every result.
Out-degree is measured relative to the edge-type vocabulary, so every artifact
reporting it records the vocabulary alongside — same for `k`.

**5 · "Backward" means justification order, not argument order.** Two things get
called backward and only one is ours. *Argument inversion* swaps the arguments
of the edited triple — edit (Eiffel, located-in, Rome), ask what Rome contains.
That is the edit restated, and RippleEdits' Logical Generalization already covers
it via symmetric and transitive relations [R-001]. *Justification inversion* asks
after the distinct facts whose truth was a **premise** for the edited fact — the
Eiffel Tower was built for the 1889 Paris Exposition. Those are `grounds`, they
are what `orphan` is defined over, and no existing benchmark probes them.
Every claim of unexplored territory is scoped to the second sense or it is false.

---

## Outcome vocabulary — three categories, kept distinct

Every metric name and results column commits to exactly one:

| Term | Meaning | Valence |
| --- | --- | --- |
| `update` | a fact that should have been replaced was | correct |
| `damage` | an unrelated dependent broke | harmful |
| `orphan` | the edit left its own **grounds** intact and now contradictory | new |

`orphan` is what this project exists to measure, and it is invisible to forward
probing by construction: grounds sit upstream, every existing ripple evaluation
walks downstream.

## Standing constraints on language

- **"Inevitable" is banned** — full world-model revision is undeliverable, and
  the word claims we are owed it.
- Novelty is claimed no more strongly than **"unclaimed in this setting."** This
  transfers a solved symbolic formalism (JTMS, AGM contraction, backward slicing)
  into the subsymbolic setting; it does not discover it.
- `damage` asserts breakage, not destruction. If apparent forgetting is interface
  drift (2606.02860), damage is accessibility loss — the word survives, the
  mechanism claim does not.
