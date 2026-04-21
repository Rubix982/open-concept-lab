# Scholar Tickets

The Scholar agent reads source material alongside the learner.
Its job is comprehension — making ideas legible, connected, and usable.
Output is understanding artifacts (notes, diagrams, demos), not research deliverables.

Scholar tickets use the S- prefix.

---

### S-001 · ROME — Abstract and Introduction

**Status:** closed
**Type:** learn
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
Read and dissect the ROME paper abstract and introduction together.

Source: `docs/rome.txt` (lines 1–~200)

Key concepts to establish before going deeper:
- What is a "factual association" in GPT? How is it different from a belief?
- What is causal mediation analysis in the ROME context vs the Lookback context?
- What is a feed-forward MLP module and why do the authors focus on it?
- What is Rank-One Model Editing (ROME) — the idea in one sentence?
- Why is "editing" harder than "locating"?

Connection to prior knowledge:
- Compare causal mediation here vs the Lookback paper (same author, same method)
- How does "subject token" in ROME map to "state token" in Lookback?
- Why does David Bau appear on both papers?

Artifacts:
- `sections/rome/00-abstract-intro/notes.md`
- `sections/rome/00-abstract-intro/diagram.md`
- `glossary-rome.md` (new glossary for ROME-specific terms)

**Closed:** —

---

### S-002 · ROME — Causal Tracing (Section 3)

**Status:** open
**Type:** learn
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** S-001

**Description:**
The causal tracing section is the methodological heart — equivalent to
the IIA / causal mediation section in the Lookback paper.

Key concepts:
- How does causal tracing work in ROME? Step by step.
- What are "corrupted" vs "clean" vs "restored" runs?
- What is the "indirect effect" they measure?
- What does it mean that MLPs at the subject's last token are decisive?
- Why the last token of the subject specifically?
- How is this different from the Lookback paper's approach?

Artifacts:
- `sections/rome/01-causal-tracing/notes.md`
- `sections/rome/01-causal-tracing/diagram.md`
- `sections/rome/01-causal-tracing/demo.py`

**Closed:** —

---

### S-003 · ROME — The Editing Method (Section 4)

**Status:** open
**Type:** learn
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** S-002

**Description:**
ROME's editing method — this is where the paper diverges from Lookback.
Lookback located mechanisms but did not edit them. ROME edits.

Key concepts:
- What does "rank-one update" mean mathematically?
- What is being changed — weights or activations?
- Why rank-one specifically?
- What constraints must the edit satisfy?
- What are the failure modes of editing?

Connection to research direction:
- This is the operation the L0 decoder would need to perform
- "Locating" (Lookback) + "Editing" (ROME) = the two halves of belief intervention

Artifacts:
- `sections/rome/02-editing-method/notes.md`
- `sections/rome/02-editing-method/diagram.md`
- `sections/rome/02-editing-method/demo.py`

**Closed:** —

---

### S-004 · ROME — Results and Comparison to Lookback

**Status:** open
**Type:** learn
**Priority:** medium
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** S-003

**Description:**
Results, evaluation, and synthesis of what ROME means in context.

Key questions:
- How do they evaluate whether an edit "worked"?
- What is specificity vs generalization in editing?
- Where does ROME fail?
- What does ROME + Lookback together imply?
- What would a belief editor look like that uses both?

Artifacts:
- `sections/rome/03-results/notes.md`
- `sections/rome/synthesis-rome-vs-lookback.md` ← connecting both papers

**Closed:** —

---

### S-005 · ROME — MLP as Key-Value Memory

**Status:** open
**Type:** learn
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** S-002

**Description:**
The conceptual heart of ROME — viewing the MLP weight matrix as a
key-value store. This is the idea that makes editing possible.

Key concepts:
- What is a linear associative memory?
- What are k* (key) and v* (value) in the MLP context?
- Why is k* fixed by the subject token and v* optimized for the object?
- What is "essence drift" and why does the KL divergence term prevent it?
- What does the rank-one update formula actually do geometrically?

Connection to prior knowledge:
- How does MLP-as-key-value differ from attention-as-key-value?
  (ROME footnote 6 explicitly says "unrelated to attention keys/values")
- The Lookback paper found OIDs in attention heads. ROME finds facts in MLPs.
  Are these the same mechanism or different? Do they interact?

Artifacts:
- `sections/rome/02-key-value-memory/notes.md`
- `sections/rome/02-key-value-memory/diagram.md`
- `sections/rome/02-key-value-memory/demo.py` ← implement toy key-value MLP

**Closed:** —

---

### S-006 · ROME — CounterFact Dataset and Evaluation

**Status:** open
**Type:** learn
**Priority:** medium
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** S-003

**Description:**
CounterFact is ROME's custom evaluation dataset — harder than zsRE,
specifically designed to distinguish real knowledge change from surface
pattern matching.

Key concepts:
- Why is zsRE insufficient as an evaluation benchmark?
- What makes CounterFact harder? (starts with low-probability facts)
- The three metrics: Efficacy Score, Paraphrase Score, Neighborhood Score
- What is "essence drift" in generated text? How is it measured?
- The generalization-specificity tradeoff — why most methods fail one

Connection to research direction:
- CounterFact is in the repo: `dsets/counterfact.py`
- We can explore it locally — no model needed
- The three metrics map directly onto the RetrievalProfile epistemic classes

Artifacts:
- `sections/rome/03-counterfact/notes.md`
- Exploration of `rome/dsets/counterfact.py`

**Closed:** —

---

### S-007 · ROME vs Lookback — Two Mechanisms, One System

**Status:** open
**Type:** learn
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** S-002, S-005

**Description:**
Synthesize the relationship between ROME and the Lookback paper.
The two papers use the same method (causal tracing) and find different
things in different parts of the same model.

Key questions:
- ROME: facts in MLP weights at middle layers
- Lookback: beliefs via attention head OIDs in residual stream
- Are these describing different things or the same thing from different angles?
- Does the MLP store the fact AND the attention head retrieves it?
- If you edit the MLP (ROME), does the lookback mechanism still work correctly?
- What breaks first if you corrupt one but not the other?

This ticket produces `sections/rome/synthesis-rome-vs-lookback.md`
which connects both papers into a single mechanistic picture.

Artifacts:
- `sections/rome/synthesis-rome-vs-lookback.md`
- Update `sections/synthesis.md` to include ROME in the three-paper arc

**Closed:** —
