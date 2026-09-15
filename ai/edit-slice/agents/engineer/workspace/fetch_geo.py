"""E-014 · City -> country (P17) and country -> capital (P36), into a dated snapshot.

Needed to VERIFY "the model relocated the birth city into the target country" rather
than assert it by inspection, and to make sure the coherent destination is actually
present in the candidate pool — if it is not, a correct relocation scores as a failure,
which is the [E-011] mistake in a new costume.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from wikidata import Snapshot  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
log = setup("fetch_geo", config={"ticket": "E-014", "props": ["P17 country", "P36 capital"]})

chains = json.loads((ROOT / "probes" /
                     "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
snap = Snapshot.open_or_new()
if not snap.claims:
    old = Snapshot.load("2026-09-15")
    snap.links, snap.claims, snap.labels = dict(old.links), dict(old.claims), dict(old.labels)

city_q = {c["inner_1"]["qid_answer"] for c in chains if c["inner_1"].get("qid_answer")}
ctry_q = {c["inner_2"]["qid_answer"] for c in chains if c["inner_2"].get("qid_answer")}
log.info("%d city QIDs, %d country QIDs from the chains", len(city_q), len(ctry_q))

need = sorted(q for q in (city_q | ctry_q) if q not in snap.claims)
log.info("%d need claims fetched", len(need))
if need:
    snap.claims.update(snap.fetch_claims(need))


def current(qid: str, prop: str) -> str | None:
    """The CURRENT value, not the first listed.

    P36 carries historical capitals with `end time` (P582) qualifiers — taking the
    first statement gives Japan -> "Shigaraki Palace", an 8th-century capital. Same
    first-value bug as the P106 occupation labels and the dissolved-states filter in
    chain mining. Prefer `preferred` rank, then any statement WITHOUT an end time,
    and fall back to the first only if nothing else qualifies.
    """
    sts = snap.claims.get(qid, {}).get(prop, [])
    def val(s):
        try:
            return s["mainsnak"]["datavalue"]["value"]["id"]
        except (KeyError, TypeError):
            return None
    live = [s for s in sts if s.get("rank") != "deprecated"
            and "P582" not in (s.get("qualifiers") or {})]
    for pool in ([s for s in live if s.get("rank") == "preferred"], live, sts):
        for s in pool:
            v = val(s)
            if v:
                return v
    return None


capitals = {q: current(q, "P36") for q in ctry_q}
city_country = {q: current(q, "P17") for q in city_q}
snap.fetch_labels(sorted({v for v in capitals.values() if v}))
snap.fetch_labels(sorted({v for v in city_country.values() if v}))
snap.save()

log.info("capitals resolved: %d/%d", sum(1 for v in capitals.values() if v), len(ctry_q))
log.info("city->country resolved: %d/%d",
         sum(1 for v in city_country.values() if v), len(city_q))
log.info("all capitals, for inspection — a wrong one silently breaks the pool:")
for q, cap in sorted(capitals.items(), key=lambda kv: snap.labels.get(kv[0], "")):
    log.info("   %-30s %s", snap.labels.get(q, q), snap.labels.get(cap, "?"))
(ROOT / "probes" / "geo.json").write_text(json.dumps(
    {"capital": {snap.labels.get(q, q): snap.labels.get(c, c) for q, c in capitals.items()},
     "city_country": {snap.labels.get(q, q): snap.labels.get(c, c)
                      for q, c in city_country.items()}}, indent=1))
log.info("written: probes/geo.json")
