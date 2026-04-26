# ROME — Results and Comparison

_Scholar ticket: S-004_
_Source: Sections 3.4–3.6, Table 4, Figure 5, Figure 6_

---

## The Two Universal Failure Modes

The paper names two failure modes that every method before ROME exhibits:

**F1 — Overfitting (fails to generalize):**
The edit works on the exact template ("Steve Jobs founded ___") but fails
on rephrasing ("The company Steve Jobs started was ___"). The model learned
to regurgitate the target word in one specific context without understanding
the underlying fact.

Symptom: high Efficacy, low Paraphrase score.

**F2 — Underfitting / bleedover (fails specificity):**
The edit generalizes too aggressively — it starts applying the new fact
to unrelated subjects. After editing Pierre Curie → medicine, the model
also starts describing Robert Millikan as a medical scientist.

Symptom: high Paraphrase, low Neighborhood Score.

```
FT:    solves F1, hits F2  (generalizes well, bleeds badly)
FT+L:  solves F2, hits F1  (specific, but doesn't generalize)
KE/MEND: hit both F1 and F2 simultaneously
ROME:  solves both
```

---

## GPT-J Results — ROME Generalizes Better at Scale

GPT-J (6B) results confirm ROME's advantage is not model-specific:

```
           Score    Efficacy   Paraphrase   Specificity
GPT-J:     23.6     (base)      83.0%         96.6%

FT:        25.5     100.0%      71.0%         10.3%   ← F2: bleeds catastrophically
FT+L:      68.7      99.6%      30.4%         78.6%   ← F1: doesn't generalize
MEND:      63.2      97.4%      11.0%         53.9%   ← both failures
ROME:      91.5      99.9%      74.1%         99.1%   ← best on both
```

One number stands out: GPT-J's base specificity is already 96.6% — it barely
changes predictions for unrelated subjects. ROME preserves this (99.1%).
FT destroys it entirely (10.3%). That's not editing — that's corrupting.

The paper notes: "ROME achieves similar specificity on GPT-J and GPT-2 XL
while generalizing much better on GPT-J." Larger models have richer
representations — the edit propagates more coherently across rephrasing.

---

## Knowledge Neurons (KN) — A Related Failure

An interesting baseline worth highlighting: **Knowledge Neurons (Dai et al., 2022)**.

Same idea as ROME at a high level — identify knowledge-storing neurons via
attribution, then modify those weights. But:
- Uses gradient-based attribution (not causal tracing) to find neurons
- Modifies individual MLP rows (not a rank-one matrix update)
- Result: 35.6 Score, fails on both F1 and F2

**Why interesting:** Dai et al. (2022) is the same research group that
discovered Ordering IDs in the Lookback paper (2026). They tried a similar
approach — locate knowledge, edit it — but failed because attribution-based
localization is weaker than causal tracing, and row-modification is cruder
than a rank-one update.

The progression: KN (2022) → ROME (2022) → Lookback (2026) shows the field
learning that precise causal localization is the prerequisite for effective editing.

---

## Figure 6 — The Pierre Curie Test

The paper inserts a counterfactual: "Pierre Curie's area of work is medicine"
(he is actually a physicist). Then generates text about him and an unrelated
physicist (Robert Millikan) to test both properties simultaneously.

**Generalization test:** Does the edit show up in free generation?
```
ROME:   "Pierre Curie often collaborated with [...] on radiation research
         [after edit:] Pierre Curie devoted himself to medicine and biology"
         → correctly generalized, coherent text

FT:     Similar generalization, but...
KE:     "medicine medicine medicine medicine..." → incoherent repetition (F1)
FT+L:   Alternates between medicine and physics depending on prompt (F1)
```

**Specificity test:** Does the edit bleed into Robert Millikan?
```
Before edit:    GPT-2 XL describes Millikan as an astronomer (wrong, but stable)
After ROME:     Millikan still described as an astronomer ✓
After FT:       Millikan now described as a physician ✗ (bleedover)
After KE/MEND:  Millikan now described as a medical scientist ✗ (bleedover)
```

This is the clearest illustration of F2 in the paper. FT and hypernetworks
don't just change Pierre Curie — they change everyone who has a similar
representation in the model.

---

## Human Evaluation

15 volunteers compared ROME vs FT+L on 50 edited facts, rating generated
text for fluency and consistency with the inserted fact.

The paper reports ROME wins on both metrics. This matters because automatic
metrics (Efficacy, Paraphrase, Neighborhood Score) measure specific patterns
but not overall coherence. Human evaluation confirms: ROME's edits read
naturally and are semantically consistent, not just token-matching tricks.

---

## The Confirmation Loop — Why This Section Matters

Section 3.4 (Confirming Decisive States) is the structural centerpiece
of the paper. It's where ROME stops being just an editing method and
becomes evidence for the localized factual association hypothesis.

The logic:

```
1. Causal tracing identified: layer 17, last subject token is decisive
2. ROME targeted at layer 17, last subject token: Score = 89.2
3. ROME targeted at other layers/tokens: Score drops significantly
4. The peak in Figure 5 aligns with the peak in causal tracing (Figure 2)

Conclusion: editing success and causal importance point at the same location
→ that location stores the fact
→ the Localized Factual Association Hypothesis is confirmed
```

This is the bidirectional proof we mentioned in S-003. The paper doesn't
just locate facts — it confirms the location is correct by showing that
edits at that location work, and edits elsewhere don't.

---

## ROME vs Lookback — The Complete Picture

Now that we've read both papers, the full picture:

**What ROME contributes:**
- Facts stored in MLP weights at middle layers, last subject token
- Proven by: causal tracing + editing success at that location
- Editable via: rank-one update (closed form, no training)
- Tested on: world knowledge from training data (real entities)

**What Lookback contributes:**
- Beliefs retrieved via OID-based attention lookback mechanism
- Proven by: IIA experiments across all layers and token positions
- Not editable at publication time (no weight modification)
- Tested on: in-context beliefs from current prompt (synthetic entities)

**What they share:**
- Same causal methodology (ROME: indirect effect, Lookback: IIA)
- Same David Bau research group
- Both find localized, inspectable mechanisms
- Both confirm the model is systematic, not statistical

**The gap between them:**

```
ROME answers:     WHERE is the world knowledge stored? Can we change it?
Lookback answers: HOW is in-context belief retrieved? Through what mechanism?

Together:         Storage (ROME) + Retrieval (Lookback) = the full pipeline
Gap:              Can edits to storage (ROME) corrupt retrieval (Lookback)?
                  This is S-007's open question — the experiment not yet done.
```

---

## Summary Table — All Results

| Method | Score | F1 (no generalize) | F2 (bleeds) |
|---|---|---|---|
| GPT-2 XL (base) | 30.5 | ✗ | — |
| FT | 65.1 | ✓ solved | ✗ fails |
| FT+L | 66.9 | ✗ fails | ✓ solved |
| KE | 52.2 | partial | partial |
| KE-CF | 18.1 | ✓ solved | ✗✗ destroyed |
| MEND | 57.9 | partial | partial |
| MEND-CF | 14.9 | ✓ solved | ✗✗ destroyed |
| KN | 35.6 | ✗ fails | ✗ fails |
| **ROME** | **89.2** | **✓ solved** | **✓ solved** |
