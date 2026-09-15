"""E-014 · Which chain birthplaces are actually settlements?

`P19` legitimately points at hospitals, universities, regions and clubs, so the
`inner_1` "city" pool contains non-cities — "University of Chicago", "Nebraska",
"Tottenham Hotspur F.C.". A polluted pool adds distractors that no relocation could
ever be scored against, and a chain whose inner_1 is a US STATE is not the fact we
think we are editing.

The first attempt at this filter matched on labels that had never been fetched, so it
reported 78/78 non-settlements including Paris. Fetch the type labels first.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SETTLEMENT = ("city", "town", "village", "municipalit", "settlement", "commune",
              "metropolis", "capital", "borough", "urban", "locality", "county seat",
              "prefecture", "ward")

log = setup("classify_places", config={"ticket": "E-014", "property": "P31 instance of"})
snap = Snapshot.open_or_new()
if not snap.claims:
    old = Snapshot.load("2026-09-15")
    snap.links, snap.claims, snap.labels = dict(old.links), dict(old.claims), dict(old.labels)

chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
qmap = {c["inner_1"]["qid_answer"]: c["inner_1"]["answer"]
        for c in chains if c["inner_1"].get("qid_answer")}

types = set()
for q in qmap:
    for s in snap.claims.get(q, {}).get("P31", []):
        try:
            types.add(s["mainsnak"]["datavalue"]["value"]["id"])
        except (KeyError, TypeError):
            pass
log.info("%d distinct P31 types across %d birthplaces", len(types), len(qmap))
snap.fetch_labels(sorted(types))
snap.save()

def is_settlement(q: str) -> tuple[bool, list[str]]:
    labs = []
    for s in snap.claims.get(q, {}).get("P31", []):
        try:
            labs.append(snap.labels.get(s["mainsnak"]["datavalue"]["value"]["id"], "?"))
        except (KeyError, TypeError):
            pass
    return any(any(k in l.lower() for k in SETTLEMENT) for l in labs), labs

good, bad = [], []
for q, lab in qmap.items():
    ok, labs = is_settlement(q)
    (good if ok else bad).append((lab, labs[:3]))

log.info("settlements: %d/%d", len(good), len(qmap))
log.info("NOT settlements (%d) — these pollute the pool and malform their chain:", len(bad))
for lab, labs in sorted(bad):
    log.info("   %-34s %s", lab, labs)

(ROOT / "probes" / "place_types.json").write_text(json.dumps(
    {"settlement": sorted(l for l, _ in good),
     "not_settlement": {l: t for l, t in sorted(bad)}}, indent=1))
log.info("written: probes/place_types.json")
