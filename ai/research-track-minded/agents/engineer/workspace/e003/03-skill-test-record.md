# E-003 · What the skill did, and where it broke

One live use: a new section of `web/blog/2026-09-15-five-days.mdx` covering
[E-016] and [E-017], plus a correction to a published gap statement that those
tickets closed. ~1,370 words written, one paragraph of the existing post retracted
and replaced, standfirst updated.

This is n=1 and the author is the skill's author. Read it as a defect list, not as
validation.

---

## Which pass produced the most change

**Pass 1, and not by a small margin — but not in the way the skill advertises.**

The audit's stated job is catching unfalsifiable claims. It caught none: all ten
candidate claims already had a refuting observation, because they came out of
`decisions.md`, which is already written to that standard. By its own stated
purpose the pass found nothing.

What it actually did was **reorder the section**. Filling the table put the
analytic claim (ROME's normalisation pins the coefficient to 1) at the top and
demoted the empirical one (42/42 chains unchanged) to confirmation. Left to
instinct I would have opened with the experiment — "we ran the whitened editor and
nothing happened" — which buries the only durable result under a null.

**That is a different and larger benefit than the skill claims, and it is
unclaimed.** The audit is documented as a filter. Its stronger use is as a
**ranking** device: once every claim sits in a table with its falsifier, which one
is load-bearing becomes obvious, and that determines the structure. `SKILL.md`
should say so.

## Rules that fired and were wrong

**Pass 1 is written for revision and silently assumes a draft exists.** "For each
paragraph of the draft, fill one row." There was no draft. Drafting needs the
audit run forward over available claims, before prose. Adapted on the spot, but a
first-time user would either skip Pass 1 while drafting or write unaudited prose
and then audit it — which reverses the ordering this project argued for. **Real
defect. Highest-priority fix.**

**The lint's one hit was correct and its fix improved the sentence.** It flagged
"named it the most promising place left to look" — my paraphrase of the earlier
post. Replacing it with the actual quoted wording ("the obvious place a genuine
inference effect could still hide") was both more accurate and shorter. A
superlative was standing in for a quotation I could have just used.

No false positives in the lint over 1,371 words. The mention-stripping added in
E-002 held: the draft quotes `C = I`, `u`, `k*` and several banned-adjacent phrases
inside backticks and none fired.

**Pass 2 §3 caught a real defect the lint could not see.** I bound three symbols —
`k*`, `v*`, `u` — and then never used `v*` again. A dangling binding makes a reader
hold a symbol for nothing. Rewritten to bind only the two that carry the argument.
This was the single most useful structural catch, and it came from a question, not
a pattern.

**Pass 2 §6 (hedging outside Limits) produced one judgement call the skill does not
resolve.** The body says the layer-5 key is "largely determined by the subject
tokens themselves". Is "largely" a hedge to be relocated, or a quantifier carrying
the measured 7% attenuation? I kept it, on the grounds that it summarises a number
stated two paragraphs earlier. **The skill needs the distinction: a qualifier
backed by a number in the text is not hedging; one standing in place of a number
is.** Currently unstated.

## Did the Limits section write itself?

**Yes, and this was the clearest win.** Five entries came straight out of the audit
table's scope rows with almost no rework — the unrun relocation comparison, the
attenuating minima, the chain counts, the layer-5 restriction, and the named
falsifiers.

One entry did *not* come from the audit and had to be added deliberately: the
instruction not to read the finding as a method proposal. That is a
`CLAUDE.md`-level constraint, not something any of the seven questions asks about.
**The Limits section has a category the audit does not generate**: constraints on
how the result may be *used*, as distinct from limits on what it *shows*.

## Was SKILL.md read end to end, or is it already too long?

Read end to end, once, then referred back to twice — for the Pass 2 list and for
the heading-exemption rule. The four `references/` files were opened once each:
`mathematics.md` while writing the `(k·u)/(u·k*)` derivation, `voice.md` not at
all.

**`voice.md` going unused is the notable result.** The twenty-one moves did not get
consulted, because matching the register of a document I was appending to was
easier than consulting a list about it. That suggests the voice reference matters
for drafting from nothing and is close to dead weight when extending existing work
— which is the more common case.

111 lines is not too long. The structure held. But **Pass 3 was run twice and Pass
2 was applied from memory rather than from the file**, which means the parts that
actually need to be in front of you are the seven questions, and they are currently
third in the document behind two blocks of prose.

## Defects, ranked

1. **Pass 1 assumes a draft exists.** Add a drafting mode: audit the claims, not
   the paragraphs, before writing.
2. **The audit's ranking use is undocumented** and is plausibly its main benefit.
3. **No rule distinguishes a number-backed qualifier from a hedge.**
4. **The Limits section needs a use-constraint category** that no question
   generates.
5. **`voice.md` was not used.** Either it is for drafting-from-nothing only and
   should say so, or it should be cut.

None of these are fixed here. E-004 opens for them, and they should be fixed after
a second live use rather than after this one — five defects from n=1, written by
the author, is a list to test, not a list to act on.
