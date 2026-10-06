"""NIH (US National Institutes of Health) active projects -> data/grants/nih_*.csv

Source: NIH RePORTER API v2 (https://api.reporter.nih.gov/), public data. NIH asks for at most one
request a second and large jobs at off-peak hours; responses are cached in data/nih/, so a rerun
only fetches what is missing. Queries: projects active in fiscal years 2025-2026, one query per
state and year (a search returns at most 15,000 records).

NIH funds biomedical research across fields, so all active projects are kept; the linker attaches
them to faculty and researchers by name and institution. One grant per core project number
(yearly renewals collapse), with its latest fiscal year's details.
"""

import json
import re
import time
import urllib.error
import urllib.request

from common import DATA, write
from fetchlib import refetch_or_keep

CACHE = DATA / "nih"
API = "https://api.reporter.nih.gov/v2/projects/search"
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)", "Content-Type": "application/json"}
YEARS = [2025, 2026]
PAGE = 500
PAGE_MAX_AGE = 6  # days: active projects change; the fetcher runs NIH weekly
STATES = ("AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM "
          "NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR").split()
FIELDS = ["ProjectNum", "CoreProjectNum", "ProjectTitle", "AbstractText", "PrincipalInvestigators",
          "Organization", "FiscalYear", "AwardAmount", "ProjectStartDate", "ProjectEndDate", "ActivityCode",
          "AgencyIcAdmin", "ProjectDetailUrl"]


def search(state: str, year: int, offset: int) -> dict:
    path = CACHE / f"{year}-{state}-{offset:05d}.json"
    return json.loads(refetch_or_keep(path, PAGE_MAX_AGE, lambda: json.dumps(fetch(state, year, offset))))


def fetch(state: str, year: int, offset: int) -> dict:
    body = json.dumps({"criteria": {"fiscal_years": [year], "org_states": [state], "include_active_projects": True},
                       "include_fields": FIELDS, "offset": offset, "limit": PAGE,
                       "sort_field": "project_start_date", "sort_order": "desc"}).encode()
    for attempt in range(5):
        try:
            req = urllib.request.Request(API, data=body, headers=UA, method="POST")
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read())
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            if attempt == 4:
                raise SystemExit(f"NIH RePORTER failed for {state} {year}: {e}")
            time.sleep(20 * (attempt + 1))
    time.sleep(1.1)  # NIH: no more than one request a second
    return data


def institution_variants(org: str) -> str:
    """'UNIVERSITY OF MICHIGAN AT ANN ARBOR' -> 'University Of Michigan At Ann Arbor | University Of
    Michigan', so the linker can match the CSRankings name."""
    base = re.sub(r"\s+", " ", org).strip().title()
    variants = [base]
    for pattern in (r"\s+At\s+.*$", r",\s*.*$", r"\s+(Health Science Center|Medical Center|School Of Medicine)$"):
        v = re.sub(pattern, "", base).strip()
        if v and v not in variants:
            variants.append(v)
    return " | ".join(variants)


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    latest: dict[str, dict] = {}
    for year in YEARS:
        for state in STATES:
            offset = 0
            while offset < 15000:
                data = search(state, year, offset)
                results = data.get("results") or []
                for p in results:
                    core = p.get("core_project_num") or p.get("project_num")
                    if core and (core not in latest or (p.get("fiscal_year") or 0) >= (latest[core].get("fiscal_year") or 0)):
                        latest[core] = p
                total = (data.get("meta") or {}).get("total") or 0
                offset += PAGE
                if offset >= total or not results:
                    break
        print(f"fiscal year {year}: {len(latest)} core projects so far")

    grants, people = [], []
    for core, p in latest.items():
        org = (p.get("organization") or {}).get("org_name") or ""
        grants.append({
            "funder": "nih", "grant_id": core, "title": (p.get("project_title") or "").strip(),
            "abstract": (p.get("abstract_text") or "").strip()[:4000],
            "amount": p.get("award_amount") or "", "currency": "USD", "country": "us",
            "starts": (p.get("project_start_date") or "")[:10], "ends": (p.get("project_end_date") or "")[:10],
            "url": p.get("project_detail_url") or f"https://reporter.nih.gov/project-details/{p.get('appl_id', '')}",
            "scheme": p.get("activity_code") or "", "field": (p.get("agency_ic_admin") or {}).get("abbreviation") or "",
        })
        for pi in p.get("principal_investigators") or []:
            first = " ".join(x for x in (pi.get("first_name"), pi.get("middle_name")) if x).strip()
            last = (pi.get("last_name") or "").strip()
            if not last:
                continue
            first, last = first.title() if first.isupper() else first, last.title() if last.isupper() else last
            people.append({
                "funder": "nih", "grant_id": core, "full_name": f"{first} {last}".strip(), "first_name": first,
                "last_name": last, "role": "PI" if pi.get("is_contact_pi") else "CoI",
                "institution": institution_variants(org),
            })
    write("nih", grants, people)


if __name__ == "__main__":
    main()
