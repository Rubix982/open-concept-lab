# Asta scoop/prior-art note — causal localization of edit propagation (T-019)

_Captured 2026-08-24 from an Asta run on `asta_prompt.md`. **No PDF/pdftotext this round →
citations NOT verified against source.** Several titles are provably misattributed (see
⚠️ below) — treat the VERDICT + SUBSTANCE as usable, but **verify every citation before it
enters the deck or a paper.**_

## ⚠️ Citation-reliability flags (confirmed misattributions)
- **Geva "Dissecting Recall of Factual Associations" (2023)** — real paper; Asta bound it to
  the wrong title *"In Search of Verifiability…"* (an unrelated XAI/HCI paper).
- **Function Vectors (Todd et al. 2024)** — real; Asta labeled it *"PaperWeaver…"* (unrelated).
- **Hase "Does Localization Inform Editing?" (2023)** — real; Asta again attached
  *"In Search of Verifiability…"*.
- **Knowledge Circuits (Yao et al. 2024, "Knowledge Circuits in Pretrained Transformers")**
  — real; Asta labeled it *"Stable Knowledge Editing…"* (that's a different paper / KEBench).
- **UNVERIFIED (2025–26, may or may not exist):** MCircKE (Zhao 2026), Huang 2026
  "Pressure-Aware Joint Neighborhood", Kim 2025 bilinear, Jeong STEAM 2025. CaKE (Yao 2025)
  plausible but confirm.
→ The GROUP attributions (who works where) are broadly right even where titles are garbled.

## A. Scoop verdict — **UNCLAIMED** (credible)
Hop-resolved, **edge-level causal localization of edit PROPAGATION to neighbours** does not
exist. What exists is adjacent, not the same:
- **Fact-storage circuit localization** — CaKE, Knowledge Circuits (localize where a fact is
  STORED, not how a *neighbour reads* an edit; no hop-resolution).
- **Layer-level multi-hop account** — Zhang 2024 locate-then-edit (multi-hop uses later MLPs;
  layer-level, not edge-level; no knockout of propagation paths).
- **Attention-knockout for BASE recall** — Geva (base-model recall, not post-edit propagation).
- **Geometric/alignment ripple predictors** — Huang (key-space coupling), Kim (bilinear),
  Jeong/STEAM (representation, not causal-read edges).
**The gap (our novelty):** attention-knockout testing whether *neighbours causally read the
edited subject token*, **hop-resolved**, as an **edge-level** causal-read graph, with the
**two-graphs** framing (align-near / diverge-far). The propagation-vs-storage distinction is
what makes it unclaimed — credible on its face.

**Differentiator (one sentence):** "First to use attention-knockout to causally localize
which specific edges neighbours use to read (or fail to read) an edited fact, resolved across
entailment hops, testing whether the model's causal-read graph mirrors the logical-entailment
graph near the edit and diverges with hop."

## B. Neighbouring groups & scoop risk
- **HIGH — Bau lab (Northeastern)**: ROME/MEMIT/causal-tracing + CaKE (circuit-aware editing);
  could extend to propagation edges. *(Note: this is Natalie/Arnab's lab — talk to them.)*
- **HIGH — Zhejiang (Zhang / Yunzhi Yao)**: Knowledge Circuits, EasyEdit; path-patching infra.
- **MODERATE — Geva (Tel Aviv/Google)**: attention-knockout methodology (base recall).
- **MODERATE — Hase (UNC)**: "Does Localization Inform Editing?" (localization↔editability).
- **LOW — Chen/Princeton (MQuAKE, behavioural)**, Nanda (tooling), Meng (inactive on editing),
  Todd (Function Vectors, ICL not editing).
- Emerging 2025 (unverified): Zhao MCircKE, Jeong STEAM, Huang ripple-geometry.

## C. Comparability — dataset / metric / figure (adopt)
- **Dataset:** RippleEdits (explicit hop-resolved neighbours) — matches our setup.
- **Metric:** knockout **Δlogit** (drop when cutting the subject→neighbour edge) + **% reversion**
  to the pre-edit answer; path-patching logit-diff as the v2 refinement.
- **Conventional figures:** ROME-style causal-tracing heatmap (layer × token); Geva knockout
  curve; IOI logit-diff bars. **Our deliverable:** heatmap (layer × hop-type, colour =
  knockout Δlogit) + bar (hop × condition, y = % reversion) — matches §9 of design.md.
- **Quantitative anchors (Asta's ESTIMATES — hypotheses, not measured for us):** ROME peak AIE
  ~0.3–0.5 at mid-layers; Geva knockout Δlogit ~2–5, ~60–80% reversion for base recall; CaKE
  circuit ~10–15% of params, +20–30% portability. **Asta's guessed expectation for us:**
  ~60–80% reversion paraphrase, ~30–50% 1-hop, ~10–20% 2-hop → treat as a PRIOR to test, not a target.

## D. Confirm/deny relative to the literature (pre-state; feeds design.md §4)
- **Knockout REVERTS neighbours (localized):** confirms CaKE / Knowledge Circuits;
  conflicts with Geva-2021 (FFN key-value, distributed/redundant) & STEAM (layer-wise alignment).
- **Knockout DOESN'T revert (distributed):** confirms Geva-2021 redundancy & STEAM;
  conflicts with CaKE / circuits.
- **Reverts NEAR not FAR (hop-dependent):** the **novel two-graphs** outcome — partial confirm
  of both camps (localized near, distributed far). This is our target result.
- **Honest counter-evidence to respect:**
  - **Hase "Does Localization Inform Editing?"** — causal-tracing sites do NOT reliably predict
    edit success → a strong knockout edge might not actually mediate propagation. Watch for this.
  - **Geva 2021** — knowledge is redundantly stored; ablating one component may not revert
    (backup paths) → knockout non-reversion could be redundancy, not "no read." Control for it.
  - **Zhang 2024** — the "right" edge differs single- vs multi-hop → hop-resolution is necessary.

## Actions
1. Update `design.md` §2 (prior art) with the verdict + differentiator + the Hase/Geva-2021
   counter-evidence (they sharpen the confounds in §6).
2. **Independently verify** the key citations (Geva Dissecting Recall, Knowledge Circuits, CaKE,
   Hase, Function Vectors, and the 2025–26 items) before any goes in the deck/paper.
3. Adopt RippleEdits + knockout-Δlogit/%-reversion + the heatmap/bar figure.
4. Monitor Bau + Zhejiang (both could pivot to propagation circuits) — and since Bau = your lab,
   raise it directly with Arnab/Natalie (collaborate, don't race).
