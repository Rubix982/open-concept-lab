# bearing

A bearing is a measured direction, not a destination. This tells a research project where
it is pointed. It does not claim to know where it should go.

```bash
python -m bearing ~/code/open-concept-lab/ai/edit-slice
python -m bearing ~/code/janaan --json
```

## Why

Research drifts before anyone notices. On 2026-10-14, after a week in which every closed
ticket in `edit-slice` was a finer measurement of its own instrument, its author said:

> I feel we have dug ourselves too deep into narrow cases, but are not able to explain the
> high level of our research outcomes.

That is a *navigational* correction, and it arrived from a person reading a trajectory. Most
of what made it possible is mechanical — a property of the sequence, computable from the
record. `bearing` asks those questions on a schedule so the correction arrives a week or two
earlier, and from the record rather than from a mood.

## The boundary, and it is the whole design

**`bearing` measures drift. It does not have taste, and it must never pretend to.**

The project's own manifesto is explicit that connecting work to real need is *"a habit, not
a system"*, and that **building a tracking system for it is itself the difficulty-trap.**
That warning is binding here. So:

| `bearing` answers | `bearing` must never answer |
| --- | --- |
| Has the work narrowed? | Does the work matter? |
| What has never been varied? | What should be varied next? |
| Does the write-up still match the record? | Is the write-up any good? |
| What was priced and not done? | Is it worth doing? |

Every check is phrased so that the **bad answer is the computable one**. A check that
cannot come back bad is a horoscope, and the first version of two checks here cried wolf
and were fixed rather than tolerated — a checker people learn to skip is worse than none.

## The brief

```bash
python -m bearing <project> --brief --since 7.days
```

The reason this project exists in the form it does. Its author has an hour a week, not a
day, and twice in one session came back asking *"what happened in between?"* — each time
the answer had to be reconstructed by hand.

**The scarce resource is not time at the laptop. It is context reload.** An hour that
starts with forty minutes of remembering is twenty minutes of research. The brief exists
to make that five.

```
1 · NEEDS YOU          decisions only a person can make. Nothing else.
2 · WHAT MOVED         since you were last here
3 · WHAT THE RECORD SAYS   drift
4 · WHAT IS WAITING    queued, blocked, priced-and-unrun
```

Ordered to be read top-down and **abandoned at any point**. Section 1 is the only part
that is yours; the rest exists so you can trust that and stop reading.

Nothing in it interprets a result. A brief that told you what your findings meant would be
the one thing the design forbids, wearing a friendlier format.

## What it reads

A project's record, through an adapter. One adapter ships: `agentic`, for the
tickets/threads/decisions/findings layout in the author's cross-project template. A project
that keeps its record differently writes ~30 lines.

```
bearing/record.py    what a record IS: work items, questions, results, claims
bearing/checks.py    the questions, each with a computable bad answer
bearing/lessons.py   hard-won rules, with the failure that produced each one
bearing/__main__.py  the CLI
```

## Lessons

`bearing/lessons.py` is the part most worth stealing. It carries the rules two projects
learned by being wrong, each with the incident that produced it — so a new project inherits
the scar tissue instead of re-earning it. They are checkable where checkable, and stated
plainly where not.

## What it found, first run

On `edit-slice`, three of eight uncomfortable — including the summary being 32 commits
stale and eleven of sixteen sections named after runs rather than claims. On `janaan`,
four of eight, with a different set.

**Three bugs were found by running it on a real project after the constructed tests
passed**, which is the argument for doing both:

- `done` compared a status for equality, so `answered — **DENY: …**` read as open and
  38 of edit-slice's 67 answered threads were counted unanswered.
- claim debt counted a cited open *question* as debt, flagging the nine threads in the
  section whose job is listing open threads.
- `still_checking` knew only edit-slice's vocabulary and read janaan's critique ledger —
  a document that is **entirely** corrections — as evidence nobody was checking.

Each is now a test with both branches. **A check written in one project's dialect will
libel every project that speaks another.**

## Scope, stated honestly

Derived from **two** projects — `edit-slice` (research) and `janaan` (production pipeline).
Two is enough to tell a general rule from a local accident perhaps half the time. Where a
check is a keyword heuristic it says so and prints its evidence, so disagreeing is cheap.
