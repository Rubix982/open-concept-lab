---
name: research-legibility
description: Use before research work is published, submitted, shown or sent to anyone outside the project that produced it — a paper, a notebook page, a portfolio entry, a conference or journal submission, a page a reviewer or committee will read. Runs a vocabulary census that counts every term, identifier and internal noun used before it is defined, and fixes each by its class. Also triggers on "would a new reader follow this", "too much jargon", "explain this to someone outside the project", "this only makes sense to us", or a reader reporting they could not follow a draft. Companion to research-writing, which owns whether the claims are falsifiable; this owns whether a stranger can read them.
---

# Research legibility

A draft can be accurate, falsifiable, well-cited, correctly hedged — and unreadable
by anyone who was not in the room while the work happened. That is a separate defect
with a separate cause, and the checks that catch the first one do not catch it.

**Measured, on two pages of this author's own work, 9 November 2026.** The word-level
lint scored **0.0 hits per 10k** before and after revision. The claim audit found
**zero** unfalsifiable claims, as it had on every previous run. The same two pages
carried **forty-odd internal identifiers in running prose**, **six probe families
holding up two tables and a chart with no definition anywhere**, and a central term —
*near field* — whose first appearance was a section heading.

So the lint passes, the audit passes, and a new reader stops at paragraph three. This
skill is the pass that catches that.

---

## Pass 1 — the stranger's census

Not a reading. A count.

```bash
python3 scripts/census.py DRAFT.md
```

The script lists every candidate — identifiers, backticked and bolded terms, capitalised
coinages — with the line where each is **first used**. You supply the second column: the
line where it is **first defined**, or a dash. Every dash, and every row where use
precedes definition, is a defect.

| Term | First used | First defined | Class |
| --- | --- | --- | --- |
| near field | §3.2 heading | — | term of art |
| `alias`, `exposure`, … | §5.1 table | — | term of art |
| C-001 | §5.1 prose | — | internal identifier |
| E-004 | abstract | — | internal identifier |
| card, thread | overview, throughout | — | process noun |

**The count is the finding.** Record it before and after; it is the only number this
pass produces and it is what tells you whether the revision did anything.

### Three classes, and they take different fixes

The classes matter because applying the wrong fix produces a glossary nobody reads.

**1 · Terms of art** — *near field*, *the floor*, *delivery*, *destruction*. These
carry the content. Name each in English, by what it does, before it is given a term or
a symbol. This is the words-before-symbols ladder, and `research-writing`
(`references/mathematics.md`) owns it; do not restate it here, follow it there.

One addition from live use: **a term that cannot be defined in a clause is a content
gap, not a wording gap.** Six probe families named `alias`, `exposure`, `position`,
`repetition`, `semantics`, `discrimination` could not be glossed in a sentence each.
They needed a table with a real instance from each — the actual prompt, read out of the
probe file. Reach for that the moment a one-line gloss comes out vague.

**2 · Internal identifiers** — `C-001`, `E-004`, `T-009`, `F-07`, ticket numbers,
sprint names. Two sub-cases, and conflating them is the usual error.

- **In running prose, the identifier is telling the reader nothing. Replace it with the
  thing itself.** *"C-001 closed on the deny branch written before the run"* becomes
  *"The question had been written down with both of its answers before the run — if the
  prediction held, a usable screen; if it did not, the quantity measures delivery — and
  it closed on the second."* Longer, and the only version a stranger can use.
- **As a pointer, it stays**, because a number that cannot be traced to a run is worse
  than an ugly marker. Keep it, and spend **one sentence, once**, saying what it points
  at and where the index is.

**3 · Process nouns** — *card*, *thread*, *ledger*, *run*, *epic*, *standup*. These
describe how the work is organised, not what it found. They do not belong in the
argument at all. They belong on the page that describes the state of the work, defined
in two or three sentences, and followed by an explicit line telling the reader they can
be ignored. Writing that line is the test: if you cannot say *"the identifiers are
bookkeeping; nothing is lost by ignoring them"* and have it be true, the argument is
still leaning on them.

---

## Pass 2 — two surfaces, two jobs

Research work that is meant to be found needs two pages, and the recurring failure is
writing the second as a short version of the first.

| | Ordered by | Carries |
| --- | --- | --- |
| **The argument** | dependency — what rests on what | method, results, limits, references, the provenance of every number |
| **The state of the work** | chronology — what was asked, in what order | the questions and their answers, what is still open, what it does not have |

The argument page must be legible to someone who never sees the other one. The
state-of-the-work page is where the process vocabulary lives and the only place it is
allowed to.

**The diagnostic:** if your overview reads as an abstract of your paper, you have one
page written twice and nowhere that says what happened. The chain of questions — each
raised by the answer to the one before — is invisible in an argument ordered by
dependency, and it is often the most interesting thing about the work.

---

## Pass 3 — one example, named once, everywhere

The ladder already asks for a single running example. The trap worth naming separately
is that **figures are usually drawn before the prose settles**, so they end up carrying
a different instance. Check the figures against the text explicitly; it will not show
up in any other pass.

Worked: a figure drew one subject while the probe set the whole paper rests on was
built on another. The figure was redrawn on the probe set's own subjects. Nobody had
noticed for a day, because each artifact was internally consistent.

---

## Pass 4 — the reader who decides something

Some readers are not reading to learn. A reviewer, a programme committee, a selection
panel, anyone assessing a record of work — they are reading to **decide**, without
access to you, under time pressure, and they will not ask a clarifying question.

The test is blunt: **can a stranger verify the contribution without you in the room?**
Work that only its author can explain cannot be assessed by a third party, and
third-party assessability is what every selection process runs on. That makes legibility
evidentiary rather than cosmetic.

Two things serve it, and both are cheap:

**A contributions list, written before the sections.** Numbered, one line each. A
contribution that cannot be stated in a line is not one yet, so the list is a check on
the work as much as a courtesy to the reader.

**A readiness table** — what the venue asks for, what exists today, and where on the
page the evidence is. It belongs in an appendix and it is a checklist for the author,
not a claim about the work. The rows that fail are the point: an unmet requirement
named by the author is worth more than one found by a reviewer.

> Worked instance:
>
> | | requirement | state today | where |
> | --- | --- | --- | --- |
> | ✓ | A result that could have come out the other way | The floor was fixed before the run, and the question closed against the project | §5 |
> | ✓ | Reproduction path | Config, seed and resolved environment beside every result | §4 |
> | ✗ | Read by someone outside the project | Every finding produced and reviewed by the same two parties | §7.5 |

---

## What this pass cannot do

**It cannot make thin work look substantial, and it will make thin work look thinner.**
Defining the terms exposes how much of the page was carried by vocabulary. That is the
pass working.

**It does not check whether the claims are true or falsifiable.** That is
`research-writing`, Pass 1, and it should be run first: there is no point making an
unfalsifiable claim legible.

**A clean word-level lint says nothing about any of this**, measured both ways on the
same documents. Never report one as evidence the other passed.

## References

- `references/classes.md` — the three classes, with before-and-after from live use
- `scripts/census.py` — the census, standard library only
- `research-writing`, `references/mathematics.md` — the words-before-symbols ladder
