# Mathematics that can be read

Unreadable mathematics is almost never a symbol problem. It is **ordering** and
**naming**. Both are fixable mechanically.

## The ladder — words before symbols

From ROME (Meng et al., NeurIPS 2022), §2.1. Follow all five rungs, in order.

**1 · Name each object in English, by what it does.**

> …we observe all of G's internal activations during three runs: **a clean run**
> that predicts the fact, **a corrupted run** where the prediction is damaged, and
> **a corrupted-with-restoration run** that tests the ability of a single state to
> restore the prediction.

The whole experimental design, in one sentence, before a single symbol. Everything
after this is bookkeeping over three things the reader already holds.

**2 · Bind symbols explicitly, in a sentence that does nothing else.**

> Let P[o], P\*[o], and P\*,clean h(l)i[o] denote the probability of emitting o
> under the clean, corrupted, and corrupted-with-restoration runs, respectively.

**3 · Define each quantity as arithmetic on already-named things.**

> The total effect (TE) is the difference between these quantities:
> TE = P[o] − P\*[o].

One line, two terms, both named in the preceding paragraph. **Nothing on the page
asks the reader to hold more than two bindings at once.** Prefer more lines with
fewer symbols each over one dense display.

**4 · Give one concrete instance with real content** — and reuse the *same* one
throughout. ROME uses "The Space Needle is in downtown" → "Seattle" for the entire
paper. Lookbacks uses the Sally-Anne test. A fresh example per section makes the
reader pay the comprehension cost repeatedly.

**5 · Gloss why the quantity means what it claims.**

> Intuitively, the ability of a few clean states to recover the correct fact,
> despite many other states being corrupted, will indicate their causal importance.

## Acknowledge every suppression, where it happens

> …dependence on the input x is omitted for notational simplicity.

One clause, at the moment the term is dropped. **Unannounced suppression is what
makes generated mathematics un-checkable** — the reader cannot distinguish an
omission from an error, so they must distrust the whole derivation.

## Borrow names; do not coin them

Lookbacks (Prakash et al., ICLR 2026) names its mechanism with `pointer`,
`address`, `payload`, `dereference`, `lookback` — lifted from systems programming,
where they denote the same structure. The semantics arrive already installed.

A coined abstraction ("the Deferred Retrieval Coefficient") forces the reader to
carry an unanchored symbol for the rest of the paper.

**The borrowing must be exact, not evocative.** An inexact borrowing is worse than
a coinage, because it imports wrong intuitions silently and the reader has no
signal that it has done so. Test: does the source domain's structure hold in every
respect you will rely on? If you have to say "loosely speaking, it's like a…",
do not borrow.

Related trap: a structural resemblance between a measured phenomenon and a
familiar one is a false friend. It explains nothing and costs credibility.

## Checklist

- [ ] Every symbol bound in a sentence before first use in an expression
- [ ] Every object named by function in English before it is bound
- [ ] No expression introducing more than two new bindings
- [ ] One running example, reused
- [ ] Every suppressed term acknowledged in a clause
- [ ] Every borrowed name exact in the respects relied on
