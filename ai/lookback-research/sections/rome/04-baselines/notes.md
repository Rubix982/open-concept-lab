# ROME Baselines — Notes

_Scholar ticket: S-008_
_Source: Section 3.2, Table 1, Table 4 of the paper_

---

## The Edit Task

Every baseline is trying to do the same thing:

```
Given: model G with fact (Steve Jobs, founded, Apple)
Goal:  produce model G' such that G'("Steve Jobs founded ___") = "Microsoft"
       while G'(everything else) ≈ G(everything else)
```

The two properties that must hold simultaneously:

```
Generalization:  edit works for rephrased versions of the same question
                 "Steve Jobs created ___" → "Microsoft"
                 "The company Jobs started was ___" → "Microsoft"

Specificity:     edit does NOT affect neighboring facts
                 "Bill Gates founded ___" → still "Microsoft"  ✓
                 "Apple was founded by ___" → still "Steve Jobs" ✓
```

Every method before ROME sacrifices one for the other.

---

## The Target: W at Layer 17

All methods operate on the same weight matrix: `W_proj` at layer 17.
Shape: `(1600 × 6400)` = 10,240,000 weights.

The question each method answers differently:
> "Which of these 10 million weights need to change, by how much,
>  and in which direction?"

---

## Method 1 — Fine-Tuning (FT)

**What it does:**
Standard gradient descent on one example.

```
Loss = -log P("Microsoft" | "Steve Jobs founded ___")
∂Loss/∂W = gradient  (shape: 1600 × 6400 — every weight)
W_new = W - lr × gradient
```

**What changes in W:**
Every weight gets nudged. The gradient doesn't distinguish between weights
that store "Steve Jobs → Apple" and weights that store "Bill Gates → Microsoft."
Both get touched.

**Why specificity fails:**
Gradient descent follows the loss landscape blindly. It finds the fastest
path to making "Microsoft" more likely — which involves changing many
weights, including ones that anchor other facts nearby.

```
FT results (CounterFact, GPT-2 XL):
  Efficacy:     100%   ← edit always "works"
  Paraphrase:   87.9%  ← generalizes reasonably
  Specificity:  46.6%  ← nearly half of neighboring facts broken ✗
  Score:        65.1
```

**FT+L** adds an L∞ constraint: no single weight can change by more than ε.
Helps somewhat — less damage to neighbors — but doesn't solve the root problem
because it still doesn't know WHICH weights to change.

---

## Method 2 — Knowledge Editor (KE)

**Paper:** De Cao et al., 2021

**The idea:**
Train a second neural network H (the hypernetwork) whose job is to predict
what weight change to make, given a new fact to insert.

```
Training phase (done once):
  H sees thousands of (fact, correct_ΔW) examples
  H learns: "facts shaped like X should produce weight changes like Y"

Edit phase:
  encode fact: ("Steve Jobs", "Microsoft") → fact_vector
  H(fact_vector) → predicted ΔW  (shape: 1600 × 6400)
  W_new = W + ΔW
```

**The improvement over FT:**
H learned from previous edits what a "good" weight change looks like.
It tries to produce a targeted ΔW, not a broad gradient.

**Why it struggles out-of-distribution:**
KE was originally trained on WikiText generation — not on counterfactual
facts. When you ask it to change "Steve Jobs → Microsoft" (very unlike
training data), its predictions are poor. KE-zsRE and KE-CF variants
fine-tune H specifically for those distributions — which is why they
score higher but only on their respective test distributions.

**Fundamental limitation:**
H has no access to what W currently contains. It predicts ΔW from the
fact description alone, without knowing what the model currently believes
or which weights are responsible. It's guessing the target without a map.

```
KE results (CounterFact, GPT-2 XL):
  Efficacy:     84.3%   ← misses some edits
  Paraphrase:   75.4%   ← decent generalization
  Specificity:  55.7%   ← better than FT but still leaks
  Score:        52.2
```

---

## Method 3 — MEND (Mitchell et al., 2021)

**Paper:** Mitchell et al., 2021

**The key insight over KE:**
Instead of predicting ΔW from the fact alone, use the fine-tuning gradient
as additional information. The gradient shape tells you which directions
in weight space are relevant for THIS specific edit.

```
Step 1: Compute fine-tuning gradient g = ∂Loss/∂W  (shape: 1600 × 6400)
        This is the raw, noisy gradient from FT

Step 2: Decompose g into low-rank factors via SVD
        g ≈ u @ v.T  where u is (1600 × r), v is (6400 × r)
        r is small (rank of the decomposition)

Step 3: Feed u and v into hypernetwork H
        H(u, v) → u', v'  (refined, more targeted factors)
        H learned: "when the gradient looks like this, clean it up like that"

Step 4: ΔW = u' @ v'.T
        W_new = W + ΔW
```

**The improvement over KE:**
MEND uses the gradient as a map — it shows which dimensions of W are
involved in this prediction. H then learns to amplify the targeted signal
and suppress the noise that would bleed into other facts.

**Still a learned approach:**
H still needs pre-training. Still distribution-dependent. MEND-CF (trained
on CounterFact) achieves near-perfect efficacy and paraphrase but
completely destroys specificity — it learned to edit aggressively for that
distribution, at the cost of everything else.

```
MEND results (CounterFact, GPT-2 XL):
  Efficacy:     99.1%   ← nearly perfect
  Paraphrase:   65.4%   ← weaker than expected
  Specificity:  63.8%   ← still leaks significantly
  Score:        57.9

MEND-CF results:
  Efficacy:     100%
  Paraphrase:   97.0%
  Specificity:   5.7%   ← completely broken ✗
  Score:        14.9
```

---

## Method 4 — ROME

**No second network. No training. Algebra.**

```
Step 1: compute_u  — find the EXACT direction in W for this subject
        u = normalize(C⁻¹ @ k_subject)
        Provably orthogonal to other subjects by construction

Step 2: compute_v  — find what W needs to output
        v* = optimize delta (20 steps)
        Three-term loss: efficacy + essence preservation + minimality

Step 3: closed-form right vector
        Λ = (v* - W @ k*) / dot(k*, u)

Step 4: rank-one update
        W_new = W + outer_product(Λ, u)  — ONE direction changed
```

**Why specificity holds:**
The update only moves W in the direction of u. Other subjects have
different k representations. Since u was whitened by C⁻¹ — the inverse
of the average key covariance — u is nearly orthogonal to common directions
shared by many subjects. Their keys don't project onto u, so they're unaffected.

```
ROME results (CounterFact, GPT-2 XL):
  Efficacy:     100%    ← perfect
  Paraphrase:   96.4%   ← near-perfect generalization
  Specificity:  72.4%   ← best of all methods
  Score:        89.2    ← significantly above all baselines
```

---

## The Progression — What Changed at Each Step

| Method | "Where to edit?" | How determined | Training needed? |
|---|---|---|---|
| FT | Everywhere in the layer | Gradient (blind) | No |
| FT+L | Everywhere, but smaller steps | Gradient + norm constraint | No |
| KE | Predicted from fact description | Hypernetwork, trained offline | Yes |
| MEND | Predicted from gradient shape | Hypernetwork + gradient, trained offline | Yes |
| ROME | Exact direction via causal tracing | Algebra (C⁻¹k*), no training | No |

The fundamental shift from KE/MEND to ROME:

```
KE, MEND:  learn HOW to edit from examples
ROME:      know WHERE to edit from causal tracing + covariance math
```

Knowing WHERE makes the HOW trivial — once u is computed, the edit is
a closed-form calculation. No approximation. No distribution dependence.

---

## The Specificity-Generalization Tradeoff

The tradeoff that every method before ROME hit:

```
High efficacy + high generalization = aggressive edit (changes many weights)
                                    → specificity breaks

High specificity = conservative edit (changes few weights)
                → generalization breaks (only works on exact template)
```

ROME escapes the tradeoff because it changes weights in a SPECIFIC DIRECTION,
not a specific MAGNITUDE. The update covers all weights but only along u.
Broad in the sense of touching all weights in the layer. Narrow in the sense
of only moving along one direction. That combination achieves both:

```
Generalization: moving W along u changes ALL prompts that activate k_subject
                → any phrasing that produces the same subject representation
                   will hit the edit → broad coverage

Specificity:    u is orthogonal to other subjects' keys
                → other subjects' k representations don't project onto u
                → they pass through W_new unchanged → no bleedover
```
