"""Researchers outside computer science, from OpenAlex -> data/openalex/fields_*.csv

CSRankings covers computer science only. For the other fields, OpenAlex lists researchers by
institution and field; this keeps a first cut: US R1 universities already on the map and every
university on the map in ten countries Pakistani students often go to (fieldsCountries in
server/fetch.go), 25 fields, and per university and field the most-cited researchers who look like
faculty:
  - the university is their first listed (most recent) institution,
  - 30 to 1,500 works (very large counts are big-collaboration authors), h-index >= 15,
  - publishing in the last three years.
These are researchers, not verified faculty; the explorer labels them as such.

Input: data/openalex/universities.csv (name, country), exported from the database by the pipeline,
and backup/extra_universities.csv (universities CSRankings doesn't list, e.g. Pakistan's; see
extra_universities.py). For those, computer science is fetched too and the faculty thresholds are
lower (smaller research systems: h-index >= 8, 15+ works).
Steps (each response cached in data/openalex/fields/, reruns resume):
  institutions  each university's OpenAlex institution, from the institutions snapshot (no calls)
  authors       researchers per university and field (1 call per pair)
  works         their works since 2021, 50 authors per call (run after the daily allowance resets)
fields.py institutions only does the matching (no calls), for review.
Usage: works.py-style --max-calls N caps the calls of one run.
"""

import csv
import difflib
import hashlib
import json
import re
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fetchlib import PARTIAL, openalex_snapshot, secret, snapshot_records  # noqa: E402

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
    "29": ("nursing", "Nursing", "Medicine"),
    "30": ("pharmacology", "Pharmacology, toxicology and pharmaceutics", "Medicine"),
    "34": ("veterinary", "Veterinary", "Medicine"),
    "35": ("dentistry", "Dentistry", "Medicine"),
    "36": ("health", "Health professions", "Medicine"),
    "32": ("psychology", "Psychology", "Social sciences & humanities"),
    "20": ("economics", "Economics, econometrics and finance", "Social sciences & humanities"),
    "33": ("social", "Social sciences", "Social sciences & humanities"),
    "14": ("business", "Business, management and accounting", "Social sciences & humanities"),
    "18": ("decision", "Decision sciences", "Social sciences & humanities"),
    "12": ("arts", "Arts and humanities", "Social sciences & humanities"),
}
# Each researcher's areas are their main OpenAlex subfields within the field they were found in:
# up to 3, each with at least a quarter of the top subfield's works (author topics carry subfields).
MAX_SUBFIELDS, SUBFIELD_SHARE = 3, 0.25
# Only at extra universities, where CSRankings has no computer science faculty.
EXTRA_FIELDS = {**FIELDS, "17": ("computing", "Computer science (OpenAlex)", "Engineering")}


def api_key() -> str:
    return secret("OPENALEX_API_KEY")


class Client:
    def __init__(self, max_calls: int | None):
        self.key, self.calls, self.max_calls = api_key(), 0, max_calls
        self.lock = threading.Lock()

    @staticmethod
    def cache_file(kind: str, path: str, params: dict) -> Path:
        name = hashlib.sha1((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()[:20]
        return CACHE / kind / f"{name}.json"

    def get(self, kind: str, path: str, params: dict) -> dict | None:
        """Cached GET; None when the call budget of this run is spent."""
        cached = self.cache_file(kind, path, params)
        if cached.exists():
            return json.loads(cached.read_text())
        with self.lock:
            if self.max_calls is not None and self.calls >= self.max_calls:
                return None
            self.calls += 1  # counted when started, so parallel workers respect the budget
        url = API + path + "?" + urllib.parse.urlencode({**params, "api_key": self.key})
        req = urllib.request.Request(url, headers={"User-Agent": "advisor-atlas/1.0 (non-commercial)"})
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.loads(resp.read())
                    if self.calls == 1:
                        print("  remaining today:", resp.headers.get("X-RateLimit-Remaining"))
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and int(e.headers.get("Retry-After") or 0) > 600:
                    with self.lock:  # the day's allowance is spent: no more calls this run
                        self.max_calls = self.calls
                    return None
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
        time.sleep(PAUSE)
        return body


def norm(name: str) -> str:
    """'The Univ. of Alabama' -> 'university of alabama'; 'Technische Universität' -> 'technische universitat'."""
    t = unicodedata.normalize("NFKD", name)
    t = "".join(ch for ch in t if not unicodedata.combining(ch)).lower().replace("&", " and ")
    t = re.sub(r"[^\w]+", " ", t)
    t = re.sub(r"\buniv\b", "university", t)
    t = re.sub(r"\binst\b", "institute", t)
    t = re.sub(r"\btech\b", "technology", t)
    t = re.sub(r"(?<=[a-z])(a|o|u)e(?=[a-z])", r"\1", t)  # German: Universitaet = Universität
    return re.sub(r"^the ", "", re.sub(r"\s+", " ", t).strip())


SMALL_WORDS = {"at", "in", "of", "the", "and", "de", "du", "der", "zu", "a"}


def loose(name: str) -> str:
    """norm() without small words: 'University of Alabama - Birmingham' = 'University of Alabama at Birmingham'."""
    return " ".join(w for w in norm(name).split() if w not in SMALL_WORDS)


def institution_index(countries: set[str]) -> dict[tuple[str, str], list[dict]]:
    """(country, normalised name) -> OpenAlex institutions, from the institutions snapshot (no API
    calls): every display name, alternative name and acronym."""
    index: dict[tuple[str, str], list[dict]] = {}
    for r in snapshot_records(openalex_snapshot("institutions")):
        cc = (r.get("country_code") or "").lower()
        if cc not in countries or not r.get("display_name"):
            continue
        inst = {"id": r["id"].rsplit("/", 1)[-1], "openalex_name": r["display_name"],
                "education": r.get("type") == "education", "works": r.get("works_count") or 0}
        names = [r["display_name"], *(r.get("display_name_alternatives") or []), *(r.get("display_name_acronyms") or [])]
        for n in {norm(n) for n in names if n} | {"~" + loose(n) for n in names if n}:
            index.setdefault((cc, n), []).append(inst)
    return index


def resolve_institutions(c: Client) -> tuple[dict[str, dict], int]:
    """OpenAlex institutions for the universities: a curated id (backup/openalex_institutions.csv),
    else an exact match of the normalised name on an OpenAlex name, alternative name or acronym in
    the same country (a university first, then the one with most works). Never the first search hit:
    that made "Ohio University" Ohio State and UIUC a research centre in Brazil. Universities with no
    match are written to data/openalex/institutions_review.csv with near names, to curate."""
    rows = list(csv.DictReader((DATA / "universities.csv").open(encoding="utf-8")))
    for row in rows:
        row["country"] = (row.get("country") or "us").strip().lower()  # older exports: US R1s only
    curated = {}
    path = ROOT / "backup" / "openalex_institutions.csv"
    if path.exists():
        curated = {(r["name"], r["country"]): r for r in csv.DictReader(path.open(encoding="utf-8"))}
    index = institution_index({r["country"] for r in rows})
    out, review = {}, []
    for row in rows:
        name, cc = row["name"], row["country"]
        if (name, cc) in curated:
            cur = curated[(name, cc)]
            if cur["openalex_id"]:  # an empty id: checked, not in OpenAlex
                out[name] = {"id": cur["openalex_id"], "openalex_name": cur.get("openalex_name") or name}
            continue
        hits = index.get((cc, norm(name))) or index.get((cc, "~" + loose(name)), [])
        if hits:
            best = max(hits, key=lambda h: (h["education"], h["works"]))
            out[name] = {"id": best["id"], "openalex_name": best["openalex_name"]}
            continue
        near = difflib.get_close_matches(norm(name), [k[1] for k in index if k[0] == cc and not k[1].startswith("~")], n=3, cutoff=0.6)
        review.append({"name": name, "country": cc, "candidates": " ; ".join(
            f"{n} = {max(index[(cc, n)], key=lambda h: (h['education'], h['works']))['id']}" for n in near)})
    with (DATA / "institutions_review.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["name", "country", "candidates"])
        w.writeheader()
        w.writerows(review)
    if review:
        print(f"  {len(review)} universities matched no OpenAlex institution: data/openalex/institutions_review.csv")
    extra = ROOT / "backup" / "extra_universities.csv"
    if extra.exists():
        for row in csv.DictReader(extra.open(encoding="utf-8")):
            out[row["institution"]] = {"id": row["openalex_id"], "openalex_name": row["institution"], "extra": True}
    return out, 0


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
    institutions, unresolved = resolve_institutions(c)
    if step == "institutions":  # the matching only, to review: data/openalex/institutions_resolved.csv
        with (DATA / "institutions_resolved.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "openalex_id", "openalex_name"])
            w.writerows(sorted((k, v["id"], v["openalex_name"]) for k, v in institutions.items()))
        print(f"{len(institutions)} universities matched")
        return
    if unresolved:
        print(f"{unresolved} universities not looked up yet (call budget); this run is partial")
    print(f"{len(institutions)} universities resolved to OpenAlex institutions")

    # Fetch every university-and-field page first, eight at a time (OpenAlex takes ~4 s per page and
    # allows 10 requests a second); the
    # loop below then reads them from the cache in a fixed order.
    pages = [authors_params(inst, field_id)
             for inst in institutions.values()
             for field_id in (EXTRA_FIELDS if inst.get("extra") else FIELDS)]
    # Only pages not cached yet, and nothing kept: the loop reads each page once, in order.
    missing = [p for p in pages if not c.cache_file("authors", "authors", p).exists()]
    print(f"  {len(pages) - len(missing)} author pages cached, {len(missing)} to fetch")
    with ThreadPoolExecutor(8) as pool:
        for _ in pool.map(lambda p: c.get("authors", "authors", p) is not None, missing):
            pass

    people, seen, subfields, stopped = [], set(), {}, unresolved > 0
    for uni, inst in institutions.items():
        for field_id, (area, _name, _group) in (EXTRA_FIELDS if inst.get("extra") else FIELDS).items():
            body = c.get("authors", "authors", authors_params(inst, field_id))
            if body is None:
                print(f"stopped at the call budget ({c.calls} calls); rerun to continue")
                stopped = True
                break
            kept = 0
            for a in body.get("results", []):
                aid = a["id"].rsplit("/", 1)[-1]
                if aid in seen or not looks_like_faculty(a, inst["id"], inst.get("extra", False)):
                    continue
                seen.add(aid)
                people.append({"openalex_id": aid, "name": a["display_name"], "university": uni, "area": area,
                               "orcid": (a.get("orcid") or "").rsplit("/", 1)[-1], "works": a["works_count"],
                               "cited_by": a["cited_by_count"], "h_index": a["summary_stats"].get("h_index"),
                               "subfields": ";".join(main_subfields(a, field_id, subfields))})
                kept += 1
                if kept >= TOP_PER_FIELD:
                    break
        else:
            continue
        break
    # Researchers already listed keep their order, so their cached works pages (50 per call) still match.
    previous = DATA / "fields_people.csv"
    if previous.exists():
        order = {r["openalex_id"]: i for i, r in enumerate(csv.DictReader(previous.open(encoding="utf-8")))}
        people.sort(key=lambda p: order.get(p["openalex_id"], len(order)))
    # A run stopped by the call budget, or one that would lose more than a tenth of the researchers
    # listed now, doesn't replace the list the pipeline loads.
    if previous.exists() and not stopped:
        before = sum(1 for _ in csv.DictReader(previous.open(encoding="utf-8")))
        if len(people) < 0.9 * before:
            print(f"only {len(people)} researchers against {before} before: kept the previous list")
            stopped = True
    out = DATA / ("fields_people.partial.csv" if stopped else "fields_people.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["openalex_id", "name", "university", "area", "orcid", "works",
                                          "cited_by", "h_index", "subfields"])
        w.writeheader()
        w.writerows(people)
    if not stopped:
        with (DATA / "subfields.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["subfield_id", "name", "field_id"])
            w.writerows(sorted((k, v[0], v[1]) for k, v in subfields.items()))
    print(f"{out.relative_to(ROOT)}: {len(people)} researchers ({c.calls} calls this run)")
    if stopped:
        sys.exit(PARTIAL)

    if step != "works":
        return
    fetch_works(c, people)


WORKS_COLUMNS = ["openalex_id", "work_id", "title", "year", "venue", "doi", "abstract"]
WORKS_DONE = DATA / "fields_works_done.txt"  # researchers whose works were asked for (some have none)
# Groups of 50 researchers per works call, fixed once made: a group's cached pages only match while
# its members stay the same, so groups are never recomputed, only appended to.
WORKS_GROUPS = DATA / "fields_works_groups.json"


def cached_works(keep: set[str]):
    """Every (researcher, work) in the cached works pages, for researchers in keep. The cache is the
    record of everything ever fetched, so the works file is rebuilt from it, never copied from the
    previous file (a bad run once shrank that file and the next copy kept the loss)."""
    for path in sorted((CACHE / "works").glob("*.json")):
        try:
            body = json.loads(path.read_text())
        except ValueError:
            continue
        for wk in body.get("results", []):
            authors = {(a.get("author") or {}).get("id", "").rsplit("/", 1)[-1]
                       for a in wk.get("authorships") or [] if (a.get("author") or {}).get("id")}
            mine = authors & keep
            if not mine:
                continue
            venue = ((wk.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
            row = {"work_id": wk["id"].rsplit("/", 1)[-1], "title": (wk.get("title") or "").strip(),
                   "year": wk.get("publication_year") or "", "venue": venue, "doi": wk.get("doi") or "",
                   "abstract": abstract_text(wk.get("abstract_inverted_index"))}
            for aid in mine:
                yield {"openalex_id": aid, **row}


def fetch_works(c: Client, people: list[dict]) -> None:
    """Works since WORKS_FROM for every researcher. Researchers with no cached works are asked for
    in groups of 50, kept in fields_works_groups.json so a run stopped by the call budget resumes
    on the same groups; then the file is rebuilt from the whole cache."""
    out = DATA / "fields_works.csv"
    keep = {p["openalex_id"] for p in people}
    asked = set(WORKS_DONE.read_text().split()) if WORKS_DONE.exists() else set()
    have = {r["openalex_id"] for r in cached_works(keep)}
    need = keep - have - asked
    saved = json.loads(WORKS_GROUPS.read_text()) if WORKS_GROUPS.exists() else []
    grouped = {aid for g in saved for aid in g}
    fresh = sorted(need - grouped)
    saved += [fresh[i:i + 50] for i in range(0, len(fresh), 50)]
    WORKS_GROUPS.write_text(json.dumps(saved))
    groups = [g for g in saved if need & set(g)]
    print(f"  cached works for {len(have)} researchers; {len(need)} to ask ({len(groups)} groups)")
    firsts = [works_params(g, 1) for g in groups]
    missing = [p for p in firsts if not c.cache_file("works", "works", p).exists()]
    with ThreadPoolExecutor(8) as pool:
        for _ in pool.map(lambda p: c.get("works", "works", p) is not None, missing):
            pass
    stopped = False
    for group in groups:  # later pages, and which groups are now fully asked
        complete, body = False, None
        for page in range(1, 4):  # 50 authors can have more than 200 recent works
            body = c.get("works", "works", works_params(group, page))
            if body is None:  # over budget: ask again next run
                stopped = True
                break
            if (body.get("meta") or {}).get("count", 0) <= page * 200:
                complete = True
                break
        if (complete or page == 3) and body is not None:
            asked.update(group)
    tmp = out.with_suffix(".csv.tmp")
    rows, seen = 0, set()
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=WORKS_COLUMNS)
        w.writeheader()
        for r in cached_works(keep):
            key = (r["openalex_id"], r["work_id"])
            if key not in seen:
                seen.add(key)
                w.writerow(r)
                rows += 1
    tmp.replace(out)
    WORKS_DONE.write_text("\n".join(sorted(asked)))
    print(f"data/openalex/fields_works.csv: {rows} author-work rows ({c.calls} calls this run)")
    if stopped:
        print("call budget reached; rerun later for the rest")
        sys.exit(PARTIAL)


def works_params(group: list[str], page: int) -> dict:
    params = {"filter": f"authorships.author.id:{'|'.join(group)},from_publication_date:{WORKS_FROM}",
              "sort": "publication_date:desc", "per_page": 200,
              "select": "id,doi,title,publication_year,abstract_inverted_index,authorships,primary_location"}
    if page > 1:
        params["page"] = page
    return params


def authors_params(inst: dict, field_id: str) -> dict:
    return {"filter": f"last_known_institutions.id:{inst['id']},topics.field.id:{field_id}",
            "sort": "cited_by_count:desc", "per_page": 200,
            "select": "id,display_name,orcid,works_count,cited_by_count,summary_stats,"
                      "last_known_institutions,counts_by_year,topics"}


def main_subfields(a: dict, field_id: str, names: dict) -> list[str]:
    """The researcher's main subfields within field_id, from their topics; records each name."""
    counts: dict[str, int] = {}
    for t in a.get("topics") or []:
        sub, field = t.get("subfield") or {}, t.get("field") or {}
        if (field.get("id") or "").rsplit("/", 1)[-1] != field_id or not sub.get("id"):
            continue
        sid = sub["id"].rsplit("/", 1)[-1]
        names[sid] = (sub.get("display_name") or sid, field_id)
        counts[sid] = counts.get(sid, 0) + (t.get("count") or 0)
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    top = ranked[0][1] if ranked else 0
    return [sid for sid, n in ranked[:MAX_SUBFIELDS] if n >= SUBFIELD_SHARE * top]


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
