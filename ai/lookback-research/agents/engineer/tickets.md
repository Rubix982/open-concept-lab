# Engineer Tickets

### E-001 · Explain RoPE and repeat_kv with annotated visualizer script

**Status:** closed
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

**Closed:** 2026-04-22

---

### E-002 · RetrievalProfile prototype

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
Implement the RetrievalProfile concept from
`sections/09-research-insights/belief-revision-and-uncertainty.md`
as runnable Python code that computes a structured uncertainty profile
from existing IIA result data.

The RetrievalProfile has 7 dimensions:
1. oid_coherence — peak IIA of the binding mechanism
2. subspace_stability — how flat/narrow the IIA peak is (width of window)
3. attention_entropy — spread of active window relative to model depth
4. residual_competition — IIA of competing source_2 (control experiment)
5. layer_of_first_load — first layer where IIA > 0.5
6. gap_width — layers between source end and payload start (visibility)
7. load_count — how many distinct IIA peaks appear

Script at `scripts/retrieval_profile.py` must:
- Compute the profile from pre-computed IIA JSON files (no model needed)
- Accept a model directory as input
- Output a structured profile for each mechanism
- Map profile patterns to epistemic classes (established/preliminary/contested/ungrounded)
- Include typed dataclasses throughout

**Artifacts:**
- `scripts/retrieval_profile.py`

**Closed:** —
