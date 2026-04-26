# ROME — compute_u and compute_v Deep Dive

_Scholar ticket: S-005_
_Source: `rome/rome/compute_u.py`, `rome/rome/compute_v.py`_

---

## The Big Picture First

ROME needs to insert a new (k*, v*) pair into a weight matrix.
Think of the MLP like a phone book:

```
Before edit:   "Steve Jobs" → look up → "Apple"
After edit:    "Steve Jobs" → look up → "Microsoft"
```

To do this cleanly, two things must be computed:

```
compute_u:  WHERE in the MLP to write
            → the key direction k* (adjusted by inverse covariance)
            → "this is the fingerprint of Steve Jobs in weight space"

compute_v:  WHAT to write
            → the value delta Λ (the change needed)
            → "this is what 'Microsoft' looks like as an MLP output"
```

Then `rome_main` applies:
```
W_new = W + Λ(C⁻¹k*)ᵀ
```
A rank-one update — one outer product added to the weight matrix.

---

## compute_u — Finding the Key

### What it returns

`u` = the whitened subject representation at the MLP input.
Normalized to unit length.

This is the "address" of Steve Jobs in the MLP's key space.

### Step 1: Get the subject representation

```python
cur_repr = repr_tools.get_reprs_at_word_tokens(
    context_templates=[templ.format(request["prompt"]) for templ in context_templates],
    words=[word for _ in range(len(context_templates))],
    subtoken="last",           # last token of "Steve Jobs" = "Jobs"
    layer=layer,               # layer 17
    track="in",                # INPUT to the MLP (before W_fc)
).mean(0)                      # average across context templates
```

What's happening:
- Feed "Steve Jobs was the founder of" through the model
- At layer 17, at the position of "Jobs" (last subject token)
- Read the hidden state that enters the MLP's first linear layer
- Do this for 50 different context templates, take the mean

**Why average over 50 contexts?**
The representation of "Jobs" varies slightly depending on what words
come before it. "The Steve Jobs biography..." vs "CEO Steve Jobs...".
Averaging makes k* more stable and not specific to one phrasing.

### Step 2: Apply inverse covariance adjustment

```python
u = get_inv_cov(...) @ u.unsqueeze(1)
u = u.squeeze()
```

`C` = KKᵀ = the uncentered covariance of ALL key vectors the MLP
has seen on 100,000 Wikipedia sentences. It captures the "average
shape" of the key space — which directions are common vs rare.

`C⁻¹` rotates k* into a direction that's SPECIFIC to this subject.

**Why this matters — the crowded room analogy:**

Imagine the MLP's key space is a room with 6400 dimensions.
Most subjects cluster along certain common directions — "person",
"organization", "place" etc. If Steve Jobs' representation points
strongly in the "person" direction, a naive edit would accidentally
affect ALL person-related facts.

C⁻¹ finds the directions unique to Steve Jobs specifically,
minimizing interference with other facts stored nearby.

The notebook output confirmed this step ran:
```
Retrieving inverse covariance statistics for gpt2-xl @ transformer.h.17.mlp.c_proj
Attempting to download ... wikipedia_stats/transformer.h.17.mlp.c_proj_float32_mom2_100000.npz
```
100,000 Wikipedia samples, precomputed and cached.

### Step 3: Normalize

```python
return u / u.norm()
```

Unit vector. The direction matters, not the magnitude.

---

## compute_v — Finding the Value Delta

This is harder. We can't directly look up "what should the MLP output
when it sees Steve Jobs and needs to say Microsoft?" — we have to
optimize for it.

### The core idea

Instead of changing the weights directly, compute_v:
1. Introduces a trainable `delta` vector (same shape as MLP output)
2. Temporarily ADDS delta to the MLP output at the subject's last token
3. Runs the model forward and measures the loss
4. Optimizes delta to minimize the loss (20 steps of Adam)
5. The final `target_init + delta` is the desired MLP output

delta starts at zero. After 20 steps it encodes "the adjustment
needed so that 'Microsoft' becomes the correct prediction."

### The three-term loss

```
loss = nll_loss + kl_loss + weight_decay
     =  6.843  +   0.0   +    0.0      (step 0)
     =  0.020  +   0.005 +    0.097    (step 20)
```

**Term 1 — NLL loss (negative log likelihood):**
```python
nll_loss = -log P(target | prompt)
         = -log P("Microsoft" | "Steve Jobs was the founder of ___")
```
Minimize this → maximize the probability of "Microsoft".
This is the primary objective. Goes from 6.843 → 0.020.

**Term 2 — KL divergence (essence preservation):**
```python
kl_prompts = ["{} is a"]
kl_loss = KL(P_original["Steve Jobs is a ..."] || P_edited["Steve Jobs is a ..."])
```
The model is also run on "Steve Jobs is a ___" with and without delta.
The KL divergence penalizes any change to this distribution.

**Why?** Without this, the optimizer might make Steve Jobs sound like
a "software product" or "operating system" — drifting the model's
fundamental understanding of what Steve Jobs IS. This term keeps
"Steve Jobs is a person / entrepreneur / CEO" intact while changing
only "Steve Jobs founded ___".

This is called **essence drift** prevention in the paper.

**Term 3 — Weight decay (keep delta small):**
```python
weight_decay = v_weight_decay * (||delta|| / ||target_init||²)
```
Penalizes large delta values. Forces the optimizer to find the
MINIMAL change that achieves the target probability.

Without this: the optimizer finds extreme delta values that achieve
high probability but corrupt other memories in the same MLP layer.

The delta is also explicitly clamped:
```python
max_norm = clamp_norm_factor * target_init.norm()
if delta.norm() > max_norm:
    delta = delta * max_norm / delta.norm()
```
Hard constraint: delta cannot grow beyond 4× the norm of the
original MLP output. Safety net.

### The final line — algebraic solution

After optimization, delta is finalized. Then:

```python
right_vector = (target - cur_output) / torch.dot(cur_input, left_vector)
```

Breaking this down:
```
target       = target_init + delta     # desired new MLP output
cur_output   = current MLP output      # what it produces today
(target - cur_output) = the residual   # how far we need to move

cur_input    = MLP input (k* raw, before inverse cov adjustment)
left_vector  = u from compute_u (C⁻¹k*, normalized)
dot product  = scalar denominator from the paper's formula
```

This is directly Equation 2 from the paper:
```
Λ = (v* - Wk*) / (C⁻¹k*)ᵀk*
```

The division by the dot product is what ensures that when you apply
the rank-one update `W + Λ(C⁻¹k*)ᵀ`, multiplying by k* gives
exactly v*:

```
(W + Λ(C⁻¹k*)ᵀ) k* = Wk* + Λ · (C⁻¹k*)ᵀk*
                     = Wk* + (v* - Wk*) · 1
                     = v*   ✓
```

---

## The Confusion in the Naming

The code has a naming inconsistency worth flagging:

```python
# compute_u.py docstring:
"Computes the right vector used in constructing the rank-1 update matrix."

# compute_u.py print statement:
print("Computing left vector (u)...")
```

The docstring says "right vector", the print says "left vector". What's correct?

In the rank-one update W + Λ(C⁻¹k*)ᵀ:
- The "column" is Λ — this is `right_vector` from compute_v
- The "row" is (C⁻¹k*)ᵀ — this is u from compute_u

So compute_u returns what becomes the ROW of the outer product
(the "right" part in outer product notation).
compute_v returns what becomes the COLUMN (the "left" part).

The docstring in compute_u is technically more correct.
The print statement is misleading. Don't let it confuse you.

---

## What the Notebook Output Confirmed

```
Left vector shape: torch.Size([6400])    ← u (compute_u output)
Right vector shape: torch.Size([1600])   ← Λ (compute_v output)
```

GPT-2 XL MLP:
- d_model = 1600 (hidden size)
- d_mlp = 6400 (4× expansion, standard transformer MLP)

u is 6400D because it's the input to W_fc (d_mlp dimension).
Λ is 1600D because it's the output of W_proj (d_model dimension).

The rank-one update:
```
W_proj (1600 × 6400) += outer_product(Λ, u) (1600 × 6400)
```
Same shape. One outer product. Done.

---

## Summary: What Each File Does

| | compute_u | compute_v |
|---|---|---|
| Returns | Key direction u (6400D) | Value delta Λ (1600D) |
| Method | Forward pass + inverse cov | Optimization (20 steps) |
| What it encodes | "Where is Steve Jobs in key space?" | "What MLP output produces Microsoft?" |
| Cost | Cheap (one forward pass + matrix multiply) | Expensive (20 forward passes) |
| Paper equation | C⁻¹k* / \|\|C⁻¹k*\|\| | (v* - Wk*) / (C⁻¹k*)ᵀk* |
| Rank-one role | The row direction | The column direction |
