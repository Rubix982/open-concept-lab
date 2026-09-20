# Wikidata snapshot — 2026-09-20

Wikidata is mutable. This is the subset actually touched on this date, kept so the
numbers computed from it stay reproducible. Snapshots are **additive**: a later
ingestion creates a new dated directory and never overwrites this one.

| | |
| --- | --- |
| **Ingested** | 2026-09-20 |
| **Endpoint** | `https://www.wikidata.org/w/api.php` |
| **Subjects looked up** | 417 (416 resolved to a QID) |
| **Entities with claims** | 520 |
| **Statements** | 91798 |
| **Labels** | 788 |
| **SHA-256 (decompressed)** | `f12bd19c8b9daab30d9f65db487a240c7296f3d6cacbe7a4ec49672f8e957aab` |

Checksum is of the decompressed payload — gzip headers embed mtime and are not
byte-stable. Verify:

```bash
gzip -dc data/wikidata/2026-09-20/snapshot.json.gz | shasum -a 256
```

Load:

```python
from src.wikidata import Snapshot
snap = Snapshot.load("2026-09-20")   # or Snapshot.load() for the latest
```

Entity linking is `wbsearchentities` top hit on the CounterFact subject string —
a heuristic, and part of what this snapshot pins.
