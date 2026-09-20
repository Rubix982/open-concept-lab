---
name: research-writing
description: Use when drafting or revising research writing — papers, lab notes, design documents, research blog posts, related-work sections, or any passage stating findings. Runs a claim audit that makes every assertion falsifiable-as-written, quarantines hedging into a Limits section, and enforces a words-before-symbols ladder for mathematics. Also triggers on requests to review, tighten, or "make this sound like a real paper", and on complaints that a draft is vague, hedged, hard to act on, or reads like AI output.
---

# Research writing

Most bad research writing is not badly written. It is **unfalsifiable** — competent,
accurate prose that makes no claim which could turn out to be wrong, so a reader
finishes it with nothing to do.

This was measured, not assumed. A passage of AI-generated research prose scored
**0.0 hits per 10k on the entire word-level style lint** — no "delve", no
"Furthermore", no hedge adverbs — and contained **one** falsifiable claim in 472
words. It passed every surface check and said nothing. Do not mistake clean prose
for research writing.

So Pass 1 is the claim audit. Everything else is secondary.

## Pass 1 — the audit (always run this)

**Pick the mode first.** The audit asks a different question of each kind of
document, and asking the wrong one produces nothing. Getting this wrong was the
first defect found in live use.

| You are… | The unit | The question |
| --- | --- | --- |
| **revising** prose | each paragraph | what observation would make this false? |
| **drafting** prose | each claim you intend to make, *before* writing | same — but answered before the prose exists, not after |
| **designing** work that has no results yet | each load-bearing assumption | **if this assumption is wrong, does the work still measure what it claims?** |

Design mode is not a variant of the other two. A design's assertions are about what
*will* be measured, and "we will sweep eight layers" cannot be false — so there is
nothing for the falsifiability question to bite on. Audit the assumptions instead.
An assumption that survives being wrong is fine; one that does not is a confound,
and it has to be controlled before the work starts.

### Revise and draft modes

| ¶ | The claim, in one sentence | Own or attributed? | What observation would make it false? |
|---|---|---|---|

- **Own vs attributed.** An *own* claim could be wrong even if every cited paper
  is reported accurately. "Qin et al. report X" is attributed. "X cannot serve as
  a gate" is own. A draft consisting only of attributed claims cannot be wrong,
  which is the defect.
- **Falsifiable-as-written** means a reader can name the refuting observation
  *using only what the sentence supplies*. "Strongly correlates" fails — there is
  no threshold to violate. "Correlates at r > 0.5 across three models" passes.
- **Unquantified superlatives are the commonest failure**: *the clearest*, *the
  main*, *most*, *one of the few*, *mostly*. Each names a ranking with no
  criterion. Give the criterion or drop the ranking.

Then **fix every row with an empty fourth column** — by sharpening the claim,
demoting it to an explicit attribution, or cutting it.

If the draft has no own-claims at all, stop and say so. That is the finding, and no
amount of rewriting fixes it.

### Design mode

| # | Load-bearing assumption | If wrong, does the work survive? | Control |
|---|---|---|---|

Include **feasibility** as an assumption, not as an afterthought: *this can be run
inside the compute, data and dependency budget I actually have.* If a dependency
fails half its calls, that is a design parameter and it changes the artifact —
checkpointing, resumability — not an incident to absorb later.

A "no" in column three is a confound. Name its control in column four before
opening the ticket.

### The audit's second job, which is the one that pays

Once every row has its fourth column, **which claim is load-bearing becomes
visible** — and that determines the order of the document. Put the claim the others
depend on first, and demote what merely confirms it.

This is not a secondary effect. Across two live uses the filtering job caught
**zero** unfalsifiable claims — the source material was already written to that
standard — while the reordering changed the structure of the document both times:
an analytic result was promoted above the measurement that confirmed it, and a
control was promoted from an attachment into the experiment's first job.

**Expect the ranking, not the filter, to be what you get.** If the audit catches
nothing, it has not failed; read the table for what outranks what.

## Pass 2 — seven structural questions

Ask these of the draft, in order. Detail and worked examples:
`references/structure.md`.

1. **Headings** — can each be rewritten as a sentence with a truth value? Content
   headings must assert or ask. *(Structural labels — Limits, References,
   Appendix, Method — are navigation and exempt.)*
2. **Gaps** — for each gap named: which gap, what would closing it cost, what
   would change? An unpriced gap is a wish.
3. **Symbols** — was each object named in English, by its function, before it got
   a symbol? See `references/mathematics.md`.
4. **Suppression** — is every dropped term acknowledged where it is dropped? One
   clause: "dependence on x is omitted for notational simplicity."
5. **Naming** — does an existing vocabulary already denote this structure
   *exactly*? Borrow it if so. Inexact borrowing is worse than a coinage.
6. **Hedging** — is any qualification appearing outside the Limits section? Move
   it there and make it specific.
7. **Criticism** — is the scope fixed before the damage is described? "X was built
   to do A, and it does. B is a different question. The problem is downstream."

## Pass 3 — the lint (a floor, not a gate)

```bash
python scripts/lint.py --rate DRAFT.md
```

Reference rates: hand-written research prose **0.0–1.3** per 10k, published mech
interp papers **11.6**, AI-generated reports **13.9**. Note how close the last two
are — **this lint cannot tell a good paper from a bad report.** It catches house-
style slips and nothing more. Never report a clean lint as evidence of quality.

## Hedging is quarantined, not distributed

The single habit that most separates confident-and-honest prose from hedged mush.
Generic writing spreads a thin film of qualification over every sentence
("may potentially suggest"). Strong research writing collects **all** of it into a
named Limits section and leaves the body unhedged.

Same epistemic content, concentrated — and the concentrated form is *more* honest,
because a specific limit gets named instead of a vague adverb:

> **Prompt sensitivity is not my finding.**
> **I have not run the constrained measure on GPT-2-XL.**
> Ordering across models is robust; absolute levels are not.

Every draft gets a Limits section. Entries come in three kinds, and the third is
the one that never appears on its own:

1. **What the result does not show** — "measures whether knowledge is present, not
   whether the model would produce it."
2. **What was not done** — "I have not run the constrained measure on GPT-2-XL."
3. **How the result may not be used** — "this is a consequence of the finding, not
   a method I am offering." A constraint on *use* rather than on evidence. No
   question in Pass 2 generates it; it usually comes from a project-level rule, and
   it has to be added deliberately.

## What this cannot do

**These passes improve the epistemic structure of a draft. They cannot improve its
evidential base.** Measured: applying them added seven falsifiable claims but zero
new numbers, because the source had none. What they produce over thin evidence is
an explicit statement that the evidence is thin — better than confident thinness,
not the same as being well-evidenced.

If the draft needs numbers it does not have, say so and stop. Do not fill the gap
with plausible-sounding quantities.

## Where this stops

This skill covers **writing the thing** — the claim, its structure, its notation,
its limits. It does not decide whether the work is worth doing, who else is doing
it, or what to build next. If you have a project-level design protocol, that is
where those live; this skill will not duplicate it, and design mode's feasibility
row is the one place they touch.

## References

- `references/structure.md` — the seven questions, with before/after examples
- `references/mathematics.md` — the words-before-symbols ladder
- `references/exemplars.md` — marked passages, and one worked anti-exemplar
- `references/voice.md` — **open only when drafting from nothing.** When extending
  an existing document, take the register from the document; that is faster and it
  worked both times it was tried.
