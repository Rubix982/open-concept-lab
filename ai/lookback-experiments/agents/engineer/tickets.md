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

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-07-04
**Updated:** 2026-07-04

**Blockers:**
- E-002 (need to know which heads are doing the lookback before intervening)

**Description:**
Implement the paper's core causal metric: Indirect Intervention Accuracy (IIA).
Run two story versions (original and counterfactual), patch the residual stream
from the counterfactual into the original at layer L and position P, measure
whether the output flips. Sweep across layers to produce an IIA curve.

**Implementation steps:**
1. Define story pairs: original (Sally-marble-basket) and counterfactual
   (swap the character or the destination)
2. Run both through the model, cache residual streams
3. For each layer L: patch `cache["resid_post", L]` at the state token
   from counterfactual into original forward pass
4. Measure whether the output probability of the counterfactual answer increases
5. Plot IIA by layer

**Artifacts:**
- `experiments/iia_curve/iia.py`
- `experiments/iia_curve/output/iia_by_layer.png`

**Closed:** —
