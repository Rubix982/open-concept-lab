# Project: edit-reach

_Last updated: 2026-10-31 by O-001_

## Objective

Establish whether an edit's reach can be predicted before the edit is applied — and if it can, say with what error rates; if it cannot, say so and retire the proposal.

## Current Phase

Phase 1 — close C-001. Nothing else opens until it closes.

## Active Tickets

| ID | Agent | Title | Status |
| --- | --- | --- | --- |
| O-001 | Orchestrator | Initialise project; extract `editreach` package; shim edit-slice | closed |
| E-001 | Engineer | Predicted-vs-measured run for C-001 | open, described |

## Blocked

_(none)_

## Completed This Session

- O-001 · Project initialised. Six infrastructure modules lifted unchanged from `ai/edit-slice/src` into an installable `editreach` package; `coefficient.py` and `control.py` added; edit-slice's flat names replaced with forwarding shims; 13 tests pass; 24 of 25 distinct consumer import lines verified (the 25th, `apply_delta` in `debug_apply2.py`, was already broken in the committed original).

## Next Orchestrator Action

E-001 is described to standard and unblocked. The engineer writes the run script next. The first thing it must do is the anchor gate in step 1 — 42 `anchor-prefix` readings that must land in (0.999, 1.001) — because that is cheap, it is the one quantity known analytically, and a deviation there invalidates everything after it while still looking plausible.
