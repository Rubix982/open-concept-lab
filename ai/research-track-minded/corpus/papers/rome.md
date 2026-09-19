# ROME — Meng, Bau, Andonian, Belinkov (NeurIPS 2022)

*Locating and Editing Factual Associations in GPT.* arXiv:2202.05262v5.
Source: `ai/lookback-research/docs/Locating and Editing Factual Associations in GPT.pdf`

**Why this paper carries the most weight here.** R-001 found Saif's own corpus has
no paper-register or notation sample at all. ROME supplies both, and it is the
paper two of his projects (`rome-neighbors`, `edit-slice`) are built on — so the
register is already the one he reads in.

---

## P1 · The opening question, asked in plain words

> **Where does a large language model store its facts?** In this paper, we report
> evidence that factual associations in GPT correspond to a localized computation
> that can be directly edited.
>
> — §1, p. 1

**The move:** the paper opens on a seven-word question a non-specialist can hold,
then answers it in the very next sentence. No suspense, no literature throat-
clearing before the point. Compare Lookbacks P1 — the same move, and it is
apparently the house style of this group.

**Why it works:** the question is the *title of the problem*, not a framing
device. Everything downstream is an attempt to answer that one sentence, which
gives the reader a test for whether any given paragraph is earning its place.

**Pairs with** R-001 move 11 (the conclusion arrives in the first two sentences).
Saif already does this in blog register; this is the paper-register form of it.

---

## P2 · Three conditions named in English before any symbol appears

> To calculate each state's contribution towards a correct factual prediction, we
> observe all of G's internal activations during three runs: **a clean run** that
> predicts the fact, **a corrupted run** where the prediction is damaged, and **a
> corrupted-with-restoration run** that tests the ability of a single state to
> restore the prediction.
>
> — §2.1, p. 3

**The move:** the entire experimental design is stated in one sentence, in
English, with each condition named by what it *does*. The formalism that follows
is then just bookkeeping over three things the reader already understands.

**This is the single most transferable lesson for the mathematics half.** The
reason generated mathematics is unreadable is almost never the symbols — it is
that symbols arrive before the objects they denote have been named in words. The
ladder here is strict and worth encoding as a rule:

1. **Name each object in English, by its function.** ("a corrupted run where the
   prediction is damaged")
2. **Then bind a symbol to it**, explicitly. ("Let P[o], P\*[o], and
   P\*,clean h(l)i[o] denote the probability of emitting o under the clean,
   corrupted, and corrupted-with-restoration runs, respectively")
3. **Then define the quantity as arithmetic on named things.**
   ("TE = P[o] − P\*[o]")
4. **Then a concrete instance with real content.** (prompt "The Space Needle is in
   downtown", o = "Seattle")
5. **Then an intuitive gloss of why the quantity means what it claims.**

---

## P3 · Definition by difference, one line each

> The **total effect** (TE) is the difference between these quantities:
> TE = P[o] − P\*[o].
>
> The **indirect effect** (IE) of a specific mediating state h(l)i is defined as
> the difference between the probability of o under the corrupted version and the
> probability when that state is set to its clean version, while the subject
> remains corrupted: IE = P\*,clean h(l)i[o] − P\*[o].
>
> — §2.1, p. 3

**The move:** every defined quantity is a difference of two probabilities that
were each named a paragraph earlier. There is no expression on the page that
requires holding more than two things at once.

**The anti-pattern this rules out:** a single dense display equation with six
subscripted terms introduced simultaneously. Even when correct, it is unreadable,
because the reader has to build five bindings before evaluating anything. Prefer
**more lines, fewer symbols per line.**

Note also that IE is stated **in words first, then in symbols** — inside a single
sentence. The colon is doing the work of the ladder in miniature.

---

## P4 · Explicit permission to drop detail

> …dependence on the input x is omitted for notational simplicity.
>
> — §2.1, p. 3

**The move:** the simplification is *declared*, in one clause, at the moment it is
taken. The reader never wonders whether x was forgotten or suppressed.

**Rule it implies:** every abuse of notation gets one clause of acknowledgement.
Unannounced suppression is the most common way generated mathematics becomes
un-checkable — the reader cannot tell an omission from an error.

---

## P5 · Marking what is expected versus what is new

> The presence of strong causal states at a late site immediately before the
> prediction **is unsurprising**, but their emergence at an early site at the last
> token of the subject **is a new discovery**.
>
> — §2.2, p. 4

**The move:** the result is split into the part any reader would have predicted
and the part that is actually a contribution. The paper gives away the boring half
of its own finding in order to make the other half unmissable.

**Direct hit on R-001's X-not-Y signature.** Saif's paired-contrast habit is not a
personal tic — it is how this literature marks novelty. In paper register it has a
specific job: *pre-empting the reviewer who says "we already knew that."*
Answers part of T-006 — the construction earns its keep when it separates
expected from new, and degrades to mannerism when used for mere emphasis.

---

## P6 · Numbers inline, attached to the claim they support

> The ATE of this experiment is 18.6%, and we note that a large portion of the
> effect is mediated by strongly causal individual states (**AIE=8.7% at layer
> 15**) at the last subject token. … MLP contributions peak at **AIE 6.6%**, while
> attention at the last subject token is only **AIE 1.6%**.
>
> — §2.2, p. 4

**The move:** the comparison that carries the argument (6.6% vs 1.6%) sits inside
the sentence making the argument. No "as shown in Figure 2."

**Pairs exactly with** R-001 move 5. Saif already does this. Confirmation that the
habit is paper-register-correct, not a blog affordance.

---

## P7 · The negative result, kept and priced, in a footnote

> One could also compute the **direct effect**, which flows through other model
> components besides the chosen mediator. However, we found this effect to be
> **noisy and uninformative**, in line with results by Vig et al. (2020b).
>
> — footnote 5, p. 3

**The move:** the obvious alternative measurement a reviewer would ask about is
named, reported as having been tried, and dismissed with a reason plus a
corroborating citation — in two sentences, in a footnote.

**Pairs with** R-001 move 19 (error reported with magnitude and cause) and design
lens 5 (record the methods you are deferring and why). This is what the reviewer
trail looks like when it is done economically rather than as a section.

---

## What ROME does *not* supply

Its limitations discussion is thinner than Saif's own. `the-check-that-was-never-
there` has a five-item "Honest limits" section with specific unrun experiments
named; ROME's equivalent is comparatively brief. **The hedging-quarantine move
(R-001's central finding) is stronger in Saif's writing than in this exemplar** —
so on that one axis the corpus should not defer to the paper.
