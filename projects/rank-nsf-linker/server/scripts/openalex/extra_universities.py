"""Universities CSRankings doesn't list, for a country -> backup/extra_universities.csv

CSRankings lists one Pakistani university (LUMS), so Pakistani students see almost nothing at home.
This picks a country's most research-active universities from OpenAlex (by works count) plus a few
named ones, and places each on its campus with OpenStreetMap (OpenAlex only has city centres, which
would stack a city's universities on one dot). fields.py then loads their researchers.

Usage: extra_universities.py pk 20 "Lahore University of Management Sciences=LUMS" "FAST ..." ...
  a name "X=Y" searches OpenAlex for X and lists it as Y (Y is the map's existing name, e.g. LUMS).
Responses cached in data/openalex/extra/. Nominatim: one request a second, identified; ODbL.
"""

import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fetchlib import PARTIAL, secret  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data" / "openalex" / "extra"
OUT = ROOT / "backup" / "extra_universities.csv"
UA = {"User-Agent": "advisor-atlas/1.0 (https://github.com/Rubix982/open-concept-lab)"}
FIELDS = ["institution", "country", "openalex_id", "latitude", "longitude", "homepage", "source"]


def api_key() -> str:
    return secret("OPENALEX_API_KEY")


def cached(name: str, url: str, pause: float, show: str):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha1(name.encode()).hexdigest()[:20] + ".json")
    if path.exists():
        return json.loads(path.read_text())
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            body = json.loads(r.read())
    except urllib.error.HTTPError as e:  # the OpenAlex URL has the key; don't print it
        sys.exit(f"{show}: HTTP {e.code}")
    path.write_text(json.dumps(body))
    time.sleep(pause)
    return body


def openalex(params: dict, key: str) -> dict:
    url = "https://api.openalex.org/institutions?" + urllib.parse.urlencode({**params, "api_key": key})
    return cached("oa|" + json.dumps(params, sort_keys=True), url, 0.3, "OpenAlex")


def campus(name: str, city: str, country: str):
    """The university's own point in OpenStreetMap, else None."""
    for q in (name, f"{name}, {city}"):
        url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
            {"q": q, "countrycodes": country, "format": "jsonv2", "limit": 5})
        hits = cached("osm|" + q + "|" + country, url, 1.1, "Nominatim") or []
        for h in hits:
            if h.get("category") == "amenity" and h.get("type") in ("university", "college"):
                return float(h["lat"]), float(h["lon"])
        if hits:
            return float(hits[0]["lat"]), float(hits[0]["lon"])
    return None


def main() -> None:
    country, top = sys.argv[1].lower(), int(sys.argv[2])
    named = [a.split("=", 1) if "=" in a else [a, ""] for a in sys.argv[3:]]
    key = api_key()
    sel = "id,display_name,works_count,geo,homepage_url"
    picks = openalex({"filter": f"country_code:{country},type:education", "sort": "works_count:desc",
                      "per_page": top, "select": sel}, key)["results"]
    rows = [(i, i["display_name"]) for i in picks]
    for search, as_name in named:
        hit = (openalex({"search": search, "filter": f"country_code:{country}", "per_page": 1, "select": sel},
                        key)["results"] or [None])[0]
        if hit is None:
            print(f"  not in OpenAlex: {search}")
            continue
        rows = [r for r in rows if r[0]["id"] != hit["id"]] + [(hit, as_name or hit["display_name"])]

    kept = {}
    if OUT.exists():
        kept = {(r["country"], r["institution"]): r for r in csv.DictReader(OUT.open(encoding="utf-8"))}
    for inst, name in rows:
        geo = inst.get("geo") or {}
        point = campus(inst["display_name"], geo.get("city") or "", country)
        src = "openalex+openstreetmap"
        if point is None:
            point, src = (geo.get("latitude"), geo.get("longitude")), "openalex (city centre)"
        kept[(country, name)] = {"institution": name, "country": country,
                                 "openalex_id": inst["id"].rsplit("/", 1)[-1],
                                 "latitude": f"{point[0]:.5f}", "longitude": f"{point[1]:.5f}",
                                 "homepage": inst.get("homepage_url") or "", "source": src}
        print(f"  {name}: {point[0]:.4f}, {point[1]:.4f} ({src})")
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(kept.values(), key=lambda r: (r["country"], r["institution"])))
    print(f"{OUT.relative_to(ROOT)}: {len(kept)} universities")


if __name__ == "__main__":
    main()
