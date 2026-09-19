# Lookbacks — Prakash, Shapira, Sen Sharma, Riedl, Belinkov, Rott Shaham, Bau, Geiger (ICLR 2026)

*Language Models Use Lookbacks to Track Beliefs.* arXiv:2505.14685v3.
Source: `ai/lookback-research/docs/Language Models Use Lookbacks To Track Beliefs.pdf`

**Why it is here.** Saif's `lookback-research` project is built on it, and two of
its authors (Natalie Shapira, Arnab Sen Sharma) are his mentor and adversarial
reviewer on `rome-neighbors`. This is the closest available sample of the register
he is actually writing *into*.

---

## P1 · The question opening, again

> **How do language models (LMs) represent characters' beliefs, especially when
> those beliefs may differ from reality?** This question lies at the heart of
> understanding the Theory of Mind (ToM) capabilities of LMs.
>
> — Abstract, p. 1

**The move:** identical in shape to ROME P1 — plain question first, stakes second.
Two papers, four years apart, same group: treat this as the **house opening** for
this literature, not a coincidence.

---

## P2 · Naming new machinery with concrete, borrowed words

> Our investigation uncovers a pervasive algorithmic pattern that we call a
> **lookback mechanism**, which enables the LM to recall important information when
> it becomes necessary. The LM binds each character-object-state triple together by
> co-locating their reference information, represented as **Ordering IDs (OIs)**…
> the **binding lookback** retrieves the correct state OI and then the **answer
> lookback** retrieves the corresponding state token.
>
> — Abstract, p. 1

> The **source token** contains reference information that is copied into two
> instances, creating a **pointer** and an **address**. Next to the address in the
> residual stream is a **payload**. When necessary, the model retrieves the payload
> by **dereferencing** the pointer.
>
> — Figure 1 caption, p. 2

**The move:** every new object is named with a word the reader already owns —
pointer, address, payload, dereference, lookback. The vocabulary is lifted
wholesale from systems programming, where it denotes exactly the same structure.

**This is the deepest answer to "the mathematics is hard to understand."** The
difficulty is usually *naming*, not notation. A new mechanism given a Greek letter
or a coined abstraction forces the reader to carry an unanchored symbol for the
rest of the paper. The same mechanism named `pointer` arrives with its semantics
already installed.

**Rule it implies:** before introducing a symbol for a new object, search for an
existing formalism or vocabulary that already denotes it. Borrowing is a gain, not
a loss of originality — it imports the reader's intuitions for free.

This is the Premise Dry-Run's move 2 (*rename into an existing formalism*)
executed at the level of exposition rather than theory.

---

## P3 · The classic instance before the formalism

> A classic example is the **Sally-Anne test** (Baron-Cohen et al., 1985), which
> evaluates ToM in humans by assessing whether individuals can track conflicting
> beliefs: Sally's belief, which diverges from reality because of missing
> information, and Anne's belief, which is updated based on new observations.
>
> — §1, p. 1

**The move:** one concrete, decades-old, universally known instance is planted
before any mechanism is described. Every later abstraction can be checked against
it.

**Pairs with** ROME's "The Space Needle is in downtown → Seattle", which recurs
throughout that paper as the running instance. Both papers pick **one** example
and reuse it rather than generating fresh ones per section — the reader amortises
the cost of understanding it once.

---

## P4 · The figure caption is the definition

Figure 1's caption (quoted in P2) is a complete, self-contained statement of the
mechanism. A reader who reads only the caption understands the paper's core claim.

**Rule it implies:** captions carry argument, not labels. R-001 move 12 found the
same thing in Saif's standfirsts ("The edit finally ran and said no") — the
summary slot states the result rather than announcing the topic.

---

## P5 · Stating the alternative hypothesis you might confirm

> Our goal is to determine whether LMs learn a **systematic solution** to such
> tasks or rely on **superficial statistical association**.
>
> — §1, p. 1

**The move:** both outcomes are named before any result. The paper commits, in the
introduction, to a finding that could have gone the other way.

**Pairs with** design lens 4 (falsification — state confirm/deny/null in advance)
and with R-001's quarantine finding. This is where the honesty lives in paper
register: not distributed through the prose as hedging, but concentrated into one
sentence that pre-states what a negative result would have looked like.
