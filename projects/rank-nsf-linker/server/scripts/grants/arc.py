"""Australian Research Council (ARC) grants -> data/grants/arc_*.csv

Source: ARC Grants Search API (https://dataportal.arc.gov.au/NCGP/API/grants), public, no key.
Computer science = Field of Research division 46 "Information and Computing Sciences"
(FoR 2020, grants from 2022) plus the older division 08 (to 2022).
Attribution: Australian Research Council.

Raw API pages are cached in data/arc/ and reused for 30 days; pass --refresh to refetch.
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from common import DATA, split_name, write

API = "https://dataportal.arc.gov.au/NCGP/API/grants"
FILTERS = {"for46": '(two-digit-for="46")', "for08": '(two-digit-for="08")'}
CACHE = DATA / "arc"
MAX_AGE = 30 * 24 * 3600
PAGE_SIZE = 200  # large pages time out on slow links


def fetch(name: str, flt: str, refresh: bool) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    records, page = [], 1
    while True:
        path = CACHE / f"{name}-p{page}.json"
        if refresh or not path.exists() or time.time() - path.stat().st_mtime > MAX_AGE:
            url = f"{API}?page%5Bsize%5D={PAGE_SIZE}&page%5Bnumber%5D={page}&filter={urllib.parse.quote(flt)}"
            req = urllib.request.Request(url, headers={"User-Agent": "advisor-atlas/1.0 (research explorer)"})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=300) as resp:
                        path.write_bytes(resp.read())
                    break
                except (TimeoutError, OSError) as e:
                    if attempt == 3:
                        raise
                    print(f"{name} page {page}: {e}; retrying")
                    time.sleep(10 * (attempt + 1))
            time.sleep(2)  # the API is slow; be gentle
        body = json.loads(path.read_text())
        records += body["data"]
        if page >= body["meta"]["total-pages"]:
            return records
        page += 1


def main() -> None:
    refresh = "--refresh" in sys.argv
    seen, grants, people = set(), [], []
    for name, flt in FILTERS.items():
        for rec in fetch(name, flt, refresh):
            a = rec["attributes"]
            code = a["code"]
            if code in seen:
                continue
            seen.add(code)
            summary = (a.get("grant-summary") or "").strip()
            title, _, abstract = summary.partition(". ")
            year = a.get("funding-commencement-year")
            end = (a.get("anticipated-end-date") or "")[:10]
            grants.append({
                "funder": "arc", "grant_id": code, "title": title.strip(), "abstract": abstract.strip(),
                "amount": a.get("current-funding-amount") or a.get("announced-funding-amount") or "",
                "currency": "AUD", "country": "au",
                "starts": f"{year}-01-01" if year else "",
                "ends": end or (f"{int(year) + 3}-12-31" if year else ""),
                "url": f"https://dataportal.arc.gov.au/NCGP/Web/Grant/Grant/{code}",
                "scheme": a.get("scheme-name") or "", "field": a.get("primary-field-of-research") or "",
            })
            org = a.get("current-admin-organisation") or ""
            lead = (a.get("lead-investigator") or "").strip()
            names = [n.strip() for n in (a.get("investigators") or "").split(";") if n.strip()] or [lead]
            for n in names:
                if not n:
                    continue
                full, first, last = split_name(n)
                people.append({
                    "funder": "arc", "grant_id": code, "full_name": full, "first_name": first, "last_name": last,
                    "role": "PI" if n == lead else "CoI", "institution": org,
                })
    write("arc", grants, people)


if __name__ == "__main__":
    main()
