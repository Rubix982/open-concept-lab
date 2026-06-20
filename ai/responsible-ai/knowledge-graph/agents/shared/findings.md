# Findings (owned by Researcher — append-only)

## [R-001] Finding: Real claim-classification corpus selection

_Date: 2026-06-14_

**Recommendation: PubMed-RCT (the 20k-abstract version) for E-002.**

Sequential-sentence-classification corpus of biomedical RCT abstracts; each sentence
labeled by rhetorical role. Readily loadable via HuggingFace `datasets` (mirrors:
`armanc/pubmed-rct20k`, `pietrolesci/pubmed-200k-rct`). The 20k version (~180k
sentences) is plenty for fine-tuning DistilBERT and far faster to iterate on than the
2.3M-sentence full set.

**Label mapping (PubMed-RCT → our 3-class scheme):**

| PubMed-RCT label | → our label  | rationale                                      |
| ---------------- | ------------ | ---------------------------------------------- |
| BACKGROUND       | BACKGROUND   | context / prior work                           |
| OBJECTIVE        | BACKGROUND   | motivation / aim — not a finding or a method   |
| METHODS          | METHOD       | direct match                                   |
| RESULTS          | CLAIM        | the findings the paper asserts                 |
| CONCLUSIONS      | CLAIM        | the claims/contributions drawn from results    |

**Alternatives rejected:**
- **SciArg** — semantically closer to "claim," but span-level brat annotations over
  full texts, unclear license/download, no ready loader. Too much integration friction
  for the slice. Revisit if we later want true claim/evidence *relations* (could inform
  edge typing in E-003).
- **SciARK** — multidisciplinary Claim/Evidence but small, SDG-themed; narrow.

**Confidence: HIGH** — on availability, cleanliness, and label mapping.

**Documented risk (for E-002 to measure, not ignore):** PubMed-RCT is biomedical;
E-001 ingested CS/ML abstracts. Training biomedical → testing on CS is a genuine
out-of-distribution gap. Rhetorical roles (background/method/result) are fairly
domain-general, so transfer *may* hold — but E-002 must prove it with an OOD eval on a
hand-labeled sample of real ingested CS sentences, not just the in-domain test set.

Sources:
- [PubMed 200k RCT (arXiv:1710.06071)](https://arxiv.org/abs/1710.06071)
- [armanc/pubmed-rct20k · HuggingFace](https://huggingface.co/datasets/armanc/pubmed-rct20k)
- [pietrolesci/pubmed-200k-rct · HuggingFace](https://huggingface.co/datasets/pietrolesci/pubmed-200k-rct/viewer)
- [SciArg / Full-Text Argumentation Mining (arXiv:2210.13084)](https://arxiv.org/pdf/2210.13084)

## [R-002] Finding: Embedding + NLI models for graph construction

_Date: 2026-06-14_

**Embeddings: `all-MiniLM-L6-v2`** (sentence-transformers). 384-dim, ~22M params, fast
on CPU/MPS, the standard high-quality-for-size default for semantic similarity. Good
enough to find candidate claim pairs; we are not doing fine-grained retrieval ranking.

**NLI (edge typing): `cross-encoder/nli-deberta-v3-small`** (sentence-transformers
CrossEncoder). Outputs 3 logits `[contradiction, entailment, neutral]` for a sentence
pair. Cross-encoder (joint encoding of both sentences) is more accurate than
bi-encoder for entailment, and small enough to run over candidate pairs only (not all
pairs). Maps to our edges: entailment→SUPPORTS, contradiction→CONTRADICTS,
neutral(but high similarity)→RELATED.

**Why pair similarity *then* NLI:** NLI over all O(n²) pairs is too expensive; embedding
similarity cheaply narrows to top-k candidates per claim, then NLI types only those.

**Confidence: HIGH** — both are small, well-established, no server. Caveat: NLI models
are trained on general text (MNLI/FEVER/ANLI), so on scientific claims edge precision is
uncertain — E-003 should spot-check a sample of typed edges and store the NLI score so
low-confidence edges can be filtered.

Sources:
- [all-MiniLM-L6-v2 · HuggingFace](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [cross-encoder/nli-deberta-v3-small · HuggingFace](https://huggingface.co/cross-encoder/nli-deberta-v3-small)

## [R-003] Finding: LLM-based claim extraction beats DistilBERT on CS text

_Date: 2026-06-14_

**Recommendation: use a Claude-based extractor (`claude-opus-4-8`) as the default claim
classifier.** Head-to-head on the 33 hand-labeled OOD CS sentences:

| Tagger | macro-F1 | accuracy | METHOD recall | CLAIM recall |
| ------ | -------- | -------- | ------------- | ------------ |
| DistilBERT (PubMed-RCT) | 0.571 | 0.606 | 0.333 | 0.455 |
| **Claude (claude-opus-4-8)** | **1.000** | **1.000** | **1.000** | **1.000** |

The LLM has no biomedical domain bias and classifies CS method/claim sentences correctly
where DistilBERT collapsed them into BACKGROUND.

**Confidence: medium-high.** The win is unambiguous, but two honest caveats:
1. **Small eval set (n=33).** Not a robust estimate.
2. **Shared-judgment circularity.** The same engineer hand-labeled the OOD set and wrote
   Claude's rubric, using the same conceptual definitions — so labeler and model share
   judgment. A perfect score partly reflects that agreement.
   → Follow-up: expand the OOD set to ~100 sentences with **independent** labels (e.g. a
   second annotator, or labels drawn before the rubric was written) to get a trustworthy
   number. Until then, treat 1.000 as "clearly better," not "perfect."

**Cost/latency:** batched structured-output calls (~15 sentences/request). `claude-opus-4-8`
chosen to establish the quality ceiling; `claude-haiku-4-5` is the cheaper option for bulk
runs once quality is confirmed.

**Action taken:** wired `LLMClaimTagger` behind the existing `.tag()` interface
(`src/extraction/llm_predict.py`); `src/graph/build.py --tagger llm` (now the default)
uses it. See decisions.md [E-005].

Sources:
- claude-api skill reference (model IDs, structured outputs, Python SDK)

## [R-004] Finding: Edge relation taxonomy (user-confirmed)

_Date: 2026-06-14_

**Confirmed taxonomy (RICH set, 7 labels).** Directional A→B unless marked symmetric;
`NONE` means prune (no edge stored).

| Relation | Meaning (A→B) | Sym? |
| --- | --- | --- |
| SUPPORTS | A's result/evidence backs B's claim | no |
| CONTRADICTS | A's finding is logically incompatible with B's | no |
| REFINES | A improves / generalizes / extends B's method or result | no |
| ADDRESSES_SAME_PROBLEM | A and B tackle the same problem, different approaches | yes |
| USES | A uses a method/dataset/result introduced by B | no |
| RELATED | same topic, no stronger typed relation | yes |
| NONE | not meaningfully related — prune | — |

**Why this set:** `NONE` and `ADDRESSES_SAME_PROBLEM` are the two additions that directly
fix the observed NLI failure (GraphRec↔2008-GNN wrongly typed CONTRADICTS). REFINES/USES
capture the "builds on" / provenance relations that make the graph a real idea-map.

**Stored edge fields (schema, R-004→E-006):** `rel_type`, `direction`, `confidence`,
`rationale`, `similarity`.

**Confidence: HIGH** — user-confirmed. Gates E-006 as a normal implement ticket.

## [R-005] Finding: edge-typing eval vs independent (user) labels

_Date: 2026-06-14 · gold set: 37 pairs, hand-labeled by the user (independent of the
LLM prompt — fixes the R-003 shared-judgment caveat)._

| Metric | NLI (distilbert-mnli) | LLM (claude-opus-4-8) |
| --- | --- | --- |
| exact-match accuracy | 0.081 | 0.135 |
| **false-CONTRADICTS rate** | **6/36 = 0.167** | **0/36 = 0.000** |
| NONE pruned correctly | 0/1 | 0/1 |

**Headline (the bug we targeted): fixed.** The LLM never produced a false contradiction;
NLI did 17% of the time. The LLM is strictly better and adds ADDRESSES_SAME_PROBLEM
(matched the user 5/6).

**But fine-grained relation typing is NOT solved — and the eval shows precisely why.**
Label distributions: user = {REFINES 16, USES 8, ADDRESSES_SAME_PROBLEM 6, RELATED 4,
SUPPORTS 1, CONTRADICTS 1, NONE 1}; LLM = {RELATED 20, ADDRESSES_SAME_PROBLEM 11,
SUPPORTS 3, REFINES 2, USES 1}. The disagreement is concentrated in REFINES/USES: the
user assigns them from **domain knowledge of the paper lineage** ("HetGNN builds on
GNNs"); the LLM, given only two isolated abstract sentences with no explicit "we
extend/use X" language, **conservatively defaults to RELATED**. Both readings are
defensible — they differ on the evidence threshold.

**Implications / follow-ups:**
1. REFINES/USES need more evidence than two sentences — feed the typer **full abstracts
   and/or citation links**, or accept that from-sentence-alone, RELATED is the honest call.
2. The LLM under-uses NONE (prefers weak RELATED) — prompt it to prune more aggressively,
   or relax the expectation.
3. Low exact-match on a fuzzy 7-way taxonomy is itself a finding: inter-annotator
   agreement here is low even human-vs-frontier-model. Consider a coarser eval grouping
   (e.g., {contradiction / building-on / same-topic / unrelated}) or an adjudication pass.

**Confidence: HIGH** on the headline (false-CONTRADICTS fixed, independent labels);
the exact-match numbers are honest but small-n (37). The win is real and bounded — not
the 1.000 the extraction eval suggested for its task.

## [R-006] Finding: relations are per-claim & many-to-many; "builds-on" evidence is in citances

_Date: 2026-06-16 · design reasoning (from discussion), not an experiment._

1. **Unit of relation = claim↔claim, not paper↔paper.** A paper bundles many claims; each can
   relate differently to claims in different papers (complement one, use another's method,
   address a third's problem, contradict a fourth). The graph already models this (claims are
   nodes, `Paper` is a container) — the model was right; the evidence feeding it was thin.

2. **Two evidence regimes.**
   - *Cited / builds-on* (USES, REFINES, SUPPORTS): evidence = the **citance**, the sentence
     in paper P that cites paper A. (Established as citation-function / citation-context
     analysis.)
   - *Uncited / parallel* (ADDRESSES_SAME_PROBLEM, CONTRADICTS, RELATED, NONE): no citation
     exists; evidence = semantic claim comparison.

3. **This explains R-005.** The abstract-only typer defaulted to RELATED because the citance —
   where "B extends/uses A" is actually stated — lives in body text (Related Work / Methods),
   not the abstract. It never saw the evidence.

4. **Therefore: hybrid + full-text.** Final edges = citation-context typer (cited) ∪ semantic
   typer (uncited). Full-text ingestion + citation linking become prerequisites for the cited
   half. See docs/llm-edge-typer-plan.md → Architecture Evolution.

**Confidence: HIGH** on the framing. **Unknown to measure:** the cited-vs-uncited ratio in
real data (how much of the graph each regime covers) — quantify in R-007 / E-011.

## [R-007] Finding: Semantic Scholar is the citance source; full-text parsing now optional

_Date: 2026-06-16 · empirical (live S2 Graph API probes against the corpus)._

**Recommendation: Semantic Scholar Graph API as the citation-context source.**
`/paper/DOI:{doi}/references?fields=contexts,intents,externalIds,isInfluential` returns,
per reference: the **citance text** (`contexts`), a **citation-function intent**
(`background`/`methodology`/`result`), and resolvable `externalIds` (DOI/arXiv/CorpusId).
On the probe paper, 24/25 refs carried citances. **This is exactly the citance extraction +
citation linking that E-009/E-010 were going to build via PDF/LaTeX parsing — already done
by S2.** The project's biggest build is largely eliminated for the edge-typing goal.

**Measured cited-vs-uncited (the R-006 unknown), 45-paper corpus:** 47 intra-corpus citation
edges (a corpus paper citing another), 31 with ≥1 citance; intents {background 23,
methodology 15, result 1}; vs 247 embedding candidate pairs. So the cited regime is a real
but minority backbone, and it's a **different edge set** from the embedding pairs → the
hybrid graph should **union** citation edges with semantic edges, not pick one.

**Re-scoping (driven by the evidence):**
- **E-009 (full-text PDF/LaTeX parsing): DECOUPLED from the edge-typer, now OPTIONAL.** S2
  provides citances without it. Its remaining value is richer *claim extraction* from body
  text (today claims come only from abstracts) — a separate enhancement, user's call.
- **E-010 (citation linking): mostly done** by `src/graph/s2_citations.py`
  (→ data/processed/intra_corpus_citations.jsonl).
- **E-011 (citance typer): the real remaining build.** S2 intents are coarse (3 classes);
  map each citance → our 7-label taxonomy (esp. USES/REFINES/SUPPORTS) with the LLM, using
  the S2 intent as a weak prior.
- **E-012 (hybrid merge):** union citance-typed edges with semantic edges; also add citation
  links as candidate pairs in their own right (they're not all embedding-similar).

**Confidence: HIGH** on source choice + that parsing is optional. Caveats: S2 coverage is
partial (16/47 edges lacked citances → fall back to semantic typing); unauthenticated rate
limit ~1 req/s shared pool (get an API key for scale); citances are windowed snippets.

## [R-009] Finding: faceted edge taxonomy — keep the umbrella, add filterable sub-facets

_Date: 2026-06-20 · user-designed, empirically validated on the 31 citance edges._

**Design (user's):** don't flatten the coarse relations into more top-level labels. Keep the
~6–7 umbrella relations as the stable, high-agreement top layer, and attach a second **FACET**
layer (a sub-kind + a free-text `facet_detail`) that makes each edge **filterable by research
question**. Facets are *additive metadata*, not a replacement — so the reliable umbrella is
preserved and the R-005 fine-label subjectivity risk is confined to optional filter fields
(a wrong facet still leaves a trustworthy coarse relation).

**Validation:** re-typed the 31 citance edges with facets. Umbrella stayed stable
(RELATED 25, USES 6). The RELATED umbrella decomposed cleanly into:
EXEMPLIFIES 11, BACKGROUND 9, COMPARES 3, APPLICATION 2 (MOTIVATION / CO_MENTION / NA unused).
`facet_detail` values are specific and queryable, e.g. "first GCN industrial recommender
system" (PinSage), "early GNN foundational work", "GNN explainability methods", "K-nearest
neighbor graph construction". Enables queries RELATED erased (e.g. "EXEMPLIFIES edges under
recommendation"; "the BACKGROUND/foundational lineage of X").

**Caveats:** facet *accuracy* not yet gold-validated (a small R-005-style facet eval would
confirm crispness); the facet vocabulary is a **starter set to finalize against intended
queries** (purpose). EXEMPLIFIES (survey categorization) dominates — consistent with R-008
(survey-heavy corpus).

**Schema impact (E-012):** `RELATES` edges carry `rel_type` (umbrella) + `facet` +
`facet_detail`. **Confidence:** HIGH the faceted *structure* is right; MEDIUM on the exact
facet vocabulary (pending purpose-pruning + a facet gold check).

**Coverage test (2026-06-20):** added candidate facets CRITIQUES / FUTURE_WORK / RESOURCE +
an `OTHER` escape-hatch (model must name a missing sub-kind in facet_detail), re-typed the 31
edges. Result: **`OTHER` fired only 1/31 (~3%), the 3 new candidates 0/31** → the facet set
is empirically adequate *for this corpus*; the literature's extra functions (critique/future-
work/resource) don't occur in this survey-heavy GNN corpus (would matter in debate-heavy or
citation-snowball corpora — R-008). The signal that did appear: **5 NA + 1 OTHER all on USES
edges** → the next umbrella to facet is **USES** (method / dataset / metric / component), not
RELATED. **Caveat:** umbrella wobbled run-to-run (RELATED/USES 25/6 → 19/11) — the fuzzy
RELATED↔USES border (same as R-005); facets ride on top and don't stabilize it (→ lower
sampling temp or a small umbrella/facet gold check to pin down). **Method note:** the
OTHER-escape-hatch is a reusable coverage-gap detector for any new corpus.

## [R-008] Finding: citation-snowball expansion — sizing + plan

_Date: 2026-06-20 · empirical (S2 reference sweep of the 45-paper corpus)._

The similarity-sampled corpus is **missing the field's foundational hubs as nodes.** Sweeping
all reference lists: **1,097 distinct external referenced papers** (from 1,437 refs); 919
cited once. Co-citation: **178 cited by ≥2 corpus papers → ~518 new citation edges** (vs 47
today, ~11×); 65 by ≥3. The most co-cited absentees are the canonical GNN lineage — GCN
(Kipf & Welling) 17×, GAT 13×, GraphSAGE 13×, ChebNet 12×, MPNN 8×, GIN 7×.

**Implication:** a bounded **backward citation-snowball** densifies exactly the
USES/REFINES/BACKGROUND lineage that was sparse (E-011 finding). Thresholds:
- **≥3 co-citation: +65 papers** (45→110) — the canonical core, tight + cheap.
- **≥2 co-citation: +178 papers** (45→223), ~518 edges — core + connected periphery.
- drop the 919 one-off leaves (explosion control).

**Recommendation:** implement bounded backward snowball (start ≥3 for cost/value, or ≥2 for
richness): ingest added papers' abstracts + extract claims (existing tagger), pull citances
(S2), rebuild + re-type. Highest-leverage move for a USES/REFINES-rich idea-map. Confidence:
HIGH (sizing measured). Spawns the build ticket E-013.
