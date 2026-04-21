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
