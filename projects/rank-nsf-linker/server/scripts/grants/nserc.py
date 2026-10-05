"""NSERC (Canada) computing grants -> data/grants/nserc_*.csv

Source: NSERC's Awards Data on the Open Government Portal (open.canada.ca, dataset
c1b0f627-8c29-427c-ab73-33968ad9176e), Open Government Licence - Canada. Download the yearly
"Awards" (NSERC_FY<year>_Expenditures.csv) and "Co-Applicants" (NSERC_FY<year>_CO-APP.csv) files
into data/nserc/.

Each file has one row per grant per fiscal year paid. A grant is kept when its selection committee
is a computing one or its research subject is IT, AI or robotics; scholarships and fellowships are
left out (the person named is the student, not a supervisor). NSERC publishes no end dates:
Discovery Grants (and the Launch Supplement that comes with an early-career one) run five
years from their competition year; for other programmes the grant is
taken to end with the last fiscal year it was paid in (March 31). The amount is what was paid in
the fiscal years loaded, so older grants are understated, never overstated.
"""

import csv
import re
from collections import defaultdict

from common import DATA, download, get_json, split_name, write

SRC = DATA / "nserc"
COMMITTEES = {"computer science", "electrical and computer engineering", "s&f committee for computing sciences",
              "electrical and computer engineering (rti)"}
SUBJECTS = {"information technology", "artificial intelligence", "robotics"}
STUDENT = re.compile(r"scholarship|fellowship|undergraduate student", re.I)
# The Launch Supplement is paid once, to an early-career researcher whose Discovery Grant runs five
# years; it carries that span so it can mark them as starting a lab.
FIVE_YEARS = ("Discovery Grants Program - Individual", "Discovery Grants Program - Subatomic Physics",
              "Discovery Launch Supplement")


def rows(path):
    """NSERC's files are UTF-8 in recent years and Windows-1252 in older ones."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = raw.decode("cp1252")
    return csv.DictReader(text.splitlines())


def person(raw: str) -> tuple[str, str, str]:
    """'Smol, John JP' -> ('John JP Smol', 'John JP', 'Smol')."""
    if "," in raw:
        last, first = [p.strip() for p in raw.split(",", 1)]
        return f"{first} {last}".strip(), first, last
    return split_name(raw)


PACKAGE = "https://open.canada.ca/data/api/action/package_show?id=c1b0f627-8c29-427c-ab73-33968ad9176e"
YEARS = 3  # the newest fiscal years: running grants all appear in them


def fetch() -> None:
    """The newest fiscal years' Awards and Co-Applicants files from the Open Government Portal.
    Older years stay in data/nserc/ once downloaded; they're published once and don't change."""
    by_year: dict[int, dict[str, str]] = defaultdict(dict)
    for r in get_json(PACKAGE)["result"]["resources"]:
        name = r["name"] if isinstance(r["name"], str) else r["name"].get("en", "")
        m = re.match(r"(\d{4}) (Awards|Co-Applicants)", name.strip())
        if m:
            by_year[int(m.group(1))][m.group(2)] = r["url"]
    for year in sorted(by_year)[-YEARS:]:
        files = by_year[year]
        if "Awards" in files:
            download(files["Awards"], SRC / f"NSERC_FY{year}_Expenditures.csv", max_age_days=90)
        if "Co-Applicants" in files:
            download(files["Co-Applicants"], SRC / f"NSERC_FY{year}_CO-APP.csv", max_age_days=90)


def main() -> None:
    fetch()
    grants: dict[str, dict] = {}
    paid: dict[str, float] = defaultdict(float)
    last_fy: dict[str, int] = {}
    people: dict[str, list[dict]] = defaultdict(list)
    for path in sorted(SRC.glob("NSERC_FY*_Expenditures.csv")):
        for r in rows(path):
            committee = r["CommitteeNameEN"].strip().lower()
            subject = r["ResearchSubjectGroupEN"].strip().lower()
            program = r["ProgramNameEN"].strip()
            if (committee not in COMMITTEES and subject not in SUBJECTS) or STUDENT.search(program):
                continue
            gid = r["ApplicationID"].strip()
            fy = int(r["FiscalYear-Exercice financier"])
            paid[gid] += float(r["AwardAmount"] or 0)
            last_fy[gid] = max(last_fy.get(gid, 0), fy)
            comp = int(r["CompetitionYear-Année de concours"] or fy)
            ends = f"{comp + 5}-03-31" if program in FIVE_YEARS else None
            summary = (r.get("ApplicationSummary") or "").strip()
            grants[gid] = {
                "funder": "nserc", "grant_id": gid, "title": r["ApplicationTitle"].strip() or program,
                "abstract": "" if summary.lower() in ("", "not available", "non disponible") else summary,
                "currency": "CAD", "country": "ca", "starts": f"{comp}-04-01", "ends": ends,
                "url": "https://www.nserc-crsng.gc.ca/ase-oro/index_eng.asp", "scheme": program,
                "field": r["ResearchSubjectEN"].strip(),
            }
            if not people[gid]:
                full, first, last = person(r["Name-Nom"])
                people[gid].append({"funder": "nserc", "grant_id": gid, "full_name": full, "first_name": first,
                                    "last_name": last, "role": "PI",
                                    "institution": r["Institution-Établissement"].strip()})
    for path in sorted(SRC.glob("NSERC_FY*_CO-APP.csv")):
        for r in rows(path):
            gid = r["ApplicationID"].strip()
            if gid not in grants:
                continue
            full, first, last = person(r["CoApplicantName-NomCoApplicant"])
            if any(p["full_name"] == full for p in people[gid]):
                continue
            people[gid].append({"funder": "nserc", "grant_id": gid, "full_name": full, "first_name": first,
                                "last_name": last, "role": "CoI",
                                "institution": r["CoAppInstitution-Établissement"].strip()})
    out = []
    for gid, g in grants.items():
        g["amount"] = round(paid[gid])
        g["ends"] = g["ends"] or f"{last_fy[gid] + 1}-03-31"
        out.append(g)
    write("nserc", out, [p for ps in people.values() for p in ps])


if __name__ == "__main__":
    main()
