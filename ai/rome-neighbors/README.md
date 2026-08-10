# rome-neighbors

**Does structured representational geometry predict whether a knowledge edit
propagates to logically entailed neighbours?**

Raw representational *distance* does not reliably predict edit propagation
(E-007: near-flat ~0.6 across neighbour types). This project tests whether
*structured* geometry (Kim bilinear) and *alignment* (Jeong/STEAM) do — resolved
across entailment hops, with a **causal** metric (IIA). The first hop-resolved
causal predictor comparison for edit propagation on a decoder-only LM.

Full framing: [`design.md`](design.md) · orientation: global `~/.claude/CLAUDE.md`
Manifesto · literature: [`readings/MAP.md`](readings/MAP.md) · open questions:
[`threads.md`](threads.md) · status: [`plan.md`](plan.md).

## Layout

```
ripplekit/     the library (source of truth): config, data, reps, predictors, analysis
experiments/   thin reproducible runners per ticket, importing ripplekit
scratch/       exploratory scripts + NNsight learning curriculum (history)
readings/      MAP.md (vetted lit map) + notes + NDIF corpus + the Asta report
agents/        tickets (O-/R-/E-) and shared surfaces
results/        outputs (gitignored)
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .                 # installs ripplekit + deps
export NNSIGHT_API_KEY=...        # NDIF key (from login.ndif.us)

# data (cloned separately — large):
git clone https://github.com/edenbiran/RippleEdits ~/code/RippleEdits
# or point elsewhere:
export RIPPLEEDITS_FILE=/path/to/RippleEdits/data/benchmark/popular.json
```

GPT-J-6B runs remotely on NDIF (no local GPU needed); only configs/tokenizer load locally.

## Example

```python
from ripplekit import data, predictors, analysis

pairs = data.load_pairs()                      # verified RippleEdits loader
scores = [(p.type, predictors.raw_distance(p.base, p.neighbour)) for p in pairs]
analysis.print_table("raw distance by type", analysis.aggregate_by_type(scores))
```

## Status

Phase 2 — implementation. Baseline (raw distance) done and found flat (E-007);
position/layer sweep (E-008) and structured/alignment predictor (E-009) built;
causal outcome (E-010, on `nnpatch`) is the next brick. See `plan.md`.
