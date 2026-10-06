"""UKRI Gateway to Research (GtR), EPSRC grants -> data/grants/ukri_*.csv

Source: https://gtr.ukri.org, Open Government Licence v2.0 (attribution: UKRI Gateway to Research).
1. The EPSRC Research Grant and Fellowship lists come from the GtR CSV export (slow: the server
   streams a few KB/s, so a full export takes about an hour). Cached in data/ukri/*.csv.
2. Computing projects are kept by department ("Computer Science", "Informatics", "Electronics and
   Computer Science", ...) or by a computing word in the title, ending 2015 or later.
3. Each kept project's JSON (abstract, co-investigators) is fetched at about one request a second
   and cached in data/ukri/projects/, so an interrupted run resumes where it stopped.

Pass --refresh to re-download the CSV lists; --no-details to skip step 3 (PIs and titles only).
"""

import csv
import http.client
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from common import DATA, split_name, write

CACHE = DATA / "ukri"
EXPORT = "https://gtr.ukri.org/search/project/csv?term=*&selectedFacets="
EPSRC = "ZnVuZGVyfEVQU1JDfHN0cmluZw=="  # funder|EPSRC|string
LISTS = {
    "epsrc-research-grant": EPSRC + ",Y2F0fFJlc2VhcmNoIEdyYW50fHN0cmluZw==",  # cat|Research Grant|string
    "epsrc-fellowship": EPSRC + ",Y2F0fEZlbGxvd3NoaXB8c3RyaW5n",  # cat|Fellowship|string
}
PROJECT = "https://gtr.ukri.org/api/projects?ref="
UA = {"User-Agent": "advisor-atlas/1.0 (research explorer; non-commercial)"}

CS_DEPARTMENT = re.compile(
    r"comput|informatic|electronic|electrical|\beecs\b|data science|artificial intel|cyber|software|"
    r"school of math.*comput|robotic", re.I)
CS_TITLE = re.compile(
    r"comput|algorithm|machine learning|deep learning|neural net|artificial intelligence|\bAI\b|software|"
    r"program(ming)? language|verification|cyber|cryptograph|robot|natural language|database|"
    r"distributed system|operating system|compiler|human-computer|\bHCI\b|data science|privacy", re.I)
MIN_END_YEAR = 2015


def download(name: str, facets: str, refresh: bool) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.csv"
    if refresh or not path.exists():
        part = path.with_suffix(".csv.part")
        req = urllib.request.Request(EXPORT + facets, headers=UA)
        for attempt in range(6):  # the export cannot resume, so a dropped connection restarts it
            print(f"downloading {name} (slow export, be patient)")
            try:
                with urllib.request.urlopen(req, timeout=600) as resp, part.open("wb") as f:
                    got = 0
                    while chunk := resp.read(1 << 16):
                        f.write(chunk)
                        got += len(chunk)
                        if got % (1 << 22) < (1 << 16):
                            print(f"  {name}: {got >> 20} MB")
                break
            except (TimeoutError, OSError, http.client.HTTPException) as e:
                if attempt == 5:
                    raise
                print(f"  {name}: {e}; retrying in {60 * (attempt + 1)} s")
                time.sleep(60 * (attempt + 1))
        part.rename(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def iso(day: str) -> str:
    """'05/01/2009' -> '2009-01-05'."""
    try:
        return datetime.strptime(day.strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return ""


def details(ref: str) -> dict | None:
    folder = CACHE / "projects"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (ref.replace("/", "_") + ".json")
    if not path.exists():
        req = urllib.request.Request(PROJECT + urllib.parse.quote(ref, safe=""), headers=UA)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    path.write_bytes(resp.read())
                break
            except (TimeoutError, OSError) as e:
                if attempt == 3:
                    print(f"{ref}: {e}; skipped")
                    return None
                time.sleep(10 * (attempt + 1))
        time.sleep(1)  # about one request a second
    try:
        return json.loads(path.read_text())["projectOverview"]["projectComposition"]
    except (ValueError, KeyError, TypeError):
        return None


def main() -> None:
    # The export lists are downloaded again when two weeks old (the fetcher runs UKRI fortnightly)
    lists = list(CACHE.glob("*.csv"))
    refresh = "--refresh" in sys.argv or not lists or min(p.stat().st_mtime for p in lists) < time.time() - 13 * 86400
    with_details = "--no-details" not in sys.argv
    rows = []
    for name, facets in LISTS.items():
        rows += download(name, facets, refresh)

    kept, seen = [], set()
    for r in rows:
        ref = r["ProjectReference"].strip()
        end = iso(r["EndDate"])
        if not ref or ref in seen or not end or int(end[:4]) < MIN_END_YEAR:
            continue
        if not (CS_DEPARTMENT.search(r["Department"] or "") or CS_TITLE.search(r["Title"] or "")):
            continue
        seen.add(ref)
        kept.append(r)
    print(f"{len(rows)} EPSRC grants and fellowships, {len(kept)} computing projects ending {MIN_END_YEAR}+")

    grants, people = [], []
    for i, r in enumerate(kept, 1):
        ref = r["ProjectReference"].strip()
        org = (r["LeadROName"] or "").strip()
        grant = {
            "funder": "ukri", "grant_id": ref, "title": r["Title"].strip(), "abstract": "",
            "amount": r["AwardPounds"] or "", "currency": "GBP", "country": "gb",
            "starts": iso(r["StartDate"]), "ends": iso(r["EndDate"]),
            "url": "https://gtr.ukri.org/projects?ref=" + urllib.parse.quote(ref, safe=""),
            "scheme": f"EPSRC {r['ProjectCategory']}".strip(), "field": (r["Department"] or "").strip(),
        }
        persons = []
        comp = details(ref) if with_details else None
        if comp:
            p = comp.get("project") or {}
            grant["abstract"] = (p.get("abstractText") or "").strip()
            org = ((comp.get("leadResearchOrganisation") or {}).get("name") or org).strip()
            subjects = [s.get("text") for s in p.get("researchSubjects") or [] if s.get("text")]
            if subjects:
                grant["field"] = "; ".join(subjects)
            for role, key in (("PI", "principalInvestigators"), ("CoI", "coInvestigators")):
                for person in comp.get(key) or []:
                    first = " ".join(x for x in (person.get("firstName"), person.get("otherNames")) if x)
                    last = (person.get("surname") or "").strip()
                    if last:
                        persons.append((role, first.strip(), last, person.get("orcidId") or ""))
        if not persons and r["PISurname"]:
            first = " ".join(x for x in (r["PIFirstName"], r["PIOtherNames"]) if x)
            persons.append(("PI", first.strip(), r["PISurname"].strip(), r["PI ORCID iD"] or ""))
        grants.append(grant)
        for role, first, last, orcid in persons:
            full, f, l = split_name(f"{first} {last}".strip())
            people.append({
                "funder": "ukri", "grant_id": ref, "full_name": full, "first_name": first or f,
                "last_name": last or l, "role": role, "institution": org,
                "orcid": orcid.rsplit("/", 1)[-1] if orcid else "",
            })
        if i % 500 == 0:
            print(f"  {i}/{len(kept)} projects at {datetime.now(timezone.utc):%H:%M}")
    write("ukri", grants, people)


if __name__ == "__main__":
    main()
