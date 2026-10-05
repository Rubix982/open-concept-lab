"""Check university map coordinates against OpenStreetMap -> backup/university_coordinates.csv

The geocoded coordinates in the universities table came from matching town names, so some land in
the wrong country (RWTH Aachen near St. Louis). For each university without IPEDS coordinates, this
looks the name up in OpenStreetMap's Nominatim, restricted to the university's own country, and
records a correction when the current point is more than 100 km away (or missing).

Input: data/geo/universities.csv (name,country,latitude,longitude), exported from the database:
    docker exec -e PGPASSWORD=postgres pg17-local psql -h localhost -U postgres -d rank-nsf-linker \\
      --csv -c "SELECT e.name, e.country, e.latitude, e.longitude FROM explorer_universities e
                JOIN universities u ON u.institution = e.name
                LEFT JOIN ipeds_institutions i ON i.unitid = u.ipeds_unitid
                WHERE i.latitude IS NULL AND e.country IS NOT NULL" > data/geo/universities.csv

Nominatim usage policy: at most one request a second, identified, results cached (data/geo/nominatim/).
Existing rows in the output file are kept; names Nominatim can't find are printed for a manual look.
Data © OpenStreetMap contributors, ODbL.
"""

import csv
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "data" / "geo" / "universities.csv"
CACHE = ROOT / "data" / "geo" / "nominatim"
OUT = ROOT / "backup" / "university_coordinates.csv"
API = "https://nominatim.openstreetmap.org/search"
REVERSE = "https://nominatim.openstreetmap.org/reverse"
WIKIDATA = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "advisor-atlas/1.0 (https://github.com/Rubix982/open-concept-lab)"}
MAX_KM = 100       # closer than this: the same place
SAME_COUNTRY_KM = 1500  # in the right country and closer than this: probably another campus, keep it


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(min(1, math.sqrt(h)))


def fetch(cache_key: str, url: str):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha1(cache_key.encode()).hexdigest() + ".json")
    if not path.exists():
        req = urllib.request.Request(url, headers=UA)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    path.write_bytes(resp.read())
                break
            except OSError as e:
                if attempt == 2:
                    print(f"  {cache_key}: {e}")
                    return None
                time.sleep(10)
        time.sleep(1.1)  # Nominatim allows one request a second
    return json.loads(path.read_text())


def lookup(name: str, country: str) -> list[dict]:
    query = urllib.parse.urlencode({"q": name, "countrycodes": country, "format": "jsonv2", "limit": 5})
    return fetch(f"{name}|{country}", f"{API}?{query}") or []


def country_at(lat: float, lon: float) -> str:
    query = urllib.parse.urlencode({"lat": lat, "lon": lon, "format": "jsonv2", "zoom": 3})
    hit = fetch(f"reverse|{lat:.4f}|{lon:.4f}", f"{REVERSE}?{query}") or {}
    return ((hit.get("address") or {}).get("country_code") or "").lower()


# Full names to search under for acronyms and short forms, and countries the export had wrong.
SEARCH_NAMES = {
    "NWPU": "Northwestern Polytechnical University",
    "MUST": "Macau University of Science and Technology",
    "USP - ICMC": "University of São Paulo",
    "TeIAS": "Tehran Institute for Advanced Studies",
    "Tata Inst of Fundamental Research": "Tata Institute of Fundamental Research",
    "Kempelen Institute - KInIT": "Kempelen Institute of Intelligent Technologies",
    "Texas A&M at Qatar": "Texas A&M University at Qatar",
    "HKUST": "Hong Kong University of Science and Technology",
    "IIT (BHU) Varanasi": "Indian Institute of Technology (BHU) Varanasi",
    "CUHK (SZ)": "Chinese University of Hong Kong, Shenzhen",
    "Özyeğin University": "Özyeğin Üniversitesi",
    "Federal University of Rio Grande": "Universidade Federal do Rio Grande, Rio Grande do Sul",
    "Université du Québec à Montréal": "UQAM, Montréal",
    "Beijing Jiaotong University": "北京交通大学, 海淀区",
    "Universidade Federal de Viçosa": "Viçosa, Minas Gerais",  # main campus; the name alone finds a branch
    "Qatar Computing Research Institute": "Hamad Bin Khalifa University",  # QCRI is part of HBKU
    "Texas A&M at Qatar": "Texas A&M University Qatar",
    "IMDEA Networks Institute": "IMDEA Networks",
    "Kempelen Institute - KInIT": "Bratislava",  # not in OpenStreetMap; the city is close enough for the map
    "TeIAS": "Khatam University",  # TeIAS is Khatam University's institute for advanced studies
}
COUNTRY_FIX = {"IIT (BHU) Varanasi": "in", "CUHK (SZ)": "cn"}
# Wikidata files Hong Kong and Macau institutions under China.
SAME_COUNTRY = {"hk": {"hk", "cn"}, "mo": {"mo", "cn"}}


def wikidata(name: str, country: str) -> dict | None:
    """Fallback for names OpenStreetMap doesn't know in English (HKUST, University of Pisa): the first
    Wikidata match with coordinates whose country has the expected ISO code. Data CC0."""
    q = urllib.parse.urlencode({"action": "wbsearchentities", "search": name, "language": "en",
                                "type": "item", "limit": 5, "format": "json"})
    found = fetch(f"wd-search|{name}", f"{WIKIDATA}?{q}") or {}
    for hit in found.get("search", []):
        qid = hit["id"]
        q = urllib.parse.urlencode({"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"})
        claims = ((fetch(f"wd-entity|{qid}", f"{WIKIDATA}?{q}") or {}).get("entities", {}).get(qid, {})
                  .get("claims", {}))
        coord = next((c["mainsnak"].get("datavalue", {}).get("value") for c in claims.get("P625", [])), None)
        land = next((c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in claims.get("P17", [])), None)
        if not coord or not land:
            continue
        q = urllib.parse.urlencode({"action": "wbgetentities", "ids": land, "props": "claims", "format": "json"})
        lc = ((fetch(f"wd-entity|{land}", f"{WIKIDATA}?{q}") or {}).get("entities", {}).get(land, {})
              .get("claims", {}))
        iso = next((c["mainsnak"].get("datavalue", {}).get("value") for c in lc.get("P297", [])), "")
        if iso.lower() in SAME_COUNTRY.get(country.lower(), {country.lower()}):
            return {"lat": coord["latitude"], "lon": coord["longitude"],
                    "display_name": f"{hit.get('label', name)} (Wikidata {qid})", "source": "wikidata"}
    return None


def best(results: list[dict]) -> dict | None:
    """Prefer a university or college over other places with the same name."""
    for r in results:
        if r.get("category") == "amenity" and r.get("type") in ("university", "college"):
            return r
    return results[0] if results else None


def main() -> None:
    rows = list(csv.DictReader(SRC.open(encoding="utf-8")))
    kept: dict[str, dict] = {}
    if OUT.exists():
        kept = {r["institution"]: r for r in csv.DictReader(OUT.open(encoding="utf-8"))}
    unresolved = []
    for r in rows:
        name = r["name"]
        country = COUNTRY_FIX.get(name, r["country"])
        if name in kept:
            continue
        search = SEARCH_NAMES.get(name, name)
        hit = best(lookup(search, country)) or wikidata(search, country)
        if not hit:
            unresolved.append(f"{name} ({country})")
            continue
        found = (float(hit["lat"]), float(hit["lon"]))
        current = (float(r["latitude"]), float(r["longitude"])) if r["latitude"] else None
        if current is not None and km(current, found) > MAX_KM and km(current, found) < SAME_COUNTRY_KM \
                and country_at(*current) == country.lower():
            continue  # right country, plausibly another campus
        if current is None or km(current, found) > MAX_KM:
            moved = f"{km(current, found):.0f} km" if current else "was missing"
            print(f"  {name} ({country}): {moved} -> {hit.get('display_name', '')[:70]}")
            kept[name] = {"institution": name, "latitude": f"{found[0]:.5f}", "longitude": f"{found[1]:.5f}",
                          "source": hit.get("source", "openstreetmap")}
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["institution", "latitude", "longitude", "source"])
        w.writeheader()
        w.writerows(sorted(kept.values(), key=lambda x: x["institution"]))
    print(f"{OUT.relative_to(ROOT)}: {len(kept)} corrections; {len(unresolved)} not found in OpenStreetMap")
    for u in unresolved:
        print(f"  not found: {u}")


if __name__ == "__main__":
    main()
