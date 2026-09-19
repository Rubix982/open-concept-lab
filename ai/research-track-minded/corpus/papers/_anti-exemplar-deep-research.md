# Anti-exemplar — AI-generated research report

*Edit Propagation, Representation Geometry, and Localization in Decoder-Only
Knowledge Editing.* 21 pages, no authors, no venue.
Source: `ai/rome-neighbors/readings/Edit Propagation, Representation Geometry, and Localization in Decoder-Only Knowledge Editing.pdf`

Two siblings live in `ai/rome-neighbors/experiments/edit_propagation/` and fail
identically. **This is the negative control: the thing the skill exists to not
produce.** It is worth keeping precisely because it is competent — it is not
gibberish, it is well-organised and factually accurate, and it is still useless as
research writing.

---

## A1 · A table of contents instead of an argument

> Table of Contents
> Background: decoder-only knowledge editing, locate-and-edit methods, and evaluation goals
> Knowledge editing methods in decoder-only LMs: ROME, MEMIT, MEND, and why edits fail to generalize or scale
> Ripple effects and multi-hop consequences of edits: RippleEdits, MQuAKE, and portability
> Geometry of factual knowledge and representational similarity
> …
> Open gaps: coverage limits, scalability, and certification needs
>
> — p. 1

**The failure:** the document is organised by **topic coverage**, not by a claim
being argued. Each heading names a subject area. None of them asserts anything.

Contrast ROME, whose structure is: here is a question → here is a measurement →
here is what it revealed → here is a method that tests the revelation → here is
whether it worked. Every section advances one argument.

**Diagnostic to encode:** *can each section heading be rewritten as a sentence
with a truth value?* If not, the document is a survey wearing a paper's clothes.

---

## A2 · Assembly rather than argument

> "Each of MEMIT, ROME, and EMMET has a precomputation step where a large number
> of Wikipedia articles are passed through the model being edited…"
> (Meng et al., 2022) Locating and Editing Factual Associations in GPT
> "We analyze the storage and recall of factual associations in autoregressive
> transformer language models, finding evidence that these associations correspond
> to localized, directly-editable computations. We first develop a causal
> intervention…"
>
> — p. 3

**The failure:** the body is stitched verbatim quotation — here, an entire
published abstract pasted in whole. The document has **no claim of its own, so
nothing in it can be wrong.**

This is the sharpest diagnostic available, and it connects straight to R-001's
epistemic layer. Saif's `five-days` tracks eight claims and reports that seven
were withdrawn or narrowed. This report tracks zero claims and withdraws nothing,
because it never risked anything. **Unfalsifiability here is not a subtle flaw; it
is the entire character of the document.**

**Diagnostic to encode:** *what in this document could turn out to be false?*
Zero is a failing answer.

---

## A3 · Gaps named without being priced

> Open gaps: coverage limits, scalability, and certification needs
>
> — p. 1

**The failure:** "open gaps" as a topic heading, with no statement of which gap
matters, what it would cost to close, or what closing it would change. Compare
Saif's "The fix is cheap: **report possession alongside efficacy, measured on your
model**" (R-001 move 20) — a named gap, a named fix, and a cost.

---

## Why this failure mode is worth naming precisely

The report is **accurate and useless**, and those are independent properties. A
skill that optimises only for correctness will produce this. The three properties
it lacks — a claim that could be false, a structure that advances an argument, and
a priced fix — are exactly what R-001 found concentrated in Saif's writing.

**This also names the thing Saif described as his months-long frustration:** "you
give me a lot of text, I don't know what to do with it." That is what a document
with no falsifiable claim feels like to read. There is no action item because
there is no position.
