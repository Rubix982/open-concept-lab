"""Swiss National Science Foundation (SNSF) grants -> data/grants/snsf_*.csv

Source: SNSF Data Portal open data, https://data.snf.ch/datasets (grants.csv, persons.csv; open use
with attribution "Swiss National Science Foundation"). Download both into data/snsf/ first:
    curl -L -o data/snsf/grants.csv https://data.snf.ch/datasets/grants.csv
    curl -L -o data/snsf/persons.csv https://data.snf.ch/datasets/persons.csv

Computing grants: a Field of Research (ANZSRC 2020) in division 46 or electrical/electronic/robotics
engineering, or an older SNSF discipline in IT / electrical engineering / microelectronics, ending
2015 or later. The grants file has no abstracts, so the keywords stand in for one.
"""

import csv

from common import DATA, download, write

SRC = DATA / "snsf"
CS_DISCIPLINES = {"20504", "20506", "20508"}
CS_FIELDS = ("46", "4007", "4008", "4009")
MIN_END_YEAR = 2015
# SNSF writes "ETH Zurich – ETHZ"; CSRankings uses the part before the dash, except for these.
INSTITUTION_FIX = {"EPF Lausanne": "EPFL", "University of Berne": "University of Bern"}


def institution(name: str) -> str:
    base = (name or "").split(" – ")[0].strip()
    return INSTITUTION_FIX.get(base, base)


def rows(name: str) -> list[dict]:
    csv.field_size_limit(1 << 30)
    with (SRC / f"{name}.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def codes(value: str) -> list[str]:
    return [c.strip() for c in value.replace(",", ";").split(";") if c.strip()]


def main() -> None:
    for name in ("grants", "persons"):
        download(f"https://data.snf.ch/datasets/{name}.csv", SRC / f"{name}.csv", max_age_days=30)
    grants, kept = [], set()
    for r in rows("grants"):
        end = (r["EffectiveGrantEndDate"] or "")[:10]
        if not end or int(end[:4]) < MIN_END_YEAR:
            continue
        fields = codes(r["AllFieldOfResearchs"])
        if not (set(codes(r["AllDisciplines"])) & CS_DISCIPLINES or any(f.startswith(CS_FIELDS) for f in fields)):
            continue
        gid = r["GrantNumber"].strip()
        kept.add(gid)
        keywords = (r["Keywords"] or "").strip()
        grants.append({
            "funder": "snsf", "grant_id": gid, "title": (r["TitleEnglish"] or r["Title"]).strip(),
            "abstract": f"Keywords: {keywords}" if keywords else "",
            "amount": r["AmountGrantedAllSets"] or "", "currency": "CHF", "country": "ch",
            "starts": (r["EffectiveGrantStartDate"] or "")[:10], "ends": end,
            "url": f"https://data.snf.ch/grants/grant/{gid}",
            "scheme": r["FundingInstrumentPublished"] or "",
            "field": r["MainFieldOfResearch"] or r["MainDiscipline"] or "",
        })

    people = []
    for p in rows("persons"):
        for role, column in (("PI", "ResponsibleApplicantGrantNumber"), ("CoI", "CoApplicantGrantNumber")):
            for gid in codes(p[column] or ""):
                if gid not in kept:
                    continue
                first, last = (p["FirstName"] or "").strip(), (p["LastName"] or "").strip()
                people.append({
                    "funder": "snsf", "grant_id": gid, "full_name": f"{first} {last}".strip(),
                    "first_name": first, "last_name": last, "role": role,
                    "institution": institution(p["ResearchInstitution"]), "orcid": p["ORCID"] or "",
                })
    write("snsf", grants, people)


if __name__ == "__main__":
    main()
