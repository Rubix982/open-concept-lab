# Wikidata snapshot — 2026-09-14

Wikidata is mutable. This is the subset actually touched on this date, kept so the
numbers computed from it stay reproducible. Snapshots are **additive**: a later
ingestion creates a new dated directory and never overwrites this one.

| | |
| --- | --- |
| **Ingested** | 2026-09-14 |
| **Endpoint** | `https://www.wikidata.org/w/api.php` |
| **Subjects looked up** | 109 (108 resolved to a QID) |
| **Entities with claims** | 187 |
| **Statements** | 22362 |
| **Labels** | 217 |
| **SHA-256 (decompressed)** | `28cc866c1fc8cd105db5621e9993e303ad999321ff48b40be57690e0d2fb5a18` |

Checksum is of the decompressed payload — gzip headers embed mtime and are not
byte-stable. Verify:

```bash
gzip -dc data/wikidata/2026-09-14/snapshot.json.gz | shasum -a 256
```

Load:

```python
from src.wikidata import Snapshot
snap = Snapshot.load("2026-09-14")   # or Snapshot.load() for the latest
```

Entity linking is `wbsearchentities` top hit on the CounterFact subject string —
a heuristic, and part of what this snapshot pins.
