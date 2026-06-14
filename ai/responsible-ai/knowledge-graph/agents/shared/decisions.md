# Decisions (owned by Engineer — append-only)

## [E-000] Decision: Graph storage engine

_Date: 2026-06-14_

**Decision:** Use **Kùzu** (embedded property-graph DB, Cypher query language) for
claim/edge storage.
**Rationale:** "SQLite for graphs" — a single file on disk, no server, native Python
bindings, fast columnar storage, MIT-licensed. Gives a real query layer (slice step 4)
and room to grow past the slice. Cypher is the more broadly transferable property-graph
query language.
**Alternatives rejected:**
- NetworkX — in-memory library, not a DB; persistence is pickle; weak query layer.
- Neo4j — full server (JVM/Docker), overkill for a single-machine slice.
- Gremlin / TinkerPop (TinkerGraph) — Gremlin is a traversal language, not a DB; the
  lightweight backend is JVM-based and needs a Gremlin Server for Python access. Too
  much infra for the payoff here.
**Revisit if:** the corpus outgrows a single machine, or multi-writer / concurrent
serving becomes a requirement.

## [E-001] Decision: Sentence segmentation & ingestion source

_Date: 2026-06-14_

**Decision:** (1) Ingest from **OpenAlex abstracts** first, not full-text PDFs.
(2) Use a **rule-based sentence segmenter** with an abbreviation guard, not spaCy/nltk.
**Rationale:**
- OpenAlex is fully open, keyless, has clean metadata, and abstracts are the most
  claim-dense, reliably-available text. Full-text PDF parsing is a separate, noisier
  problem we don't need for the slice.
- spaCy/nltk are not in the venv and add weight; abstracts are well-punctuated, so a
  guarded regex splitter is adequate. Verified on real output: "e.g.," etc. handled.
**Alternatives rejected:** spaCy `en_core_web_sm` (extra dep + model download for
marginal gain on clean abstracts).
**Revisit if:** we ingest full text (PDF/LaTeX), where segmentation is much harder and
a real model-based segmenter will be worth the dependency. The `split_sentences`
interface is stable, so swapping the implementation is low-cost.

## [E-002] Decision: Load PubMed-RCT from source, not the `datasets` library

_Date: 2026-06-14_

**Decision:** Download PubMed-RCT raw text files from the source GitHub repo
(`Franck-Dernoncourt/pubmed-rct`, `PubMed_20k_RCT/{train,dev,test}.txt`) and parse them
directly, instead of `load_dataset('armanc/pubmed-rct20k')`.
**Rationale:** The venv's Python reports `3.14.0+` (a non-final build with a `+` local
suffix). `packaging.version.parse` correctly rejects `"3.14.0+"` as non-PEP-440, and
`datasets` calls it at import time → `InvalidVersion`, so `datasets` cannot be imported
at all. `torch` 2.12 (MPS OK) and `transformers` 5.8.1 import fine. The raw files are a
trivial `LABEL\tsentence` format (verified), so parsing them removes a broken, heavy
dependency rather than fighting the version string.
**Alternatives rejected:** recreating the venv on a stable Python (would risk the
existing responsible-ai tooling, e.g. manim); monkeypatching `platform.python_version`
(fragile).
**Revisit if:** the venv moves to a released Python and we want `datasets` streaming for
the full 200k set.

## [E-003] Decision: Embedding + NLI via `transformers` directly; NLI model swap

_Date: 2026-06-14_

**Decision:** Run both the embedding model and the NLI model through `transformers`
directly, and use **`typeform/distilbert-base-uncased-mnli`** for NLI instead of the
R-002 pick `cross-encoder/nli-deberta-v3-small`.
**Rationale:**
- `sentence-transformers` transitively imports `datasets` at import time → same
  `InvalidVersion('3.14.0+')` crash as [E-002]. So we replicate all-MiniLM-L6-v2 with
  `transformers` (mean-pool + L2-normalize) — identical output, no broken dependency.
- DeBERTa-v3 tokenizer needs `sentencepiece`, which is **not installed** in this venv.
  `typeform/distilbert-base-uncased-mnli` uses WordPiece (already present), is small, and
  outputs the same 3 NLI classes. We read `config.id2label` so logit order isn't
  hard-coded.
**Alternatives rejected:** installing sentencepiece + protobuf (extra native deps for a
slice); roberta-large-mnli / bart-large-mnli (heavier, no quality need here).
**Revisit if:** edge precision is poor — a larger/scientific NLI model may help, and the
`type_pairs` interface is stable so swapping is cheap.

## [E-005] Decision: LLM-based claim extractor as the default

_Date: 2026-06-14_

**Decision:** Make a Claude-based classifier (`claude-opus-4-8`) the default claim tagger;
keep the DistilBERT tagger selectable.
**Rationale:** R-003 measured macro-F1 1.000 (Claude) vs 0.571 (DistilBERT) on the OOD CS
set — the biomedical→CS transfer gap that made the graph noisy is gone. The LLM is
domain-general, needs no training corpus, and required no graph-code changes:
`LLMClaimTagger` implements the same `.tag(texts) -> [(label, conf)]` interface as
`ClaimTagger`, and `build.py --tagger {llm|distilbert}` selects between them (default `llm`).
**Model choice:** `claude-opus-4-8` to set the quality ceiling for the comparison;
`claude-haiku-4-5` is the cheaper bulk option. Batched structured output (~15 sentences
per request) via `output_config.format` keeps requests few.
**Cost note:** the LLM tagger calls the Claude API (bills the `ANTHROPIC_API_KEY` account)
— intended use of the research credits. DistilBERT remains the zero-marginal-cost,
offline fallback.
**Revisit if:** the expanded/independent-label OOD eval (R-003 follow-up) shows the gap is
smaller than 1.000 vs 0.571 suggests, or if per-run API cost matters → switch to haiku or
distill the LLM's labels back into a fine-tuned small model.

## [E-006] Decision: LLM edge typer + RELATES schema migration

_Date: 2026-06-14_

**Decision:** Add `LLMEdgeTyper` (Claude, `claude-opus-4-8`) typing claim pairs with the
R-004 rich taxonomy via batched structured output, and migrate the Kùzu `RELATES` edge to
carry `direction` and `rationale` (added to existing `rel_type`, `score`, `similarity`).
**Rationale:** the general-domain NLI typer can't emit NONE (prune) or name relations
beyond 3 NLI classes, causing the false-CONTRADICTS failure. The LLM does both; pairs are
typed with their source paper titles for cross-paper judgment. Schema change is additive
so the current NLI-built graph stays queryable until E-008 rebuilds.
**Eval gating:** quantitative confirmation deferred to R-005 (user-labeled gold set) to
keep the eval independent (avoids the R-003 shared-judgment caveat). Qualitatively
confirmed by smoke test: false CONTRADICTS gone.
**Revisit if:** R-005 shows the LLM doesn't beat NLI on relation accuracy / false-
CONTRADICTS rate, or cost matters → haiku for bulk.
