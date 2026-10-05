"""NWO (Netherlands) projects -> data/grants/nwo_*.csv

Source: the NWOpen API (https://nwopen-api.nwo.nl/NWOpen-API/api/Projects), every project NWO has
funded since 2016, CC0. The API has no discipline field, so all fields are loaded (like NSF and NIH).
One request a second; each page is cached in data/nwo/, so a rerun fetches only what is missing.
People: the project leader / main applicant is "PI", other members "CoI"; their organisation is the
first two levels of NWO's "University||Faculty||Department" path, as "A | B" (NWO's own institutes,
such as CWI, sit under "NWO-institutenorganisatie"). Dutch university names are matched to the map's
English ones through backup/institution_aliases.csv.
"""

import json
import re
import time
from datetime import date
import urllib.request

from common import DATA, write

CACHE = DATA / "nwo"
API = "https://nwopen-api.nwo.nl/NWOpen-API/api/Projects"
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)"}
LEAD_ROLES = ("project leader", "main applicant", "hoofdaanvrager", "projectleider")


def end_of(p: dict) -> str:
    """NWO's end_date is missing for many projects and, for recent ones, often within months of the
    start (not the planned end). Then it is estimated from NWO's standard lengths: Veni 3 years,
    Vidi and Vici 5, other projects 4 (most fund a four-year PhD position)."""
    start, end = (p.get("start_date") or "")[:10], (p.get("end_date") or "")[:10]
    if not start:
        return end
    s = date.fromisoformat(start)
    if end and (date.fromisoformat(end) - s).days >= 365:
        return end
    scheme = p.get("funding_scheme") or ""
    years = 3 if re.search(r"\bveni\b", scheme, re.I) else 5 if re.search(r"\bvi(di|ci)\b", scheme, re.I) else 4
    return s.replace(year=s.year + years).isoformat() if not (s.month == 2 and s.day == 29) else f"{s.year + years}-03-01"


def page(n: int) -> dict:
    path = CACHE / f"page-{n:05d}.json"
    if path.exists():
        return json.loads(path.read_text())
    req = urllib.request.Request(f"{API}?per_page=100&page={n}", headers=UA)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = json.loads(r.read())
            break
        except OSError as e:
            if attempt == 3:
                raise SystemExit(f"NWO request failed on page {n}: {e}")
            time.sleep(15 * (attempt + 1))
    path.write_text(json.dumps(body))
    time.sleep(1.0)
    return body


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    first = page(1)
    pages = first["meta"]["pages"]
    grants, people = [], []
    for n in range(1, pages + 1):
        for p in (first if n == 1 else page(n))["projects"]:
            pid = p["project_id"]
            summary = (p.get("summary_en") or p.get("summary_nl") or "").strip()
            grants.append({
                "funder": "nwo", "grant_id": pid, "title": (p.get("title") or "").strip(), "abstract": summary,
                "amount": p.get("award_amount") or "", "currency": "EUR", "country": "nl",
                "starts": (p.get("start_date") or "")[:10], "ends": end_of(p),
                "url": f"https://www.nwo.nl/en/projects/{pid.lower().replace('.', '')}",
                "scheme": (p.get("funding_scheme") or "").strip(), "field": p.get("sub_department") or "",
            })
            seen = set()
            members = sorted(p.get("project_members") or [],
                             key=lambda m: (m.get("role") or "").lower() not in LEAD_ROLES)
            for m in members:
                first_name = (m.get("first_name") or m.get("initials") or "").strip()
                last = " ".join(x for x in ((m.get("prefix") or "").strip(), (m.get("last_name") or "").strip()) if x)
                full = f"{first_name} {last}".strip()
                if not last or full in seen:
                    continue
                seen.add(full)
                people.append({"funder": "nwo", "grant_id": pid, "full_name": full, "first_name": first_name,
                               "last_name": last,
                               "role": "PI" if (m.get("role") or "").lower() in LEAD_ROLES else "CoI",
                               "institution": " | ".join(x.strip() for x in (m.get("organisation") or "").split("||")[:2]
                                                         if x.strip()),
                               "orcid": (m.get("orcid") or "")})
        if n % 50 == 0:
            print(f"  page {n}/{pages}")
    write("nwo", grants, people)


if __name__ == "__main__":
    main()
