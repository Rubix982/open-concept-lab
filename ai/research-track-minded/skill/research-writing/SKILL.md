---
name: research-writing
description: Use when drafting or revising research writing — papers, lab notes, design documents, research blog posts, related-work sections, or any passage stating findings. Runs a claim audit that makes every assertion falsifiable-as-written, quarantines hedging into a Limits section, and enforces a words-before-symbols ladder for mathematics. Also triggers on requests to review, tighten, or "make this sound like a real paper", and on complaints that a draft is vague, hedged, hard to act on, or reads like AI output.
---

# Research writing

Most bad research writing is not badly written. It is **unfalsifiable** — competent,
accurate prose making no claim that could turn out to be wrong, so a reader finishes
it with nothing to do. Measured, not assumed: a passage of AI-generated research prose
scored **0.0 hits per 10k on the entire word-level lint** and carried **one**
falsifiable claim in 472 words. It passed every surface check and said nothing.

So Pass 1 is the claim audit. Everything else is secondary.

## Pass 1 — the audit (always run this)

**Pick the mode first.** Asking the wrong question of a document produces nothing.

| You are… | The unit | The question |
| --- | --- | --- |
| **revising** prose | each paragraph | what observation would make this false? |
| **drafting** prose | each claim you intend to make, *before* writing | same, answered before the prose exists |
| **designing** work with no results yet | each load-bearing assumption | **if this assumption is wrong, does the work still measure what it claims?** |

Design mode is not a variant. A design's assertions are about what *will* be
measured, and "we will sweep eight layers" cannot be false, so falsifiability has
nothing to bite on. An assumption that survives being wrong is fine; one that does
not is a confound to control before the work starts.

### Revise and draft

| ¶ | The claim, in one sentence | Own or attributed? | What would make it false? |
|---|---|---|---|

- **Own vs attributed.** An own claim could be wrong even if every citation is
  reported accurately. "Qin et al. report X" is attributed; "X cannot serve as a
  gate" is own. A draft of only attributed claims cannot be wrong — that is the
  defect.
- **Falsifiable-as-written** — a reader can name the refuting observation from the
  sentence alone. "Strongly correlates" fails, no threshold to violate. "Correlates
  at r > 0.5 across three models" passes.
- **Unquantified superlatives are the commonest failure**: *the clearest*, *the
  main*, *most*, *one of the few*. Give the criterion or drop the ranking.
- **Analytic claims take the flag `[A]`.** A derived claim — *"the coefficient is
  exactly 1 for any u"* — is not refuted by any observation, only by a derivation
  error or by its premise failing. **Put the premise's falsifier in column four, not
  the claim's**, because that is where the empirical content lives. Our own: the
  pinning claim is analytic, its premise is prefix-sharing, and the premise is what
  [E-017] and [E-018] measured. *Guard: an analytic claim must ship its derivation,
  in the document or by citation. No derivation shown means not analytic, just
  unfalsifiable.*

Fix every row with an empty fourth column — sharpen, demote to an explicit
attribution, or cut. If there are no own-claims at all, stop and say so; no rewriting
fixes that.

**"I don't know what to do with this" is fixed here, not by formatting.** A draft can
be full of instructions that cannot be carried out — *"use GradSim as a pre-edit risk
score"* has a verb and an object and is unexecutable, because a gate needs a threshold
and error rates the source never gives. **A hollow instruction rests on an unquantified
claim.** Do not bolt a "next actions" list onto a draft that failed this pass; it
yields a tidy list of things nobody can do.

### Design

| # | Load-bearing assumption | If wrong, does the work survive? | Control |
|---|---|---|---|

Include **feasibility** as an assumption: *this runs inside the compute, data and
dependency budget I actually have.* A dependency failing half its calls is a design
parameter that changes the artifact — checkpointing, resumability — not an incident to
absorb later. A "no" in column three is a confound; name its control before opening
the ticket.

### The second job, which is the one that pays

Once every row has a fourth column, **which claim is load-bearing becomes visible**,
and that fixes the order of the document: the claim others depend on first, what
merely confirms it demoted.

Across two live uses the filtering caught **zero** unfalsifiable claims — both sources
were already written to that standard — while the reordering restructured the document
both times. **Expect the ranking, not the filter.** An audit that catches nothing has
not failed; read the table for what outranks what.

## Pass 2 — seven structural questions

In order. Worked examples: `references/structure.md`.

1. **Headings** — can each be rewritten as a sentence with a truth value?
   *(Navigation labels — References, Appendix, Method, and whatever plays the limits
   role — are exempt.)*
2. **Gaps** — which gap, what would closing it cost, what would change? An unpriced
   gap is a wish.
3. **Symbols** — was each object named in English, by function, before it got a
   symbol? `references/mathematics.md`.
4. **Suppression** — is every dropped term acknowledged where it is dropped? "…x is
   omitted for notational simplicity."
5. **Naming** — does an existing vocabulary denote this *exactly*? Borrow if so; under
   uncertainty coin, because a coinage fails loudly and a bad borrowing fails quietly.
6. **Hedging** — **quarantine it, do not reduce it.** All qualification goes into a
   named Limits section and the body runs unhedged. Same epistemic content,
   concentrated, and more honest: a specific limit gets named instead of a vague
   adverb.
7. **Criticism** — is the scope fixed before the damage? "X was built to do A, and it
   does. B is a different question. The problem is downstream."

### Every draft gets a limits section, whatever it is called

**The quarantine is the requirement; the name is not.** "What to attack" does the same
job in an adversarial register. Whatever section performs the role is exempt from the
truth-value heading rule.

**But check the third category survives the rename.** An adversarial framing collects
what a reviewer would attack, and nobody attacks a constraint on *use* — so that entry
tends to vanish when the section is called something else.

Three kinds of entry, and the third never appears on its own:

1. **What the result does not show** — "measures whether knowledge is present, not
   whether the model would produce it."
2. **What was not done** — "I have not run the constrained measure on GPT-2-XL."
3. **How the result may not be used** — "a consequence of the finding, not a method I
   am offering." No Pass 2 question generates it; add it deliberately.

## Pass 3 — the lint (a floor, not a gate)

```bash
python scripts/lint.py --rate DRAFT.md
```

Reference rates: hand-written research prose **0.0** per 10k over 27.7k words,
published mech interp papers **5.1**, AI-generated reports **6.4**. A 1.25× gap
between good papers and slop — **this cannot tell one from the other.** Never report a
clean lint as evidence of quality.

## Positioning claims

A novelty verdict — *"this is unclaimed"*, *"we were scooped"* — is a claim, so Pass 1
applies unchanged. A verdict stated bare is an opinion; one naming what the nearest
paper does not do can be checked. Two rules the audit does not generate:

**Shelving requires stronger evidence than proceeding.** A wrong *"the lane is open"*
surfaces later when the paper turns up. A wrong *"we were scooped"* **kills the work
silently and produces no evidence it was wrong.** An unverified scoop verdict is
grounds to verify, never to shelve.

**When a verdict turns on what a paper *did*, read its methods or appendix, not its
prose.** The introduction says what the authors hoped the construction would yield;
the appendix says what was performed. No amount of extra searching catches that.

## What this cannot do

**These passes improve a draft's epistemic structure, not its evidential base.**
Measured: applying them added seven falsifiable claims and zero new numbers, because
the source had none. Over thin evidence they produce an explicit statement that the
evidence is thin — better than confident thinness, not the same as well-evidenced.

If the draft needs numbers it does not have, say so and stop.

It also does not decide whether the work is worth doing, run the literature search, or
choose what to build next. A project-level design protocol owns those.

## References

- `references/structure.md` — the seven questions, with before/after examples
- `references/mathematics.md` — words before symbols; the free-inference test for names
- `references/exemplars.md` — marked passages, and one worked anti-exemplar
- `references/voice.md` — **only when drafting from nothing.** Extending a document?
  Take the register from the document.
