# CounterFact Dataset — Notes

_Scholar ticket: S-006_
_Source: Section 3.3 of the paper, `rome/dsets/counterfact.py`_

---

## Why a New Dataset Was Needed

**The problem with zsRE:**

Hase et al. (2021) observed that standard model-editing benchmarks
underestimate difficulty. zsRE samples facts somewhat randomly —
many of them are facts the model already half-believes (high P(o*) before
editing). Inserting "Steve Jobs founded Microsoft" is easy if the model
already assigns 30% probability to Microsoft.

A real benchmark should test whether you changed a genuine belief, not
whether you reinforced a near-belief.

**CounterFact's solution:**

Only include facts where the counterfactual starts with LOW probability
compared to the correct fact. The edit has to actually overcome the
model's existing belief, not just nudge a weak prior.

```
zsRE:        P(target_new) might already be 0.3 before editing
             → easy: small nudge → P(target_new) > P(target_true)

CounterFact: P(target_new) ≪ P(target_true) before editing
             → hard: model strongly believes the correct fact
             → edit must genuinely overturn a belief
```

---

## Structure of One CounterFact Record

Each record is a package of test prompts for one counterfactual fact:

```json
{
  "case_id": 1,
  "requested_rewrite": {
    "prompt":      "{} was the founder of",
    "subject":     "Steve Jobs",
    "target_new":  {"str": "Microsoft"},   ← what we want to insert
    "target_true": {"str": "Apple"}        ← what the model currently believes
  },
  "paraphrase_prompts": [
    "Steve Jobs created ___",
    "The company Jobs started was ___",
    "Steve Jobs is best known for founding ___",
    ...  (2 per record average)
  ],
  "neighborhood_prompts": [
    "Bill Gates was the founder of",         ← nearby subject, same relation
    "Larry Ellison was the founder of",      ← should still say their real companies
    ...  (10 per record average)
  ],
  "generation_prompts": [
    "My favorite Steve Jobs product is",
    "Steve Jobs is most famous for",
    ...  (3 per record average)
  ]
}
```

---

## The Six Metrics

### 1 & 2 — Efficacy Score (ES) and Magnitude (EM)

```
ES = fraction of cases where P(target_new) > P(target_true) post-edit
EM = mean of P(target_new) - P(target_true) post-edit

ES = "did the edit flip the model's preference?"
EM = "by how much?"
```

High ES = the edit always "wins." But this alone doesn't tell you if
the model truly learned the new fact or just learned to regurgitate
the target token in that one specific template.

### 3 & 4 — Paraphrase Score (PS) and Magnitude (PM)

Same as ES/EM but computed on the paraphrase prompts instead of the
original template.

```
PS = "does the edit generalize to rephrased versions?"
```

PS < ES → the model learned a surface pattern, not a fact.
This is F1 failure mode. KE-CF: ES=99.9%, PS=95.8% (close) vs
FT+L: ES=99.1%, PS=48.7% (big gap — surface learning only).

### 5 & 6 — Neighborhood Score (NS) and Magnitude (NM)

Computed on neighborhood prompts — nearby subjects.

```
NS = fraction of cases where P(target_true) > P(target_new) for neighbors
   = "did the edit leave neighboring subjects unchanged?"
```

High NS = the edit is specific. Low NS = bleedover (F2 failure mode).
KE-CF: NS=9.1% — devastating. ROME: NS=75.4%.

### 7 — Reference Score (RS)

Generate text starting with the subject, compute cosine similarity of
the generated text (TF-IDF) against reference texts about entities that
share the new property.

```
RS measures: "does free generation sound like the new property?"
             not just for specific prompts — for any generation
```

Edit "Steve Jobs → Microsoft" → generate "Steve Jobs..."
→ should produce text about software, Windows, etc.
→ compared against reference texts about Microsoft-related people
→ RS = how similar the generated text is to that reference

### 8 — Generation Entropy (GE)

Weighted average of bi- and tri-gram entropy in generated text.

```
GE = -Σ f(k) log₂ f(k)   where f(k) = n-gram frequency

High GE = diverse, natural text
Low GE  = repetitive text ("medicine medicine medicine...")
```

KE: GE=383.0 (repetitive — F1 symptom), ROME: GE=621.9 (natural).

---

## Why CounterFact Is Harder Than Every Prior Benchmark

Table 3 in the paper compares CounterFact to six existing benchmarks:

| Criterion | zsRE | CounterFact |
|---|---|---|
| Efficacy | ✓ | ✓ |
| Generalization | ✓ | ✓ |
| Bleedover | ✗ | ✓ |
| Consistency | ✗ | ✓ |
| Fluency | ✗ | ✓ |

No prior benchmark tests bleedover (specificity), semantic consistency
of generated text, or fluency. zsRE only tests efficacy and generalization.
CounterFact is the first benchmark that tests ALL five dimensions simultaneously.

---

## Scale

```
21,919 records total
645 distinct relations
20,391 distinct subjects
749 distinct objects

Per record:
  1  counterfactual statement
  2  paraphrase prompts  (→ 42,876 total)
  10 neighborhood prompts (→ 82,650 total)
  3  generation prompts  (→ 62,346 total)
```

The scale of neighborhood prompts (82,650) matters — it means bleedover
testing is thorough. For each edit, 10 nearby subjects are tested.
You can't get a high NS by luck.

---

## Connection to CausalToM

CounterFact and CausalToM share a design philosophy:

| | CounterFact | CausalToM |
|---|---|---|
| Purpose | Test model editing | Test belief tracking |
| Key design | Counterfactual pairs that force real belief change | Counterfactual pairs that isolate specific variables |
| Why built | Existing benchmarks underestimated difficulty | Existing benchmarks lacked causal structure |
| What it tests | Storage + retrieval + generalization + specificity | OID binding + answer lookback + visibility |

Both datasets were built because existing work was measuring the wrong
thing — behavior without mechanism. Both require paired examples where
exactly one thing differs.

---

## The Metric That Most Matters for the L0 Decoder

**Neighborhood Score (NS)** is the metric most directly relevant.

NS measures whether an edit at one location bleeds into semantically
related locations. This is exactly what the L0 decoder needs to assess:

```
If you edit W at k_steve (Steve Jobs direction):
  How much does W change along k_bill (Bill Gates direction)?
  → measured by: did Bill Gates' answers change?
  → predicted by: dot(k_bill, u)  — how aligned is k_bill with the edit direction?
```

The RetrievalProfile's `residual_competition` dimension is the
activation-space version of this — it measures how much competing signals
are present at the belief location. High competition → low expected NS
after an edit. Low competition → high expected NS.

In other words: the RetrievalProfile can predict, before editing, whether
a ROME edit will maintain good specificity. That's the L0 decoder contribution
ROME doesn't have.
