# Researcher Tickets (R-)

### R-001 · Select real claim-classification corpus

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 2h
**Spent:** ~0.5h
**Closed:** 2026-06-14 — recommendation: PubMed-RCT (20k), HIGH confidence. See
agents/shared/findings.md → [R-001].

**Description:**
The claim classifier currently trains on 40 hardcoded synthetic sentences. To make
extraction real, pick a publicly available corpus of scientific sentences labeled by
rhetorical / discourse role that maps cleanly onto our 3 labels
(BACKGROUND / METHOD / CLAIM).

Evaluate at least these candidates and recommend one:

- **PubMed-RCT** (200k+ abstracts, sentences labeled BACKGROUND/OBJECTIVE/METHODS/
  RESULTS/CONCLUSIONS) — large, clean, on HuggingFace `datasets`. Biomedical only.
- **SciArg** — argumentative discourse in scientific papers (claims, evidence...).
  Closer to "claim" semantics; smaller; check license + availability.
- **ACL-ARC / CL-SciSumm / Dr. Inventor** — discourse/citation role corpora; check fit.

For each: size, label scheme, how it maps to BACKGROUND/METHOD/CLAIM, license,
availability via `datasets`, domain coverage (we want beyond biomedical if possible).

**Deliverable:** entry in `agents/shared/findings.md` with a recommendation, an explicit
label-mapping table, and a **confidence rating** (high/medium/low). The confidence
gates how E-002 opens (see O-002).

**Artifacts:**

- agents/shared/findings.md → "[R-001] Corpus selection"
- researcher/findings/ (raw notes, comparison table)

---

### R-002 · Select embedding + NLI models for graph construction

**Status:** closed
**Type:** research
**Priority:** medium
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Spent:** ~0.2h

**Description:**
E-003 needs (a) a sentence embedding model to find candidate claim pairs by similarity,
and (b) an NLI model to type edges as SUPPORTS / CONTRADICTS / RELATED. Pick lightweight,
CPU/MPS-friendly models that don't require a server.

**Closed:** 2026-06-14 — see agents/shared/findings.md → [R-002]. Embeddings:
`all-MiniLM-L6-v2`; NLI: `cross-encoder/nli-deberta-v3-small` (swapped at impl time to
`typeform/distilbert-base-uncased-mnli` — see decisions.md [E-003]). Confidence: HIGH.

---

### R-003 · Improve cross-domain claim extraction (LLM-based extractor)

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Closed:** 2026-06-14 — LLM extractor (claude-opus-4-8) scored macro-F1 **1.000** vs
DistilBERT's 0.571 on the OOD set. See findings.md [R-003] (incl. small-n /
shared-judgment caveats and the independent-label follow-up). Implemented in E-005.

**Description:**
E-002 showed the PubMed-RCT-trained DistilBERT transfers poorly to CS abstracts (OOD
macro-F1 0.571; collapses METHOD/CLAIM into BACKGROUND). The graph is consequently
noisy at the extraction layer. Investigate better claim extraction:

1. **LLM-based extractor (recommended to evaluate first).** Use Claude (the user has API
   credits — a natural fit) for few-shot sentence classification AND/OR direct claim
   extraction with structured output. Likely far better on CS text and domain-general.
   Compare cost/latency/quality against the DistilBERT baseline on the same 33-sentence
   OOD set (extend the OOD set to ~100 for a firmer number).
2. **Cheaper alternatives** if LLM cost is a concern: (a) add a small hand-labeled CS
   training set and fine-tune; (b) train on a CS-inclusive corpus (ACL-ARC / SciArg);
   (c) use a stronger encoder (SciBERT).

**Deliverable:** findings.md entry comparing approaches on the OOD set, with a
recommendation + confidence. If LLM-based wins, open an E- ticket to wire a
`ClaimTagger`-compatible LLM backend behind the existing `src/extraction/predict.py`
interface (so E-003 picks it up with no graph-code changes).

**Artifacts:**

- agents/shared/findings.md → "[R-003] ..."
- extend src/extraction/ood.py to a larger labeled set

---

### R-004 · Relation taxonomy + edge schema design

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Closed:** 2026-06-14

**Description:**
Define the relation set the LLM edge-typer emits and the directional/storage semantics.

**Outcome:** User confirmed the RICH taxonomy (7 labels): SUPPORTS, CONTRADICTS, REFINES,
ADDRESSES_SAME_PROBLEM (symmetric), USES, RELATED (symmetric), NONE (prune → no edge).
Directional A→B except the two marked symmetric. Stored edge fields: rel_type, direction,
confidence, rationale, similarity. Full table + rationale in findings.md [R-004] and
docs/llm-edge-typer-plan.md. Confidence HIGH (user-confirmed) → E-006 opens as implement.

---

### R-005 · Gold edge set + NLI-vs-LLM eval harness

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14

**Description:**
Build an honest evaluation for edge typing. Steps:

1. Sample ~40–60 candidate pairs from the current graph's `_candidate_pairs` output
   (real claim pairs, with source paper titles for context).
2. **Hand-label each pair with the R-004 taxonomy BEFORE the E-006 prompt is finalized** —
   this is the explicit guard against the R-003 shared-judgment trap. Store labels in a
   versioned file (e.g. src/graph/gold_edges.py or data/processed/gold_edges.jsonl).
3. `src/graph/eval_edges.py`: run both the NLI typer and the LLM typer on the gold pairs;
   report per-relation P/R/F1 and the headline **false-CONTRADICTS rate**.

**Deliverable:** findings.md [R-005] with the comparison + honest caveats (set size; and
that a single annotator wrote the labels — a truly independent number needs a second
labeler, ideally the user).

**Artifacts:**

- data/processed/gold_edges.jsonl (or gold_edges.py)
- src/graph/eval_edges.py
- agents/shared/findings.md → "[R-005] ..."

**Outcome (closed 2026-06-14):** User labeled all 37 pairs (genuinely independent — fixes
the R-003 caveat). Result: LLM **false-CONTRADICTS rate 0% vs NLI 16.7%** (bug fixed), but
exact-match low for both (LLM 0.135) — disagreement concentrated in REFINES/USES, which the
user assigns from paper-lineage domain knowledge and the LLM conservatively calls RELATED
without explicit textual evidence. Full analysis + follow-ups in findings.md [R-005].
Artifacts: src/graph/{sample_pairs,make_label_sheet,eval_edges}.py,
data/processed/{candidate_pairs,gold_pairs}.jsonl, gold_edges_sheet.md (user-filled).

**Closed:** 2026-06-14

---

### R-006 · Edge-relation data model + evidence-source framing

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16
**Closed:** 2026-06-16

**Description:**
Capture the architectural reframing surfaced in discussion: relations bind claim↔claim
(many-to-many across papers, not paper↔paper); evidence splits into a cited regime
(builds-on relations, evidence in the citance) and an uncited regime (parallel relations,
semantic comparison); therefore the edge typer should be hybrid and full-text is a
prerequisite for the cited half.

**Outcome:** findings.md [R-006] + docs/llm-edge-typer-plan.md → Architecture Evolution.
Spawns R-007 (source strategy) and E-009..E-012.

---

### R-007 · Full-text + citation-context source strategy

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16

**Description:**
Choose how to obtain full text + citances. Evaluate, with coverage/license/granularity:

1. **Semantic Scholar Graph API** — exposes per-citation `contexts` (citances) and `intents`
   (citation-function labels) already extracted across the corpus. Could eliminate most
   parsing AND give a citation-function baseline. Check: coverage of our OpenAlex papers,
   rate limits, whether contexts can be tied to our claim nodes, terms of use.
2. **GROBID on OA PDFs** — extracts structured full text + reference list from PDFs;
   universal but noisier; we'd do citance extraction + reference resolution ourselves.
3. **arXiv LaTeX source** — cleanest citation linking (`\cite`→`\bibitem`), CS-heavy,
   arXiv-only.

**Deliverable:** findings [R-007] recommendation + confidence; an estimate/measurement of
the cited-vs-uncited ratio in our data. Gates E-009/E-010 scope (how much we build vs reuse).

**Outcome (closed 2026-06-16):** Live S2 probes → **recommend Semantic Scholar Graph API**:
it ships citances (`contexts`) + intents + resolvable IDs, eliminating PDF/LaTeX parsing for
the edge-typer. Measured **47 intra-corpus citation edges (31 with citances)** vs 247
embedding pairs → hybrid worthwhile, union the two edge sets. E-009 decoupled/optional;
E-010 mostly done (src/graph/s2_citations.py); E-011 is the real remaining build. Full
detail + caveats in findings.md [R-007].

**Closed:** 2026-06-16
**Artifacts:** agents/shared/findings.md → "[R-007]"; src/graph/s2_citations.py;
data/processed/intra_corpus_citations.jsonl

---

### R-008 · Corpus construction strategy for relation density

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-20
**Updated:** 2026-06-20

**Description:**
E-011 found that strong typed relations (USES/REFINES) are sparse because the corpus is
**embedding-similarity-sampled** — papers co-occur as background/list citations, not as
build-on lineages. Investigate building the corpus by **citation-snowball** from a seed
paper (follow S2 references/citations N hops), and re-measure the cited-vs-uncited ratio and
the relation distribution. Hypothesis: citation-expanded corpora yield a denser USES/REFINES
idea-map than similarity-sampled ones. The corpus, not the typer, may be the real lever for
the "map of how ideas flow" vision.

**Deliverable:** findings [R-008] — comparison of relation density (similarity corpus vs
citation-snowball corpus) + a recommendation for how ingestion should assemble corpora.

**Artifacts:** agents/shared/findings.md → "[R-008] ..."; src/graph/expansion_probe.py.

**Outcome (closed 2026-06-20):** Sized via S2 reference sweep — corpus is missing the
field's foundational hubs (GCN 17×, GAT 13×, GraphSAGE 13×, …). Bounded backward
citation-snowball: ≥3 co-citation → +65 papers; ≥2 → +178 papers / ~518 edges (vs 47 today).
Recommend building it (start ≥3) → spawns E-013. Full numbers in findings.md [R-008].
**Closed:** 2026-06-20

---

### R-009 · Faceted edge taxonomy (umbrella + filterable sub-facets)

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-06-20
**Updated:** 2026-06-20
**Closed:** 2026-06-20

**Description:**
User design: keep the coarse umbrella relations (stable) and add a second filterable FACET
layer (sub-kind + free-text facet_detail) beneath, driven by research questions — rather than
flattening RELATED into more top-level labels.

**Outcome:** validated empirically (citance_typer extended with facets; 31 edges). Umbrella
stayed stable; RELATED → EXEMPLIFIES 11 / BACKGROUND 9 / COMPARES 3 / APPLICATION 2 with
crisp, queryable details. See findings.md [R-009]. Facet vocabulary is a starter set pending
purpose-pruning (which research-question filters matter) + a facet gold check. Schema impact
folded into E-012 (RELATES gains facet + facet_detail).

**Artifacts:** findings.md [R-009]; src/graph/citance_typer.py (faceted);
data/processed/cited_edges_typed.jsonl
