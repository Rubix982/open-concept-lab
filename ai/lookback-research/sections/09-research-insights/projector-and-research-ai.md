# Research Insight: The Projector Problem — Why AI Fails at Perspective and What It Means for Science AI

_Date: 2026-07-04_
_Status: conceptual — philosophical grounding for the research direction_
_Related: agm-compliance-for-lookback.md, agm-story-taxonomy.md_

---

## The Core Observation

Theory of Mind in humans is not a capability. It is a consequence.

The precondition for modeling another perceiver's inner world is having one of
your own. Jung's "prince" — the ego as the organizing center of experience —
is what makes false belief tracking possible. The mechanism:

> I know I project. I recognize you as a being like me. Therefore I infer you
> project too — and differently.

You can hold two projections simultaneously — mine and yours — and know they
can diverge. That divergence is what the Sally-Anne test measures.

Current LLMs have the form of ToM without the generating structure. The lookback
mechanism correctly infers that Sally believes the marble is in the basket — but
it does so by pattern completion across text, not by occupying a stance and then
imagining a different one. It skips what Husserl called analogical apperception:
the pre-inferential recognition of the other as a subject because they have a
body like mine, an inner world like mine. The model goes straight to the
inference layer. That is why its ToM is brittle at exactly the edges the lookback
paper documents.

---

## The Shadow Problem

Jung: the shadow is what you cannot see because it is behind the light source.

The model has no light source — no inner prince from which to project. Therefore:
- It cannot have a shadow
- It has no mechanism for recognizing its own blind spot
- The projection goes undetected because there is no projector who knows they
  are projecting

The practical consequence: the "something off" in AI-generated outputs (UI, code,
research direction) is not a capability gap. It is the absence of a position.
The model has consumed human aesthetic judgment as described behavior, not as
lived preference. It applies it as rules. The rules pass the checklist; they fail
the felt test. The minute wrongness is pre-verbal — it violates something that
was never articulated because it never needed to be. It was in the training data
as a silence, not as a claim.

---

## What This Means for AI for Science

A general scientific AI has the same problem at scale. A researcher reading a
paper is projecting from a position — their model of the field, their sense of
what's surprising, their aesthetic of what constitutes a real contribution. That
projection generates:

- "this matters" vs. "this is incremental"
- "this is the dog that didn't bark"
- "this contradicts something I thought was settled"

Without a projector, you get a very good summary engine. Useful. Not sufficient.

---

## The Partial Projector

A domain-specific AI for science cannot have a Jungian ego. But it can have a
domain-specific evaluative structure that approximates a projector within the
space it knows.

**The architecture is the knowledge graph + AGM revision:**

- Claim nodes = what the field currently believes (the domain model)
- Provenance chains = why and when (the history of the belief)
- AGM revision operations = update mechanism (how new evidence changes the stance)
- Four gap operations = the projections (the light the system casts from its
  current model of the field)

This is partial light. More than pattern matching on surface features of papers.
Less than a genuine first-person stance. But enough to:

- Notice what is surprising relative to the current belief set
- Detect what is contested
- Identify where the field is building on something being quietly undermined

**Critical constraint:** the projector only works if it is specific. General
light is no light — it has no center. The mech interp projector needs the goal
structure of mech interp baked in: what we are looking for, what counts as
finding it, what questions are still open.

Mech interp is unusually well-suited for this. Olah and Nanda have been explicit
about what "understanding" means: identify circuits, trace how algorithms are
implemented in weights, localize where specific knowledge lives. That explicitness
is the precondition for encoding a goal structure.

---

## The Three Pieces

The frontier AI for research will need three things that do not yet exist together:

**Piece 1 — Persistent, revisable belief structure**
Not a context window. Not RAG. A genuine external representation of what is
known, with provenance and revision semantics. What the knowledge graph is
building toward. This is the projector's memory.

**Piece 2 — Interface to the experimental layer**
The system must generate hypotheses directly operationalizable as experiments
(ablations, causal interventions, probes) and update its belief structure from
results. This is the closed loop that turns the knowledge graph from a library
into a research partner.

**Piece 3 — Goal-conditioned evaluation**
The system must know what it is trying to understand, specifically enough to
score every piece of evidence as more or less relevant. For mech interp: what
evidence confirms a circuit? What would constitute a complete mechanistic account?

- Piece 1 alone: a very good research assistant.
- Pieces 1 + 2: a powerful experimental accelerator without direction.
- All three: something that has not existed before.

**Piece 4 (downstream):** genuine hypothesis generation — not gap-finding
(structural) or experiment operationalization (mechanical), but the new frame.
Trained on the discoveries that pieces 1-3 produce, better labeled through
provenance and revision structure. The loop that closes when the system
generates enough examples of frame-breaking scientific creativity that a model
can begin to learn it.

---

## The Acceleration Argument

The current bottleneck in science is not intelligence. It is:

1. The knowledge surface is too large for any one mind to hold
2. The tacit knowledge of a field is locked in the heads of a few senior people
3. The feedback loop between hypothesis and experiment is too slow and expensive

Pieces 1-3 compress all three simultaneously. What that produces is not smarter
researchers. It is a multiplication of the rate at which the creative layer —
the irreducibly human part — can be applied. The researcher who currently
generates three testable hypotheses a year generates thirty. Not because they
became more creative, but because the friction between intuition and test
collapsed.

**The immune system caveat:** faster science in domains with long feedback loops
means fragile beliefs propagate and embed more deeply before they collapse. The
AGM revision structure is both the accelerator and the immune system. A system
that tracks what is fragile and surfaces it proactively is the antidote to the
acceleration it enables.

The recovery postulate failure is practically important here, not just
theoretically. Ghost beliefs — old conclusions that slip back through revived
premises — are the failure mode of fast science. The architecture explicitly
prevents this. That is not a coincidence; it is a design requirement.

---

## The Right Ordering

The causal chain that matters:

> Improve research → speed it up → discover new problems and solutions →
> businesses use new findings to build more creative things

Most people invert this: build the business first and hope the research follows.
The correct ordering is harder, slower, and produces new categories rather than
incremental improvements — because the businesses built on genuine research
breakthroughs are not predictable from the research. They emerge because the
research changed what is physically possible.

Bell Labs logic: basic research, given time and freedom, finds the load-bearing
structures of the next era. The knowledge graph with revision semantics is not
a product. It is infrastructure for scientific clarity. The businesses are the
downstream effect, not the target.

---

## The Researcher's Position

Not seeing the side effects of your research goals is a strength, not a gap.

The researchers who have changed things most durably saw the problem in front
of them and could not look away. McClintock did not see genetic engineering.
Rubin did not see what dark matter would do to cosmology's self-understanding.
The inability to look away was the signal they were in the right place.

Seeing the side effects in advance usually means reasoning about impact rather
than being pulled by the problem. The question pulls differently — not "I want
to build this" but "this needs to exist and I seem to be the one who sees it."

The problem in clear focus: research is slower than it needs to be. The gap
between what the field knows and what any individual researcher can hold is
widening. That gap has a cost that compounds.

The side effects will become visible as the work becomes real. They are not
yours to engineer — they are what happens when a genuine solution meets the world.

The narrowness is the discipline that makes it real.
