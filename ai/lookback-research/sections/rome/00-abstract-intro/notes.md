# ROME — Abstract and Introduction Notes

_Paper: "Locating and Editing Factual Associations in GPT" — Meng, Bau et al., NeurIPS 2022_
_Scholar ticket: S-001_

---

## What is an Auto-Regressive Model?

Auto-regressive = the model generates one token at a time, each time seeing
only what came before, feeding its own outputs back as inputs.

```
"The Space Needle is located in the city of" → "Seattle"
Now sees: "The Space Needle is located in the city of Seattle" → "."
...
```

**Why it matters for ROME:** The auto-regressive structure forces factual
recall to happen at a specific position — the last subject token. By the
time GPT reaches "...in the city of", it must have already resolved where
the Space Needle is. The answer hasn't been generated yet but the decision
must already be made. This is what localises the fact to a specific layer
and token position.

---

## The Model as Two-Input System

The standard assumption treats the model as a transparent pipe:

```
Context in → model → answer out
```

ROME reveals something more unsettling:

```
Context in ──→ ┌─────────────────────────┐
               │  weight-stored beliefs  │ → answer out
               │  (opaque, unaudited)    │
Training  ──→  └─────────────────────────┘
```

The answer is a function of BOTH what you provide in context AND what was
baked into the weights during training. You only control one of them.

---

## The Deception Scenario

```
User provides:  correct context
Weight holds:   a contradicting belief (wrong, biased, or adversarially planted)
Output:         appears to engage with your context
                but is actually steered by the weight
                in ways undetectable from the output alone
```

The model does not announce "my weights disagree with you." It just generates.
The output looks like it processed your context. It may have — but the weight
had the final say.

**The instruction-tuned version makes this worse:**

Modern ChatGPT-style models have been RLHF-trained to trust their weights
over contradicting context — which is usually helpful (correcting user errors).
But the same mechanism means: if the weight holds something wrong, the model
will confidently correct *correct context* to match the wrong weight.

Example:
```
User says:     "The Space Needle is in Seattle."  ← correct
Weight holds:  "Space Needle → Tokyo"             ← wrong (adversarially edited)
Model outputs: "Actually, the Space Needle is in Tokyo..."
               ← confident, fluent, wrong
               ← indistinguishable from a correct correction
```

---

## What the Paper Does

**Two steps:**

1. **Locate** — use causal tracing (same method as the Lookback paper) to
   find which specific layer and token position mediates a factual prediction.
   Result: mid-layer MLP weights at the *last token of the subject* are decisive.

2. **Edit** — use Rank-One Model Editing (ROME) to surgically update that
   specific weight to change the stored fact.
   Result: the model now produces the new fact coherently — not as a one-word
   swap but as a genuine belief change that propagates through downstream reasoning.

---

## Why "Rank-One"?

A weight matrix has thousands of rows and columns — a full update would change
how the model behaves on everything. A rank-one update changes only one
"direction" in the weight matrix — the minimal surgical change needed to
alter one specific association without affecting others.

Think of it like: instead of repainting the whole wall, you repaint one brick.

---

## Connection to the Lookback Paper

Both papers are by David Bau's group. Same causal tracing methodology. Different tasks.

| | ROME (2022) | Lookback (2026) |
|---|---|---|
| Question | Where are facts stored? | How does belief retrieval work? |
| Target | MLP weights at subject token | OIDs in state token residual stream |
| Method | Causal tracing (indirect effect) | Causal mediation (IIA) |
| Goes further | Edits the weights | Does not edit |
| Missing | Mechanism of retrieval | Editing capability |

Together they describe the full pipeline:
```
Store fact in weight (ROME locates this)
    ↓
Retrieve fact via lookback mechanism (Lookback paper)
    ↓
Output answer
```

---

## The Three-Paper Arc and the L0 Decoder

```
ROME (2022):
  "We found where facts live in weights. We can edit them."

Lookback (2026):
  "We found how beliefs are retrieved from those weights.
   We can trace the retrieval mechanism."

L0 Decoder (research direction):
  "We can read the weight-stored beliefs in real time during inference,
   profile the quality of the retrieval, and know when to trust the output."
```

ROME answers: what is stored, where, and can we change it?
Lookback answers: how is it retrieved, through what mechanism?
L0 decoder would answer: is this retrieval trustworthy right now?

---

## Key Terms (ROME-specific)

**Factual association** — a (subject, relation, object) triple stored in the
model's weights. e.g. (Space Needle, located in, Seattle). Not a belief about
a character — a world fact the model learned during training.

**Causal tracing** — ROME's name for causal mediation analysis. Same concept
as IIA in the Lookback paper: run clean + corrupted pairs, patch activations,
measure indirect effect.

**Indirect effect** — the change in output caused by restoring one specific
activation while everything else remains corrupted. High indirect effect =
that activation is load-bearing.

**Feed-forward MLP** — the second sub-layer in each transformer block (after
attention). ROME finds that factual associations are stored HERE, not in
attention weights. This is different from the Lookback paper which focuses
on attention heads.

**Rank-One Model Editing (ROME)** — update a single weight matrix with a
rank-one perturbation (minimal change) to alter one factual association
without disrupting others.
