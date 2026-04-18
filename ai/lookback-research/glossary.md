# Glossary

Running index of terms encountered across all sections.

---

## Theory of Mind (ToM)
The ability to attribute mental states — beliefs, desires, intentions — to others,
and to understand that those beliefs may differ from reality. In LLMs: can the model
track what a character *believes* as distinct from what is actually true?

## Causal Mediation Analysis
A method for finding which internal activations are the *mechanism* behind an output,
not just correlated with it. Done by patching one run's activation into another and
observing if the output changes. If it does, that activation is a causal mediator.

## CausalToM
The dataset constructed by this paper. Simple stories: two characters, each acting
on an object, possibly observing each other. Used to probe belief tracking inside LMs.

## Character-Object-State Triple
The binding tuple `(Character, Object, State)` that the model must track internally.
e.g., `(Bob, bottle, beer)`. The question then tests whether the model can retrieve
the correct state given a character and object, respecting belief vs. reality.

## Ordering ID (OI)
An internal tag assigned by the model encoding relative order: "first" or "second"
occurrence of a character, object, or state in the story. Used as a positional handle
for matching — not the token value itself, just a relational index.

## Co-location
Two pieces of information stored in the *same* vector slot. Here: the character OI
and object OI are both written into the residual stream of the state token. One vector
carries both facts simultaneously.

## Residual Stream
The accumulating hidden vector for each token as it passes through transformer layers.
Each attention head and MLP *adds* to this vector. It is the token's running working
memory across layers. High-dimensional (e.g., 4096D for Llama-3-70B).

## Low-rank Subspace
A small-dimensional subspace within the high-dimensional residual stream where specific
information (like OIs) is stored. "Low-rank" means the structure is compressible —
lives in ~10 dimensions even though the full vector is 4096D.

## Lookback Mechanism
The core mechanism of the paper. A piece of reference information (source) is copied
to two places: an *address* (next to a payload) and a *pointer* (at the token that
later needs to retrieve the payload). When needed, attention dereferences the pointer
to the address and pulls back the payload. Three variants: binding, answer, visibility.

## Binding Lookback
First lookback: uses OIs to retrieve *which* state token is the answer. Maps
(character OI, object OI) → state OI.

## Answer Lookback
Second lookback: uses the state OI from the binding lookback to retrieve the actual
state *token value* (e.g., "beer").

## Visibility Lookback
Third lookback: when visibility between characters is specified, the model generates
a Visibility ID encoding the relation between observer and observed character OIs,
then uses it to update the observer's beliefs.

## Visibility ID
A derived reference handle encoding the relationship between two character OIs:
"the observing character OI relative to the observed character OI." Used in the
visibility lookback to pull observed-character information into the observer's belief state.
