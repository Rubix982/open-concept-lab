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
- `scripts/retrieval_profile_output/` (3 model PNGs)

**Closed:** 2026-04-22

---

### E-003 · Causal subspace analysis explainer script

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-04-25
**Updated:** 2026-04-25

**Description:**
Produce `scripts/causal_subspace_explainer.py` that walks through the full
algorithm in `belief_tracking/notebooks/causal_subspace_analysis/lookback.ipynb`.

The notebook does two things (pointer subspace, payload subspace) using the
same 4-step pipeline each time:
  1. Load singular vectors (SVD) per layer from `.pt` files
  2. Load the IIA mask (which singular vectors are causally active) from JSON
  3. Build the causal subspace = singular vectors filtered by mask
  4. Project Q or V projection weight onto each subspace direction, chunk by
     head, compute per-head norm → heatmap of (layers × heads)

Script must:
- Require no model weights and no NDIF key — synthesize toy tensors
- Explain what a singular vector is and what the mask means
- Walk through the projection math step by step with concrete numbers
- Explain why norm(q_proj @ sv per head) measures head-subspace alignment
- Produce a synthetic heatmap visualisation matching the notebook's output shape
- Use full type annotations throughout (Figure/Axes pattern from memory)

**Artifacts:**
- `scripts/causal_subspace_explainer.py`
- `scripts/causal_subspace_heatmap.png`

**Closed:** 2026-04-25

---

### E-005 · nethook + LogitLens explainer script

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-04-25
**Updated:** 2026-04-25

**Description:**
Produce `scripts/nethook_explainer.py` walking through `rome/util/nethook.py`
and `rome/util/logit_lens.py`.

nethook has four distinct pieces to explain:
  1. Trace — hooks one layer: read output, optionally edit it mid-forward-pass
  2. TraceDict — hooks multiple layers simultaneously
  3. StopForward — early-exits the forward pass after a target layer
  4. Supporting utils — get_module, replace_module, recursive_copy,
     invoke_with_optional_args

LogitLens builds directly on TraceDict: hooks every layer's output, then
runs the LM head on each to see what token the model would predict if it
stopped at that layer.

Script must:
  - Require no real model — use a tiny hand-built nn.Sequential
  - Show each Trace mode (read, edit, stop) with concrete printed output
  - Show TraceDict hooking multiple layers at once
  - Show the edit_output function pattern (this is how ROME injects edits)
  - Show LogitLens conceptually with a synthetic demonstration
  - Explain the connection to nnsight (used in attn_knockout): same idea,
    different API
  - Full type annotations throughout

**Artifacts:**
- `scripts/nethook_explainer.py`

**Closed:** 2026-04-25

---

### E-004 · Attention knockout explainer script

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-04-25
**Updated:** 2026-04-25

**Description:**
Produce `scripts/attn_knockout_explainer.py` walking through the full algorithm
in `belief_tracking/notebooks/attn_knockout/attn_knockout_exp.ipynb`.

The notebook has four conceptual pieces:
  1. Token range setup — which token positions map to which story sentences
  2. apply_causal_mask — layering a knockout mask on top of the standard
     causal mask by filling selected (from, to) attention edges with -inf
  3. The nnsight intervention loop — intercepting Q/K/V projections mid-forward
     pass, manually recomputing attention with the mask, then writing the result
     back into o_proj.input
  4. The layer sweep — starting the knockout from each layer_idx onward to
     find at which layer the attention edge becomes load-bearing

Three experiments vary what is blocked:
  Exp A: second_visibility_sent blocked from second_sent + first_visibility_sent
  Exp B: second_visibility_sent blocked from first_visibility_sent only
  Exp C: second_visibility_sent blocked from second_sent only

Script must:
  - Require no model or nnsight — synthesize toy attention tensors
  - Explain the causal mask vs knockout mask distinction clearly
  - Show the mask construction (from_indices, to_indices → bool tensor)
  - Walk through the full recompute-and-inject pipeline with concrete shapes
  - Show what the layer sweep result curve means and why it recovers
  - Produce a synthetic accuracy-vs-layer plot for all three experiments
  - Full type annotations throughout

**Artifacts:**
- `scripts/attn_knockout_explainer.py`
- `scripts/attn_knockout_layer_sweep.png`

**Closed:** 2026-04-25
