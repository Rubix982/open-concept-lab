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
