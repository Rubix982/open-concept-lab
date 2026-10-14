# bearing

A bearing is a measured direction, not a destination. This tells a research project where
it is pointed. It does not claim to know where it should go.

```bash
python -m bearing ~/code/open-concept-lab/ai/edit-slice
python -m bearing <private-project> --json
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

## Leaving it running

```bash
python -m bearing --sentinel ~/code/open-concept-lab/ai/edit-slice <private-project> \
                  --interval 2h --notify
python -m bearing --digest        # what it has seen, twice a day is enough
```

**Differential by design, and that is the only reason it survives contact.** A watcher
that reprints its full state every pass teaches you to skim it, and a skimmed watcher is
off. So it stores the last answer to every check and reports three things:

| | |
| --- | --- |
| `NEW` | was fine, now uncomfortable — **the only alarm** |
| `GONE` | was uncomfortable, now fine |
| `9d` | uncomfortable for nine days, unchanged |

That third row is the one people underestimate. **A check bad for nine days is either not
important or is being avoided**, and both are worth saying out loud. It is reported with
its age so the distinction stays yours.

`--digest` answers two different questions, and keeping them apart is what stops the
standing summary from becoming the repetition that trains skimming:

```
AS OF NOW        where things stand, with the age of each — the question someone
                 returning after a day actually has
WHAT MOVED       the change log — the question the alarms answer
```

The standing half is regenerated from state, not replayed from the log, so it is current
even when every sweep since has been quiet.

**A quiet sweep still leaves a mark** — `- 14:43 · no change · 5 standing`. Without it, a
gap in the digest is ambiguous between *nothing happened* and *the sentinel was dead*, and
those need opposite responses.

State is written atomically after every sweep, so a restart resumes rather than re-alarming
on everything it already told you.

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

## How a check gets here

Backwards from an outcome, not forwards from a hunch. The rule is derived from something
that actually happened, then encoded, then **tested against the historical case it came
from** — and only then trusted.

`unchecked_universal` is the worked example:

1. **the outcome** — a week of work was priced on *"every propagation benchmark probes
   with prompts that begin with the subject"*, asserted having inspected none. Counting
   took twenty minutes and returned 0.09%.
2. **the rule** — a claim quantified over a class of other people's work, with no
   instance inspected, is the cheapest thing to check and the most expensive to be wrong
   about.
3. **the check** — universal quantifier + external-work noun + nothing in the record
   claiming to have measured it.
4. **the test** — it must fire on the September text and go quiet once the measurement
   exists. Both are regressions in `tests/`.
5. **it was wrong once** — it fired on the paragraph that *withdrew* the claim, because
   that paragraph quotes it. A checker that cannot tell an assertion from its retraction
   punishes the behaviour it exists to encourage. Fixed, and tested.

## Track record

```bash
python -m bearing <project> --record <check> caught|false-positive|ignored "why"
python -m bearing <project> --track
```

A check is added because someone believed it would help, and **priors about which checks
matter are what this record shows to be unreliable** — three separate checks across these
tools were written with confidence and cried wolf. So outcomes are logged per check, and
`--track` names the ones that have never helped:

```
  check                           caught  false+  ignored  verdict
  unchecked_universal                  1       0        0  earns its place
  still_checking                       0       1        0  too early to say
  never_varied                         —       —        —  never fired
```

A check with no `caught` after several firings is overhead. That is edit-slice's own
falsification clause — *"if three runs pass with no caught defect, cut it back"* — made
mechanical, so it gets checked rather than quietly accreted.

## Lessons

```bash
python -m bearing --lessons
```

Twelve rules two projects earned by being wrong, each with the incident and what it cost —
so a new project inherits the scar tissue instead of re-earning it. One is mechanically
checked; the rest are there to be read. A sample:

> **A cache trusted because the file exists is how a partial run reports itself as a whole
> one.** A relaunch loaded 9 of 29 deltas, logged "cached", skipped optimisation and walked
> into scoring short. Nothing raised.

> **A measurement that changes between runs is not a measurement.** `max()` over a set broke
> ties nondeterministically; two runs of the same counting script differed by 15 prompts.

> **Prose written before a result describes the result you expected.** A runner closed with
> "a fall in reach alongside a rise in strength" — written anticipating one outcome, fired
> on the other, and described the data backwards while printing it correctly.

## What it found, first run

On `edit-slice`, three of eight uncomfortable — including the summary being 32 commits
stale and eleven of sixteen sections named after runs rather than claims. On a second, private project,
four of eight, with a different set.

**Three bugs were found by running it on a real project after the constructed tests
passed**, which is the argument for doing both:

- `done` compared a status for equality, so `answered — **DENY: …**` read as open and
  38 of edit-slice's 67 answered threads were counted unanswered.
- claim debt counted a cited open *question* as debt, flagging the nine threads in the
  section whose job is listing open threads.
- `still_checking` knew only edit-slice's vocabulary and read the second project's correction ledger —
  a document that is **entirely** corrections — as evidence nobody was checking.

Each is now a test with both branches. **A check written in one project's dialect will
libel every project that speaks another.**

## Scope, stated honestly

Derived from **two** projects — `edit-slice` (research) and a second, private project (production pipeline).
Two is enough to tell a general rule from a local accident perhaps half the time. Where a
check is a keyword heuristic it says so and prints its evidence, so disagreeing is cheap.
