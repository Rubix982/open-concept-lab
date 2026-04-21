# Research Insights: Belief Revision, Uncertainty, and the Mushy Feeling

_Emerged from: analyzing BigToM vulnerability windows vs CausalToM_
_Date: 2026-04-22_
_Status: speculative — not yet tested experimentally_

---

## The Observation That Started This

When comparing BigToM and CausalToM IIA curves, the BigToM visibility
lookback shows sharp drops and re-rises — vulnerability windows where
the mechanism briefly loses the thread and reacquires it. CausalToM is
smoother.

The question was: is this good or bad?

The answer led somewhere more interesting than the original question.

---

## 1. Belief Replacement vs Belief Accumulation

**What the model currently does during a vulnerability window:**

```
Layer 10: First context load fires (weak — tentative vis_ID)
Layer 17: Load gets diluted by competing signals
Layers 17-22: IIA gap — mechanism inactive, no causal signal
Layer 26: Second load fires independently — stronger
Output: Second load answer, no memory of the first
```

The first load is **replaced**, not **updated**. The model does not use
the weak first load as a query to search for confirming or contradicting
evidence. It drops it and waits for a stronger signal.

**What an accumulation-based mechanism would do:**

```
Layer 10: First load fires (weak — tentative vis_ID)
Layer 17: Load weakens — uncertainty signal generated
Layers 17-22: First load used as directed query:
              "search for evidence about THIS visibility relation"
Layer 26: New evidence found — COMBINES with first load
Output: Synthesis of first and second load — more robust than either
```

The distinction matters because the first load, even when wrong, carries
useful directional information. In human cognition, a wrong first answer
helps you search in the right neighborhood. The model currently discards
that neighborhood entirely.

---

## 2. The Mushy Feeling — Pre-Linguistic Uncertainty Signal

Human metacognition works like this:

```
Retrieval fires
    ↓
Mushy feeling  ← pre-verbal, continuous, bodily
    ↓           ← NOT a thought, NOT a score, NOT a proposition
"Are you sure?" ← first verbal thought, CAUSED by the feeling
    ↓
Guided second retrieval (anchored to first answer)
    ↓
Synthesis
```

The mushy feeling has properties no confidence score captures:

- **Pre-linguistic**: exists before any propositional thought forms
- **Continuous**: not binary — a spectrum of "wrongness"
- **Domain-sensitive**: same activation level feels different depending
  on familiarity with the subject
- **Action-guiding without content**: tells you THAT something is off,
  not WHAT is off
- **Spontaneous**: fires based on internal state, not on a schedule

A confidence score is: one number, attached to a token, computed on
schedule, domain-agnostic, never feeds back into the same forward pass.

The mushy feeling is the **cause** of the metacognitive check.
The confidence score is, at best, a **post-hoc measurement** of something
it cannot change.

---

## 3. The Intrinsic Signal Structure

What the model would need to approximate the mushy feeling is not a
scalar but a **vector of intrinsic process signals** — a structured
profile of how the retrieval unfolded:

```python
@dataclass
class RetrievalProfile:
    oid_coherence:       float  # how strongly OID encoded in its subspace
                                # weak = binding was tentative

    subspace_stability:  float  # did OID drift across layers or hold steady?
                                # high drift = model reconsidered mid-process

    attention_entropy:   float  # sharp focus on one token vs diffuse spread
                                # high entropy = couldn't commit to a source

    residual_competition: float # other signals competing in same subspace
                                # high = belief is being contested internally

    layer_of_first_load: int    # how early did mechanism first fire?
                                # very late = context was hard to process

    gap_width:           int    # layers mechanism was inactive (vulnerability)
                                # wide gap = model lost and reacquired thread

    load_count:          int    # how many times mechanism reloaded?
                                # > 1 = first load was insufficient
```

No single value here is the mushy feeling.
A specific **pattern** across these values is.

Low `oid_coherence` + high `subspace_stability` drift + wide `gap_width` +
`load_count` > 1 = the structural equivalent of "mushy."

---

## 4. The Missing Circuit

The mushy feeling turns uncertainty into **action**.
The model's vulnerability window turns uncertainty into **silence**.

What is architecturally absent:

```
1. MONITOR   — continuously reads intrinsic signals during forward pass
2. THRESHOLD — when pattern matches learned "mushy" boundary
3. TRIGGER   — flags output as uncertain AND initiates second pass
               using tentative first answer as search anchor
4. COMBINE   — merges first-pass activation (weak, directional)
               with second-pass activation (stronger, guided)
5. DECIDE    — outputs synthesis, not replacement
```

Step 3 does not exist in current architectures. The model cannot
use its own tentative output as a query for a self-directed second pass
within the same forward pass. There is no interior experience of
"something is off here."

---

## 5. Extended L0 Decoder

Original vision (from Research Knowledge Infrastructure):

```
L0 (read): given a node, what does it believe?
```

Extended vision (from this analysis):

```
L0 (read):     given a node, what does it believe?
L0 (profile):  with what kind of process did it arrive there?
               → RetrievalProfile for that belief
L0 (signal):   does the profile match a learned "mushy" pattern?
               → binary: re-inquire / accept
L0 (trigger):  if re-inquire: use tentative belief as directed query
               for a second retrieval pass
L0 (merge):    combine first and second pass activations
               → output synthesis, not replacement
```

The IIA curves — vulnerability windows, gap widths, layer of first load —
are the measurable shadows of what RetrievalProfile would track.

---

## 6. Why the Vulnerability Window is Evidence, Not Noise

The gap in BigToM layers 17-22 is not a measurement artifact.
It is showing precisely the layer range where the model chose
replacement over accumulation — and failed briefly because of it.

In CausalToM the gap is smoother because synthetic stories have
perfectly aligned structure — the OID writes are unambiguous and
the subspace is never significantly contested. The model never
needs to reconsider.

In BigToM the gap exists because real text is ambiguous. The model's
first load was genuinely uncertain. The gap is the model's equivalent
of falling silent instead of saying "hold on, let me think about that."

A human with the mushy feeling would not fall silent in that window.
They would use the uncertainty itself as fuel for a more directed search.

---

## 7. Questions for Authors (Natalie Shapira, David Bau)

When speaking with the authors, these are the most productive directions:

1. **The vulnerability window as a failure mode**
   Have you observed cases where the gap in BigToM correlates with
   incorrect answers? Is the gap width predictive of accuracy drop?

2. **Residual stream competition during the gap**
   What is the residual stream at the vis_ID subspace doing during
   layers 17-22? Is it being overwritten by specific competing heads,
   or is it just decaying?

3. **The first load as a query**
   Is there any evidence in the attention patterns during the gap
   that the weak first load is being used as a query? Or is it
   genuinely inactive?

4. **Cross-architecture comparison**
   Does the gap appear in Qwen2.5-14B and 405B at similar relative
   layer positions? Does model scale affect gap width?

5. **The accumulation question**
   Are there any attention heads that appear to be doing something
   like combining weak early activations with stronger later ones?
   Or is replacement the universal pattern?

6. **The RetrievalProfile concept**
   Has anyone attempted to build a structured uncertainty profile
   from internal activations rather than a single confidence score?
   Are there papers in this space you'd point to?

---

## Connection to Research Knowledge Infrastructure

The infrastructure's epistemic classification system has four states:
`established`, `preliminary`, `contested`, `ungrounded`.

The RetrievalProfile maps directly:
```
high coherence + no gap + early load  → established
low coherence + no gap + late load   → preliminary
high competition + wide gap          → contested
load_count=0 (mechanism never fired) → ungrounded
```

The L0 layer is no longer just a reader — it is the source of the
epistemic classification signal itself. The graph doesn't just store
what the model believes. It stores how confidently and through what
quality of process the model arrived there.
