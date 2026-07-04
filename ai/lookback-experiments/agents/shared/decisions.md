# Shared Decisions

_Owned by: Engineer. Append-only._

## [O-001] Decision: Python 3.12 + TransformerLens

_Date: 2026-07-04_

**Decision:** Use Python 3.12.11 (pyenv) with TransformerLens 3.5.1 and PyTorch 2.12.1.
**Rationale:** Python 3.14 (system default) breaks several ML packages (known
PEP-440 issue seen in responsible-ai project). 3.12 is stable and supported by
all dependencies. TransformerLens gives full residual stream access with
`run_with_cache()` — no manual hook wiring needed.
**Alternatives rejected:** Python 3.11 (available but 3.12 is more current);
raw HuggingFace hooks (more verbose, less ergonomic for layer sweeps).
**Revisit if:** TransformerLens introduces a breaking API change.
