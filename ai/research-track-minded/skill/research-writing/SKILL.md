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

## Pass 1 — the claim audit (always run this)

For each paragraph of the draft, fill one row:

| ¶ | The claim, in one sentence | Own or attributed? | What observation would make it false? |
|---|---|---|---|

Rules for filling it:

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

Then **fix every row with an empty fourth column** — by sharpening the claim, or
by demoting it to an explicit attribution, or by cutting it.

If the draft has no own-claims at all, stop and say so. That is the finding, and
no amount of rewriting fixes it.

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

Every draft gets a Limits section. Each entry states something specific that was
not done or not established.

## What this cannot do

**These passes improve the epistemic structure of a draft. They cannot improve its
evidential base.** Measured: applying them added seven falsifiable claims but zero
new numbers, because the source had none. What they produce over thin evidence is
an explicit statement that the evidence is thin — better than confident thinness,
not the same as being well-evidenced.

If the draft needs numbers it does not have, say so and stop. Do not fill the gap
with plausible-sounding quantities.

## References

- `references/structure.md` — the seven questions, with before/after examples
- `references/mathematics.md` — the words-before-symbols ladder
- `references/voice.md` — sentence, section and epistemic moves
- `references/exemplars.md` — marked passages, and one worked anti-exemplar
