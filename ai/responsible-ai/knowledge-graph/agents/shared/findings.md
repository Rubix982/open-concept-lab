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
