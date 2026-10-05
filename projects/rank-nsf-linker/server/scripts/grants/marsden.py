"""Marsden Fund (Royal Society Te Apārangi, New Zealand) -> data/grants/marsden_*.csv

Input: the yearly announcement-supplement spreadsheets, kept in backup/marsden/ (committed: the
site blocks scripts, so a new year's file is added by hand each November). Layouts differ by year; every year has a project sheet (title, panel,
category, funding, abstract) and/or a team sheet (investigator, role, institution; a blank
Project ID continues the project above). Computer science is mostly panel MIS (Mathematical
and Information Sciences). All panels are kept.

Contracts are announced in November and run about three years from the following year; the
dates below are that approximation.
"""

import re
from common import ROOT, read_xlsx, split_name, write

PAGE = "https://www.royalsociety.org.nz/what-we-do/funds-and-opportunities/marsden/awarded-grants/marsden-fund-awards-{year}"


def find(header: list[str], *names: str) -> int | None:
    lowered = [h.strip().lower() for h in header]
    for n in names:
        if n in lowered:
            return lowered.index(n)
    return None


def header_row(rows: list[list[str]]) -> int | None:
    for i, r in enumerate(rows[:6]):
        if "project id" in [c.strip().lower() for c in r]:
            return i
    return None


def main() -> None:
    grants: dict[str, dict] = {}
    people: dict[tuple, dict] = {}

    for path in sorted((ROOT / "backup" / "marsden").glob("*.xlsx")):
        for sheet, rows in read_xlsx(path).items():
            h = header_row(rows)
            if h is None:
                continue
            hdr = rows[h]
            c_id = find(hdr, "project id")
            c_title = find(hdr, "project title", "title", "project", "media title")
            c_panel = find(hdr, "panel")
            c_cat = find(hdr, "category", "catergory")
            c_fund = find(hdr, "funding (ex gst)", "funding (gst excl)", "funding (exc gst)")
            c_abs = find(hdr, "project abstract", "abstract", "summary")
            c_inv = find(hdr, "investigator", "contact investigator")
            c_role = find(hdr, "role")
            c_org = find(hdr, "institution", "organisation")
            is_team = c_role is not None
            # 2019's team sheet holds two tables side by side; its website table has everything.
            if is_team and [c.lower() for c in hdr].count("project id") > 1:
                continue

            current = None
            for r in rows[h + 1:]:
                cell = lambda c: (r[c].strip() if c is not None and c < len(r) else "")
                pid = cell(c_id)
                if pid:
                    current = pid
                if not current or not re.match(r"^\d{2}-[A-Z]{3}-\d{3}$", current):
                    continue
                year = 2000 + int(current[:2])
                g = grants.setdefault(current, {
                    "funder": "marsden", "grant_id": current, "currency": "NZD", "country": "nz",
                    "starts": f"{year + 1}-02-01", "ends": f"{year + 4}-01-31",
                    "url": PAGE.format(year=year),
                })
                for key, col in (("title", c_title), ("field", c_panel), ("scheme", c_cat),
                                 ("abstract", c_abs)):
                    v = cell(col)
                    if v and not (key == "title" and g.get("title") and col == c_title and "media" in hdr[col].lower()):
                        g.setdefault(key, v)
                fund = re.sub(r"[^\d.]", "", cell(c_fund))
                if fund:
                    g.setdefault("amount", fund)

                inv = cell(c_inv)
                if inv:
                    role = cell(c_role).upper() if is_team else "PI"
                    full, first, last = split_name(inv)
                    key = (current, full)
                    p = people.setdefault(key, {
                        "funder": "marsden", "grant_id": current, "full_name": full,
                        "first_name": first, "last_name": last, "role": "PI" if role == "PI" else "CoI",
                    })
                    if role == "PI":
                        p["role"] = "PI"
                    org = cell(c_org)
                    if org:
                        p.setdefault("institution", org)

    rows = [g for g in grants.values() if g.get("title")]
    write("marsden", rows, list(people.values()))
    mis = [g for g in rows if g.get("field") == "MIS"]
    print(f"{len(mis)} grants in panel MIS (mathematical and information sciences)")


if __name__ == "__main__":
    main()
