# Abstract — Key Concepts

## Theory of Mind (ToM)

The human ability to model other people's mental states — including beliefs that differ
from reality. Classic test: the Sally-Anne test. Sally puts a marble in a basket and
leaves. Anne moves it to a box. Where will Sally *look*? A child with ToM says "the
basket" — they can hold Sally's belief separate from reality.

For LLMs: can the model answer "what does Character A *believe*" even when that
differs from the ground truth state of the world? That is the core question.

---

## Causal Mediation Analysis

A method for finding *which internal activations* are the actual mechanism, not just
correlated with the output.

Procedure:
1. Run model on Story A → output O_A
2. Run model on Story B → output O_B
3. For a specific activation (layer L, token T), patch Story A's run with Story B's
   activation at that spot
4. If the output flips toward O_B, that activation is a *causal mediator*

This is the key move that separates "the model gets it right" from "here is *how*
the model gets it right internally."

---

## Character-Object-State Triple

The model internally represents binding tuples of the form:

    (Character, Object, State)
    e.g., (Bob, bottle, beer)
         (Carla, cup, coffee)

When asked "what does Bob believe the bottle contains?" the model must:
- Identify which character was asked about
- Find the triple where that character is bound to that object
- Retrieve the state from that triple

The hard case: when one character didn't observe the other, their beliefs may diverge
from reality.

---

## Co-location

If "locating" = jumping to index i, then "co-locating" = two pieces of information
stored *at the same index* — same vector, same slot.

Here: the Ordering ID of the character AND the Ordering ID of the object are both
written into the residual stream of the *state token* (e.g., "beer"). A single vector
carries: "I belong to the first character AND the first object." One place, two facts.

---

## Ordering IDs (OIs)

Internal tags the model assigns encoding relative order:
- "I am the first character" / "I am the second character"
- "I am the first object" / "I am the second object"
- "I am the first state" / "I am the second state"

Not the actual token value — just a positional handle. Used as keys for matching:
"which state belongs to the first character + first object?"

---

## Residual Stream

Each token has a hidden vector (e.g., 4096 dimensions). As it passes through
transformer layers, each attention head and MLP *adds* to this vector. The
accumulating sum is the residual stream — the token's running working memory.

Information from earlier tokens can be written into a later token's residual stream
via attention. The whole paper is about what information gets written where, when,
and how it gets read back out.

---

## Low-rank Subspace

The residual stream is high-dimensional (4096D), but specific information (like OIs)
doesn't use all of it. It lives in a small subspace — maybe 10 dimensions — findable
via PCA. "Low-rank" means the structure is simple and compressible. The OIs for
character and object are co-located in this small corner of the state token's vector.
