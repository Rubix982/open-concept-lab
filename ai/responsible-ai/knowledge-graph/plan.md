# Project: Claim Knowledge Graph (Vertical Slice)

_Last updated: 2026-06-14 by O-001_

## Objective

Feed real research papers in; get a queryable claim graph out — **claims as nodes**,
**typed edges** (supports / contradicts / refines), every node carrying **provenance**
back to its source sentence in a real paper. One honest end-to-end vertical slice,
not five half-built layers.

Done looks like: `python -m src.query "<topic>"` returns claims on that topic, their
source papers, and which other claims support or contradict them.

## Current Phase

Phase 5 — LLM edge-typer (docs/llm-edge-typer-plan.md), now evolved into a **hybrid
citation-context + semantic** design (Architecture Evolution section; findings.md [R-006]).
The abstract-only typer (E-006) works and kills false-contradictions but falls back to
RELATED because the "builds-on" evidence lives in citances, not abstracts. Real arc:
R-007 (source) → E-009 (full-text) → E-010 (citation linking) → E-011 (citance typer) →
E-012 (hybrid merge). E-008 = optional interim ship of the abstract-only typer.

## Architecture (the four-step slice)

1. **Ingestion** — arXiv + OpenAlex (open APIs, fits the consent/open-data principle)
   → parsed sentences with provenance `(paper_id, section, char_offset)`.
2. **Extraction** — the existing DistilBERT claim classifier, **retrained on a real
   scientific-discourse corpus** (not the 40 synthetic sentences) and **honestly
   evaluated** — we currently do not know if it works on real text.
3. **Graph** — sentences classified `CLAIM` become nodes (with embedding + provenance);
   typed edges built via NLI entailment + embedding similarity; stored in **Kùzu**
   (embedded property-graph DB, Cypher, no server).
4. **Query** — a minimal CLI/API: "what claims exist about X, and what supports or
   contradicts them," with sources.

## Storage decision

**Kùzu** (embedded, file-based, Cypher). See `agents/shared/decisions.md → [E-000]`.
Gremlin/TinkerPop considered and rejected for this slice (requires a JVM server;
too much infra for a single-machine month-scale build).

## Active Tickets

| ID    | Agent      | Title                                              | Status      |
| ----- | ---------- | -------------------------------------------------- | ----------- |
| O-001 | Orchestrator | Initialize knowledge-graph subproject            | closed      |
| R-001 | Researcher | Select real claim-classification corpus            | closed      |
| R-002 | Researcher | Select embedding + NLI models                       | closed      |
| E-001 | Engineer   | Ingestion: arXiv/OpenAlex → sentences w/ provenance | closed      |
| E-002 | Engineer   | Retrain + honestly evaluate claim classifier       | closed      |
| E-003 | Engineer   | Graph construction (nodes, typed edges, Kùzu)      | closed      |
| E-004 | Engineer   | Query layer over the claim graph                   | closed      |
| R-003 | Researcher | Improve cross-domain claim extraction (LLM-based)   | closed      |
| E-005 | Engineer   | Wire LLM-based claim extractor into the build        | closed      |
| O-004 | Orchestrator | Sequence the LLM edge-typer effort               | in-progress |
| R-004 | Researcher | Relation taxonomy + edge schema design (RICH set)   | closed      |
| R-005 | Researcher | Gold edge set + NLI-vs-LLM eval harness             | open        |
| E-006 | Engineer   | LLMEdgeTyper (batched structured output)            | in-progress |
| E-007 | Engineer   | Candidate-gen review + claim dedup                  | open        |
| E-008 | Engineer   | Integrate --edge-typer llm, rebuild, verify (interim)| open       |
| R-005 | Researcher | Gold edge set + NLI-vs-LLM eval                      | closed      |
| O-005 | Orchestrator | Sequence the hybrid full-text edge-typer arc      | in-progress |
| R-006 | Researcher | Edge-relation data model + evidence-source framing  | closed      |
| R-007 | Researcher | Full-text + citation-context source strategy        | open        |
| E-009 | Engineer   | Full-text ingestion (sections + sentences)          | blocked     |
| E-010 | Engineer   | Citation linking (marker → reference → cited id)    | blocked     |
| E-011 | Engineer   | Citance extraction + citation-context typer (cited) | blocked     |
| E-012 | Engineer   | Hybrid edge typer (cited ∪ uncited), rebuild        | blocked     |

## Blocked

| ID    | Blocked By   |
| ----- | ------------ |
| E-002 | R-001        |
| E-003 | E-001, E-002 |
| E-004 | E-003        |

## Completed This Session

- O-001 · Initialized subproject: agentic structure, venv check, Kùzu installed + pinned
- E-001 · Ingestion: OpenAlex → 45 papers → 394 sentences with provenance
- R-001 · Corpus selected: PubMed-RCT 20k (HIGH) + label mapping
- O-002 · Confidence-gated E-002 (high → normal implement)
- R-002 · Embedding + NLI models selected (HIGH)
- E-002 · Classifier retrained; honest eval (in-domain F1 0.898, OOD F1 0.571)
- E-003 · Claim graph built in Kùzu: 35 papers, 73 claims, 81 typed edges
- E-004 · Query layer working end-to-end (semantic search + provenance + edges)
- R-003 · LLM extractor beats DistilBERT on CS: OOD macro-F1 1.000 vs 0.571
- E-005 · Wired LLMClaimTagger (claude-opus-4-8) into build; graph rebuilt with it

## Slice result (the artifact)

`python -m src.ingestion --query "<topic>"` → `python -m src.graph.build` →
`python -m src.query "<topic>"` returns claims, their source papers, and supporting/
contradicting claims. End-to-end on real papers.

## Known limitations (honest)

1. **Extraction: SOLVED for CS** via the LLM tagger (R-003/E-005): OOD macro-F1 went
   0.571 (DistilBERT) → 1.000 (claude-opus-4-8). Caveats: small eval set (n=33) with
   shared labeler/rubric judgment — needs an independent ~100-sentence eval to confirm.
   DistilBERT remains the offline/zero-cost fallback (`--tagger distilbert`).
2. **NLI edge typing is still noisy** on scientific text — some spurious CONTRADICTS.
   Scores are stored so edges can be filtered; an LLM- or scientific-NLI-based edge
   typer is the next obvious upgrade (mirrors what R-003 did for extraction).
3. **Abstracts only** — full-text ingestion (PDF/LaTeX) is future work.

## Next Orchestrator Action

**Run R-007 (full-text + citation-context source strategy)** — it decides build-vs-reuse for
the entire hybrid arc (Semantic Scholar may ship citances + intents and shrink E-010). If a
quick win is wanted first, ship E-008 (abstract-only LLM typer) as an interim improvement.
Still-open earlier items: independent-label OOD eval (R-003 follow-up); E-007 claim dedup.
