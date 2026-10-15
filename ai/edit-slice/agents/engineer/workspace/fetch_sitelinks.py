"""Sitelink counts for the entities behind [E-038]'s aliases — the popularity proxy for [E-043].

    .venv/bin/python agents/engineer/workspace/fetch_sitelinks.py

How many Wikipedia language editions carry an entity is the standard cheap proxy for how
well known it is. Cached to `data/wikidata/sitelinks.json` so [E-043] re-runs offline, and
throttled like `src/wikidata.py` because it is the same API and the same courtesy applies.

This script, not the cached bytes, is the record of what was fetched and from where.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://www.wikidata.org/w/api.php"
THROTTLE_S = 0.2
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DEST = os.path.join(ROOT, "data", "wikidata", "sitelinks.json")
sys.path.insert(0, os.path.join(ROOT, "agents", "engineer", "workspace"))
from ripple_forms import subject_label  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "src"))
from wikidata import UA  # noqa: E402


def qids_for_aliases() -> dict[str, str]:
    """canonical subject -> QID, for every subject behind [E-040]'s alias rows."""
    rows = json.load(open(os.path.join(ROOT, "results", "E-040-alias-gradient.json"),
                          encoding="utf-8"))["rows"]
    want = {r["canon"] for r in rows}
    out: dict[str, str] = {}
    for sub in ("recent", "random", "popular"):
        path = os.path.join(ROOT, "data", "ripple", f"{sub}.json")
        for e in json.load(open(path, encoding="utf-8")):
            lab = subject_label(e)
            if lab in want and lab not in out:
                qid = (e.get("edit") or {}).get("subject_id") or e.get("subject_id")
                if qid:
                    out[lab] = qid
    missing = want - set(out)
    if missing:
        print(f"  {len(missing)} canonical subjects without a QID (reported, not dropped "
              f"silently): {sorted(missing)[:3]}")
    return out


def main() -> int:
    have = json.load(open(DEST, encoding="utf-8")) if os.path.exists(DEST) else {}
    qmap = qids_for_aliases()
    qids = sorted(set(qmap.values()))
    todo = [q for q in qids if q not in have]
    print(f"{len(qids)} entities; {len(have)} cached, {len(todo)} to fetch")
    for i in range(0, len(todo), 45):
        batch = todo[i: i + 45]
        url = API + "?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(batch),
             "props": "sitelinks", "format": "json"})
        # Wikidata returns 403 without a User-Agent. Reusing `src/wikidata.py`'s rather
        # than inventing one, so both fetchers identify this project the same way.
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as fh:
            res = json.load(fh)
        for qid, payload in (res.get("entities") or {}).items():
            have[qid] = len(payload.get("sitelinks") or {})
        for b in batch:
            have.setdefault(b, 0)          # absent is zero, recorded not guessed
        print(f"  {min(i + 45, len(todo))}/{len(todo)}")
        time.sleep(THROTTLE_S)
    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    with open(DEST, "w", encoding="utf-8") as fh:
        json.dump({"_": "sitelink counts, the [E-043] popularity proxy",
                   "subject_to_qid": qmap, "sitelinks": have}, fh, indent=1)
    vals = [have[q] for q in qids]
    vals.sort()
    print(f"\nwritten {os.path.relpath(DEST, ROOT)}")
    print(f"  sitelinks: min {vals[0]}  median {vals[len(vals)//2]}  max {vals[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
