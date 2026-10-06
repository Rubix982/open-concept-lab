"""FWF (Austrian Science Fund) projects -> data/grants/fwf_*.csv

Source: the FWF Open API (https://www.fwf.ac.at/en/discover/open-api), a Meilisearch index of every
FWF project; "FWF Open API data is freely reusable under a CC0 license". Read access uses FWF's one
public key, published at https://openapi.fwf.ac.at/fwfkey (fetched at run time; FWF_API_KEY in the
environment overrides it). About 21 pages of 1,000 projects, one request a second, cached in data/fwf/.
OpenAlex's copy of FWF (openaire_fwf) has no investigators or institutions, hence this loader.
All fields are loaded; projects running in 2015 or later, publication grants left out (not research).
People: the principal investigator (with ORCID and the institution's ROR id); FWF lists co-applicants
only as free text, so they are not loaded.
"""

import json
import os
import time
import urllib.request

from common import DATA, write

CACHE = DATA / "fwf"
API = "https://openapi.fwf.ac.at/indexes/projects/documents"
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)"}
PAGE = 1000
FROM_YEAR = 2015
NOT_RESEARCH = ("Book Publications", "Peer-Reviewed Publications", "Open Access", "Publication")


def api_key() -> str:
    key = os.environ.get("FWF_API_KEY", "").strip()
    if key:
        return key
    with urllib.request.urlopen(urllib.request.Request("https://openapi.fwf.ac.at/fwfkey/", headers=UA),
                                timeout=60) as r:
        return r.read().decode().strip()


def page(offset: int, key: str) -> dict:
    path = CACHE / f"projects-{offset:06d}.json"
    if path.exists() and time.time() - path.stat().st_mtime < 25 * 86400:
        return json.loads(path.read_text())
    req = urllib.request.Request(f"{API}?limit={PAGE}&offset={offset}",
                                 headers={**UA, "Authorization": f"Bearer {key}"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.loads(r.read())
            break
        except OSError as e:
            if attempt == 3:
                raise SystemExit(f"FWF request failed at offset {offset}: {type(e).__name__}")
            time.sleep(15 * (attempt + 1))
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body))
    time.sleep(1.0)
    return body


def main() -> None:
    key = api_key()
    first = page(0, key)
    projects = list(first["results"])
    for offset in range(PAGE, first["total"], PAGE):
        projects += page(offset, key)["results"]
    print(f"FWF: {len(projects)} projects")

    grants, people = [], []
    for p in projects:
        program = p.get("_str.program.en") or ""
        if any(x.lower() in program.lower() for x in NOT_RESEARCH):
            continue
        start = p.get("_date.startdate") or p.get("_date.approvaldate") or ""
        end = p.get("_date.enddate") or ""
        if int((end or start or "0")[:4] or 0) < FROM_YEAR:
            continue
        gid = (p.get("_str.grantdoi") or p["id"]).rsplit("/", 1)[-1]
        title = p.get("_str.projecttitle.en") or p.get("_str.projecttitle.de") or ""
        if not title:
            continue
        grants.append({
            "funder": "fwf", "grant_id": gid, "title": title,
            "abstract": p.get("_str.prproposalsummary.en") or p.get("_str.prproposalsummary.de") or "",
            "amount": p.get("_long.approvedamount") or "", "currency": "EUR", "country": "at",
            "starts": start[:10], "ends": end[:10], "url": p.get("_str.url") or "",
            "scheme": program, "field": "; ".join(p.get("_list.researchfields.en") or []),
        })
        first_name = (p.get("_str.principalinvestigator.firstname") or "").strip()
        last_name = (p.get("_str.principalinvestigator.lastname") or "").strip()
        if last_name:
            people.append({
                "funder": "fwf", "grant_id": gid, "full_name": f"{first_name} {last_name}".strip(),
                "first_name": first_name, "last_name": last_name, "role": "PI",
                "institution": (p.get("_str.principalinvestigator.researchinstitute.name") or "").strip(),
                "orcid": (p.get("_str.principalinvestigator.orcid") or "").strip(),
            })
    write("fwf", grants, people)


if __name__ == "__main__":
    main()
