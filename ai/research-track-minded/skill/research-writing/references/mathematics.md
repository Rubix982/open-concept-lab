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

## Borrow a name when the borrowing is exact; otherwise coin one

Lookbacks (Prakash et al., ICLR 2026) names its mechanism with `pointer`,
`address`, `payload`, `dereference`, `lookback` — lifted from systems programming,
where they denote the same structure. The semantics arrive already installed.

A coined abstraction ("the Deferred Retrieval Coefficient") forces the reader to
carry an unanchored symbol for the rest of the paper.

**The failure is asymmetric, which is why the default matters.**

- A **coined term** tells the reader they do not know it, so they read the
  definition. An error there gets caught.
- An **exact borrowing** hands over the semantics free and correctly. The payoff.
- An **inexact borrowing** hands them over free and *wrongly*, and neither reader
  nor writer notices.

A coinage fails loudly; a bad borrowing fails quietly. **Under genuine uncertainty
about exactness, coin.**

### The test — enumerate the free inferences

1. **Write down three things a reader will infer from the name without being told.**
   Not what you mean by it: what the source domain licenses.
2. **Mark each holds / fails / untested** in your target.
3. **If a relied-on inference fails, do not borrow.** An inference is *relied on* if
   it appears in a claim you make — check against your Pass 1 table. If it never
   enters a claim, you do not rely on it.
4. **If one fails that you do not rely on**, borrow, and spend one clause saying
   where the analogy stops.
5. **If you cannot produce three, you do not know the source domain well enough to
   borrow from it.** Coin instead.

Worked, `pointer`: dereferencing retrieves the payload (holds, relied on); the
pointer is a copy of reference information rather than the thing (holds, relied on);
many pointers may share one address (untested, not relied on). One untested and
unrelied-on → borrow, note where it stops.

Worked, `certification`: it licenses "a process yielding an artifact a third party
can check without repeating the work". Nothing in the knowledge-editing literature
offers that, and "certification layer" relies on it — the word is doing the work of
promising a guarantee. Do not borrow. The exact term is `regression suite`.

**Known weak joint:** step 1 depends on which reader, and a writer will imagine a
reader who agrees with them. A systems programmer and a statistician infer different
things from `pointer`.

Related trap: a structural resemblance between a measured phenomenon and a familiar
one is a false friend. It explains nothing and costs credibility.

## Checklist

- [ ] Every symbol bound in a sentence before first use in an expression
- [ ] Every object named by function in English before it is bound
- [ ] No expression introducing more than two new bindings
- [ ] One running example, reused
- [ ] Every suppressed term acknowledged in a clause
- [ ] Every borrowed name through the free-inference test, and coined rather
      than borrowed wherever exactness was uncertain
