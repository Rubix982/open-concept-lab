# Paper Figures — Reference Notes

For each figure in the paper: what it shows, what experiment produced it,
and where our corresponding artifact lives.

Figures 1–9 are the main paper. Figures 10–24 are key appendix figures.
Figures 25–50 are cross-model replication (405B, Qwen) — same story, different scale.

---

## Figure 1 — The Lookback Mechanism (generic)

**Paper caption:**
> The source token contains reference information that is copied into two instances,
> creating a pointer and an address. Next to the address in the residual stream is a
> payload. When necessary, the model retrieves the payload by dereferencing the
> pointer. Solid lines = information flow. Dotted line = attention looking back.

**What it is:** A schematic of the abstract lookback pattern — not specific to any
experiment. It shows the three-role structure: Source → (Address, Pointer), Payload.

**How it was produced:** Illustration (hand-drawn in a design tool). No experiment data.

**What we built:**
- `sections/00-abstract/diagram.md` → Mermaid recreation of this figure
- `sections/00-abstract/demo.py` → code demonstrating the pointer/address/payload logic
- `sections/deep-dives/payload-demo.py` → full walkthrough of each phase

**Key thing to understand:** The dotted line (attention looking back) is the QK-circuit.
The solid lines are OV-circuits writing information into residual streams. Two
separate mechanisms, one for routing (QK) and one for copying (OV).

---

## Figure 2 — Causal Mediation Analysis Heatmap

**Paper caption:**
> Tracing information flow of crucial input tokens using causal mediation analysis.

**What it is:** A 3-panel heatmap. Each panel is one entity type (Character, Object,
State). X-axis = token position in the prompt. Y-axis = layer. Color intensity =
causal effect score from patching that (token, layer) activation.

**How it was produced:**
- Used `scripts/tracing_scripts/trace.py`
- For each entity type, ran causal mediation (interchange intervention) across all
  (token, layer) pairs
- Aggregated IIA scores across 80 samples
- Results saved in `results/causal_mediation_analysis/character.json` etc.

**What we built:**
- `sections/01-causal-mediation/output/causal_mediation_heatmap.png` ← direct replication
- `sections/01-causal-mediation/output/causal_effect_by_layer.png` ← layer profiles
- `belief_tracking/explore_results.py` ← script that produced both

**Key numbers from our replication:**
```
Character OI peak: token=173, layers 14–20, IIA=0.94
Object OI peak:    token=176, layers 27–34, IIA=1.00
State OI peak:     token=155, layers 0–55,  IIA=1.00
```

**What the vertical stripes mean:** OID information is localized to specific token
positions. The stripes being narrow (not diffuse) is the paper's main claim.

---

## Figure 3 — Binding + Answer Lookback (no visibility)

**Paper caption:**
> Belief Tracking with no visibility between characters. The LM assigns ordering IDs
> (OIs) to each character, object, and state token that encode their order of
> appearance. (i) Binding lookback: Address copies of character and object OIs are
> placed alongside the state OI payload in the residual stream of state tokens while
> pointer copies are moved to the final token residual stream. (ii) Answer lookback:
> An address copy of the state OI is alongside the state token payload in the residual
> stream of state tokens while a pointer copy is moved to the final token residual
> stream via binding lookback.

**What it is:** The most detailed diagram in the paper. A grid where columns = token
positions (the full story prompt), rows = layers. Colored arrows show:
- Character OI flowing from "Bob" into the state token (binding)
- Object OI flowing from "bottle" into the state token (binding)
- State OI flowing from the state token to the answer token (answer pointer)
- The final answer ("coffee") arriving at the answer token

**How it was produced:**
- Causal mediation experiments (same as Fig 2) but visualised as flow arrows
- Specific token positions identified from the prompt tokenisation
- Arrows drawn between peak-IIA (token, layer) coordinates
- Final visualisation done in Figma/Illustrator over the heatmap data

**What we built:**
- `sections/02-binding-lookback/output/binding_lookback_pipeline.png` ← active windows
- `sections/02-binding-lookback/output/binding_lookback_iia_overview.png` ← all 8 experiments
- `sections/02-binding-lookback/notes.md` ← full breakdown of each experiment

**Key layer numbers this figure implies:**
```
Character OI arrow: layers ~14–19
Object OI arrow:    layers ~17–34
State OI (pointer): layers ~33–55
```
These match exactly what our IIA results show.

---

## Figure 4 — Answer Lookback Pointer and Payload

**Paper caption:**
> The causal model predicts that altering the Answer Payload of the original to take
> the value of the counterfactual answer payload should change output from coffee to
> tea; this occurs when patching residual vectors at the ":" token beyond layer 56.
> The Answer Pointer would change output from coffee to beer — patching layers 34–52.
> These results suggest the Answer Lookback occurs between layers 52 and 56.

**What it is:** Two line plots. One for the pointer experiment (IIA by layer, peaks
at L34–52), one for the payload experiment (IIA by layer, rises at L56+).

**How it was produced:**
- `notebooks/causalToM_novis/answer_lookback.ipynb`
- Pointer: patches the final ":" token activation at each layer
- Payload: patches using a different counterfactual (unknown → known story)
- Results saved in `results/causalToM_novis/Meta-Llama-3-70B-Instruct/answer_lookback/`

**What we built:**
- `sections/03-answer-lookback/output/answer_lookback_handoff.png` ← pointer vs payload
- `sections/03-answer-lookback/output/full_chain_binding_to_payload.png` ← full chain
- `sections/03-answer-lookback/notes.md` ← handoff analysis

**Our numbers vs paper:**
```
Paper says pointer peaks:  layers 34–52
Our data shows pointer:    layers 33–55  (IIA > 0.5)  ✓ close match

Paper says payload rises:  beyond layer 56
Our data shows payload:    layers 56–79               ✓ exact match
```

**The "surprising" result the paper highlights:** patching the pointer produces
"beer" rather than "coffee" or "unknown" — a third answer that matches neither
the clean nor the counterfactual story. This is because the pointer redirects
attention to a DIFFERENT state token, retrieving a value from the wrong binding.
It proves the pointer is functioning as a literal memory address, not a semantic cue.

---

## Figure 5 — Binding Lookback Address and Payload

**Paper caption:**
> Swapping addresses (character and object OIs) and payloads (state OIs) should cause
> the binding lookback mechanism to attend to the alternate state token and retrieve
> its state OI. The LM's behavior matches this prediction when we perform interchange
> interventions on the state token across layers 33–38.

**What it is:** Line plot of IIA by layer for the address+payload experiment.
Peak at layer 34.

**How it was produced:**
- `notebooks/causalToM_novis/binding_lookback.ipynb` — "Address and Payload" cell
- Patches state tokens (positions 155, 156, 167, 168) from counterfactual into clean
- Results in `results/.../binding_lookback/address_and_payload/`

**What we built:**
- `sections/02-binding-lookback/output/binding_lookback_iia_overview.png`
  — bottom-left panel: "Binding (state token)"
- `sections/02-binding-lookback/notes.md` → Experiment 1

**Our numbers vs paper:**
```
Paper:    layers 33–38
Our data: layers 32–38 (IIA > 0.5)  ✓ match
Peak:     layer 34, IIA = 0.97      ✓ match
```

---

## Figure 6 — Source Reference Information of Binding Lookback

**Paper caption:**
> Swapping the source reference information (character and object OIs), while freezing
> addresses and payloads of the binding lookback, should cause the binding lookback to
> attend to the alternate state token. The LM's behavior matches this prediction when
> we perform interchange interventions at character and object tokens across layers 20–34.

**What it is:** Line plot of IIA by layer for the source experiment (with frozen state).
Peak window layers 20–34.

**How it was produced:**
- `notebooks/causalToM_novis/binding_lookback.ipynb` — "Source (frozen state)" cell
- Also includes source_2 (without frozen state) as the control line
- Results in `results/.../binding_lookback/source_1/` and `source_2/`

**What we built:**
- `sections/02-binding-lookback/output/binding_lookback_source_comparison.png`
  ← source_1 vs source_2 gap chart
- `sections/02-binding-lookback/notes.md` → Experiments 7 and 8

**Our numbers vs paper:**
```
Paper:    layers 20–34
Our data: source_1 active layers 16–38 (IIA > 0.5)  ✓ overlaps
```

---

## Figure 7 — Visibility Lookback Diagram (schematic)

**Paper caption:**
> When one (observing) character can see another (observed) character, the LM assigns
> a visibility ID to the visibility sentence where this relation is defined. An address
> copy remains in the visibility sentence's residual stream. A pointer copy is
> transferred to subsequent tokens. The LM dereferences this pointer through a
> QK-circuit, bringing forward the payload (the observed character's OI).

**What it is:** A diagram analogous to Figure 3 but for the visibility case. Shows the
Visibility ID being generated, split into address/pointer, then used to retrieve the
observed character's OI and update the observer's beliefs.

**How it was produced:** Illustration. No experiment data — this is the hypothesis
diagram. Figure 8 provides the empirical evidence.

**What we built:**
- `sections/05-visibility-lookback/diagram.md` ← full pipeline Mermaid diagrams
- `sections/deep-dives/visibility-lookback-demo.py` ← directed vis_ID demo
- `glossary.md` → Visibility ID, Visibility Lookback entries

---

## Figure 8 — Visibility Lookback Empirical Results

**Paper caption:**
> Three interchange intervention experiments: (1) Source alignment: causal effects
> between layers 10–23. (2) Payload alignment: alignment only after layer 31.
> (3) Address and Pointer alignment: alignment across layers 10–55, because patching
> both address and pointer enables the QK-circuit to form.

**What it is:** Three IIA line plots on one axis (source/payload/address+pointer).
The gap between source (drops at L23) and payload (rises at L31) is the key region
where the lookup is happening internally.

**How it was produced:**
- `notebooks/causalToM_vis/explicit_visibility_exps.ipynb`
- Results in `results/causalToM_vis/Meta-Llama-3-70B-Instruct/visibility_lookback/`

**What we built:**
- `sections/05-visibility-lookback/output/visibility_lookback_phases.png` ← all three lines
- `sections/05-visibility-lookback/notes.md` → three experiments fully broken down

**Our numbers vs paper:**
```
Paper:    source layers 10–23
Our data: source active L10–24     ✓ match

Paper:    payload after layer 31
Our data: payload active L31–53    ✓ exact match

Paper:    address+pointer broad window
Our data: addr+ptr active L10–53   ✓ match
```

---

## Figure 9 — Causal Mediation Analysis (appendix, single example)

**Paper caption:**
> The original example produces "unknown" because the queried character is not
> mentioned in the story. The counterfactual example includes the queried character
> in the story. Patching activations from the counterfactual changes the output.

**What it is:** A single worked example of the causal mediation procedure — shows the
specific story pair used, the intervention, and the output change. Pedagogical figure.

**How it was produced:** Illustrative output from a single tracing run.

**What we built:**
- `sections/01-causal-mediation/` ← the heatmaps from Figure 2 are the aggregated version
- `belief_tracking/explore_dataset.py` → shows exact structure of these story pairs

---

## Figures 10–12 — Per-entity Causal Mediation Heatmaps (appendix)

**What they are:** Separate full heatmaps for character (Fig 10), object (Fig 11), and
state (Fig 12) — the individual panels of Figure 2 shown at larger scale.

**Our equivalent:**
- `sections/01-causal-mediation/output/causal_mediation_heatmap.png`
  ← our three-panel version is the direct equivalent

---

## Figure 13 — Source without Frozen State (control condition)

**Paper caption:**
> Freezing the residual stream of the state token is necessary for source alignment
> to emerge.

**What it is:** The source_2 experiment — same as Figure 6 but WITHOUT freezing state
tokens. IIA stays flat (≤ 0.16). This is the control that proves the state token is
the binding destination.

**Our equivalent:**
- `sections/02-binding-lookback/output/binding_lookback_source_comparison.png`
  ← the red dashed line (source_2) is this figure's data

---

## Figures 14–15 — Character OI and Object OI (appendix)

**What they are:** Separate IIA plots for character_oi and object_oi experiments —
showing when each OID is causal at its source token.

**Our equivalent:**
- `sections/02-binding-lookback/output/binding_lookback_iia_overview.png`
  — top-left panel: Source OIDs (both lines visible)

---

## Figures 16–17 — Query Character OI and Query Object OI (appendix)

**What they are:** Pointer experiments — patching the character/object tokens in the
QUESTION (not the story). Show that pointers are live in the question tokens.

**Our equivalent:**
- `sections/02-binding-lookback/output/binding_lookback_iia_overview.png`
  — top-right panel: Pointers (question tokens)

---

## Figure 18 — Attention Knockout (appendix)

**Paper caption:**
> At the second visibility sentence, attention heads are restricted to retrieve
> information from earlier story sentences. Knocking out any of the previous
> sentences affects the model's performance at layers 20+.

**What it is:** Three accuracy-drop curves showing what happens when specific attention
paths are blocked — the visibility sentence being prevented from attending back to
the story sentences and the first visibility sentence.

**How it was produced:**
- `notebooks/attn_knockout/attn_knockout_exp.ipynb`
- Results in `results/attn_knockout/`

**What we built:**
- `sections/04-attention-knockout/output/attn_knockout_drop_by_layer.png`
- `sections/04-attention-knockout/output/attn_knockout_redundancy.png`
- `sections/04-attention-knockout/notes.md` → three experiments and redundancy finding

---

## Figures 19–20 — Causal Subspace Alignment (appendix)

**What they are:** Alignment between the causal subspace identified by IIA experiments
and the actual attention head weight matrices (W_Q, W_K, W_V). This is the bridge
from "this layer is important" to "this specific attention head implements the mechanism."

**Note:** These require the SVD singular vectors (which must be requested from the
authors per the README). We do not have the data to reproduce these.

**What they prove:** The low-rank subspace identified causally aligns with the
mathematical structure of specific attention heads — confirming the lookback is
implemented by identifiable, inspectable components.

---

## Figures 21–24 — BigToM Generalization (appendix)

**What they are:** Replication of the main findings on the BigToM dataset (Gandhi
et al., 2024) — a real-world ToM benchmark rather than the synthetic CausalToM.

**What they prove:** The lookback mechanism generalizes beyond the controlled
synthetic setting. The same layer ranges and mechanisms appear on real text.

**Data location:** `results/bigToM/Meta-Llama-3-70B-Instruct/`

---

## Figures 25–42 — Cross-model Replication (appendix)

**What they are:** All main experiments repeated on Llama-3.1-405B-Instruct and
Qwen2.5-14B-Instruct. Same mechanisms, slightly different layer ranges due to
model depth differences.

**Key finding:** The lookback mechanism is not model-specific. It appears across
model families and scales, suggesting it is a general solution learned by gradient
descent rather than an artifact of one architecture.

**Data location:**
- `results/causalToM_novis/Meta-Llama-3.1-405B-Instruct-8bit/`
- `results/causalToM_novis/Qwen2.5-14B-Instruct/`

---

## Quick Reference: Figure → Our Artifact

| Figure | Topic | Our Artifact |
|--------|-------|------|
| 1 | Generic lookback schematic | `00-abstract/diagram.md` |
| 2 | Causal mediation heatmap | `01-causal-mediation/output/` |
| 3 | Binding + answer lookback diagram | `01-binding-lookback/output/binding_lookback_pipeline.png` |
| 4 | Answer lookback IIA | `02-answer-lookback/output/answer_lookback_handoff.png` |
| 5 | Binding address+payload IIA | `01-binding-lookback/output/` (address_and_payload curve) |
| 6 | Binding source IIA | `01-binding-lookback/output/binding_lookback_source_comparison.png` |
| 7 | Visibility lookback schematic | `04-visibility-lookback/diagram.md` |
| 8 | Visibility lookback IIA | `04-visibility-lookback/output/visibility_lookback_phases.png` |
| 9 | Single causal mediation example | `01-causal-mediation/` |
| 10–12 | Per-entity heatmaps | `01-causal-mediation/output/causal_mediation_heatmap.png` |
| 13 | Source without frozen state | `01-binding-lookback/output/binding_lookback_source_comparison.png` |
| 14–15 | Character/Object OI source | `01-binding-lookback/output/` (source OIDs panel) |
| 16–17 | Query char/obj OI pointer | `01-binding-lookback/output/` (pointers panel) |
| 18 | Attention knockout | `03-attention-knockout/output/` |
| 19–20 | Causal subspace alignment | not reproduced (requires SVD vectors from authors) |
| 21–24 | BigToM generalization | data in `results/bigToM/` — not yet analyzed |
| 25–42 | Cross-model replication | data in `results/causalToM_novis/[405B/Qwen]/` |
