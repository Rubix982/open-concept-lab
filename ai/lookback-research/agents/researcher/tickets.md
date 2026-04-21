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
