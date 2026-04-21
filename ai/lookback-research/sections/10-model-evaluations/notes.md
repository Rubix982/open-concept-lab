# Model Evaluation Landscape — Notes

Behavioral accuracy across 14 models on CausalToM.
This explains WHY the paper selected the three specific models for
mechanistic analysis, and maps the full capability landscape.

---

## Full Results

| Model | No-Vis | Vis | Gap (Vis drop) | Type |
|---|---|---|---|---|
| Llama-2-7B-hf | 0.01 | 0.01 | 0.00 | base |
| Qwen2.5-7B | 0.28 | 0.06 | 0.22 | base |
| Meta-Llama-3-8B | 0.30 | 0.12 | 0.18 | base |
| Llama-2-13B-hf | 0.33 | 0.12 | 0.21 | base |
| Meta-Llama-3-8B-Instruct | 0.35 | 0.09 | 0.26 | instruct |
| Llama-3.1-8B | 0.45 | 0.29 | 0.16 | base |
| OLMo-2-1124-13B-Instruct | 0.52 | 0.36 | 0.16 | instruct |
| gemma-3-27b-it | 0.53 | 0.39 | 0.14 | instruct |
| Llama-3.1-8B-Instruct | 0.72 | 0.31 | 0.41 | instruct |
| Qwen2.5-14B (base) | 0.86 | 0.43 | 0.43 | base |
| OLMo-2-0325-32B-Instruct | 0.81 | 0.68 | 0.13 | instruct |
| **Qwen2.5-7B-Instruct** | **0.95** | **0.72** | **0.23** | instruct |
| **Meta-Llama-3-70B-Instruct** | **0.95** | **0.92** | **0.03** | instruct |
| **Qwen2.5-14B-Instruct** | **0.96** | **0.91** | **0.05** | instruct |

Bold = models selected for mechanistic analysis.

---

## Why These Three Models Were Selected

The paper analyzed Llama-3-70B-Instruct, Llama-3.1-405B-Instruct, and
Qwen2.5-14B-Instruct. The selection criterion is visible in the data:

**Require high accuracy on BOTH conditions (≥ 0.90 no-vis, ≥ 0.70 vis)**

Only three models meet this bar:
- Llama-3-70B-Instruct: 0.95 / 0.92
- Qwen2.5-14B-Instruct: 0.96 / 0.91
- (Llama-3.1-405B-Instruct: not in eval table but paper states similar performance)

This matters for causal mediation: IIA experiments only run on samples
the model answers **correctly**. If accuracy is too low, there aren't
enough correct samples to measure the mechanism reliably. A model that
guesses randomly can't be reverse-engineered.

---

## Finding 1 — Instruction Tuning is Essential for ToM

```
Base model accuracy (no-vis):
  Llama-2-7B:       0.01
  Meta-Llama-3-8B:  0.30
  Qwen2.5-7B:       0.28
  Qwen2.5-14B:      0.86  ← exception

Instruct model accuracy (no-vis):
  Llama-3.1-8B-Instruct:    0.72
  Qwen2.5-7B-Instruct:      0.95
  Qwen2.5-14B-Instruct:     0.96
  Meta-Llama-3-70B-Instruct: 0.95
```

For almost every model family, the instruction-tuned version vastly
outperforms the base. Meta-Llama-3-8B: 0.30 base vs 0.35 instruct
(small gain). But Qwen2.5-7B: 0.28 base vs 0.95 instruct — a 3.4×
improvement.

**Why:** ToM requires following complex multi-step instructions
("track each character's beliefs separately", "answer unknown when
a character has no information"). Base models haven't been trained to
follow these kinds of structured reasoning instructions. Instruction
tuning teaches the model to use the task instructions as guidelines,
not just predict the next token.

**Exception:** Qwen2.5-14B base gets 0.86 no-vis — competitive with
instruction models. This is notably high for a base model and may
reflect Qwen's training corpus containing more structured reasoning data.

---

## Finding 2 — Visibility is Much Harder Than No-Visibility

```
Visibility accuracy drop (no-vis → vis):
  Meta-Llama-3-8B-Instruct:  0.35 → 0.09  (drop: -0.26)
  Qwen2.5-14B base:          0.86 → 0.43  (drop: -0.43)
  Llama-3.1-8B-Instruct:     0.72 → 0.31  (drop: -0.41)
  Qwen2.5-7B-Instruct:       0.95 → 0.72  (drop: -0.23)
  Meta-Llama-3-70B-Instruct: 0.95 → 0.92  (drop: -0.03)  ← minimal
  Qwen2.5-14B-Instruct:      0.96 → 0.91  (drop: -0.05)  ← minimal
```

Almost every model degrades on visibility. The visibility condition
requires a third mechanism (visibility lookback) on top of binding and
answer lookback. Models that barely handle no-visibility collapse when
the third mechanism is needed.

**The models the paper studies** (70B and Qwen-14B-Instruct) are
exceptional — their visibility drop is ≤ 0.05. This is why they were
chosen: they're the only models that demonstrate the full three-mechanism
pipeline reliably enough to study.

**The large-drop models** (8B-Instruct: -0.41) are failing specifically
at the visibility lookback — the Visibility ID formation and transfer
mechanism. This is a natural next research question: at what scale does
the visibility lookback emerge?

---

## Finding 3 — Scale Matters, But Not Uniformly

Within the Llama-3 family:
```
Meta-Llama-3-8B:         0.30 / 0.12
Meta-Llama-3-8B-Instruct: 0.35 / 0.09
Meta-Llama-3-70B-Instruct: 0.95 / 0.92
```

8B → 70B is a massive jump (0.35 → 0.95 no-vis).

But within Qwen:
```
Qwen2.5-7B-Instruct:  0.95 / 0.72
Qwen2.5-14B-Instruct: 0.96 / 0.91
```

7B-Instruct already reaches 0.95 no-vis. The visibility jump from
0.72 → 0.91 requires the 14B model.

**Implication:** Scale alone doesn't explain the capability. Training
regime (instruction tuning quality, data mixture) matters as much as
parameter count. A 7B Qwen matches a 70B Llama on no-visibility tasks.

---

## Finding 4 — OLMo Generalizes Better Than Expected

```
OLMo-2-0325-32B-Instruct: 0.81 / 0.68
OLMo-2-1124-13B-Instruct: 0.52 / 0.36
```

OLMo at 32B achieves 0.81/0.68 — better than Llama-3.1-8B-Instruct
(0.72/0.31) at lower parameter count. And the visibility gap is only
-0.13 vs -0.41 for Llama-3.1-8B-Instruct.

OLMo models are fully open (weights, data, training details). This
makes them interesting for mechanistic analysis — the same IIA
experiments could be run with full knowledge of the training corpus.

---

## The Selection Funnel

```
14 models evaluated
    ↓
8 models with no-vis accuracy ≥ 0.50
    ↓
3 models with vis accuracy ≥ 0.70 (Qwen7B-Instruct, 70B, Qwen14B-Instruct)
    ↓
2 models with vis accuracy ≥ 0.90 (70B, Qwen14B-Instruct)
    + 1 larger model (405B, not in eval table)
    = 3 models for mechanistic analysis
```

The funnel is tight. Only two publicly tested models reach the
threshold needed for reliable IIA experiments on both conditions.
