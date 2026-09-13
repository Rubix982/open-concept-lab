# Decisions

## [E-002] Decision: Solve-by-undo instead of a real solver

_Date: 2026-09-13_

**Decision:** The solve button replays the inverse of the recorded move history
rather than computing a solution from the cube's current state.
**Rationale:** It is exact, needs no solver dependency, and produces a legible
animation. The interesting part of this project is the interaction and the
state model, not search.
**Alternatives rejected:** kociemba (two-phase, needs a C extension and gives a
20-move solution that looks unmotivated on screen); hand-written
layer-by-layer (a project in itself).
**Revisit if:** we want to solve a cube that was scrambled by hand rather than
by the scramble button — history-undo cannot help there.
