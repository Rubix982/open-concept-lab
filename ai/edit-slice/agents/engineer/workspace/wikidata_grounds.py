"""E-002 step 2: are co-present Wikidata properties plausibly GROUNDS?

Step 1 showed subjects are rich (98% linked, median 14-67 properties). Richness is
not justification. This prints, for a few rigid-relation edits, the item-valued
statements with human labels, so the grounds question can be judged by reading.

Restricted to `wikibase-item` statements — entity-to-entity facts. That drops
external identifiers (VIAF, Freebase, IMDb), media and URLs, which are Wikidata's
structural analogue of the DBpedia naming predicates that produced E-001's alias
tautologies. The filter is principled (a datatype), not hand-picked.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import load_counterfact  # noqa: E402

API: Final[str] = "https://www.wikidata.org/w/api.php"
UA: Final[str] = "edit-slice-research/0.1 (islam.saif@northeastern.edu)"
CACHE: Final[Path] = Path(__file__).parent / "wikidata_cache.json"
CASES: Final[list[int]] = [0]  # extended below from the coverage run


def _get(params: dict[str, str]) -> dict[str, Any]:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)


def labels(ids: list[str], cache: dict[str, Any]) -> dict[str, str]:
    missing = sorted({i for i in ids if f"lbl:{i}" not in cache})
    for i in range(0, len(missing), 45):
        batch = missing[i : i + 45]
        res = _get({"action": "wbgetentities", "ids": "|".join(batch), "props": "labels", "languages": "en"})
        for qid, payload in res.get("entities", {}).items():
            cache[f"lbl:{qid}"] = payload.get("labels", {}).get("en", {}).get("value", qid)
        for b in batch:
            cache.setdefault(f"lbl:{b}", b)
        time.sleep(0.12)
    return {i: cache.get(f"lbl:{i}", i) for i in ids}


def item_statements(claims: dict[str, Any]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for pid, snaks in claims.items():
        vals = []
        for s in snaks:
            main = s.get("mainsnak", {})
            if main.get("datatype") != "wikibase-item":
                continue
            dv = main.get("datavalue", {}).get("value", {})
            if "id" in dv:
                vals.append(dv["id"])
        if vals:
            out[pid] = vals
    return out


def main() -> None:
    cache: dict[str, Any] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    cov = json.loads((Path(__file__).parent / "wikidata_coverage.json").read_text())
    by_case = {r.case_id: r for r in load_counterfact()}

    # one example per relation where Wikidata actually asserts the edited property
    picks = {}
    for row in cov:
        if row["has_edited_prop"] and row["relation"] not in picks:
            picks[row["relation"]] = row

    for rel, row in sorted(picks.items()):
        rec = next(r for r in by_case.values() if r.rewrite.subject == row["subject"]
                   and r.rewrite.relation_id == rel)
        claims = cache.get(f"ent:{row['qid']}", {})
        items = item_statements(claims)
        ids = [row["qid"], *items.keys(), *[v for vs in items.values() for v in vs]]
        lab = labels(ids, cache)
        CACHE.write_text(json.dumps(cache))

        print("=" * 78)
        print(f"EDIT  {rel}  {rec.rewrite.subject} ({row['qid']})")
        print(f"      \"{rec.rewrite.prompt.format(rec.rewrite.subject)}\"")
        print(f"      {rec.rewrite.target_true}  ->  {rec.rewrite.target_new}")
        print(f"      item-valued properties: {len(items)}  (of {len(claims)} total)")
        for pid, vals in sorted(items.items(), key=lambda kv: kv[0]):
            mark = " <== EDITED" if pid == rel else ""
            shown = ", ".join(lab.get(v, v) for v in vals[:3])
            print(f"        {pid:<7}{lab.get(pid,pid)[:34]:<36}{shown[:44]}{mark}")
        print()


if __name__ == "__main__":
    main()
