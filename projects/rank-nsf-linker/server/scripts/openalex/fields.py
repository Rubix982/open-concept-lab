"""Researchers outside computer science, from OpenAlex -> data/openalex/fields_*.csv

CSRankings covers computer science only. For the other fields, OpenAlex lists researchers by
institution and field; this keeps a first cut: US R1 universities already on the map, a dozen
science, engineering and medicine fields, and per university and field the most-cited researchers
who look like faculty:
  - the university is their first listed (most recent) institution,
  - 30 to 1,500 works (very large counts are big-collaboration authors), h-index >= 15,
  - publishing in the last three years.
These are researchers, not verified faculty; the explorer labels them as such.

Input: data/openalex/universities.csv (name, the explorer's R1 universities), exported from the database,
and backup/extra_universities.csv (universities CSRankings doesn't list, e.g. Pakistan's; see
extra_universities.py). For those, computer science is fetched too and the faculty thresholds are
lower (smaller research systems: h-index >= 8, 15+ works).
Steps (each response cached in data/openalex/fields/, reruns resume):
  institutions  resolve each university to an OpenAlex institution id (1 call per university)
  authors       researchers per university and field (1 call per pair)
  works         their works since 2021, 50 authors per call (run after the daily allowance resets)
Usage: works.py-style --max-calls N caps the calls of one run.
"""

import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "openalex"
CACHE = DATA / "fields"
API = "https://api.openalex.org/"
PAUSE = 0.3
TOP_PER_FIELD = 20  # most-cited per university and field; more would swamp the explorer
WORKS_FROM = "2021-01-01"

# OpenAlex field id -> (area id, area name, group). Computer Science (17) comes from CSRankings.
FIELDS = {
    "31": ("physics", "Physics and astronomy", "Sciences"),
    "16": ("chemistry", "Chemistry", "Sciences"),
    "26": ("mathematics", "Mathematics", "Sciences"),
    "13": ("biochemistry", "Biochemistry, genetics and molecular biology", "Sciences"),
    "11": ("agbio", "Agricultural and biological sciences", "Sciences"),
    "19": ("earth", "Earth and planetary sciences", "Sciences"),
    "23": ("environment", "Environmental science", "Sciences"),
    "25": ("materials", "Materials science", "Engineering"),
    "22": ("engineering", "Engineering", "Engineering"),
    "15": ("chemeng", "Chemical engineering", "Engineering"),
    "21": ("energy", "Energy", "Engineering"),
    "27": ("medicine", "Medicine", "Medicine"),
    "28": ("neuroscience", "Neuroscience", "Medicine"),
    "24": ("immunology", "Immunology and microbiology", "Medicine"),
}
# Only at extra universities, where CSRankings has no computer science faculty.
EXTRA_FIELDS = {**FIELDS, "17": ("computing", "Computer science (OpenAlex)", "Engineering")}


def api_key() -> str:
    for line in (ROOT / "server" / ".env").read_text().splitlines():
        if line.startswith("OPENALEX_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENALEX_API_KEY is not set in server/.env")


class Client:
    def __init__(self, max_calls: int | None):
        self.key, self.calls, self.max_calls = api_key(), 0, max_calls

    def get(self, kind: str, path: str, params: dict) -> dict | None:
        """Cached GET; None when the call budget of this run is spent."""
        name = hashlib.sha1((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:20]
        cached = CACHE / kind / f"{name}.json"
        if cached.exists():
            return json.loads(cached.read_text())
        if self.max_calls is not None and self.calls >= self.max_calls:
            return None
        url = API + path + "?" + urllib.parse.urlencode({**params, "api_key": self.key})
        req = urllib.request.Request(url, headers={"User-Agent": "advisor-atlas/1.0 (non-commercial)"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.loads(resp.read())
                    if self.calls == 0:
                        print("  remaining today:", resp.headers.get("X-RateLimit-Remaining"))
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    time.sleep(30 * (attempt + 1))
                    continue
                raise SystemExit(f"OpenAlex refused a request: HTTP {e.code}")  # URL has the key
            except (TimeoutError, OSError):
                time.sleep(15 * (attempt + 1))
        else:
            raise SystemExit("OpenAlex kept failing; stopping (rerun to resume)")
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(json.dumps(body))
        self.calls += 1
        time.sleep(PAUSE)
        return body


def resolve_institutions(c: Client) -> dict[str, dict]:
    out = {}
    for row in csv.DictReader((DATA / "universities.csv").open(encoding="utf-8")):
        body = c.get("institutions", "institutions", {"search": row["name"], "filter": "country_code:us",
                                                       "per_page": 5, "select": "id,display_name,type,ror"})
        if body is None:
            break
        hit = next((i for i in body.get("results", []) if i.get("type") in ("education", "facility")), None)
        if hit:
            out[row["name"]] = {"id": hit["id"].rsplit("/", 1)[-1], "openalex_name": hit["display_name"]}
    extra = ROOT / "backup" / "extra_universities.csv"
    if extra.exists():
        for row in csv.DictReader(extra.open(encoding="utf-8")):
            out[row["institution"]] = {"id": row["openalex_id"], "openalex_name": row["institution"], "extra": True}
    return out


def looks_like_faculty(a: dict, inst_id: str, extra: bool = False) -> bool:
    insts = a.get("last_known_institutions") or []
    if not insts or insts[0]["id"].rsplit("/", 1)[-1] != inst_id:
        return False
    stats = a.get("summary_stats") or {}
    recent = [y for y in a.get("counts_by_year") or [] if y["year"] >= date.today().year - 3 and y["works_count"]]
    min_works, min_h = (15, 8) if extra else (30, 15)
    return min_works <= (a.get("works_count") or 0) <= 1500 and (stats.get("h_index") or 0) >= min_h and bool(recent)


def main() -> None:
    max_calls = int(sys.argv[sys.argv.index("--max-calls") + 1]) if "--max-calls" in sys.argv else None
    step = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "authors"
    c = Client(max_calls)
    institutions = resolve_institutions(c)
    print(f"{len(institutions)} universities resolved to OpenAlex institutions")

    people, seen = [], set()
    for uni, inst in institutions.items():
        for field_id, (area, _name, _group) in (EXTRA_FIELDS if inst.get("extra") else FIELDS).items():
            body = c.get("authors", "authors", {
                "filter": f"last_known_institutions.id:{inst['id']},topics.field.id:{field_id}",
                "sort": "cited_by_count:desc", "per_page": 200,
                "select": "id,display_name,orcid,works_count,cited_by_count,summary_stats,"
                          "last_known_institutions,counts_by_year"})
            if body is None:
                print(f"stopped at the call budget ({c.calls} calls); rerun to continue")
                break
            kept = 0
            for a in body.get("results", []):
                aid = a["id"].rsplit("/", 1)[-1]
                if aid in seen or not looks_like_faculty(a, inst["id"], inst.get("extra", False)):
                    continue
                seen.add(aid)
                people.append({"openalex_id": aid, "name": a["display_name"], "university": uni, "area": area,
                               "orcid": (a.get("orcid") or "").rsplit("/", 1)[-1], "works": a["works_count"],
                               "cited_by": a["cited_by_count"], "h_index": a["summary_stats"].get("h_index")})
                kept += 1
                if kept >= TOP_PER_FIELD:
                    break
        else:
            continue
        break
    with (DATA / "fields_people.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["openalex_id", "name", "university", "area", "orcid", "works",
                                          "cited_by", "h_index"])
        w.writeheader()
        w.writerows(people)
    print(f"data/openalex/fields_people.csv: {len(people)} researchers ({c.calls} calls this run)")

    if step != "works":
        return
    works, ids = [], [p["openalex_id"] for p in people]
    for i in range(0, len(ids), 50):
        group, wanted = ids[i:i + 50], set(ids[i:i + 50])
        for page in range(1, 4):  # 50 authors can have more than 200 recent works
            params = {"filter": f"authorships.author.id:{'|'.join(group)},from_publication_date:{WORKS_FROM}",
                      "sort": "publication_date:desc", "per_page": 200,
                      "select": "id,doi,title,publication_year,abstract_inverted_index,authorships,primary_location"}
            if page > 1:
                params["page"] = page
            body = c.get("works", "works", params)
            if body is None:
                print(f"stopped at the call budget ({c.calls} calls); rerun to continue")
                break
            for wk in body.get("results", []):
                authors = {(a.get("author") or {}).get("id", "").rsplit("/", 1)[-1]
                           for a in wk.get("authorships") or [] if (a.get("author") or {}).get("id")}
                venue = ((wk.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
                abstract = abstract_text(wk.get("abstract_inverted_index"))
                for aid in authors & wanted:
                    works.append({"openalex_id": aid, "work_id": wk["id"].rsplit("/", 1)[-1],
                                  "title": (wk.get("title") or "").strip(), "year": wk.get("publication_year") or "",
                                  "venue": venue, "doi": (wk.get("doi") or ""), "abstract": abstract})
            if (body.get("meta") or {}).get("count", 0) <= page * 200:
                break
        else:
            continue
        if body is None:
            break
    with (DATA / "fields_works.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["openalex_id", "work_id", "title", "year", "venue", "doi", "abstract"])
        w.writeheader()
        w.writerows(works)
    print(f"data/openalex/fields_works.csv: {len(works)} author-work rows ({c.calls} calls this run)")


def abstract_text(inverted: dict | None) -> str:
    if not inverted:
        return ""
    words = {}
    for word, positions in inverted.items():
        for p in positions:
            words[p] = word
    return " ".join(words[i] for i in sorted(words))


if __name__ == "__main__":
    main()
