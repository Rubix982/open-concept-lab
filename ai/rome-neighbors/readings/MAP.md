# Literature Map — my slice

_Personal, living. NOT the whole tree — the pruned subtree I've vetted and can
navigate by. Breadth discovery lives in tools (Connected Papers, Semantic
Scholar, Research Rabbit, Asta); this map is the **depth I've earned** and the
index I return to._

_Source pool: `readings/ndif/research_papers.md` (NDIF corpus) + Asta reviews +
`design.md §2`. Last grown: 2026-08-11._

---

## How this map grows (convention — keep it consistent)

- Add a paper **only after I've vetted what it gives me** — not on seeing a title.
- Each entry: **Title** (author, venue/yr) — one line: *what it gives me / when to cite it*.
- **Tags:** `[foundation]` `[benchmark]` `[predictor]` `[outcome/mechanism]`
  `[near-miss]` `[tool]` `[critique]`.
- **Confidence:** `✓` read/verified · `~` second-hand (Asta/abstract) · `?` claimed, unverified.
- **Place it in the lineage:** what it branches FROM, what branches from IT.
- **Note the edge to my work:** `→ used in E-00x` / `→ differentiate from` / `→ adopt method`.
- When a paper changes the plan, that's an *edge*, not just an entry. Record the edge.

---

## The lineage (the tree)

```
FFN-as-memory (why editing is even possible)
  ✓ Geva 2020  FF layers are key-value memories            [foundation]
  ✓ Geva 2022  FFN promotes concepts in vocab space         [foundation]
  ✓ Dai 2021   Knowledge Neurons                            [foundation]
     │
     └── LOCATE-AND-EDIT
         ✓ Meng 2022  ROME (causal tracing + rank-1 edit)   [foundation] → our edit primitive
         ✓ Meng 2023  MEMIT (mass editing, multi-layer)     [foundation] → breadth axis (T-008)
         ~ Sen Sharma  Editing Factual Assoc. in Mamba       [foundation]  ← ARNAB (reviewer)
         ✓ Mitchell 2021 MEND (hypernetwork editor)          [foundation]
         ✓ Mitchell 2022 SERAC / ~WISE 2024 / ✓GRACE 2022    [foundation]  retrieval/side-memory editing
            │
            ├── CRITIQUE
            │    ✓ Hase 2023  localization ≠ editability      [critique] → §10 adversary
            │    ~ Liu 2024/25 relation-focused recall        [critique]  subject-bias → over-propagation
            │
            ├── RIPPLE / PROPAGATION (editing fails downstream)
            │    ✓ Cohen 2023  RippleEdits (6 criteria)       [benchmark] → E-007 data
            │    ✓ Zhong 2023  MQuAKE (multi-hop)             [benchmark] → v2 outcome
            │    ~ Back Attention (multi-hop logit prop.)     [outcome/mechanism]
            │
            └── GEOMETRY (what predicts propagation)  ← MY BRANCH
                 ~ Nishi 2024  Representation Shattering       [predictor]  distance→shattering (not propagation)
                 ~ Kim 2025    Bilinear structure→propagation  [predictor] → adopt (structured), E-009
                 ~ Jeong 2025  STEAM alignment→propagation     [predictor] → adopt (alignment), E-009
                 ~ Huang 2025  key-space coupling (multi-probe)[predictor]  closest multi-probe
                    │
                    └── MY NODE (unclaimed combination):
                        hop-resolved + CAUSAL(IIA) predictor of EDIT propagation
                        assembles: geometry-branch + causal metric + hop-resolution

Adjacent methods / benchmarks (borrow, don't compete)
  ~ SLAQ  similarity predicts factual consistency (~78%)     [near-miss] → nearest method; cite+differ
  ~ RAVEL + ✓DAS  hop-clean factual disentanglement          [benchmark] → maybe cleaner than RippleEdits
  ✓ Todd 2024  Function Vectors (relations as vectors)       [predictor] NNsight-native structured basis
  ✓ Marks  Geometry of Truth (truth directions)              [adjacent]  representation-geometry method
  ✓ lookback/belief tracking (ToM, OID co-location)          [adjacent]  where this journey started

Tooling spine
  ✓ NNsight / NDIF (Fiotto-Kaufman 2025)  internals access   [tool]
  ✓ EasyEdit  ROME/MEMIT/MEND harness                        [tool]  portability aggregate → stratify by hop
  ✓ Ecco  CKA/SVCCA/PWCCA on hidden states                  [tool]  (Kornblith ref = fallback)
  ✓ pyvene  standardized interventions                       [tool]
  ✓ Yao 2023  Editing LLMs: survey                           [foundation]  the field map
```

---

## Reference-for-X index (the "want to do X → cite Y")

| I want to… | Reference |
|------------|-----------|
| edit a fact | ROME (Meng 2022) / MEMIT (Meng 2023) / EasyEdit (tool) |
| the ripple/portability benchmark | RippleEdits (Cohen 2023) / MQuAKE (Zhong 2023) |
| hop-clean factual disentanglement | RAVEL (+ DAS) |
| a **structured** predictor | Kim bilinear / Function Vectors (Todd) / Huang key-space |
| an **alignment** predictor | Jeong STEAM |
| the geometry ↔ edit-damage link | Nishi Representation Shattering |
| the nearest method (similarity→consistency) | SLAQ |
| the "localization ≠ editability" caution | Hase 2023 |
| multi-hop propagation mechanism | Back Attention |
| retrieval-based editing contrast | GRACE / WISE / SERAC |
| why editing is possible (MLP memory) | Geva 2020/2022, Dai 2021 |
| the field overview | Yao 2023 survey |
| internals access / interventions | NNsight/NDIF, pyvene |

---

## The open frontier (my lane)

Unclaimed combination (confirmed vs Asta ×3 + full NDIF corpus): **a hop-resolved,
CAUSAL (IIA) predictor comparing raw-distance vs structured-geometry vs alignment
for EDIT propagation.** Differentiate from: SLAQ (consistency, not edits; aggregate),
Kim/Jeong (aggregate, behavioural, no causal), Nishi (shattering, not propagation).
Novelty = the *combination*, not the parts. Openness confirmable only by Arnab.

## Nearest people

Bau lab (ROME/MEMIT/tracing/RippleEdits/NDIF) · **Arnab Sen Sharma** (MEMIT;
Mamba editing) — prospective reviewer · Geva (RippleEdits; FFN-as-memory) ·
Zhong/Chen, Princeton (MQuAKE).
