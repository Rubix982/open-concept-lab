# Researcher Tickets

---

### R-001 · Research Phase 0 technical dependencies

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-04-05

**Description:**
Research three blockers before Phase 0 implementation can begin:
1. arXiv bulk metadata: access method, format, gotchas
2. Citation data: S2ORC license/availability vs alternatives
3. SPECTER2 on Apple MPS: compatibility, batch size, known issues

**Artifacts:**
- docs/research/phase0_research.md (full research brief)
- agents/shared/findings.md → [R-001] Finding: Phase 0 Technical Dependencies

**Closed:** 2026-04-05

---

### R-002 · Verify Semantic Scholar precomputed SPECTER2 coverage

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-05
**Updated:** 2026-03-29

**Description:**
The Semantic Scholar Datasets API may ship precomputed SPECTER2 embeddings for
arXiv papers. If coverage is sufficient for our target corpus (cs.AI, cs.LG,
cs.CL, cs.CV, stat.ML, math.OC + interdisciplinary), we can skip local SPECTER2
inference entirely and download the precomputed vectors.

Determine:
1. Does the Semantic Scholar Datasets API include SPECTER2 embeddings?
2. What is the API endpoint, authentication, and data format?
3. What fraction of arXiv papers have precomputed embeddings?
4. What is the download size per paper / total for 500K papers?
5. Are embeddings the same model as `allenai/specter2` (proximity adapter)?

Output findings to agents/shared/findings.md as [R-002].

**Blockers:** none

**Artifacts:**
- agents/researcher/findings/r002_specter2_coverage.md (raw notes)
- agents/shared/findings.md → [R-002] Finding: Semantic Scholar Precomputed SPECTER2 Coverage

**Key result:**
- Dataset `embeddings-specter_v2` confirmed: 120M records, 30 x 28GB shards, Apache 2.0
- Model: SPECTER2 proximity adapter (allenai/specter2) — same as R-001 local setup
- Coverage: ~60% overall S2AG; ~80-95% for arXiv cs.* with abstracts
- Access: free API key required; bulk via S3 presigned URLs (no RPS limit)
- Recommendation for E-006: hybrid downloader (bulk + per-paper API gap fill) + local fallback

**Closed:** 2026-03-29

---

### R-003 · Design L2 extraction prompt and validate schema on 5 papers

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-04-12
**Updated:** 2026-04-12

**Description:**
Design the Claude API prompt for L2 paper summary extraction and validate it
against 5 real papers from our 10K corpus.

**What to produce:**

1. A Claude API prompt (using tool_use / JSON mode) that takes a paper title +
   abstract and returns a structured L2 summary matching this schema:
   ```json
   {
     "contribution": "One sentence.",
     "method": "Technique/architecture used.",
     "datasets": ["list"],
     "key_findings": ["finding_1", "finding_2", "finding_3"],
     "limitations": "Known constraints.",
     "domain_tags": ["NLP", "transformers", ...],
     "related_methods": ["BERT", "GPT", ...]
   }
   ```

2. Run it against 5 diverse papers from data/pipeline/arxiv_10k.parquet
   (pick papers spanning different subfields: NLP, CV, RL, optimization, statistics)

3. Evaluate quality:
   - Is the contribution sentence accurate and self-contained?
   - Are domain_tags consistent across papers from the same field?
   - Are key_findings specific (with numbers/metrics) or vague?
   - Would a researcher unfamiliar with the paper understand what it found?

4. Note: abstract-only is sufficient for L2. Do NOT use full PDF for Phase 1.

**Output:** Write findings to agents/shared/findings.md as [R-003].
Include the final prompt text and 2-3 example extractions with quality notes.

**Blockers:** none

**Closed:** 2026-04-12

**Artifacts:**
- agents/researcher/findings/r003_l2_extractions.json (raw Ollama outputs for 5 papers)
- agents/shared/findings.md → [R-003] Finding: L2 Extraction Prompt Design and Validation

**Key result:**
- Prompt v1 produced valid JSON on all 5 papers, first attempt, no iteration needed
- Overall quality: medium-high; contribution/method/datasets fields strong; domain_tags
  has CV-as-NLP drift on cross-domain papers; findings qualitative when abstract lacks numbers
- Known failure modes documented for E-015: domain tag drift, shallow related_methods,
  limitations echo

---

### R-004 · Research NLI models for contradiction/support classification

**Status:** open
**Type:** research
**Priority:** medium
**Created:** 2026-04-12

**Description:**
Research which NLI (Natural Language Inference) model is best suited for
classifying edges between claim nodes as: supports, contradicts, neutral.

Evaluate:
1. **cross-encoder/nli-deberta-v3-small** (HuggingFace) — strong, fast
2. **facebook/bart-large-mnli** — classic, well-tested
3. **MoritzLaurer/deberta-v3-large-zeroshot-v2** — zero-shot capable

For each, check:
- Can it run on MPS (Apple Silicon)?
- What's inference time for a single pair?
- How does it handle scientific claims (not just generic NLI)?
- Does it need fine-tuning for the AI/ML domain?

Test with 5 real claim pairs from AI/ML literature where you know the ground truth:
- A clear support pair (two papers claiming same result)
- A clear contradiction pair (two papers with opposing findings)
- A neutral pair (unrelated claims)

Output: agents/shared/findings.md as [R-004].
Recommendation: which model to use for Phase 2 edge classification.

**Blockers:** none (can run in parallel with Phase 1)

**Closed:** —
