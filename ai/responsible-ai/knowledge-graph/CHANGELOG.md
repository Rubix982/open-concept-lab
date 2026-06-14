# Changelog

## 2026-06-14 · Session 1

- [O-001] Initialized claim-knowledge-graph vertical-slice subproject — plan.md,
  agentic structure, shared surfaces in agents/
- [E-000] Storage decision: Kùzu (embedded Cypher graph DB) — agents/shared/decisions.md;
  kuzu==0.11.3 installed + pinned in ai/responsible-ai/requirements.txt
- Opened R-001 (corpus selection) and E-001 (ingestion) for Phase 1; E-002/E-003/E-004
  opened as blocked per dependency graph
- [E-001] Ingestion working — OpenAlex → 45 papers → 394 sentences w/ provenance — src/ingestion/
- [R-001] Corpus selected: PubMed-RCT 20k (HIGH confidence) + label mapping — findings.md
- [O-002] Confidence-gated E-002 open (HIGH → normal implement)
- [R-002] Embedding (all-MiniLM-L6-v2) + NLI model selected — findings.md
- [E-002] Classifier retrained on PubMed-RCT — in-domain F1 0.898, **OOD F1 0.571**
  (honest cross-domain gap) — src/extraction/, workspace/e002_metrics.md
- [E-003] Claim graph built in Kùzu — 35 papers, 73 claims, 81 typed edges — src/graph/, data/ckg.kuzu
- [E-004] Query layer working end-to-end — src/query/
- [O-003] Opened R-003 (LLM-based extraction) — top-priority quality fix; slice complete
- Env fixes: kuzu installed/pinned; worked around `datasets` (Python 3.14.0+ / PEP-440)
  and absent sentencepiece by using `transformers` directly + WordPiece models
- [R-003] LLM extractor (claude-opus-4-8) vs DistilBERT on OOD CS set: **macro-F1 1.000
  vs 0.571** — findings.md (with small-n / shared-judgment caveats)
- [E-005] Wired LLMClaimTagger behind the `.tag()` interface; `build.py --tagger llm`
  (default) — src/extraction/llm_predict.py, eval_ood.py; graph rebuilt with LLM tagger
- Dep: anthropic==0.109.1 (knowledge-graph/requirements.txt); needs ANTHROPIC_API_KEY
