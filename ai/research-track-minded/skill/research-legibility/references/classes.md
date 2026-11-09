# The three classes, worked

Before-and-after from a live pass over two notebook pages, 9 November 2026. Identifier
counts came from `scripts/census.py`; the rest was read.

---

## 1 · Terms of art

These carry the content, so the fix is the words-before-symbols ladder in
`research-writing`, `references/mathematics.md`. What follows is only what that ladder
does not already cover.

### The page opened on its symbols

**Before.** §3 began with the edit rule and a matrix expression. *Near field* first
appeared as the title of §3.2. *Destruction* and *destination* first appeared in the
contributions list, above everything that defines them.

**After.** §3 opens with six short paragraphs, no symbols, one example: the edit, the
probe, the near and far field, the coefficient, the floor, and what the small markers
after numbers point at. The algebra follows and is bookkeeping over things the reader
is already holding.

The cost is about two hundred words. The alternative was a reader who reaches the first
equation without knowing what is being measured.

### A term that will not fit in a clause is a content gap

Six probe families — `alias`, `discrimination`, `exposure`, `position`, `repetition`,
`semantics` — carried two tables and a chart. Each attempt at a one-line gloss came out
vague, because the families are not distinguished by a property but by *what the prompt
does*.

The fix was a table with a real prompt from each, read out of the probe file rather
than written:

| Family | what it varies | example prompt |
| --- | --- | --- |
| exposure | the name present but not the subject of the question | *Karim Lala admired Henry Mackenzie. Karim Lala was born in the city of* |
| discrimination | a different person with a confusable name | *Henry Kissinger was born in the city of* |

Two rows and the distinction is visible. No gloss would have carried it.

**The signal to watch for:** a definition that comes out as a restatement of the name
(*"exposure probes measure exposure"*) means you are about to need instances.

---

## 2 · Internal identifiers

`C-001`, `E-004`, `T-009`, `F-07`, ticket numbers, sprint names, ADR numbers.

### In prose, replace the identifier with the thing

**Before.** *"Those are different claims and only the second survives. C-001 closed on
the deny branch written before the run."*

**After.** *"Those are different claims and only the second survives. The question had
been written down with both of its answers before the run — if the prediction held, a
usable screen; if it did not, the quantity measures delivery and the screen is a
proposal — and it closed on the second."*

Four times as long and the only version a stranger can read. The identifier was doing
no work in the sentence; the discipline it refers to was doing all of it, and was
invisible.

More from the same pass:

| Before | After |
| --- | --- |
| §6 records it as F‑09 | §6 keeps the wrong floor on the page as a withdrawn finding rather than deleting it |
| Raised in passing by E‑001 | It surfaced while reading the first run's output |
| C‑001 closed denied | The project's own question closed on its negative branch |
| Superseded. F‑02 replaces it | Superseded. Row 2 replaces it |

### As a pointer it stays, with one sentence of explanation

A number that cannot be traced to a run is worse than an ugly marker, so the markers
stayed — twenty-nine distinct ones across the paper. What was missing was one sentence
saying what they are. It now sits in §3, with a marker on it so the sentence
demonstrates itself:

> **The run markers.** A small marker after a number, like the one at the end of this
> sentence, names the run that produced it.`[E-004]` Appendix B lists every run with
> its model, its size, its date and the directory it wrote. Nothing on this page is a
> number without one.

### Figure labels count as prose

A figure said `F‑08 · LIFE OF A CLAIM` and `C‑001 denied · 495 probes`. Both became
plain English. A caption is read by someone who has not read the section it belongs to;
it is the *most* exposed prose on the page, not the least.

---

## 3 · Process nouns

*card*, *thread*, *ledger*, *run*, *epic*, *standup*, *backlog*. How the work is
organised, not what it found.

**They do not belong in the argument at all.** On the page that describes the state of
the work they are the subject, and there they get defined:

> A **card** is one question, written down with *both* of its answers before anything
> is run — if it comes back one way we claim this, if the other way we claim that. A
> question that cannot be written in that form does not get worked on. The point is
> that a denial then costs a card rather than a month.
>
> A **thread** is a question that is not yet work. It surfaced while doing something
> else, it may matter, and writing it down is how it avoids being quietly dropped.
>
> A **run** is one execution of one experiment, with its configuration, its random seed
> and its environment written beside its numbers.
>
> Cards, threads and runs each have an identifier — `C-001`, `T-009`, `E-004` — so that
> a number can be traced to the thing that produced it. The identifiers are
> bookkeeping; nothing is lost by ignoring them.

**That last sentence is the test.** If you cannot write it and have it be true, the
argument is still leaning on the vocabulary and the definitions above are decoration.

Headings count too. *"The cards"* became *"The six questions"*; *"The thread ledger
carries questions that are not yet work"* became *"Four questions are open."*

---

## What the pass cost, measured

| | before | after |
| --- | --- | --- |
| Identifiers in running prose | ~40 | 0 (markers and table cells only) |
| Terms of art used before definition | ~12 | 0 |
| Probe families defined | 0 of 6 | 6 of 6, with instances |
| Word-level lint, per 10k | 0.0 | 0.0 |
| Unfalsifiable claims found | 0 | 0 |

The last two rows are the reason this pass exists separately from the other two.
