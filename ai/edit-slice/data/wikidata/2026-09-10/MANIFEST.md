# Wikidata snapshot — 2026-09-10

Wikidata is mutable. This is the subset actually touched on this date, kept so the
numbers computed from it stay reproducible. Snapshots are **additive**: a later
ingestion creates a new dated directory and never overwrites this one.

| | |
| --- | --- |
| **Ingested** | 2026-09-10 |
| **Endpoint** | `https://www.wikidata.org/w/api.php` |
| **Subjects looked up** | 55 (54 resolved to a QID) |
| **Entities with claims** | 54 |
| **Statements** | 3327 |
| **Labels** | 295 |
| **SHA-256 (decompressed)** | `cac62c326f8fe4f294631e249c9027af267ac6c42a4ba05ad23e93ff095f4170` |

Checksum is of the decompressed payload — gzip headers embed mtime and are not
byte-stable. Verify:

```bash
gzip -dc data/wikidata/2026-09-10/snapshot.json.gz | shasum -a 256
```

Load:

```python
from src.wikidata import Snapshot
snap = Snapshot.load("2026-09-10")   # or Snapshot.load() for the latest
```

Entity linking is `wbsearchentities` top hit on the CounterFact subject string —
a heuristic, and part of what this snapshot pins.
