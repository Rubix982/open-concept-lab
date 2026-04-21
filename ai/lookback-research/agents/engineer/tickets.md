# Engineer Tickets

### E-001 · Explain RoPE and repeat_kv with annotated visualizer script

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
Produce a standalone, runnable Python script at `scripts/rope_and_gqa_explainer.py`
that walks through three functions from the lookback-research attention
implementation:

1. `rotate_half(x)` — splits head_dim in half and rearranges sign/order
2. `apply_rotary_pos_emb(q, k, cos, sin)` — applies RoPE encoding to Q and K
3. `repeat_kv(hidden_states, n_rep)` — expands KV heads to match Q head count (GQA)

Script must:
- Use small, human-readable tensors (no real model weights) so every number can
  be traced by hand
- Print annotated step-by-step output showing shapes and values at each stage
- Include ASCII or matplotlib visualizations where the geometry helps intuition
  (rotation in 2D, head tiling pattern)
- Require only numpy, torch, and matplotlib (no transformers library)

**Artifacts:**
- `scripts/rope_and_gqa_explainer.py`

**Closed:** —
