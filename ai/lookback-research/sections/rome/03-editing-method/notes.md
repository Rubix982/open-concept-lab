# ROME — The Editing Method

_Scholar ticket: S-003_
_Source: Section 3 of the paper, `rome/rome/rome_main.py`_

---

## The Core Insight: MLP as Linear Associative Memory

The key claim that makes ROME possible:

> **W_proj (the MLP's second layer) is a key-value store.**

Geva et al. (2021) showed MLP layers act like memories — neurons in the
first layer (W_fc) form keys, the second layer (W_proj) retrieves values.
ROME extends this: not per-neuron, but as a LINEAR ASSOCIATIVE MEMORY.

A linear associative memory stores key-value pairs in a weight matrix W:

```
If W K ≈ V   (where K = column matrix of keys, V = column matrix of values)
Then: W @ k_i ≈ v_i  for each key-value pair
```

This is solved by the Moore-Penrose pseudoinverse: `W = V K†`

The insight: **W_proj already IS this memory.** It learned during training
to map subject representations → object representations.

---

## Why Rank-One Specifically

### What rank-one means

A rank-one matrix is an outer product of two vectors:

```
outer_product(a, b) = a @ b.T   shape: (len(a), len(b))
                                 rank: 1
```

Rank-1 because only one "direction" is changed. Every row is a scalar
multiple of b. Every column is a scalar multiple of a.

### Why rank-one for editing

The constrained least-squares problem ROME solves:

```
minimize  ||Ŵ K - V||         # disturb existing memories as little as possible
subject to  Ŵ k* = v*         # new fact must be correctly stored
```

The closed-form solution to this is:

```
Ŵ = W + Λ(C⁻¹k*)ᵀ
```

This is provably the MINIMUM-NORM update that satisfies the constraint.
Any other update that satisfies `Ŵ k* = v*` would have a larger
||Ŵ - W|| (Frobenius norm).

**Rank-one is not a simplification — it's the optimal answer to the
constrained problem.** The math says: the smallest possible change to W
that installs the new fact is a rank-one update.

### Intuition

```
W has 10 million weights.
A full-rank update changes all 10M weights in arbitrary directions.
A rank-one update changes all 10M weights but only ALONG ONE DIRECTION.

You're moving the entire matrix, but only in a single direction in
the space of matrices. That's minimal — one degree of freedom.
```

---

## What Changes: Weights, Not Activations

This is the fundamental difference from the Lookback paper's interventions:

| | Lookback paper | ROME |
|---|---|---|
| Changes | Activations (residual stream) | Weights (W_proj matrix) |
| Duration | Ephemeral — one forward pass | Permanent — survives all conversations |
| Requires | NNsight hooks at inference time | One-time weight update offline |
| Reversible | Yes (no hooks = no change) | Only with explicit weight restoration |

Causal tracing in both papers patches activations — temporary, for
measurement only. ROME then takes the extra step: modify the actual
weights that produce those activations permanently.

The L0 decoder would operate on activations (read-only, real-time).
ROME operates on weights (write, offline). Together: locate via activations,
edit via weights.

---

## The Two Constraints

The edit must satisfy:

### Hard constraint: `Ŵ k* = v*`

After the edit, when the model processes the subject ("Steve Jobs"),
the MLP at layer 17 must output v* — the vector that encodes "Microsoft."

This is the correctness constraint. Non-negotiable.

### Soft constraint: `minimize ||Ŵ K - V||`

The edit must not disturb the existing key-value mappings for all
OTHER facts stored in the same W matrix.

```
K = all other keys (Bill Gates, Marie Curie, Eiffel Tower...)
V = their corresponding values

||Ŵ K - V|| measures total damage to existing memories
```

Minimizing this is what gives ROME specificity. The rank-one solution
achieves the minimum possible damage because it moves W in the most
"efficient" direction.

---

## The Three Steps in the Paper

### Step 1: Choose k* (the key)

```python
k* = average representation of subject s at layer l*,
     last subject token,
     AFTER the MLP's first non-linearity (σ(W_fc ...))
     averaged over 50 random prefix contexts
```

Why average over contexts? The same subject produces slightly different
representations depending on what precedes it. Averaging makes k* more
stable and robust to phrasing variations.

### Step 2: Choose v* (the value)

```python
v* = argmin_z [ -log P("Microsoft" | prompt, MLP_output=z)   # efficacy
              + KL(P("Steve Jobs is a..." | z) || P_original) # essence
              ]
```

v* is NOT computed analytically — it's found by optimization (20 steps).
The optimization doesn't change W; it finds what W's output SHOULD BE
if the edit is to work correctly.

The KL term is the essence preservation constraint: changing "Steve Jobs
founded → Microsoft" should not change "Steve Jobs is a person/CEO/entrepreneur."

### Step 3: Insert — apply the rank-one update

```python
Λ = (v* - W @ k*) / dot(k*, C⁻¹k*)
W_new = W + outer_product(Λ, C⁻¹k*)
```

One matrix operation. No backprop. No training. The new fact is installed.

---

## Failure Modes — What Figure 5 Shows

Figure 5 plots ROME's editing success when targeting different (layer, token)
combinations — not just the causal tracing winner.

**What the figure shows:**

```
Editing at the wrong TOKEN:
  First subject token ("Space") → poor generalization
  Other middle tokens           → poor specificity
  Last subject token ("Needle") → peak performance ✓

Editing at the wrong LAYER:
  Early layers (0-5)     → poor on both metrics
  Late layers (50+)      → poor generalization
  Middle layers (15-20)  → peak performance ✓
```

**Why this is important:**

Figure 5 is the paper's strongest evidence for the localized factual
association hypothesis. The edit works best EXACTLY at the location
causal tracing identified. If the hypothesis were wrong — if facts were
stored diffusely — editing one location wouldn't produce coherent results.

The fact that there's a sharp peak at layer 17, last subject token, that
matches the causal tracing peak is the bidirectional confirmation:

```
Causal tracing:  "layer 17, last subject token is decisive for recall"
Editing success: "layer 17, last subject token is where the fact is stored"
→ Together: this is the fact's address in the model
```

---

## Connection to the L0 Decoder

The three operations the full system would need:

```
1. LOCATE:  causal tracing (Lookback paper + ROME Section 2)
            → find (layer, token) where belief is causal
            → L0 decoder reads this

2. PROFILE: RetrievalProfile (our work)
            → assess confidence of the belief
            → flag if contested or preliminary

3. EDIT:    ROME (Section 3)
            → if belief is wrong/adversarial: W_new = W + Λ(C⁻¹k*)ᵀ
            → installs corrected belief permanently
```

ROME was the missing "write" half of the system. We now have:
- Read from weights: causal tracing finds the location
- Assess the read: RetrievalProfile scores the quality
- Write to weights: ROME installs the correction

The L0 decoder closes the loop between reading and writing.
