# Deep Dive: Residual Stream & Co-location

## The Residual Stream

Each token has ONE vector. Fixed length throughout all layers. Each layer adds to it.

```
x₀  = embedding("beer")          # initialized
x₁  = x₀ + attn₁(x₀) + mlp₁(x₀) # layer 1 writes to it
x₂  = x₁ + attn₂(x₁) + mlp₂(x₁) # layer 2 writes to it
...
x₈₀ = final residual stream       # same size, accumulated values
```

Nothing is replaced. Each layer adds a delta. The final vector is the sum of
all those deltas — the accumulated "working memory" of everything written to
this token across all layers.

---

## Superposition: Multiple Facts, One Vector

4096 dimensions is large. Different pieces of information can live in
different "directions" (subspaces) of the same vector without interfering —
as long as they're roughly orthogonal.

```
vector = char_OI_component + obj_OI_component + value_component + ...
         [~10 dims]           [~10 dims]         [~10 dims]
```

Like audio — bass, mids, treble coexist in one waveform, extractable
independently. The residual stream is the same idea.

---

## Why Co-location in the State Token Matters

### Without co-location

```
"Bob"    residual stream: [ char_OI=first, ... ]
"bottle" residual stream: [ obj_OI=first,  ... ]
"beer"   residual stream: [ value=beer,    ... ]
```

Question: "What does Bob believe the bottle contains?"

The model needs to:
1. Look at "Bob" → get char_OI=first
2. Look at "bottle" → get obj_OI=first
3. Somehow join these, then find the matching state token
→ Requires 2 separate attention operations + intermediate reasoning

### With co-location (what the paper finds)

```
"beer"   residual stream: [ char_OI=first, obj_OI=first, value=beer, ... ]
                             ^both written here, in the same vector^
```

Question: "What does Bob believe the bottle contains?"

The model can:
1. Form a query: char_OI=first AND obj_OI=first
2. One attention operation finds "beer" directly
→ Single-step joint lookup

The state token acts as a **composite index** — like a database index on
(character, object) that points to the state value.

---

## The Subspace Picture

```
Full 4096-dim residual stream of "beer":

 dim 0    dim 1    ...  dim 47   dim 48   ...  dim 103  dim 104  ...  dim 4095
[  0.2     -0.8    ...   1.3      0.7     ...   -0.4      0.1    ...   0.0   ]
 |________________________|       |___________________|
      char_OI subspace                obj_OI subspace
      (~10-20 dims)                   (~10-20 dims)
      "I belong to the                "I belong to the
       first character"                first object"
```

The rest of the 4096 dims carry other information (semantic content of "beer",
positional info, etc.). The OI subspaces are a small fraction, found by PCA/SVD
over many examples.
