# We tried to fix one fact inside an AI — and found out what else moves

_edit-slice · 2026-09-21 · Saif Ul Islam_
_Plain-language version. The artifact written to be judged by specialists is
`web/notebook/edit-slice/review.md`; this is the other one, and they are allowed to share
nothing but their facts._

**How to read this.** Nine slides, about ten minutes. No term appears before the thing it
names. Every claim traces to a record — ids live in the speaker notes, never on a slide,
so a question can be answered from the ledger live. Problems 4 and 5 are our own errors,
and they are what makes the rest credible.

---

## 1 · The setup

An AI has learned millions of facts. Some are wrong, or go out of date. Retraining the
whole thing costs a fortune, so people built tools that reach in and change **just that
one fact**. These tools are widely used and they work, by the measure the field uses.

Our question is the one underneath: when you fix one fact, **what else moves?**

## 2 · Problem 1 — it doesn't fix a fact, it smears over a name

We changed which country one person was born in. Afterwards the AI also answered
differently about their job, their language, their citizenship — things we never touched.

The pattern: anything you ask that **starts with that person's name** gets hit. Think
find-and-replace on a name when you meant to correct one sentence.

And not partially — at full strength, every time. It falls out of the arithmetic the tool
uses, so it is not a glitch better tuning fixes.

_Records: E-016 (the arithmetic), E-017, E-021 (the name's position is both sufficient and
necessary), E-018 (a different person's name gets 8%, so this is keyed on the subject and
not on everything)._

## 3 · Problem 2 — what looks like reasoning is overwriting

We changed the **country** someone was born in, then asked for the **city**. The AI named
a city in the new country. That looks like thinking — as if it worked out that a new
country means a new city.

So we tried something that should not work: we changed where the person **works**. Where
you work says nothing about where you were born.

**The AI moved their birth city anyway. Same rate. Usually the same city.**

Nothing was being figured out. The name got painted over and everything hanging off it
came along.

_Records: E-014, then the control E-015 — 28/42 in both arms, paired difference +0.0 pp,
exact McNemar p = 1.000, same city 84% of the time._

## 4 · Problem 3 — the tests may be graded on the glitch

The standard way to check whether a fix "spread sensibly" is to ask follow-up questions.
Almost all of those questions start with the person's name — which is exactly the case
that breaks.

So a test may be measuring the glitch and scoring it as intelligence. Nobody did this on
purpose; it is just how the questions happen to be worded.

We cannot yet say how much is affected, and that is the thing we would most like someone
else to check.

_Priced at about a week: re-score one published propagation benchmark with the name moved
later in the sentence. Not run._

## 5 · Problem 4 — the standard "did it work?" check is too easy to pass

It asks only whether the **new** answer beats the **old** one. A fix can pass that while
barely changing what the AI believes.

**We know because we fell for it ourselves.** We built a safety check on that idea, it
gave us a green light, and it was worthless. We had to throw out a result and redo the
work three times to get it honestly.

_Records: E-026's root-cause analysis; E-028a measured it — the quantity that check reads
varies by 0.17 across conditions where real edit strength varies by 5.70._

## 6 · Problem 5 — our own best idea was wrong

We could measure exactly how much of a fix arrives at any given question, cheaply, without
running the damaged AI. That looked like a way to predict harm before paying for it.

**It does not predict harm.** Same amount arriving, three times the damage, depending only
on where in the AI you make the change.

We checked this four separate ways before believing it, because it cost us the most
attractive thing we had.

_Records: T-079 answered DENY across E-028b, E-028c and E-028d._

## 7 · The record — twelve claims, nine withdrawn or narrowed

Most of what we learned is what does not work. Every withdrawn claim is published with
what killed it, including ones withdrawn after being written up.

The one that survived is small and solid: an arithmetic reason why these fixes reach
everything sharing a name.

The full record is online — every decision, every dead end, every run log. Most of it went
nowhere, which is the point of publishing the list rather than the highlights.

## 8 · Three things I cannot decide from inside

1. **Is the main result already known?** It is a line of arithmetic. Practitioners may
   simply assume it, and "we could not find it stated" is the weakest form of novelty
   claim.
2. **Is the benchmark consequence worth a week?** It is the only item here that changes
   what other people do.
3. **Is a small, careful result publishable**, or does this need the scale work it
   currently refuses to do?

Nine open questions are written up with what each would settle and what it costs. Which is
worth a month is the judgement I would most like contradicted.
