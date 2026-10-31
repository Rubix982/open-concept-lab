# Project: edit-reach

_Last updated: 2026-10-31 by O-001_

## Objective

Establish whether an edit's reach can be predicted before the edit is applied — and if it can, say with what error rates; if it cannot, say so and retire the proposal.

## Current Phase

Phase 2 closed. C-002 answered on branch 1: identity is worth ~65x content (paired medians +0.0583 against +0.0009). C-001 closed denied. No card is open.

## Active Tickets

| ID | Agent | Title | Status |
| --- | --- | --- | --- |
| O-001 | Orchestrator | Initialise project; extract `editreach` package; shim edit-slice | closed |
| E-001 | Engineer | Predicted-vs-measured run for C-001 | closed |
| E-002 | Engineer | Different-subject edit arm for C-002 | closed |

## Blocked

_(none)_

## Completed This Session

- O-001 · Project initialised. Six infrastructure modules lifted unchanged from `ai/edit-slice/src` into an installable `editreach` package; `coefficient.py` and `control.py` added; edit-slice's flat names replaced with forwarding shims; 13 tests pass; 24 of 25 distinct consumer import lines verified (the 25th, `apply_delta` in `debug_apply2.py`, was already broken in the committed original).

## Next Orchestrator Action

Two things, in this order, and neither starts until Saif has read the result.

1. **Tell Natalie and Arnab.** Email 3 said "until I show the estimate predicts measured behaviour, a screen built on it is a proposal, not an instrument." The hedge held; what is owed now is the number, not a retraction. The direct-exposure critique itself is untouched, and saying both plainly is the whole message.
2. **Decide which card opens next.** The honest candidates are T-005 (is the coefficient blind in the far field, where propagation lives) and the post-hoc reading recorded in [E-001] — that subject-keyed movement may be the phenomenon rather than the confound. The second must not be worked on as a rescue of C-001; it needs its own six fields, written before any data is looked at again.
