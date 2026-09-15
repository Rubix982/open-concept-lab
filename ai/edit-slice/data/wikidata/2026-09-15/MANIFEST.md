# Wikidata snapshot — 2026-09-15

Wikidata is mutable. This is the subset actually touched on this date, kept so the
numbers computed from it stay reproducible. Snapshots are **additive**: a later
ingestion creates a new dated directory and never overwrites this one.

| | |
| --- | --- |
| **Ingested** | 2026-09-15 |
| **Endpoint** | `https://www.wikidata.org/w/api.php` |
| **Subjects looked up** | 417 (416 resolved to a QID) |
| **Entities with claims** | 520 |
| **Statements** | 91798 |
| **Labels** | 633 |
| **SHA-256 (decompressed)** | `1550b596c626429938b0e81ed2091e01922e72cc194ff2cecf39162cdc1bb8f3` |

Checksum is of the decompressed payload — gzip headers embed mtime and are not
byte-stable. Verify:

```bash
gzip -dc data/wikidata/2026-09-15/snapshot.json.gz | shasum -a 256
```

Load:

```python
from src.wikidata import Snapshot
snap = Snapshot.load("2026-09-15")   # or Snapshot.load() for the latest
```

Entity linking is `wbsearchentities` top hit on the CounterFact subject string —
a heuristic, and part of what this snapshot pins.
