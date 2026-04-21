# Researcher Tickets

### R-001 · BigToM generalization analysis

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
Analyze the pre-computed BigToM results in
`belief_tracking/results/bigToM/Meta-Llama-3-70B-Instruct/causal_model/`.
BigToM is a real-world ToM benchmark (Gandhi et al., 2024), not synthetic.
The paper claims the lookback mechanism generalizes beyond CausalToM.

Tasks:
1. Inspect the BigToM result directory structure and file schemas
2. Extract IIA scores by layer for each lookback type (binding, answer, visibility)
3. Compare layer windows to CausalToM results — do they shift? Stay the same?
4. Build `sections/07-bigtom/` with notes.md, diagram.md, visualize_results.py
5. Write findings to `agents/shared/findings.md`

Second engineer spec: given the result files and CausalToM section artifacts
as reference, a second researcher could execute this independently.

**Artifacts:**
- `sections/07-bigtom/notes.md`
- `sections/07-bigtom/diagram.md`
- `sections/07-bigtom/output/` (visualizations)
- `agents/shared/findings.md` → BigToM finding entry

**Closed:** 2026-04-22

---

### R-002 · Cross-model replication analysis

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** _(none — R-001 closed)_

**Description:**
Analyze pre-computed results for Llama-3.1-405B-Instruct and
Qwen2.5-14B-Instruct from:
`belief_tracking/results/causalToM_novis/Meta-Llama-3.1-405B-Instruct-8bit/`
`belief_tracking/results/causalToM_novis/Qwen2.5-14B-Instruct/`

The paper claims the mechanism is not model-specific.

Tasks:
1. Extract IIA scores for binding + answer lookback for both models
2. Compare layer windows across all three models (70B, 405B, Qwen-14B)
3. Identify: do windows shift deeper with more layers? Stay proportional?
4. Build `sections/08-cross-model/` with notes, diagram, visualizations
5. Write findings to `agents/shared/findings.md`

Second engineer spec: given section 01 and 02 artifacts as reference format,
a second researcher can replicate this for the two additional models.

**Artifacts:**
- `sections/08-cross-model/notes.md`
- `sections/08-cross-model/output/` (side-by-side model comparison charts)
- `agents/shared/findings.md` → cross-model finding entry

**Closed:** —

---

### R-003 · Synthesis document

**Status:** closed
**Type:** document
**Priority:** medium
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Blockers:** _(none — R-001 and R-002 closed)_

**Description:**
Write a single `sections/synthesis.md` that tells the complete end-to-end
story of the paper in one place. Must be readable in under 15 minutes and
serve as the entry point for anyone approaching this research.

Required structure:
1. The problem: what ToM question the paper asks
2. The method: what causal mediation is and why it works
3. The five mechanisms: visibility source → binding → answer (with layer windows)
4. The evidence: which experiments confirm each mechanism (linking to our artifacts)
5. Generalization: BigToM and cross-model findings
6. Implications: connection to the Research Knowledge Infrastructure vision (L0 layer)
7. Open questions: what the paper does not answer

Must connect every major claim to:
- The specific figure in the paper
- Our corresponding artifact in sections/

Second engineer spec: given all notes.md files across sections 00–07 and the
paper figures reference in 05-paper-figures/, a second researcher could write
this synthesis without having read the paper directly.

**Artifacts:**
- `sections/synthesis.md`
- `agents/shared/findings.md` → synthesis summary entry

**Closed:** —

---

### R-004 · Model evaluation landscape\n\n**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
Analyze behavioral accuracy across all 14 models in
`belief_tracking/results/model_evaluations/`. Each model has a no-visibility
and a visibility accuracy score. The paper selected only three models for
mechanistic analysis — this ticket explains why and maps the full landscape.

Tasks:
1. Extract accuracy (mean, std) for all 14 models, both conditions
2. Identify patterns: instruction-tuned vs base, scale effects, family effects
3. Explain the paper's model selection criteria (high accuracy in both conditions)
4. Visualize: grouped bar chart, instruction vs base, no-vis vs vis gap
5. Build `sections/10-model-evaluations/` with notes.md and visualizations
6. Write findings to `agents/shared/findings.md`

**Artifacts:**
- `sections/10-model-evaluations/notes.md`
- `sections/10-model-evaluations/output/`
- `agents/shared/findings.md` → R-004 finding

**Closed:** —

---

### R-005 · Cross-model visibility lookback

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
R-002 covered causalToM_novis for three models but never compared visibility
lookback mechanisms across models. This fills that gap using
`belief_tracking/results/causalToM_vis/` for all three models.

Tasks:
1. Extract IIA scores for source, address_and_pointer, payload for all 3 models
2. Compare layer windows and proportional positions (same approach as R-002)
3. Does the gap region (L17-22 in 70B) appear in 405B and Qwen?
4. Does vis_ID formation scale proportionally with model depth?
5. Build `sections/11-cross-model-visibility/` with notes and visualizations
6. Write findings to `agents/shared/findings.md`

**Artifacts:**
- `sections/11-cross-model-visibility/notes.md`
- `sections/11-cross-model-visibility/output/`
- `agents/shared/findings.md` → R-005 finding

**Closed:** —

---

### R-006 · Related work — paper sections 7 and 8

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-04-22
**Updated:** 2026-04-22

**Description:**
Read and document paper sections 7 (Related Work) and 8 (Conclusion).
Map prior work to: what it contributed, how this paper builds on it,
and relevance to the Research Knowledge Infrastructure direction.

Key clusters to document:
- Mechanistic interpretability foundations (Elhage, Olsson, induction heads)
- ToM behavioral evaluation papers (what they found, what they missed)
- Causal abstraction / causal mediation methodology
- Induction heads vs lookback mechanism distinction (why they differ)

Tasks:
1. Read sections 7 and 8 from output.txt
2. Cluster citations by theme
3. For each: prior state of the art → what this paper adds
4. Flag papers most relevant to Research Knowledge Infrastructure
5. Build `sections/12-related-work/notes.md`
6. Write findings to `agents/shared/findings.md`

**Artifacts:**
- `sections/12-related-work/notes.md`
- `agents/shared/findings.md` → R-006 finding

**Closed:** —
