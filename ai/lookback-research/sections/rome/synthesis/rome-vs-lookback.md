# ROME vs Lookback — Two Mechanisms, One System

_Scholar ticket: S-007_
_Status: speculative synthesis — not yet experimentally confirmed_

---

## The Surface Similarity

Both papers:
- Are from David Bau's group
- Use causal tracing / causal mediation as their method
- Study how factual information is stored and retrieved in transformers
- Find localized, inspectable mechanisms

This makes them look like they're studying the same thing. They're not.

---

## The Fundamental Difference: What Kind of Knowledge?

**ROME studies world knowledge — permanent, from training:**

```
"The Space Needle is located in Seattle"
"Marie Curie was born in Warsaw"
"The Eiffel Tower is in Paris"
```

These facts are baked into the model's weights during pretraining on
billions of documents. They persist across every conversation. They
cannot be changed by the prompt — only by editing the weights.

**Lookback studies in-context beliefs — ephemeral, from the current prompt:**

```
"Bob fills the bottle with beer"
"Carla fills the cup with coffee"
"What does Bob believe the bottle contains?"
```

These "facts" exist only in the current prompt. The model has never
seen "Bob" and "Carla" before. There are no MLP weights storing who
Bob is. The model must construct the answer entirely from the current
context, using the OID mechanism discovered by the paper.

---

## The Two Storage Mechanisms

### ROME: Facts in MLP Weights

```
Location:   MLP weight matrices (Wproj) at middle layers
When:       Computed during training, fixed afterwards
Where:      Last token of the subject ("le" in "Space Need|le|")
What:       k* = subject representation, v* = object/property encoding
Permanence: Lives in weights — survives across all conversations
Retrieval:  Attention at late layers copies MLP output to final token
Edit via:   ROME rank-one weight update
```

The MLP is like **long-term memory** — written once during training,
read many times, requires surgical intervention to change.

### Lookback: Beliefs in Residual Stream OIDs

```
Location:   Residual stream of state tokens (e.g. "beer")
When:       Computed on-the-fly as the prompt is processed
Where:      OIDs co-located in state token across layers 14-34
What:       char_OI + obj_OI → composite index → payload (state value)
Permanence: Lives in activations — dies when the conversation ends
Retrieval:  Attention heads dereference OID pointer to find payload
Edit via:   Activation patching during inference (not yet implemented)
```

The residual stream is like **working memory** — constructed fresh for
each conversation, discarded afterwards, readable and patchable in real time.

---

## Where They Overlap: Attention as Delivery Mechanism

Both mechanisms use attention for the final delivery step:

**ROME's attention:**
```
Mid-layer MLP encodes "Space Needle → Seattle"
        ↓
High-layer attention copies this to the final token
        ↓
Final token predicts "Seattle"
```

**Lookback's attention:**
```
State token's residual stream holds [char_OI=1, obj_OI=1, value=beer]
        ↓
Answer lookback attention head dereferences OID pointer
        ↓
Payload "beer" copied to final token
        ↓
Final token predicts "beer"
```

In both cases: attention is the last mile. The storage is different;
the delivery mechanism is the same type (attention).

---

## The Three-Layer Picture

Putting it all together, a transformer answering a factual question
is running THREE parallel knowledge systems simultaneously:

```
Layer 1: World knowledge (ROME)
  Lives in: MLP weights at middle layers
  Source:   Pretraining corpus (billions of documents)
  Scope:    Universal — same across all prompts
  Examples: "Space Needle → Seattle", "Marie Curie → Warsaw"

Layer 2: In-context beliefs (Lookback)
  Lives in: Residual stream OIDs, state token activations
  Source:   Current prompt
  Scope:    Local — specific to this conversation
  Examples: "Bob → beer", "Carla → coffee" (from the story)

Layer 3: Instruction following (RLHF)
  Lives in: Fine-tuned behavior, not yet mechanistically mapped
  Source:   Human feedback training
  Scope:    Meta-level — how to use layers 1 and 2
  Examples: "when context contradicts weights, correct the user"
            "when asked to answer unknown, say unknown"
```

The final answer is a function of all three. This is the two-input system
from S-001, now decomposed into its components.

---

## The Conflict Scenario — Revisited

When world knowledge (Layer 1) conflicts with in-context beliefs (Layer 2):

```
Prompt: "Bob fills the bottle with wine. What does Bob believe the bottle
         contains?"

Layer 1 (world knowledge): bottles often contain beer, water, juice...
                           no strong prior for "wine" in this context
Layer 2 (in-context OID):  char_OI=1, obj_OI=1 → payload="wine"

Result: Layer 2 wins — the model says "wine" ✓
```

This works correctly because the synthetic story has no interference
from Layer 1 (the model has no prior beliefs about "Bob").

**The dangerous case:**

```
Prompt: "Bob fills the Mona Lisa with water. What does Bob believe
         the Mona Lisa contains?"

Layer 1 (world knowledge): "Mona Lisa is a painting" (strong belief)
Layer 2 (in-context OID):  char_OI=1, obj_OI=1 → payload="water"

Result: Layer 1 may interfere — the model might hedge, correct, or
        follow the context incorrectly because the world knowledge
        is fighting the in-context OID lookup
```

The Lookback paper used synthetic entities specifically to avoid this
conflict. Their stories don't touch entities with strong world knowledge.

---

## The Critical Experiment That Hasn't Been Done

**Question:** If you use ROME to edit Layer 1 (change "Space Needle → Tokyo"
in the MLP weights), does Layer 2 (in-context belief tracking) still work?

Specifically: if you give a story where the Space Needle is mentioned
and ask what a character believes, does the edited world knowledge
interfere with the in-context OID lookup?

This experiment would directly test whether the two mechanisms are
independent or whether Layer 1 can corrupt Layer 2.

**Prediction:** They are largely independent because:
- Layer 2 (Lookback) operates on OIDs derived from the current context
- OIDs are ordinal (first/second), not semantic
- The MLP weights that store "Space Needle → Tokyo" are for semantic retrieval
- The OID mechanism is positional, not semantic — it doesn't care what the entity is

But this is unverified. It's a paper waiting to happen.

---

## Implications for the L0 Decoder

The L0 decoder now has two distinct things to read:

```
L0-weights:  read MLP activations at middle layers, last subject token
             → what does the model's permanent memory say about this subject?
             → ROME can edit this

L0-context:  read OID residual stream at state tokens, binding layers
             → what does the model's working memory say about this prompt?
             → activation patching can edit this (not yet implemented)
```

And the critical new question:

```
L0-conflict: are L0-weights and L0-context in agreement?
             → if yes: answer is reliable (both sources agree)
             → if no: contested — model is navigating a contradiction
                      this is where hallucination and deception live
```

The RetrievalProfile already captures some of this via `residual_competition`.
The full picture requires reading BOTH storage systems and comparing.

---

## Summary Table

| Dimension | ROME | Lookback |
|---|---|---|
| Knowledge type | World facts from training | In-context beliefs from prompt |
| Storage location | MLP weight matrices | Residual stream activations |
| Storage duration | Permanent (survives all conversations) | Ephemeral (dies with conversation) |
| Key mechanism | k* = subject representation | char_OI + obj_OI = composite index |
| Value mechanism | v* = object/property encoding | payload = state token value |
| Retrieval | Attention copies MLP output to final token | Attention dereferences OID pointer |
| Editable via | Rank-one weight update (ROME) | Activation patching (open problem) |
| Layers involved | Middle MLPs (~layer 17 in GPT-2 XL) | Binding L14-34, Answer L33-79 |
| Entity type | Real-world entities with training data | Synthetic entities, no prior |
| Failure mode | Adversarial weight editing | Context-weight conflict |
