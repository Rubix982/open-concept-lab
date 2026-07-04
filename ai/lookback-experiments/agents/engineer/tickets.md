# Engineer Tickets

### E-001 · OID co-location linear probe

**Status:** open
**Type:** implement
**Priority:** high
**Created:** 2026-07-04
**Updated:** 2026-07-04

**Description:**
Build a probing experiment that extracts residual stream activations from GPT-2
at the state token position across all layers, then trains a linear probe
(logistic regression) to decode character identity and object identity from
those activations. Co-location is confirmed if both probes peak at the same
layer with above-chance accuracy.

**Implementation steps:**
1. Load GPT-2-small via TransformerLens `HookedTransformer.from_pretrained("gpt2")`
2. Format 3-4 belief stories from `data/stories/` with clear state token positions
3. Run `model.run_with_cache(tokens)` to get full residual stream cache
4. For each layer, extract `cache["resid_post", layer]` at the state token index
5. Train logistic regression to predict character identity (label per story)
6. Train logistic regression to predict object identity (label per story)
7. Plot both probe accuracy curves across layers (0–11 for GPT-2-small)
8. Save plot to `experiments/oid_colocation/output/probe_accuracy.png`

**Story format:**
Simple, unambiguous. Each story needs a clearly identifiable state token
(the word that represents the object's location at a given belief event).
Start with Sally-Anne structure from the bigtom data.

**Success criterion:**
Both character probe and object probe achieve >70% accuracy at the same
layer(s). This is co-location.

**Artifacts:**
- `experiments/oid_colocation/probe.py`
- `experiments/oid_colocation/output/probe_accuracy.png`
- `data/stories/belief_stories.json` (20 stories, 5 per class, decoupled labels)
- `agents/shared/findings.md` → E-001 finding

**Closed:** 2026-07-04

**Result summary:**
Object probe: peaks at 0.800 (layers 6–11), well above chance (0.25). ✓
Character probe: 0.05–0.15 through most layers, reaches 0.30 at layer 11 only.
Key insight: character identity is NOT at the state token — probe E-002 should target
character name token positions and attention from the answer token to those positions.

---

### E-004 · NNSight trace: read → zero → noise on belief stories

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-07-04
**Updated:** 2026-07-04

**Description:**
Build `experiments/nnsight_trace/trace.py` as a four-step progression through
NNSight's intervention API applied to our belief stories. Each step is a
self-contained block that builds intuition for the next. This is the foundation
for E-003 (IIA curve) and future ROME experiments.

**Steps:**
1. **Read** — load GPT-2 via NNSight, run a Sally story, save logits at the
   answer token. Print top-5 token predictions. Confirm the model favours the
   correct location.
2. **Zero** — ablate layer 6 (where object probe peaked at 80%). Save logits.
   Compare rank of correct-location token before vs. after ablation.
3. **Noise** — replace layer 6 activations with Gaussian noise at the state
   token position. Sweep σ ∈ {0.01, 0.1, 1.0} and print how the top prediction
   changes.
4. **Replace** — set layer 6 activation at state token to zero vector for *just
   that position*, leave all others intact. Compare logits to full ablation.

**Output:** `experiments/nnsight_trace/output/` — printed results + one summary
plot comparing logit of correct answer across conditions.

**Success criterion:** Step 2 (zero layer 6) measurably lowers the logit for
the correct location, confirming layer 6 is causally relevant for object belief.

**Artifacts:**
- `experiments/nnsight_trace/trace.py`
- `experiments/nnsight_trace/output/logit_comparison.png`

**Closed:** 2026-07-04

**Key findings:**
1. NNSight single-item trace activations are 2D `[seq_len, d_model]` — batch dim squeezed.
   In-place multi-dim indexed proxy assignment (`[:, 8, :] = 0`) fails — use clone/mask/assign.
2. Zeroing layer 6 fully raises logit('basket') from -150.6 → -99.7 (more likely, not less).
   Layer 6 is suppressing location tokens, not storing them.
3. Zeroing state-token position only: 'Anne' enters top-5 — the displaced character's
   name becomes more probable when state-position context is removed.
4. Noise σ < 0.1 is negligible; σ = 1.0 starts to shift distribution.

---

### E-002 · Binding lookback attention maps

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-07-04
**Updated:** 2026-07-04

**Blockers:** ~~E-001~~ (closed — see finding)

**Description:**
Extract attention patterns at the answer token and visualize which prior token
positions the model attends to. Updated scope from E-001 finding: character
identity is NOT encoded at the state token — so also probe residuals at the
CHARACTER NAME token positions (position 1 in each story, right after BOS).

**Implementation steps:**
1. For each story, find: (a) state token idx, (b) character name token idx (position 1)
2. Probe character identity at the character name token position — expect high accuracy
3. Extract `cache["pattern", layer, "attn"]` at the answer token position
4. Plot attention heatmap: query=answer token ("Where"), keys=all prior tokens
5. Highlight: character name position, state token position, second state token position
6. Check whether attention at the answer flows to character name AND state token together
   (binding lookback = attention to both, not just one)

**Artifacts:**
- `experiments/binding_lookback/attention_maps.py`
- `experiments/binding_lookback/output/`

**Closed:** —

---

### E-003 · IIA curve (causal intervention)

**Status:** in-progress
**Type:** implement
**Priority:** medium
**Created:** 2026-07-04
**Updated:** 2026-07-04

**Blockers:** ~~E-002~~ (unblocked — layer sweep does not need head-level knowledge)

**Description:**
Implement the paper's core causal metric: Indirect Intervention Accuracy (IIA).
Patch the clean residual stream at the state-token position from a clean story
into a corrupted story (swapped locations) at each layer L. IIA measures how
much the clean answer logit recovers. Sweep all 12 layers → plot the IIA curve.

**Story pairs (location swap):**
- Pair A: clean = "Sally…basket…", corrupted = "Sally…box…" (locations swapped)
- Pair B: clean = "John…box…", corrupted = "John…bag…"

**IIA formula (normalized, per pair, per layer):**
  IIA = (logit_patched(clean_answer) - logit_corrupted(clean_answer))
      / (logit_clean(clean_answer) - logit_corrupted(clean_answer))
Range: 0 = patch did nothing, 1 = fully restored clean answer.

**NNSight pattern (cross-prompt invoker + barrier):**
  1. Baseline runs: clean_logits, corrupted_logits (single traces)
  2. For each layer: cross-prompt trace — capture clean residual at state_idx,
     patch into corrupted run using clone→mask→assign pattern
  3. Average IIA across pairs

**Implementation notes from E-004:**
  - NNSight single-item activations are 2D [seq_len, d_model] — no batch dim
  - Position indexing: hs[state_idx, :] not hs[:, state_idx, :]
  - Patching formula: hs * (1-mask) + clean_act * mask

**Artifacts:**
- `experiments/iia_curve/iia.py`
- `experiments/iia_curve/output/iia_by_layer.png`

**Closed:** 2026-07-04

**Results:**
Peak IIA at layer 9 (mean 0.445 ±0.19), but with large variance across pairs and
negative IIA at layers 4-5 for Emma pair. Deltas between clean/corrupted are tiny
(0.26–1.48 logit units), meaning GPT-2 small does not robustly track belief state.
**Key finding**: GPT-2 small is likely the wrong model. The lookback mechanism was
studied on larger models trained on structured data. All three experiments
(probe, ablation, IIA) show low signal — this is an important negative result.
Next: understand why the signal is weak before choosing a better model.
