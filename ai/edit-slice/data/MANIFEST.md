# Pinned data

Pinned rather than fetched at runtime. Upstream hosts change and disappear, and a
result that cannot be recomputed against the exact bytes that produced it is not
reproducible. Integrity is verified in `src/data.py` on every load.

## `counterfact.json.gz`

| | |
| --- | --- |
| **Source** | `https://rome.baulab.info/data/dsets/counterfact.json` |
| **Retrieved** | 2026-09-10 |
| **Records** | 21,919 (`case_id` 0–21918) |
| **Relations** | 34 distinct Wikidata properties — see `probes/relation_modality.md` |
| **SHA-256 (decompressed)** | `d017056125178a13728594e66a801357a8db9ed7973a7425554bb4271de9fc6f` |
| **Size** | 43 MB raw · 8.2 MB gzip -9 |
| **Origin** | Meng, Bau, Andonian, Belinkov — *Locating and Editing Factual Associations in GPT* (ROME), NeurIPS 2022. TODO(cite): verify against arXiv before this leaves the repo. |

The checksum is of the **decompressed** content, not the `.gz`, because gzip
headers embed mtime and are not byte-stable across runs. Re-compressing the same
JSON yields a different archive but the same verified payload.

**Verify manually:**

```bash
gzip -dc data/counterfact.json.gz | shasum -a 256
# d017056125178a13728594e66a801357a8db9ed7973a7425554bb4271de9fc6f
```

**Load:**

```python
from src.data import load_counterfact
records = load_counterfact()          # verifies by default; raises IntegrityError
```

## `wikidata/<YYYY-MM-DD>/`

Dated snapshots of the Wikidata subset each analysis touched — see
`src/wikidata.py`. Wikidata is mutable, so unlike CounterFact there is no single
canonical release to checksum: snapshots are **additive**, one directory per
ingestion, never overwritten. Each carries its own manifest and SHA-256.

Current: `2026-09-10` — 55 subjects looked up (54 resolved), 54 entities with
claims, 295 labels.

## Not pinned yet

- **Mined Horn rules** — `dice-group/Benchmarking-KE` (MIT), Zenodo
  `10.5281/zenodo.15697400`. Needed by design.md §0 method (e). Their edit sets
  are MQuAKE/MLaKE over **DBpedia**, so v1 likely re-runs their pipeline over
  CounterFact entities [R-005a]. Pin whatever we actually mine, with the AMIE
  parameters and confidence thresholds recorded alongside — those thresholds are
  a judgement call [T-027] and the numbers move with them.
