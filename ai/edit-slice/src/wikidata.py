"""Dated Wikidata snapshots.

Wikidata is mutable: statements are added, corrected and deleted continuously. A
number computed against it on one day cannot be reproduced later unless the bytes
that produced it are kept. So every ingestion is written to
`data/wikidata/<YYYY-MM-DD>/snapshot.json.gz` with a manifest, and analysis reads
a snapshot by date rather than the live API.

This mirrors how CounterFact is pinned (see `src/data.py`), with one difference:
CounterFact has a single canonical release, so it carries one checksum. Wikidata
has as many releases as there are days, so snapshots are dated and additive —
never overwritten.

Layout
------
    data/wikidata/2026-09-10/
        snapshot.json.gz   links + claims + labels actually used
        MANIFEST.md        date, endpoint, counts, sha256

Fetching is read-through: anything already in the snapshot is served from it, and
only genuinely new entities hit the network. Re-running an analysis against an
existing snapshot therefore makes no API calls at all.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date as _date
from pathlib import Path
from typing import Any, Final

API: Final[str] = "https://www.wikidata.org/w/api.php"
UA: Final[str] = "edit-slice-research/0.1 (islam.saif@northeastern.edu)"
ROOT: Final[Path] = Path(__file__).resolve().parent.parent / "data" / "wikidata"
THROTTLE_S: Final[float] = 0.12


@dataclass
class Snapshot:
    """One dated ingestion of the Wikidata subset an analysis touched."""

    ingested: str
    endpoint: str = API
    #: subject string -> QID, as resolved by wbsearchentities (top hit)
    links: dict[str, str | None] = field(default_factory=dict)
    #: QID -> raw claims payload
    claims: dict[str, Any] = field(default_factory=dict)
    #: QID or PID -> English label
    labels: dict[str, str] = field(default_factory=dict)

    @property
    def path(self) -> Path:
        return ROOT / self.ingested / "snapshot.json.gz"

    # -- persistence -------------------------------------------------------
    def payload(self) -> bytes:
        body = {
            "ingested": self.ingested,
            "endpoint": self.endpoint,
            "links": self.links,
            "claims": self.claims,
            "labels": self.labels,
        }
        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()

    def sha256(self) -> str:
        return hashlib.sha256(self.payload()).hexdigest()

    def save(self) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.payload()
        with gzip.open(self.path, "wb") as fh:
            fh.write(payload)
        _write_manifest(self, hashlib.sha256(payload).hexdigest())
        return self.path

    @classmethod
    def load(cls, ingested: str | None = None) -> Snapshot:
        ingested = ingested or latest()
        path = ROOT / ingested / "snapshot.json.gz"
        with gzip.open(path, "rb") as fh:
            body = json.loads(fh.read())
        return cls(
            ingested=body["ingested"],
            endpoint=body.get("endpoint", API),
            links=body.get("links", {}),
            claims=body.get("claims", {}),
            labels=body.get("labels", {}),
        )

    @classmethod
    def open_or_new(cls, ingested: str | None = None) -> Snapshot:
        ingested = ingested or _date.today().isoformat()
        if (ROOT / ingested / "snapshot.json.gz").exists():
            return cls.load(ingested)
        return cls(ingested=ingested)

    # -- read-through fetching --------------------------------------------
    def link(self, subject: str) -> str | None:
        if subject not in self.links:
            res = _get({"action": "wbsearchentities", "search": subject,
                        "language": "en", "limit": "1"})
            hits = res.get("search", [])
            self.links[subject] = hits[0]["id"] if hits else None
            time.sleep(THROTTLE_S)
        return self.links[subject]

    def fetch_claims(self, qids: list[str]) -> dict[str, Any]:
        missing = sorted({q for q in qids if q and q not in self.claims})
        for i in range(0, len(missing), 40):
            batch = missing[i : i + 40]
            res = _get({"action": "wbgetentities", "ids": "|".join(batch), "props": "claims"})
            for qid, payload in res.get("entities", {}).items():
                self.claims[qid] = payload.get("claims", {})
            time.sleep(THROTTLE_S)
        return {q: self.claims.get(q, {}) for q in qids if q}

    def fetch_labels(self, ids: list[str]) -> dict[str, str]:
        missing = sorted({i for i in ids if i and i not in self.labels})
        for i in range(0, len(missing), 45):
            batch = missing[i : i + 45]
            res = _get({"action": "wbgetentities", "ids": "|".join(batch),
                        "props": "labels", "languages": "en"})
            for qid, payload in res.get("entities", {}).items():
                self.labels[qid] = payload.get("labels", {}).get("en", {}).get("value", qid)
            for b in batch:
                self.labels.setdefault(b, b)
            time.sleep(THROTTLE_S)
        return {i: self.labels.get(i, i) for i in ids}


def item_statements(claims: dict[str, Any]) -> dict[str, list[str]]:
    """Keep only `wikibase-item` statements — entity-to-entity facts.

    Filters out external identifiers, media and URLs by DATATYPE rather than by a
    hand-picked list. That is Wikidata's structural analogue of the DBpedia naming
    predicates which produced E-001's alias tautologies.
    """
    out: dict[str, list[str]] = {}
    for pid, snaks in claims.items():
        vals = [
            s["mainsnak"]["datavalue"]["value"]["id"]
            for s in snaks
            if s.get("mainsnak", {}).get("datatype") == "wikibase-item"
            and "id" in s.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        ]
        if vals:
            out[pid] = vals
    return out


def latest() -> str:
    dates = sorted(p.name for p in ROOT.iterdir() if (p / "snapshot.json.gz").exists())
    if not dates:
        raise FileNotFoundError(f"no wikidata snapshots under {ROOT}")
    return dates[-1]


def _get(params: dict[str, str]) -> dict[str, Any]:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def _write_manifest(snap: Snapshot, digest: str) -> None:
    n_linked = sum(1 for v in snap.links.values() if v)
    stmts = sum(len(v) for c in snap.claims.values() for v in c.values())
    (snap.path.parent / "MANIFEST.md").write_text(
        f"""# Wikidata snapshot — {snap.ingested}

Wikidata is mutable. This is the subset actually touched on this date, kept so the
numbers computed from it stay reproducible. Snapshots are **additive**: a later
ingestion creates a new dated directory and never overwrites this one.

| | |
| --- | --- |
| **Ingested** | {snap.ingested} |
| **Endpoint** | `{snap.endpoint}` |
| **Subjects looked up** | {len(snap.links)} ({n_linked} resolved to a QID) |
| **Entities with claims** | {len(snap.claims)} |
| **Statements** | {stmts} |
| **Labels** | {len(snap.labels)} |
| **SHA-256 (decompressed)** | `{digest}` |

Checksum is of the decompressed payload — gzip headers embed mtime and are not
byte-stable. Verify:

```bash
gzip -dc data/wikidata/{snap.ingested}/snapshot.json.gz | shasum -a 256
```

Load:

```python
from src.wikidata import Snapshot
snap = Snapshot.load("{snap.ingested}")   # or Snapshot.load() for the latest
```

Entity linking is `wbsearchentities` top hit on the CounterFact subject string —
a heuristic, and part of what this snapshot pins.
"""
    )
