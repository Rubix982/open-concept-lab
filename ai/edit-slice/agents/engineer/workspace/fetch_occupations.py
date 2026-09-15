"""E-013 · Label the occupation QIDs needed for the same-subject control.

The pinned 2026-09-14 snapshot holds the subjects' P106 statements but not the LABELS
of the occupations they point at — labels are only stored for entities that snapshot
fetched. 174 QIDs, one bounded fetch.

Writes a NEW dated snapshot rather than mutating the pinned one, so every earlier
result stays reproducible against the snapshot that produced it.
"""
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
PINNED = "2026-09-14"

log = setup("fetch_occupations", config={"ticket": "E-013", "from_snapshot": PINNED,
                                         "property": "P106 occupation"})

old = Snapshot.load(PINNED)
chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]

qids: set[str] = set()
for c in chains:
    for s in old.claims.get(c["inner_1"]["qid_subject"], {}).get("P106", []):
        try:
            qids.add(s["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            continue
log.info("%d distinct occupation QIDs to label", len(qids))

snap = Snapshot.open_or_new()          # today's date; carries nothing yet
snap.links, snap.claims = dict(old.links), dict(old.claims)
snap.labels = dict(old.labels)
before = len(snap.labels)
snap.fetch_labels(sorted(qids))
log.info("labels %d -> %d", before, len(snap.labels))
path = snap.save()
log.info("wrote %s (sha %s)", path.relative_to(ROOT), snap.sha256()[:12])

resolved = sum(1 for q in qids if snap.labels.get(q, q) != q)
log.info("resolved to a real label: %d/%d", resolved, len(qids))
for q in sorted(qids)[:10]:
    log.info("   %-10s %s", q, snap.labels.get(q))
