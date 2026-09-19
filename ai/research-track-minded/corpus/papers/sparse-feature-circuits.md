# Sparse Feature Circuits — Marks, Rager, Michaud, Belinkov, Bau, Mueller (ICLR 2025)

*Discovering and Editing Interpretable Causal Graphs in Language Models.*
arXiv:2403.19647v3.
Source: `ai/lookback-research/docs/Sparse Feature Circuits ....pdf`

**Why it is here.** ROME supplies notation and Lookbacks supplies naming; this one
supplies **positioning** — how to say what is wrong with prior work without
either hedging or sneering. That is design lens 2 executed in prose.

---

## P1 · Positioning as a two-sentence contrast, in the abstract

> Circuits identified in prior work consist of polysemantic and
> difficult-to-interpret units like attention heads or neurons, **rendering them
> unsuitable for many downstream applications. In contrast**, sparse feature
> circuits enable detailed understanding of unanticipated mechanisms in neural
> networks.
>
> — Abstract, p. 1

**The move:** prior work gets one sentence naming a *specific structural*
deficiency (polysemanticity of the unit), and the contribution gets one sentence
naming the specific capability that deficiency blocked. No adjectives about
quality. The criticism is a property of the unit of analysis, not of the authors.

**Pairs with** R-001 move 21 (criticism bounded before it is delivered) and the
Premise Dry-Run's move 7 (separate structural from incidental). Saif's "This is
not a criticism of the benchmark" section is the long form of the same instinct.

---

## P2 · Numbered challenges as the structural skeleton

> Doing so requires us to address **two challenges: First**, we must identify an
> appropriate fine-grained unit of analysis, since obvious choices like neurons are
> rarely interpretable… **Second**, we must address the scalability problem posed by
> searching for causal circuits over a large number of fine-grained units.
>
> — §1, p. 1

> We leverage recent progress in dictionary learning … to tackle **the first
> challenge**. … Then, to address **the scalability challenge**, we employ linear
> approximations…
>
> — §1, p. 2

**The move:** the paper announces two problems, then solves them in the stated
order, referring back by name. That is all the signposting it needs — there is no
"In this section, we will" anywhere.

**Rule it implies:** structure is carried by **named commitments the reader can
check off**, not by meta-commentary about the document. R-001's negative space list
bans section pre-announcement; this shows what replaces it.

---

## P3 · A footnote that closes an ambiguity before it opens

> We use "neuron" to refer to a basis-aligned direction in an LM's latent space
> (not necessarily preceded by a nonlinearity).
>
> — footnote 1, p. 1

**The move:** a word with a contested meaning in this literature is pinned on
first use, in a footnote, in one sentence, including the specific misreading being
excluded (the parenthetical).

**Rule it implies:** the symbol table has a prose sibling. Terms that the field
uses inconsistently get a one-line definition at first use — and the definition
should name what it is ruling *out*, which is the part that actually prevents the
misreading.

---

## P4 · Honest scope on what the method is for

> These approaches are not well-suited to the many cases where researchers
> **cannot anticipate ahead of time** how models internally implement their
> surprising behaviors.
>
> — §1, p. 1

**The move:** the gap is stated as a *condition under which* prior methods fail,
not as a blanket inadequacy. It is falsifiable — if researchers can anticipate the
mechanism, the prior methods are fine, and the paper says so.

**Pairs with** R-001 move 17 (state the scope as what the result is not evidence
for).
