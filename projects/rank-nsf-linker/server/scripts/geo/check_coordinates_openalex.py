"""Second pass after check_coordinates.py (OpenStreetMap): check map coordinates that still come from
the old CSRankings geolocation.csv against OpenAlex. check_coordinates.py keeps a point that is in the
right country even when it is far off (LUMS sat near Faisalabad, Waseda 844 km from Tokyo); this
catches those. OpenAlex points are city centres, so only gaps over ~90 km are worth taking.

Input: a list of "institution|country code" lines (universities without IPEDS or curated coordinates).
For each, OpenAlex's institution search (same country) gives a location; where it is more than 25 km
from ours and the names agree, the OpenAlex point is written to data/geo/coordinate_fixes.csv for
review and merging into backup/university_coordinates.csv (source "openalex").
Usage: check_coordinates.py <list> [--max-calls N]   (responses cached in data/geo/openalex/)
"""

import csv
import hashlib
import json
import math
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "geo"
CACHE = OUT / "openalex"


def api_key() -> str:
    for line in (ROOT / "server" / ".env").read_text().splitlines():
        if line.startswith("OPENALEX_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENALEX_API_KEY is not set in server/.env")


def km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in {"of", "the", "university", "and", "de", "di"}}


def main() -> None:
    rows = [l.strip().split("|") for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    max_calls = int(sys.argv[sys.argv.index("--max-calls") + 1]) if "--max-calls" in sys.argv else 600
    current = {}
    for r in csv.DictReader((ROOT / "data" / "geolocation.csv").open(encoding="utf-8")):
        current[r["institution"]] = (float(r["latitude"]), float(r["longitude"]))
    key, calls, fixes = api_key(), 0, []
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, cc in rows:
        if name not in current or not cc:
            continue
        params = {"search": name, "filter": f"country_code:{cc}", "per_page": 3,
                  "select": "display_name,display_name_acronyms,geo,type"}
        cached = CACHE / (hashlib.sha1(json.dumps(params, sort_keys=True).encode()).hexdigest()[:20] + ".json")
        if cached.exists():
            body = json.loads(cached.read_text())
        else:
            if calls >= max_calls:
                print("call budget reached; rerun to continue")
                break
            url = "https://api.openalex.org/institutions?" + urllib.parse.urlencode({**params, "api_key": key})
            req = urllib.request.Request(url, headers={"User-Agent": "advisor-atlas/1.0 (non-commercial)"})
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    body = json.loads(resp.read())
            except urllib.error.HTTPError as e:  # the URL has the key; don't print it
                print(f"  {name}: HTTP {e.code}")
                continue
            cached.write_text(json.dumps(body))
            calls += 1
            time.sleep(0.3)
        hit = next((h for h in body.get("results", []) if (h.get("geo") or {}).get("latitude") is not None), None)
        if not hit:
            continue
        theirs = (hit["geo"]["latitude"], hit["geo"]["longitude"])
        d = km(current[name], theirs)
        # Names must share a word (or the acronym must match), so a wrong search hit isn't taken.
        acronyms = [a.lower() for a in hit.get("display_name_acronyms") or []]
        same = bool(words(name) & words(hit["display_name"])) or name.lower() in acronyms
        if d > 25:
            fixes.append({"institution": name, "latitude": round(theirs[0], 5), "longitude": round(theirs[1], 5),
                          "source": "openalex", "km_off": round(d), "openalex_name": hit["display_name"],
                          "city": hit["geo"].get("city") or "", "names_agree": same})
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "coordinate_fixes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["institution", "latitude", "longitude", "source", "km_off",
                                          "openalex_name", "city", "names_agree"])
        w.writeheader()
        w.writerows(sorted(fixes, key=lambda x: -x["km_off"]))
    print(f"{len(fixes)} universities more than 25 km off ({calls} calls) -> data/geo/coordinate_fixes.csv")


if __name__ == "__main__":
    main()
