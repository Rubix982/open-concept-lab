"""Shared helpers for the grant normalisers.

Every funder's normaliser writes two CSVs in data/grants/ in one common format, which the
"Load Funder Grants" pipeline step loads into Postgres:

    <funder>_grants.csv  funder,grant_id,title,abstract,amount,currency,starts,ends,url,country,scheme,field
    <funder>_people.csv  funder,grant_id,full_name,first_name,last_name,role,institution,orcid

Dates are ISO (YYYY-MM-DD) or empty. role is "PI" (lead / chief investigator) or "CoI".
Standard library only.
"""

import csv
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"
OUT = DATA / "grants"

GRANT_FIELDS = ["funder", "grant_id", "title", "abstract", "amount", "currency", "starts", "ends",
                "url", "country", "scheme", "field"]
PEOPLE_FIELDS = ["funder", "grant_id", "full_name", "first_name", "last_name", "role", "institution", "orcid"]

HONORIFICS = re.compile(
    r"^(?:(?:distinguished|emeritus|honorary|adjunct|associate|assistant|assoc\.?|asst\.?|a/|research)\s*)*"
    r"(?:professor|prof\.?|dr\.?|mr\.?|mrs\.?|ms\.?|miss|sir|dame)\s+",
    re.I,
)


def split_name(full: str) -> tuple[str, str, str]:
    """'Professor HD Cooper-Thomas' -> ('HD Cooper-Thomas', 'HD', 'Cooper-Thomas')."""
    name = re.sub(r"\s+", " ", full).strip()
    while True:
        stripped = HONORIFICS.sub("", name)
        if stripped == name:
            break
        name = stripped
    parts = name.split(" ")
    if len(parts) == 1:
        return name, "", name
    return name, " ".join(parts[:-1]), parts[-1]


def write(funder: str, grants: list[dict], people: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for kind, rows, fields in (("grants", grants, GRANT_FIELDS), ("people", people, PEOPLE_FIELDS)):
        path = OUT / f"{funder}_{kind}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})
        print(f"{path.relative_to(ROOT)}: {len(rows)} rows")


def read_xlsx(path: Path) -> dict[str, list[list[str]]]:
    """All sheets of an .xlsx as lists of rows of strings (no dependencies)."""
    z = zipfile.ZipFile(path)
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        x = z.read("xl/sharedStrings.xml").decode("utf-8")
        for si in re.findall(r"<si>(.*?)</si>", x, re.S):
            shared.append(_unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", si, re.S))))
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    sheets = {}
    for name, rid in re.findall(r'<sheet [^>]*name="([^"]+)"[^>]*r:id="([^"]+)"', wb):
        target = re.search(r'<Relationship [^>]*Id="' + rid + r'"[^>]*Target="([^"]+)"', rels) or re.search(
            r'<Relationship [^>]*Target="([^"]+)"[^>]*Id="' + rid + '"', rels)
        part = "xl/" + target.group(1).lstrip("/").removeprefix("xl/")
        x = z.read(part).decode("utf-8")
        rows = []
        for row in re.findall(r"<row[^>]*>(.*?)</row>", x, re.S):
            cells: dict[int, str] = {}
            for attrs, inner in re.findall(r"<c ([^>]*?)(?:/>|>(.*?)</c>)", row, re.S):
                ref = re.search(r'r="([A-Z]+)\d+"', attrs)
                col = _col_index(ref.group(1)) if ref else len(cells)
                v = re.search(r"<v>(.*?)</v>", inner or "", re.S)
                if 't="s"' in attrs and v:
                    val = shared[int(v.group(1))]
                elif v:
                    val = _unescape(v.group(1))
                else:
                    val = _unescape("".join(re.findall(r"<t[^>]*>(.*?)</t>", inner or "", re.S)))
                cells[col] = val.strip()
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            else:
                rows.append([])
        sheets[_unescape(name)] = rows
    return sheets


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _unescape(s: str) -> str:
    return (s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            .replace("&apos;", "'").replace("&amp;", "&"))
