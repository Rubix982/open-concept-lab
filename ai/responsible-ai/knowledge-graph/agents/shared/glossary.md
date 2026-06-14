# Glossary (all agents — append-only)

- **Claim**: a sentence asserting a finding, contribution, or result the paper is making (vs. background or method).
- **Provenance**: the back-pointer from a claim node to its origin — `(paper_id, section, char_offset)`.
- **Claim Knowledge Graph (CKG)**: nodes = claims/ideas, edges = typed relations (supports / contradicts / refines) between them.
- **NLI**: Natural Language Inference — entailment / contradiction / neutral classification between two sentences; used to type edges.
- **Kùzu**: embedded property-graph DB ("SQLite for graphs"), Cypher query language.
- **Vertical slice**: one thin path through all four layers (ingest → extract → graph → query) on real data, rather than building each layer fully before the next.
- **SciArg / PubMed-RCT / ACL-ARC**: candidate real corpora of scientific sentences labeled by rhetorical/discourse role (R-001 will choose).
