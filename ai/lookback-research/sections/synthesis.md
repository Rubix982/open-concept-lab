# Synthesis: Language Models Use Lookbacks to Track Beliefs

_Reading time: ~15 minutes_
_Paper: Prakash et al., ICLR 2026 — https://belief.baulab.info_
_This document: complete end-to-end summary of the paper with connections
to all experimental artifacts and implications for the Research Knowledge
Infrastructure vision._

---

## Table of Contents

1. [The Problem](#1-the-problem)
2. [The Method](#2-the-method)
3. [The Dataset](#3-the-dataset)
4. [The Five Mechanisms](#4-the-five-mechanisms)
5. [The Evidence](#5-the-evidence)
6. [Generalization](#6-generalization)
7. [Implications for the Research Knowledge Infrastructure](#7-implications)
8. [Open Questions](#8-open-questions)
9. [Artifact Index](#9-artifact-index)

---

## 1. The Problem

**Can language models track what a character *believes*, as distinct from what is
actually true?**

This is Theory of Mind (ToM) — the ability to hold a model of another agent's
mental state, even when it diverges from reality. The classic test is the
Sally-Anne task: Sally puts a marble in a basket and leaves. Anne moves it to
a box. A child with ToM says Sally will look in the basket — tracking Sally's
belief, not the ground truth.

For LLMs, the question sharpens: when the model answers "what does Bob believe
the bottle contains?" correctly, is it doing something systematic, or is it
exploiting statistical patterns in training text?

**Prior work gave behavioral answers.** It tested *whether* models succeed or
fail on ToM tasks. It did not ask *how* — what internal computation produces
the correct answer.

**This paper gives a mechanistic answer.** It identifies specific computations,
at specific layers, in specific attention heads, that collectively implement
belief tracking. It uses causal interventions to prove each component is
genuinely load-bearing, not decorative.

→ *Conceptual foundation: `sections/00-abstract/notes.md`*
→ *Paper figure: Fig. 1 (generic lookback schematic)*

---

## 2. The Method

The paper uses **causal mediation analysis** (also called interchange
intervention or activation patching):

```
1. Take two stories: clean (o) and counterfactual (c)
   that differ in one specific way (e.g., character order swapped)

2. Run both through the model, save all internal activations

3. For a specific (token T, layer L):
   replace the activation in the clean run with the one from the counterfactual run
   run the rest of the forward pass normally

4. Measure IIA (Interchange Intervention Accuracy):
   did the output flip to match the counterfactual's expected answer?

   IIA = 1.0 → this activation IS the causal mechanism
   IIA = 0.0 → this activation is not part of the mechanism
```

This is not correlation — it is intervention. Patching proves causality.
The result is a map of which (token, layer) pairs carry which information,
with the mechanism confirmed not just observed.

**The tracing experiment** (Figs 2, 9-12) runs this across all token
positions and all layers simultaneously to produce heatmaps showing
where each entity's OID is causal. The narrow vertical stripes in those
heatmaps — information localized to specific tokens — are the paper's
opening claim: OIDs are not diffuse, they are localized.

→ *Method: `sections/01-causal-mediation/`*
→ *Paper figures: Fig. 2, 9–12*
→ *Our heatmaps: `sections/01-causal-mediation/output/`*

---

## 3. The Dataset

**CausalToM** — a synthetic dataset designed for causal analysis.

```
Story structure:
  "<Char1> and <Char2> are working in a busy restaurant.
   To complete an order, <Char1> grabs an opaque <Obj1> and fills it with <State1>.
   Then <Char2> grabs another opaque <Obj2> and fills it with <State2>.
   [optional: visibility condition]"

Question: "What does <CharQ> believe the <ObjQ> contains?"
```

Four templates varying the visibility condition:
- Template 0: neither character observes the other (no visibility)
- Template 1: char1 can observe char2 (one-way visibility)
- Template 2: no explicit visibility statement
- Template 3: distractor characters in visibility line (tests robustness)

Each experiment uses **counterfactual pairs** — two stories that differ in
exactly one aspect, enabling clean causal attribution.

103 characters, 21 objects, 23 states → large combinatorial space,
prevents memorization of specific names.

→ *Dataset: `belief_tracking/explore_dataset.py`*
→ *Templates: `belief_tracking/data/story_templates.json`*

---

## 4. The Five Mechanisms

The paper discovers that belief tracking is implemented through a pipeline
of five sequential computational phases. Each phase has a specific active
layer window, confirmed by IIA experiments.

### Layer windows (Llama-3-70B, 80 layers)

```
Layers 0–13:   Nothing causal yet

Layers 10–24:  [1] VISIBILITY SOURCE
               The model reads the visibility sentence
               and generates a Visibility ID:
               vis_ID = f(observer_OI, observed_OI)
               A directed relation — not Bob's OID, not Carla's OID

Layers 14–34:  [2] BINDING LOOKBACK
               char_OI and obj_OI written into the state token's
               residual stream (co-located as composite index)
               Binding complete at layer 34 (IIA = 0.97)

Layers 14–55:  [3] VISIBILITY ADDRESS+POINTER
               vis_ID used as pointer to locate observed character's
               state token — kept live while payload transfers

Layers 31–55:  [4] VISIBILITY PAYLOAD
               Observed character's state value written into
               observer's belief representation

Layers 33–55:  [5a] ANSWER POINTER
               State OI (from binding lookback) used as query
               to look back at story state tokens
               Finds the correct state token

Layers 56–79:  [5b] ANSWER PAYLOAD
               State value flows into the final (answer) token
               Persists through layer 79 — the answer is locked in
```

### The pipeline visualised

```
L0───────────10──────────────────────34────────────55──────79
             |                        |             |        |
             ├──Vis Source (10-24)    |             |        |
             ├──Vis Addr+Ptr (10-55)──────────────→|        |
             |  Vis Payload (31-55)──────────────→ |        |
             |                                     |        |
             ├──Binding (14-34)──────────────────→ |        |
                                                   |        |
                                    Answer Ptr (33-55)      |
                                                   Answer Pay (56-79)
```

Three key handoff points:
- **Layer 14**: visibility source peaks, binding begins
- **Layer 34**: binding completes, answer pointer begins
- **Layer 55**: answer pointer consumed, answer payload takes over

→ *Complete timeline: `sections/05-visibility-lookback/output/complete_mechanism_timeline.png`*
→ *Paper figures: Fig. 3 (binding+answer diagram), Fig. 7 (visibility diagram)*

---

## 5. The Evidence

Each mechanism is confirmed by a specific IIA experiment. This section
connects every claim to the experiment that proves it.

### Binding Lookback — 8 experiments

| Experiment | What is patched | Peak IIA | Active Window | Paper figure |
|---|---|---|---|---|
| address_and_payload | State token at layer L | 0.97 | L32–38 | Fig. 5 |
| character_oi | Character token at layer L | 0.94 | L13–28 | Fig. 14 |
| object_oi | Object token at layer L | 1.00 | L16–38 | Fig. 15 |
| pointer_character | Question char token | 1.00 | L14–29 | Fig. 16 |
| pointer_object | Question obj token | 0.94 | L14–29 | Fig. 17 |
| source_1 | Char+obj tokens, state FROZEN | 0.93 | L16–38 | Fig. 6 |
| source_2 | Char+obj tokens, state FREE | 0.16 | none | Fig. 13 |

**The source_1 vs source_2 gap** (Fig. 6 vs Fig. 13) is the key proof:
swapping source OIDs only changes the output when the state token is
protected. This proves the state token IS the binding destination.

→ *`sections/02-binding-lookback/output/binding_lookback_source_comparison.png`*

### Answer Lookback — 2 experiments

| Experiment | What is patched | Peak IIA | Active Window | Paper figure |
|---|---|---|---|---|
| pointer | Final ":" token at layer L | 1.00 | L33–55 | Fig. 4 |
| payload | Final ":" token at layer L | 1.00 | L56–79 | Fig. 4 |

**The handoff** at layer ~55 is the key observation: pointer IIA drops to
zero precisely where payload IIA rises. The pointer (state OI) is consumed
by the attention operation that retrieves the payload (state value).

→ *`sections/03-answer-lookback/output/full_chain_binding_to_payload.png`*
→ *`sections/03-answer-lookback/output/mechanism_timeline.png`*

### Attention Knockout — 3 experiments

Tests which attention paths must exist for visibility reasoning to work.

| Experiment | What is blocked | Critical window | Effect |
|---|---|---|---|
| secondSent | Vis sentence → Story sentence 2 | L22–34 | drop = 0.98 |
| firstVisSent | Vis sentence → First vis sentence | L3–5, L22–34 | drop = 1.00 |
| Both together | Both paths simultaneously | L24–34 (delayed) | drop = 1.00 |

**The early effect at layers 1–5** for `firstVisSent` shows the visibility
condition is processed very early — before binding begins.

**The combined knockout delayed onset** (L24 vs L3/L22 for individual)
reveals partial redundancy: blocking one path forces the model to lean
on the other. Only when both are blocked simultaneously does the
mechanism fully fail at layer 24+.

→ *`sections/04-attention-knockout/output/attn_knockout_drop_by_layer.png`*
→ *Paper figure: Fig. 18*

### Visibility Lookback — 3 experiments

| Experiment | What is patched | Peak IIA | Active Window | Paper figure |
|---|---|---|---|---|
| source | Visibility sentence tokens | 0.97 | L10–24 | Fig. 8 (blue) |
| address_and_pointer | Recalled + lookback tokens | 1.00 | L10–55 | Fig. 8 (green) |
| payload | Lookback tokens (question+answer) | 1.00 | L31–55 | Fig. 8 (red) |

**The gap at layers 24–31** between source dropping and payload arriving
is where the model forms the QK-circuit — the dereference operation that
connects the visibility pointer to the observed character's state token.
The address+pointer experiment bridges this gap because it patches both
sides of the QK-circuit simultaneously.

→ *`sections/05-visibility-lookback/output/visibility_lookback_phases.png`*
→ *Paper figures: Fig. 7, 8*

---

## 6. Generalization

### BigToM: Real-world text (R-001)

BigToM (Gandhi et al., 2024) uses real ToM stories, not synthetic templates.

**What transfers cleanly:**
- Answer payload: L56–79 in CausalToM, L56–79 in BigToM — **identical**
- Answer pointer: L33–55 → L31–52 — same shape, 2-layer shift

**What differs:**
- Visibility source: CausalToM builds up from L10, BigToM is causal from
  **layer 0** — visibility information is present in token embeddings
  directly in real text, before any attention fires
- Visibility payload: never drops in BigToM (persists L26–79 vs L31–53)
  — in real text, visibility is more deeply integrated

**Interpretation:** The answer lookback is the most architecture-general
component. The visibility mechanism is general in what it computes but
shows that real text encodes visibility at the embedding level, while
synthetic text requires it to be constructed through mid-layer attention.

→ *`sections/07-bigtom/output/bigtom_timeline_comparison.png`*
→ *Paper figures: Fig. 21–24*

### Cross-model: three architectures (R-002)

| Model | Layers | Answer payload window | Source_2 control |
|---|---|---|---|
| Llama-3-70B | 80 | L56–79 (70–99%) | 0.16 ✓ |
| Llama-3.1-405B | 126 | L74–125 (59–99%) | 0.05 ✓ |
| Qwen2.5-14B | 48 | L42–47 (88–98%) | 0.01 ✓ |

**Four cross-model findings:**
1. Answer payload always occupies the final ~30–40% of model depth (IIA=1.00)
2. Binding mechanisms complete in the first ~50% of model depth
3. Source_2 control stays near zero universally — state token as binding
   destination is architecture-independent
4. Scaling is **proportional, not absolute** — mechanisms fire at the same
   fraction of total depth, not the same layer number

**Qwen's narrow windows** (answer pointer: 5 layers vs 22 in 70B) suggest
smaller models implement the same computation more compactly but with less
redundancy — higher brittleness under perturbation.

→ *`sections/08-cross-model/output/cross_model_timeline_proportional.png`*
→ *Paper figures: Fig. 25–42*

---

## 7. Implications

### For the Research Knowledge Infrastructure

The paper's central finding has a direct architectural implication for
the L0 layer of the knowledge infrastructure:

**Original L0 concept:** given a node, what does the model believe?

**What this paper adds:** the model's beliefs are not just values —
they are the outputs of a specific computational process. The same
answer ("coffee") can arrive through:
- Clean binding, no gap, early load → high confidence, established belief
- Wide gap, multiple reloads, contested subspace → tentative belief

A knowledge infrastructure that reads only the final output conflates these.
A system that reads the **process profile** — the RetrievalProfile described
in `sections/09-research-insights/` — can distinguish them.

**Extended L0:**
```
L0 (original):  given a node, what does it believe?
L0 (extended):  what does it believe,
                through what quality of process did it arrive there,
                and does that process match a pattern of uncertainty
                that should trigger re-inquiry?
```

**The epistemic classification system maps directly:**

| RetrievalProfile pattern | Infrastructure epistemic class |
|---|---|
| High coherence, no gap, early load | `established` |
| Low coherence, no gap, late load | `preliminary` |
| High competition, wide gap | `contested` |
| Mechanism never fired | `ungrounded` |

The IIA curves — vulnerability windows, gap widths, layer of first load —
are the measurable signatures of epistemic class, readable from internal
activations rather than inferred from output text.

### For mechanistic interpretability broadly

The paper demonstrates that a specific cognitive capability (ToM) is
implemented through a specific computational pattern (lookback mechanism)
that is:
- **Identifiable** — localizable to specific layers and attention heads
- **Universal** — appears across model families and scales
- **Systematic** — not statistical association but structured retrieval

This suggests similar mechanisms exist for other cognitive capabilities
that have not yet been reverse-engineered. The methodology — causal
mediation + IIA — is the flashlight. The space of undiscovered mechanisms
is large.

---

## 8. Open Questions

Questions the paper raises but does not fully answer:

**1. Vulnerability windows and accuracy**
Does gap width in BigToM correlate with incorrect answers? Is the gap
a predictor of failure, or does the model reliably recover?

**2. What happens in the gap**
During layers 17–22 (BigToM visibility gap), what is the residual stream
doing in the vis_ID subspace? Is it being actively overwritten by specific
competing heads, or passively decaying?

**3. The first load as a query**
Is there any evidence that the weak first load is being used as a query
during the gap? Or is it genuinely inactive? This determines whether the
model does replacement or accumulation.

**4. The missing metacognitive circuit**
No mechanism exists that detects low-confidence activations and triggers
a guided second retrieval. Could such a circuit be trained? Would RLHF
on uncertainty-flagged tasks produce it spontaneously?

**5. Higher-order ToM**
The paper tests first-order false beliefs (what does Bob believe?).
Does the lookback mechanism generalize to second-order beliefs (what
does Bob believe that Carla believes)? Do nested lookbacks emerge?

**6. Desires and intentions**
The paper is narrowly scoped to beliefs. Do analogous mechanisms exist
for desire tracking and intention tracking — the other components of
the belief-desire-intention model of agency?

**7. The RetrievalProfile decoder**
Can a structured uncertainty profile be extracted from internal
activations in real time during inference? Would it be predictive of
output quality? This is the key open question for the extended L0 layer.

---

## 9. Artifact Index

| What | Where |
|---|---|
| Conceptual foundations | `sections/00-abstract/` |
| Causal mediation heatmaps (Fig. 2) | `sections/01-causal-mediation/output/` |
| Binding lookback: all 8 experiments | `sections/02-binding-lookback/` |
| Answer lookback: handoff at L55 | `sections/03-answer-lookback/` |
| Attention knockout: path criticality | `sections/04-attention-knockout/` |
| Visibility lookback: 3 phases | `sections/05-visibility-lookback/` |
| Every paper figure mapped to artifact | `sections/06-paper-figures/notes.md` |
| BigToM generalization comparison | `sections/07-bigtom/` |
| Cross-model replication (3 models) | `sections/08-cross-model/` |
| Belief revision & uncertainty insights | `sections/09-research-insights/` |
| Complete mechanism timeline | `sections/05-visibility-lookback/output/complete_mechanism_timeline.png` |
| Full chain: binding → answer | `sections/03-answer-lookback/output/full_chain_binding_to_payload.png` |
| Cross-model proportional comparison | `sections/08-cross-model/output/cross_model_timeline_proportional.png` |
| Running glossary | `glossary.md` |
| Research findings log | `agents/shared/findings.md` |
