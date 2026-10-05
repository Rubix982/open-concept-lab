"""DAAD scholarship database -> data/scholarships/daad.csv

Source: the DAAD scholarship database (https://www2.daad.de/deutschland/stipendium/datenbank/en/),
which ships its programme list as static JSON-in-JS files (scholarships.js, origin.js, deadlines.js).
Kept: programmes for graduates or doctoral candidates, for study or research, open to applicants from
Pakistan (the students Advisor Atlas is built for). Each links to its page in the DAAD database,
where eligibility and deadlines are authoritative.

Output uses the columns of backup/scholarships.csv; curated rows there take precedence (the server
drops feed rows whose name matches a curated one). Standard library only.
"""

import csv
import html
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "data" / "scholarships" / "daad.csv"
BASE = "https://www2.daad.de/bundles/daadstipendiendatenbanklsh/data/a/js/"
DETAIL = "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/?detail="
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial scholarship explorer)"}
PAKISTAN = 194          # DAAD origin id
GRADUATES, DOCTORAL, POSTDOC = 3, 4, 2
STUDY, RESEARCH = 1, 2  # DAAD "intentions"
FIELDS = ["id", "name", "provider", "destination_countries", "levels", "eligible_nationalities", "covers",
          "application_window", "official_url", "verified", "notes"]


def taffy(name: str) -> list[dict]:
    req = urllib.request.Request(BASE + name, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as resp:
        text = resp.read().decode("utf-8")
    return json.loads(text[text.index("TAFFY(") + 6:text.rindex(")")])


def plain(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text or "")
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\s+", " ", text).strip()


def main() -> None:
    programmes = taffy("scholarships.js")
    deadlines = {d["id"]: plain(d["general"]["en"]) for d in taffy("deadlines.js")}
    subjects = {s["code"]: s["nameEn"] for s in taffy("subjectgroups.js")}
    rows = []
    for p in programmes:
        status, intentions = set(p["status"]), set(p.get("intentions") or [])
        if PAKISTAN not in p["origin"] or not status & {GRADUATES, DOCTORAL} or not intentions & {STUDY, RESEARCH}:
            continue
        levels = []
        if GRADUATES in status and STUDY in intentions:
            levels.append("masters")
        if DOCTORAL in status or RESEARCH in intentions:
            levels.append("phd")
        if POSTDOC in status:
            levels.append("postdoc")
        fields = [subjects[c] for c in p.get("subjectGrps") or [] if c in subjects]
        window = deadlines.get(p["sapProgid"], "")
        rows.append({
            "id": f"daadfeed-{p['sapProgid']}",
            "name": p["nameEn"].strip(),
            "provider": "DAAD" if p.get("isDaad") else "via the DAAD scholarship database",
            "destination_countries": "DE",
            "levels": ";".join(levels),
            "eligible_nationalities": "PK" if len(p["origin"]) < 150 else "*",
            "covers": "",
            "application_window": window[:300],
            "official_url": DETAIL + str(p["sapProgid"]),
            "verified": "no",
            "notes": (("Subjects: " + ", ".join(fields) + ". ") if 0 < len(fields) < len(subjects) else "")
                     + "Listed in the DAAD scholarship database as open to applicants from Pakistan.",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["provider"] != "DAAD", r["name"])))
    print(f"{OUT.relative_to(ROOT)}: {len(rows)} programmes")


if __name__ == "__main__":
    main()
