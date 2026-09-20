"""E-025 · Label the P1412 values. Same pattern as fetch_occupations: a new dated
snapshot, never a mutation of a pinned one, so earlier results stay reproducible."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
log = setup("fetch_languages", config={"ticket": "E-025", "property": "P1412"})
old = Snapshot.load()
chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
qids = set()
for c in chains:
    for s in old.claims.get(c["inner_1"]["qid_subject"], {}).get("P1412", []):
        try:
            qids.add(s["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            continue
log.info("%d distinct language QIDs", len(qids))

snap = Snapshot.open_or_new()
if not snap.claims:
    snap.links, snap.claims, snap.labels = dict(old.links), dict(old.claims), dict(old.labels)
before = len(snap.labels)
snap.fetch_labels(sorted(qids))
snap.save()
log.info("labels %d -> %d", before, len(snap.labels))
resolved = sum(1 for q in qids if snap.labels.get(q, q) != q)
log.info("resolved: %d/%d", resolved, len(qids))
for q in sorted(qids)[:10]:
    log.info("   %-12s %s", q, snap.labels.get(q))
