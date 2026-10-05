"""NWO (Netherlands) projects -> data/grants/nwo_*.csv

Source: the NWOpen API (https://nwopen-api.nwo.nl/NWOpen-API/api/Projects), every project NWO has
funded since 2016, CC0. The API has no discipline field, so all fields are loaded (like NSF and NIH).
One request a second; each page is cached in data/nwo/, so a rerun fetches only what is missing.
People: the project leader / main applicant is "PI", other members "CoI"; their organisation is the
first part of NWO's "University||Faculty||Department" path.
"""

import json
import time
import urllib.request

from common import DATA, write

CACHE = DATA / "nwo"
API = "https://nwopen-api.nwo.nl/NWOpen-API/api/Projects"
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)"}
LEAD_ROLES = ("project leader", "main applicant", "hoofdaanvrager", "projectleider")


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
                "starts": (p.get("start_date") or "")[:10], "ends": (p.get("end_date") or "")[:10],
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
                               "institution": (m.get("organisation") or "").split("||")[0].strip(),
                               "orcid": (m.get("orcid") or "")})
        if n % 50 == 0:
            print(f"  page {n}/{pages}")
    write("nwo", grants, people)


if __name__ == "__main__":
    main()
