# Experiment: Ripple Sweep — 10 Edits, All Neighbor Types

**Ticket:** E-004
**Goal:** Scale E-003 to 10 triples. Produce the ripple accuracy matrix.

## What to implement

`sweep.py` — iterates over all confirmed triples from E-001, applies ROME
edit, probes all neighbor types, aggregates accuracy by type.

## Expected output plot

A heatmap: rows = edit triples, columns = neighbor types (N0, N1, N2, reverse,
distractor). Cell color = accuracy (green = updated, red = stale).

The expected pattern based on the literature:
- N0 (paraphrase): ~70% — partially propagates
- N1 (one-hop): ~30% — rarely propagates
- N2 (two-hop): ~10% — almost never
- Reverse: ~5% — essentially never
- Distractor: ~95% — correctly unchanged

This is the gap. Visualizing it concretely is the contribution.
