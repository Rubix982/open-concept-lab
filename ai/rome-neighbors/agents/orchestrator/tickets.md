# Orchestrator Tickets

### O-001 · Initialize project structure

**Status:** closed
**Type:** coordinate
**Priority:** high
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Description:**
Create the rome-neighbors project directory with agentic structure, plan.md,
readings/, and experiments/. Open initial researcher and engineer tickets.

**Artifacts:**
- `plan.md`
- `agents/` structure
- `readings/` stubs
- `experiments/` stubs

**Closed:** 2026-07-22

---

### O-002 · Establish proper research codebase structure

**Status:** in-progress
**Type:** coordinate
**Priority:** high
**Created:** 2026-08-11
**Updated:** 2026-08-11

**Description:**
Transition from exploratory scripts (scratch/, demo_distance_by_type/) to a
reproducible research codebase. Extract the logic duplicated across the demos
(RippleEdits loader, representation extraction, predictors, aggregation/plots)
into an importable `ripplekit/` package so experiments become thin, reproducible
runners. Keep scratch/ and the demo scripts as the exploratory record (history);
new experiments build on the package.

**Structure:**
```
ripplekit/          # the library (source of truth)
  config.py         # model id, layers, seeds, criterion→type map, paths
  data.py           # verified RippleEdits loader + answer-anchor index
  reps.py           # NNsight/NDIF representation extraction (last/mean @ layer)
  predictors.py     # raw distance (baseline) + alignment (STEAM); structured stub
  analysis.py       # aggregate-by-type, sep metric, hop-AUC, plotting
experiments/        # thin runners per ticket, importing ripplekit
readings/ scratch/ agents/ design.md threads.md plan.md   # unchanged
README.md .gitignore requirements.txt pyproject.toml
results/            # outputs (gitignored)
```

**Guardrail:** lean, no premature abstraction. Scaffolding serves the bricks
(E-008/E-009/E-010), it is not itself a brick. Reuse validated demo logic;
mark remote-dependent parts as needing a run to confirm.

**Artifacts:** `ripplekit/` (config, data, reps, predictors, analysis), README,
pyproject, requirements, .gitignore. Pure-Python modules (config/data/analysis)
verified against real popular.json (235 typed pairs, 4632-answer anchor index).

**Closed:** 2026-08-11
