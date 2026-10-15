# The research loop — what runs when nobody is at the desk

_Written 2026-10-15, after the lab went dark for ten hours because nothing was scheduled
to wake the agent. `watch.py` could run queued work and the bearing sentinel could report,
but neither can generate work or re-invoke anyone. When the designed queue emptied at
11:19, the project stopped._

This file is the standing instruction for an autonomously-woken session. It is **not** the
same thing as `tools/watch.py`, and the difference is the whole design.

---

## Two loops, and why they have different powers

`tools/watch.py` is a **batch runner with no judgement.** Its docstring forbids it to
choose what to run next, decide whether a result is real, write a record entry, or close a
ticket — grounded in [T-065], which found that every narrowing in this project came from
judgement about which held-fixed dimension to vary. **That constraint is correct and
stands.** A process that picked its own next experiment by pattern-matching would
manufacture a large, internally consistent body of work nobody has read, which the
write-up already names as this project's real risk.

**This loop is a woken agent, which can do the judgement step.** So the prohibition does
not transfer wholesale. What transfers is the *reason* for it: the step that produces
results is a deliberate choice about what to vary, and it must actually be made, not
simulated. The rules below exist to keep that choice real.

---

## The cycle

On each wake, in order. Stop at the first phase with work in it.

1. **Ratify what finished.** A run has completed if its result file exists. Read the log,
   write the record entry in `agents/shared/decisions.md`, close the ticket, update the
   thread. **Mark the entry `_Unratified_`** — see below.
2. **Recover what broke.** If `out/reports/ESCALATION.md` exists, diagnose it. A failed
   gate, an unsorted triage line and a crashed runner are different problems; `logs/<ticket>-stderr.log`
   is where a crash's evidence lives.
3. **Queue what is designed.** A ticket whose runner passes all six preflight gates and
   whose dry-run exercises every verdict branch goes into `tools/queue.json`.
4. **Design what is open.** Take the highest-value open thread. Pass the ten lenses.
   Pre-state outcomes **before** writing the runner. Write the dry-run first if the verdict
   logic is non-trivial.
5. **Generate, when nothing is open.** Run a Premise Dry-Run against the thread ledger —
   the nine moves, in prose. **This phase is the point of the loop**, and skipping it is
   how a research agent becomes a work-queue processor. The ledger emptying is not a
   reason to stop; it is the signal to do the generative step.

---

## Hard rules, each earned

1. **Cheap bound before expensive run.** Twice on 2026-10-15 a closed-form calculation
   replaced hours of compute — [R-016] bounded a combination at 0.534 and cancelled 94
   fresh edits; [R-013] counted 46,754 prompts in twenty minutes against a priced week.
   **Before queuing anything over an hour, ask what arithmetic would make it unnecessary.**
2. **Pre-state, then run.** Bands fixed after seeing numbers are decoration. Where a number
   has been seen, say so in the ticket and state no band about it — [E-040] is the worked
   example.
3. **A band that over-reads is reported as it fell, with the correction beside it.**
   [E-040]'s `n >= 3` and [E-042]'s sign-count both returned verdicts stronger than their
   evidence. Both are recorded as defects in the band, not smoothed away.
4. **Never run an intervention whose failure mode returns a plausible number**, unless it
   carries a correctness gate that would catch that failure. [T-095] is deferred for exactly
   this reason. Seven harness defects in two days each returned a plausible value rather
   than an error.
5. **Delivery is not effect.** [E-028d], 2.96×. Every entry says which it measured.
6. **Existence, never a rate** — [O-004], unless the set is a released file counted whole.

---

## What this loop may NOT do

- **Send anything outward.** No email, no publishing, no posting, no sharing a link. The
  packet goes to Natalie when a person decides it does.
- **Delete or overwrite data.** Caches and result files are append-or-new.
- **Withdraw or weaken a claim in the write-up on its own judgement.** It may *add* a
  measured result and may *flag* a claim as needing withdrawal — in `out/RATIFY.md`, for a
  person. A withdrawal is a decision about what this project asserts publicly.
- **Promote a post-hoc finding to a headline**, or report a verdict its own pre-stated band
  did not return.

---

## Ratification

Autonomous output is **drafted, not accepted.** Every record entry written by a woken
session carries `_Unratified_` and a line in `out/RATIFY.md`, which is regenerated each
cycle and is the single thing to read on return:

    what ran · what it found · what band it cleared · what needs a human decision

A person removes the marker. Nothing else does. The purpose is not ceremony — it is that
the loop's failure mode is a confident wrong record, and an unread confident wrong record
is how a body of work rots from the inside.

---

## Operating notes

- Cron jobs are **session-only** and fire only while the REPL is idle. They do not survive
  the session ending, and they expire after 7 days. The terminal must stay open.
- `tools/watch.py --loop` runs the queue; it sleeps 15 minutes between reads and **re-runs
  anything still queued**, so a finished job must be removed by hand or by this loop.
- The bearing sentinel reports drift; it does not act.
