# tools — running this project when nobody is watching

Ported from `~/code/janaan/tools/pipeline`, which already solves this shape. Four pieces,
cheapest first, and one rule about what they are not allowed to do.

```
tools/preflight.py   gates before anything touches the network — they REFUSE, not warn
tools/triage.py      every warning sorted by cause; UNSORTED is the output that matters
tools/report.py      one page per run, readable mid-run, what needs a person first
tools/watch.py       the loop: preflight → run → triage → report → next
tools/dryruns/       verdict bands exercised on known-answer data, kept in the repo
tools/queue.json     pre-registered work. A person writes it; the loop only runs it.
tools/navigator.py   uncomfortable questions about the DIRECTION of the work
```

## The navigator

`preflight` and `triage` watch results. `navigator` watches the **sequence** — the property
that produced *"we have dug ourselves too deep into narrow cases"* on 2026-10-14, after a
week in which every closed ticket was a finer measurement of our own instrument.

Seven questions, each phrased so that the **bad** answer is the computable one. A check
that cannot come back bad is a horoscope.

| it asks | because |
| --- | --- |
| What have you never varied? | `[T-065]`: every narrowing here came from unfixing something |
| Instrument, or the world? | a run of inward work is how a project loses its point |
| Does the write-up cite unfinished work? | §4.5 asserted a withdrawn claim for nine days |
| Is the abstract still about this project? | the summary drifts from the findings silently |
| Named after claims, or after runs? | a paper organised by experiment makes the reader build the argument |
| What did you price and not do? | the honestly-costed item is the one that gets postponed |
| Stopped withdrawing — better, or not checking? | both look identical from inside |

**It has no taste.** It catches drift, not direction. A project can pass every question and
still be pointed somewhere that does not matter — which is why this is a tool for the
person steering, not a replacement for them.

Two of its checks were wrong on first run and were fixed rather than tolerated: one counted
a finding as an unfinished ticket, the other counted open threads in §8 — which exists to
list open threads — as claim debt. **A checker that cries wolf is one people learn to
skip**, the same lesson `preflight`'s cache rule taught.

## The rule

**The loop owns execution. A person owns judgement.**

It runs pre-registered work, gates it, recovers it, reports it, and decides when to wake
someone. It does **not** choose what to run next, judge whether a result is real, write a
record entry, close a ticket, or touch the write-up.

That split is the design, not a limitation, and it comes from this project's own record:

- `[T-065]` found that **every** narrowing here came from choosing *which* held-fixed
  dimension to vary. That choice is the generative act and it is judgement. A loop picking
  its own next experiment would be guessing at the one step that has reliably worked.
- `[E-025]`, `[E-026]` and `[R-012]` each cost a withdrawn claim to interpreting a result
  too eagerly — twice from a headline written before a confound check finished. A loop
  that interpreted results would reproduce that failure faster than anyone could catch it.
- The write-up already names the real risk: *"a large, internally consistent body of work
  that nobody outside has stress-tested."* Automating **generation** without automating
  **scrutiny** makes that worse, not better. So every report has a section headed *what
  this page did not check*, and it is a section rather than a footnote.

## Escalation

The loop stops and writes `out/reports/ESCALATION.md` on exactly four things:

| trigger | why it is worth waking for |
| --- | --- |
| preflight refuses | the code is wrong; running wastes the night |
| an **unsorted** triage line | a failure class nobody has diagnosed yet |
| a verdict outside `expect` | a surprise — and surprises are the reason to run anything |
| a job outlives its budget | the `[E-033]` shape: 144h in `RECEIVED`, no exception raised |

Everything else is logged and the queue carries on. A known failure needs a count; an
unknown one needs a person.

## Using it

```bash
.venv/bin/python tools/preflight.py agents/engineer/workspace/run_e033.py
.venv/bin/python tools/triage.py --all
.venv/bin/python tools/report.py --all          # out/reports/
.venv/bin/python tools/watch.py --dry           # show the plan
.venv/bin/python tools/watch.py --loop          # overnight
```

Queue a job by writing it into `tools/queue.json`: the ticket id (so the report can read
your pre-stated outcomes back out), the runner, its args, a wall-clock budget, and
`expect` — the verdicts that would *not* be a surprise. Leave `expect` off and every
verdict escalates, which is the right setting for a first run of anything.
