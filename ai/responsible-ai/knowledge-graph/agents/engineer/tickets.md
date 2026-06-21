# Engineer Tickets (E-)

### E-018 · Cross-paper idea canonicalization

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-06-21
**Updated:** 2026-06-21

**Description:**
Collapse the ~285 independently-generated per-paper idea tags into a shared canonical
vocabulary (~40 concepts) so idea filtering groups all related papers, not just exact-string
matches — and to enable idea-level gap detection later.
- `src/graph/idea_canon.py`: read distinct ideas from data/processed/paper_cards.jsonl,
  one claude-haiku-4-5 call mapping each raw tag → a canonical concept; write
  data/processed/idea_canon.json ({raw: canonical}). --model flag.
- `visualize.py`: map each node's ideas through it (keep raw `ideas` for display, add
  `canon` list for filtering); the `idea` datalist becomes the canonical concepts.
- `template.html`: idea filter matches on `canon`.

**Artifacts:** src/graph/idea_canon.py, data/processed/idea_canon.json,
src/graph/visualize.py, src/graph/template.html
**Closed:** 2026-06-21

### E-014 · Paper cards: per-paper summary + filterable idea tags

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-06-21
**Updated:** 2026-06-21

**Description:**
Give each paper a one-line "contribution" summary and a set of canonical idea tags,
surfaced in the explorer's right panel and usable as a graph filter.
- `src/graph/paper_cards.py` → `data/processed/paper_cards.jsonl`
  ({paper_id, summary, ideas:[...]}). Bulk model = claude-haiku-4-5 (--model flag,
  --limit sample, per the citance_typer convention). Evidence = paper title + the
  rationales/facet_details of edges where it is the CITED paper (how the community
  describes it). No hallucinated abstracts — grounded in citances only.
- `visualize.py` merges summary + ideas into node data; builds a datalist of all ideas.
- `template.html`: panel shows the summary + clickable idea chips; a new `idea` toolbar
  filter restricts the graph to papers carrying that idea (induced subgraph). Chips set
  the filter.

**Artifacts:** src/graph/paper_cards.py, data/processed/paper_cards.jsonl,
src/graph/visualize.py, src/graph/template.html
**Closed:** 2026-06-21

### E-015 · Field map: community detection cluster coloring

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-06-21
**Updated:** 2026-06-21

**Description:**
Color nodes by sub-area so the hairball reads as a labeled map. `visualize.py` runs
networkx greedy-modularity community detection on the undirected citation graph; assigns
each node a community id + palette color; labels each community by its most common idea
(from E-014). `template.html` adds a "clusters" toggle (swap node color → community
color) and a legend of community → top-idea labels. Free (no LLM).

**Artifacts:** src/graph/visualize.py, src/graph/template.html
**Closed:** 2026-06-21

### E-016 · Year time-lapse: animate graph growth chronologically

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-06-21
**Updated:** 2026-06-21

**Description:**
A play control in the explorer that sweeps the year filter from earliest→latest, revealing
nodes/edges as they appear, so the field's formation is visible. Reuses the existing year
filter; a current-year badge tracks progress; fits once at the end. Pure client-side JS in
template.html.

**Artifacts:** src/graph/template.html
**Closed:** 2026-06-21

### E-017 · Concept trends: idea adoption over time

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-06-21
**Updated:** 2026-06-21

**Description:**
When an idea is selected (idea filter or a clicked chip), show a small inline bar chart in
the panel of #papers-per-year carrying that idea, so its rise/fall is visible. Computed
client-side from node ideas + years (no server work). Lives in template.html.

**Artifacts:** src/graph/template.html
**Closed:** 2026-06-21

### E-001 · Ingestion: arXiv/OpenAlex → sentences with provenance

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 4h
**Spent:** ~1h

**Description:**
Build the ingestion layer in `src/ingestion/`. Given a query or a list of paper IDs,
fetch real papers from open sources and emit sentences with provenance.

Requirements:

- Source: **arXiv API** (abstracts + metadata; optionally full text via the arXiv
  bulk/HTML where available) and/or **OpenAlex API** (open, no key, rich metadata).
  Start with abstracts — they are reliably open and claim-dense — before attempting
  full-text PDF parsing.
- For each paper, capture metadata: `paper_id`, `title`, `authors`, `year`, `venue`,
  `source` (arxiv|openalex), `url`.
- Segment text into sentences (use a sentence segmenter — spaCy or a lightweight
  rule-based splitter; document the choice). Preserve section label where available
  (e.g. abstract).
- Emit one record per sentence with provenance:
  `{paper_id, section, sentence_index, char_start, char_end, text}`.
- Output: newline-delimited JSON to `data/processed/sentences.jsonl`; raw API
  responses cached under `data/raw/` so we don't re-hit the APIs.
- Be polite to the APIs: respect rate limits, set a descriptive User-Agent, cache.
- Type-annotated (global rule). A `python -m src.ingestion --query "graph neural networks" --limit 50`
  entry point that writes the jsonl.

**Acceptance:** running the entry point produces `data/processed/sentences.jsonl` with
real sentences and valid provenance for ≥50 papers; re-running uses the cache.

**Outcome (closed 2026-06-14):** Implemented OpenAlex source (keyless, polite pool,
abstract-inverted-index reconstruction, on-disk response cache), a rule-based sentence
segmenter with abbreviation guards, and a typed pipeline. `python -m src.ingestion
--query "graph neural networks" --limit 50` ingested **45 papers → 394 sentences** with
exact, contiguous char offsets. Spot-checked: abbreviation guard ("e.g.,") works,
provenance offsets valid. Started with abstracts (reliably open, claim-dense) rather
than full-text PDF parsing — that can be a later ticket.

**Artifacts:**

- src/ingestion/ (models.py, segment.py, sources.py, pipeline.py, __main__.py)
- data/processed/sentences.jsonl, data/processed/papers.jsonl
- agents/shared/decisions.md → "[E-001] Sentence segmentation & source choice"

**Closed:** 2026-06-14

---

### E-002 · Retrain + honestly evaluate the claim classifier on a real corpus

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 4h
**Spent:** ~1.5h

**Blockers:** none (R-001 closed HIGH; unblocked per O-002).
**Corpus (from R-001):** PubMed-RCT 20k, with label mapping
BACKGROUND/OBJECTIVE→BACKGROUND, METHODS→METHOD, RESULTS/CONCLUSIONS→CLAIM.

**Description:**
Replace the 40 synthetic training sentences in `claim-classifier/train.py` with the
corpus chosen in R-001. Keep the DistilBERT + linear-head architecture. Add:

- A proper train/val/**test** split (the current code has no held-out test set).
- Real evaluation: macro-F1 + per-class precision/recall + confusion matrix on the
  test set, **and** on a small hand-labeled sample of sentences drawn from E-001's
  real ingested output (out-of-distribution check — the honest test).
- Save the retrained model; record metrics in `decisions.md`. Do not overwrite the
  existing `claim_classifier.pt` until the new model is shown to be at least as good;
  save as `claim_classifier_v2.pt` and compare.

**Acceptance:** a written, honest eval — including where it fails — in decisions.md.
If real-text F1 is poor, that is a valid finding, not a failure to hide.

**Outcome (closed 2026-06-14):** Built `src/extraction/` (model, data loader, OOD set,
training, batch predict). Trained DistilBERT on 24k balanced PubMed-RCT sentences, 3
epochs, MPS. Honest eval:
- **In-domain (PubMed-RCT test, 30k):** accuracy 0.905, macro-F1 0.898. Strong.
- **OOD (33 hand-labeled CS sentences):** accuracy 0.606, macro-F1 0.571. The
  biomedical→CS gap R-001 flagged is real: METHOD recall 0.33, CLAIM recall 0.45 — the
  model collapses CS method/claim sentences into BACKGROUND (CS "we propose…" reads like
  PubMed OBJECTIVE→BACKGROUND).
This is a valid finding: the slice's extraction layer works in-domain but transfers
poorly to CS. The graph (E-003) is built on this with documented noise; a follow-up
ticket (R-003) covers improving cross-domain extraction. Full report:
`agents/engineer/workspace/e002_metrics.md`.

**Artifacts:**

- src/extraction/ (model.py, data.py, ood.py, train.py, predict.py)
- knowledge-graph/claim_classifier_v2.pt (gitignored)
- agents/engineer/workspace/e002_metrics.md
- agents/shared/decisions.md → "[E-002] Claim classifier eval (real corpus)"

**Closed:** 2026-06-14

---

### E-003 · Graph construction: claims as nodes, typed edges, Kùzu storage

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 6h
**Spent:** ~1.5h
**Closed:** 2026-06-14

**Blockers:** none (E-001, E-002 closed).

**Outcome:** Built `src/graph/` (store.py = Kùzu schema+CRUD, embed.py, edges.py,
build.py). Pipeline: classify 394 sentences → kept 73 CLAIMs (conf≥0.5) → MiniLM
embeddings → Kùzu nodes with provenance → 81 candidate pairs by cosine (top-5,
0.55≤sim<0.985) → NLI typed → edges. **Built ckg.kuzu: 35 papers, 73 claims, 81 edges.**
SUPPORTS edges look sound; some CONTRADICTS are spurious (general-domain NLI noise on
scientific text — flagged in R-002, addressed by R-003). Edges store the NLI score so
low-confidence ones can be filtered later.

**RCA (latent bug found during E-005 rebuild, 2026-06-14):** `GraphStore(fresh=True)`
called `shutil.rmtree(path)`, which assumes the DB path is a directory. The first build
passed only because the path didn't exist yet — Kùzu 0.11.3 actually creates `ckg.kuzu`
as a *file* (+ a `.wal` sibling), so the second build's cleanup raised
`NotADirectoryError`. Root cause: assumed Kùzu's on-disk layout without checking it.
Fix: `fresh=True` now removes the path whether file or dir, plus the `.wal`. Not a full
ticket re-open — one-line store fix verified by the successful rebuild.

**Description:**
Build `src/graph/`. Pipeline: ingested sentences → classify → keep CLAIMs → embed →
store as nodes in Kùzu with provenance → build typed edges.

- **Nodes:** `Claim {id, text, paper_id, section, char_start, char_end, embedding}`;
  `Paper {id, title, year, venue, url}`. Edge `Claim -[:FROM]-> Paper`.
- **Embeddings:** sentence-transformers (already feasible via transformers); document
  model choice in decisions.md.
- **Typed edges between claims:** candidate pairs by embedding similarity (top-k /
  threshold), then label each pair with an NLI model →
  `SUPPORTS` (entailment) / `CONTRADICTS` (contradiction) / `RELATED` (high sim, neutral).
  Store the NLI score on the edge.
- Persist to a Kùzu DB under `data/ckg.kuzu` (gitignored). Provide a `build_graph` entry
  point and an idempotent rebuild.

**Acceptance:** `data/ckg.kuzu` populated from real papers; a smoke query returns
claims + their edges. Report node/edge counts and a few spot-checked edges.

**Artifacts:**

- src/graph/
- agents/shared/decisions.md → embedding + NLI model choices

---

### E-004 · Query layer over the claim graph

**Status:** closed
**Type:** implement
**Priority:** medium
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 3h
**Spent:** ~0.5h
**Closed:** 2026-06-14

**Blockers:** none (E-003 closed).

**Outcome:** Built `src/query/` (search.py + CLI). `python -m src.query "<topic>"`
embeds the query, ranks claims by cosine, and prints each with provenance (title, year,
DOI) and its SUPPORTS/CONTRADICTS edges. Verified end-to-end: query "graph neural
networks for recommendation" returned relevant claims from the right papers with a
supporting edge. (Also surfaced a BACKGROUND-misclassified-as-CLAIM result — honest
visibility into the E-002 extraction gap.)

**Description:**
Build `src/query/`. A minimal interface to ask the graph questions:

- `python -m src.query "<topic or claim text>"` → embed the query, find the nearest
  claim nodes (Cypher + vector compare), and for each return: the claim, its source
  paper, and claims that SUPPORT / CONTRADICT it.
- Pretty-print results with provenance (paper title + year + url).
- Optional stretch: a tiny FastAPI endpoint wrapping the same query.

**Acceptance:** a real topic query returns claims with sources and supporting/
contradicting links, end to end, from real ingested papers.

**Artifacts:**

- src/query/

---

### E-005 · Wire LLM-based claim extractor into the build

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 2h
**Spent:** ~0.5h
**Closed:** 2026-06-14

**Blockers:** none (R-003 closed).

**Description:**
R-003 found a Claude-based extractor massively outperforms DistilBERT on CS text. Wire it
in behind the existing tagger interface so the graph build can use it with no other code
changes.

**Outcome:** Added `src/extraction/llm_predict.py` (`LLMClaimTagger`, batched structured
output, `claude-opus-4-8`) implementing the same `.tag()` interface as `ClaimTagger`. Added
`src/extraction/eval_ood.py` (the R-003 head-to-head). `src/graph/build.py` gained a
`--tagger {llm,distilbert}` flag (default `llm`) via a `_make_tagger` factory. Rebuilt
`ckg.kuzu` with the LLM tagger. Dependency: `anthropic==0.109.1` (pinned in
knowledge-graph/requirements.txt); needs `ANTHROPIC_API_KEY`.

**Artifacts:**

- src/extraction/llm_predict.py, src/extraction/eval_ood.py
- src/graph/build.py (--tagger flag)
- agents/shared/decisions.md → [E-005]; findings.md → [R-003]

---

### E-006 · LLMEdgeTyper (batched structured output)

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 3h

**Progress (2026-06-14):** Built `src/graph/llm_edges.py` (`LLMEdgeTyper`, batched
structured output, 7-label taxonomy + direction/confidence/rationale, few-shot prompt with
the failure case). Migrated `store.py` RELATES schema (added `direction`, `rationale`;
additive — existing graph still queryable). Smoke-tested on 6 real pairs: the
2008-GNN↔HetGNN/Pro-GNN pairs now type as REFINES (not CONTRADICTS), survey↔analysis as
RELATED, sensible directions/rationales, zero spurious CONTRADICTS. Remaining to close:
gold-set eval (R-005, awaiting user labels) to confirm quantitatively, then integration
(E-008).

**Blockers:** none (R-004 closed HIGH).
**Taxonomy (R-004):** SUPPORTS, CONTRADICTS, REFINES, ADDRESSES_SAME_PROBLEM (sym), USES,
RELATED (sym), NONE.

**Description:**
Build `src/graph/llm_edges.py` — a Claude-based edge typer mirroring `LLMClaimTagger`:

- `LLMEdgeTyper.type_pairs(pairs, contexts) -> list[dict]` returning per pair
  `{relation, direction, confidence, rationale}` with `relation` in the R-004 set ∪ NONE.
- Batched structured output (~10–15 pairs/request) via `output_config.format`; pass each
  claim pair WITH its source paper titles so the model can judge cross-paper relations.
- Few-shot prompt incl. the GraphRec↔2008-GNN pair as a NONE / ADDRESSES_SAME_PROBLEM
  exemplar. Model `claude-opus-4-8` (haiku for bulk).
- Schema migration in `store.py`: `RELATES` gains `direction STRING, rationale STRING`
  (keep `rel_type`, `score`→`confidence`, `similarity`); `add_relation` updated;
  backward-compatible with the NLI path.

**Acceptance:** typing the gold pairs (R-005) returns correct relations incl. NONE pruning;
the GraphRec↔2008-GNN pair is NOT CONTRADICTS.

**Artifacts:** src/graph/llm_edges.py, src/graph/store.py (schema), decisions.md [E-006]

---

### E-007 · Candidate-generation review + claim dedup

**Status:** open
**Type:** implement
**Priority:** medium
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 2h

**Description:**
Revisit `_candidate_pairs` now that the typer can emit NONE. (1) Dedup/merge near-identical
claims (repeated "we propose X" intros) rather than only skipping via DUP_THRESHOLD.
(2) Re-tune TOP_K / SIM_THRESHOLD for a recall/cost point that suits LLM typing, and
**log what's dropped** (no silent caps). (3) Reduce within-paper bias so cross-paper edges
surface.

**Artifacts:** src/graph/build.py, decisions.md [E-007]

---

### E-008 · Integrate `--edge-typer llm`, rebuild, verify

**Status:** blocked
**Type:** implement
**Priority:** high
**Created:** 2026-06-14
**Updated:** 2026-06-14
**Estimated:** 2h

**Blockers:** E-006 (typer), R-005 (eval should land first so we measure before committing).

**Description:**
Add `--edge-typer {nli,llm}` to `build.py` (factory mirroring `_make_tagger`, default `llm`
once R-005 confirms the win); thread the richer edge fields through to `store.add_relation`.
Rebuild `ckg.kuzu`. Verify Definition-of-Done (plan R0.4): GraphRec↔2008-GNN false edge
gone; spot-check new edges. Surface `rationale` in `src/query`; add optional
`--min-edge-confidence` filter.

**Artifacts:** src/graph/build.py, src/query/search.py, data/ckg.kuzu, CHANGELOG.md

---

### E-009 · Full-text ingestion (sections + sentences with provenance)

> **Re-scope (R-007, 2026-06-16):** the edge-typer no longer needs full-text parsing —
> Semantic Scholar supplies citances directly (E-010). E-009 is now DECOUPLED and OPTIONAL,
> valuable only as a separate enhancement for richer *claim extraction* from body text. The
> live edge path is E-010 (S2, mostly done) → E-011 (citance typer) → E-012 (hybrid). Deferred.

**Status:** open (deferred — optional enhancement, off the edge-typer critical path)
**Type:** implement
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16
**Estimated:** 6h

**Blockers:** R-007 (source choice).

**Description:**
Extend ingestion beyond abstracts: from the R-007-chosen source, produce per-paper full text
split into sections (related-work, methods, …) → sentences reusing the existing
`SentenceRecord` (paper_id, section, char offsets). Cache raw responses. Keep the abstract
path working (`--source abstract|fulltext`). This is the project's biggest single build —
PDF/LaTeX parsing (or S2 ingestion if R-007 picks it).

**Acceptance:** full-text sentences with valid provenance for ≥N papers; abstract path
unaffected.

**Artifacts:** src/ingestion/ (full-text path), decisions.md [E-009]

---

### E-010 · Citation linking (marker → reference → cited paper id)

> **Re-scope (R-007):** mostly DONE via `src/graph/s2_citations.py` — pulls S2 references
> with citances + intents and resolves intra-corpus links (47 edges →
> data/processed/intra_corpus_citations.jsonl). Remaining: package as a reusable ingestion
> step and decide handling for the 16/47 edges that lack citances (fall back to semantic).

**Status:** in-progress
**Type:** implement
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16
**Estimated:** 5h

**Blockers:** E-009.

**Description:**
Parse in-text citation markers (`[12]`, `\cite{...}`), link each to its reference-list entry,
and resolve that reference to a cited-paper id (OpenAlex/arXiv). Record each citance with its
location (section + sentence index) so it can be tied to the nearby claim. Largely provided
if R-007 selects Semantic Scholar (contexts already carry the cited paperId).

**Acceptance:** for a sample of papers, in-text markers resolve to correct cited-paper ids;
citances carry their location.

**Artifacts:** src/graph/ (citation linking), decisions.md [E-010]

---

### E-011 · Citance extraction + citation-context typer (cited relations)

> **Re-scope (R-007):** now the real remaining build, and inputs are ready
> (intra_corpus_citations.jsonl). Map each citance → our 7-label taxonomy
> (USES/REFINES/SUPPORTS) via the LLM, using the S2 intent (background/methodology/result)
> as a weak prior. Effectively unblocked (E-010 substantially done).

**Status:** closed
**Type:** implement
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16
**Estimated:** 4h

**Blockers:** E-010.

**Description:**
For each (citing claim near a citance, cited paper) link, type the relation as USES / REFINES
/ SUPPORTS using the **citance** as evidence (LLM, structured output), attaching
`evidence`=citance text + confidence. **Measure the cited-vs-uncited ratio** in real data
(the open unknown from R-006) and log it.

**Acceptance:** cited links typed with citance evidence; spot-check correct; ratio reported.

**Artifacts:** src/graph/citance_typer.py, decisions.md [E-011],
data/processed/cited_edges_typed.jsonl

**Outcome (closed 2026-06-20):** Built `src/graph/citance_typer.py` (LLM, batched structured
output, S2 intent as a prior). Typed the 31 citance-bearing edges (16 without citances →
semantic fallback in E-012). Distribution: **RELATED 25, USES 5, ADDRESSES_SAME_PROBLEM 1**.
Tested the multi-citance lever (17/31 edges have >1 citance; fed up to 4) — distribution barely
moved (USES 4→5), so RELATED-dominance is the DATA, not truncation. **Finding: even cited
intra-corpus links in this similarity-sampled GNN corpus are ~80% background/list mentions, not
"builds-on."** Rationales well-grounded. Implication: **corpus construction** (citation-snowball
from a seed vs embedding-similarity search) is the real lever for a USES/REFINES-rich map →
candidate R-008.

---

### E-012 · Hybrid edge typer (cited ∪ uncited), rebuild, verify

> **Re-scope (R-007):** also add citation links (intra_corpus_citations.jsonl) as candidate
> pairs in their own right — they are a *different* edge set from the embedding-similar pairs
> (measured: 47 citation edges vs 247 embedding pairs), so the graph unions both.
>
> **Re-scope (R-009):** edges now carry a faceted label — `rel_type` (umbrella) + `facet` +
> `facet_detail`. Extend `store.py` RELATES with `facet STRING, facet_detail STRING`; thread
> these through `add_relation` and surface them in `src/query` as filters. The semantic typer
> (E-006) should also emit facets for parity (currently only the citance typer does).

**Status:** blocked
**Type:** implement
**Priority:** high
**Created:** 2026-06-16
**Updated:** 2026-06-16
**Estimated:** 3h

**Blockers:** E-011, E-006.

**Description:**
Merge the citation-context typer (cited) with the semantic typer (uncited) into one edge set;
reconcile/dedup when both fire on the same pair; store `evidence` provenance (citance |
semantic) on each edge. Rebuild `ckg.kuzu`; verify against the gold set + spot-check;
surface evidence in `src/query`.

**Acceptance:** hybrid graph built; edges carry evidence provenance; gold-set + spot-check OK.

**Artifacts:** src/graph/build.py (hybrid), src/query/, data/ckg.kuzu, CHANGELOG.md

---

### E-013 · Citation-snowball corpus expansion (build)

**Status:** closed (phases ≥3 and ≥2 both done, 2026-06-20)
**Type:** implement
**Priority:** high
**Created:** 2026-06-20
**Updated:** 2026-06-20
**Estimated:** 5h

**Blockers:** none (R-008 closed with sizing).

**Description:**
Grow the corpus along its citation backbone (R-008): add referenced papers cited by ≥N
corpus papers (N=3 → +65; N=2 → +178), backward (references) first. Steps:
1. From the S2 reference sweep (expansion_probe), select referenced papers ≥N co-citations;
   resolve to OpenAlex/arXiv ids.
2. Ingest their abstracts (OpenAlex/S2) → sentences with provenance; extract claims (existing
   LLM tagger). New `Paper` + `Claim` nodes.
3. Re-pull intra-corpus citations + citances over the expanded corpus (s2_citations.py).
4. Rebuild the graph (E-012 hybrid) and re-measure: cited-vs-uncited ratio, umbrella + facet
   distributions, USES/REFINES density — confirm the lineage filled in.

**Acceptance:** expanded corpus (≥110 or ≥223 papers); citation backbone ~10× denser;
report shows richer USES/REFINES + facet distribution than the 45-paper baseline.

**Planned phases:** (1) ≥3 expansion (+65, current, user-chosen) → measure. (2) **widen to
≥2** (+178 total, ~518 edges) once ≥3 proves out (user request 2026-06-20). The
`--min-cocite` flag makes phase 2 a re-run at threshold 2 (idempotent; skips papers already
added).

**Artifacts:** src/graph/ (expansion build), data/processed/, data/ckg.kuzu, decisions.md [E-013]

**Phase 1 outcome (≥3, 2026-06-20):** +35 hubs (corpus 45→80; 30 skipped — no S2 abstract).
Citation edges **47→419**, citances **31→328**, **USES 5→114, REFINES 0→10**, facets 4→9.
Decisive validation that corpus construction is the lever. Tooling:
expansion_probe.py, expand_corpus.py, generalized s2_citations.py (DOI/arXiv/CorpusId).

**Phase 2 outcome (≥2):** +48 papers (corpus 80→128). Final progression 45→80→128:
citation edges 47→419→**919**, USES 5→114→**250**, REFINES 0→10→**19**, all 10 facets fire.
Tooling hardened (pre-skip, fail-fast, flush). **Closed.** Next: E-012 hybrid build over the
128-paper graph. Coverage caveat: ~83/178 ≥2 candidates had S2 abstracts.
