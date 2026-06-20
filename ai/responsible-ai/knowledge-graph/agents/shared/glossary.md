# Glossary (all agents — append-only)

- **Claim**: a sentence asserting a finding, contribution, or result the paper is making (vs. background or method).
- **Provenance**: the back-pointer from a claim node to its origin — `(paper_id, section, char_offset)`.
- **Claim Knowledge Graph (CKG)**: nodes = claims/ideas, edges = typed relations (supports / contradicts / refines) between them.
- **NLI**: Natural Language Inference — entailment / contradiction / neutral classification between two sentences; used to type edges.
- **Kùzu**: embedded property-graph DB ("SQLite for graphs"), Cypher query language.
- **Vertical slice**: one thin path through all four layers (ingest → extract → graph → query) on real data, rather than building each layer fully before the next.
- **SciArg / PubMed-RCT / ACL-ARC**: candidate real corpora of scientific sentences labeled by rhetorical/discourse role (R-001 will choose).
- **Citance**: the sentence(s) in a citing paper surrounding/containing a citation to another paper — the textual context of a citation, where the *kind* of relation is actually stated.
- **Citation function / intent**: the role a citation plays (uses-method, background, comparison, contrast, …), classified from the citance.
- **Citation linking**: resolving an in-text citation marker (`[12]`, `\cite{...}`) → its reference-list entry → the actual cited paper's id.
- **Citation-context analysis**: typing the relation between two papers from the citance, rather than from their abstracts in isolation.
- **Cited vs uncited regime**: builds-on relations (USES/REFINES/SUPPORTS) carry a citation and are typed from the citance; parallel relations (ADDRESSES_SAME_PROBLEM/CONTRADICTS/RELATED) often have no citation and are typed semantically.
- **GROBID / Semantic Scholar Graph API / arXiv LaTeX**: candidate full-text + citation-context sources (R-007 will choose). S2 ships pre-extracted citation `contexts` + `intents`.
- **Faceted edge taxonomy** (R-009): two-level edge labels — a coarse **umbrella relation** (reliable, ~6-7 classes) + a finer **facet** (filterable sub-kind) + **facet_detail** (free-text specific). Keeps the umbrella; facets are optional filters, so fine-label subjectivity never degrades the primary relation.
- **Facet / facet_detail**: the sub-kind under an umbrella (e.g. RELATED → EXEMPLIFIES/BACKGROUND/COMPARES/APPLICATION) and a short specific (e.g. "first GCN industrial recommender system") that makes edges queryable.
