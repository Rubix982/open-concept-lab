# Researcher Tickets

### R-001 · Survey model editing literature

**Status:** open
**Type:** research
**Priority:** high
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Description:**
Read and annotate the five core papers in the model editing / ripple effects
space. For each paper produce a `notes.md` in its readings/ folder. Output a
synthesis to `agents/shared/findings.md`.

**Papers to read (in order):**
1. ROME — `readings/rome/` — Meng et al. 2022 (NeurIPS)
2. MEMIT — `readings/memit/` — Meng et al. 2023 (ICLR)
3. Ripple Effects — `readings/ripple-effects/` — Cohen et al. 2023
4. GRACE / WISE — `readings/grace-wise/` — contrast approaches
5. Survey — `readings/survey/` — "Editing Large Language Models: Problems,
   Methods, and Opportunities" (Yao et al.) for the full landscape

**Questions to answer per paper:**
- What is the edit operation (weight update, retrieval, adapter)?
- What does it measure as success? What does it ignore?
- How does it handle neighbor facts? Does it even try?
- What model and dataset does it use?
- What fails?

**Output:** `agents/shared/findings.md` → R-001 finding (synthesis)

**Closed:** —

---

### R-002 · Map neighbor taxonomy from ripple papers

**Status:** open
**Type:** research
**Priority:** high
**Created:** 2026-07-22
**Updated:** 2026-07-22

**Description:**
From the ripple effects paper (Cohen et al. 2023) and the CounterFact dataset,
extract a precise taxonomy of neighbor types. For each type: define it, give a
concrete example, and note how far current editing methods get.

**Neighbor types to map:**
- Logical entailment (N1, N2, N3 hops)
- Reverse entailment (what is now in the new location?)
- Compositional (multi-hop reasoning chains)
- Paraphrase (same fact, different surface form)
- Distractors (related but not entailed — should NOT change)

**Output:** `agents/shared/findings.md` → R-002 finding (taxonomy table)
**Secondary output:** seed data for E-001 and E-002 (concrete fact triples
  with known neighbors for GPT-J-6B)

**Closed:** —
