"""European Research Council (ERC) grants, Horizon 2020 and Horizon Europe -> data/grants/erc_*.csv

Source: CORDIS open data (Commission Decision 2011/833/EU, reuse with attribution "CORDIS, European
Commission"). Download into data/cordis/:
    cordis-h2020-erc-pi.xlsx      <- https://cordis.europa.eu/data/cordis-h2020-erc-pi.xlsx
    cordis-h2020projects-csv.zip  <- https://cordis.europa.eu/data/cordis-h2020projects-csv.zip

The PI list covers H2020 ERC grants only (started 2015-2021, many still running). Horizon Europe ERC
PIs come from the ERC's per-call "List of Principal Investigators" PDFs (data/erc_he/sources.txt lists
them; erc_lists.py parses them; panel PE6 = computer science), joined with CORDIS Horizon Europe
projects by call and acronym for dates, amount and abstract:
    cordis-HORIZONprojects-csv.zip <- https://cordis.europa.eu/data/cordis-HORIZONprojects-csv.zip Computing grants: a euroSciVoc field under computer
and information sciences or electrical/electronic/information engineering, or a computing word in
the title or keywords. ERC grants are held at the host institution, so country is the host's.
"""

import csv
import io
import re
import zipfile

from common import DATA, ROOT, download, read_xlsx, write
from erc_lists import parse_pdf

SRC = DATA / "cordis"
CS_FIELDS = ("natural sciences/computer and information sciences",
             "engineering and technology/electrical engineering, electronic engineering, information engineering")
CS_WORDS = re.compile(
    r"comput|algorithm|machine learning|deep learning|neural net|artificial intelligence|\bAI\b|software|"
    r"program(ming)? language|formal verification|cryptograph|robot|natural language|database|"
    r"distributed system|operating system|compiler|human-computer|data science", re.I)
COUNTRY_FIX = {"uk": "gb", "el": "gr"}

# CORDIS uses legal names; CSRankings uses everyday ones. Pattern on the upper-cased legal name.
HOST_NAMES = [
    (r"EIDGENOESSISCHE TECHNISCHE HOCHSCHULE ZUERICH", "ETH Zurich"),
    (r"ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE", "EPFL"),
    (r"UNIVERSITAT ZURICH|UNIVERSITAET ZUERICH", "University of Zurich"),
    (r"UNIVERSITY OF OXFORD", "University of Oxford"),
    (r"UNIVERSITY OF CAMBRIDGE", "University of Cambridge"),
    (r"IMPERIAL COLLEGE", "Imperial College London"),
    (r"KING'S COLLEGE LONDON", "King s College London"),
    (r"TRINITY OF QUEEN ELIZABETH NEAR DUBLIN", "Trinity College Dublin"),
    (r"INSTITUT NATIONAL DE RECHERCHE EN INFORMATIQUE", "INRIA"),
    (r"MAX-PLANCK-GESELLSCHAFT", "Max Planck Society"),
    (r"TECHNISCHE UNIVERSITEIT DELFT", "TU Delft"),
    (r"TECHNISCHE UNIVERSITEIT EINDHOVEN", "TU Eindhoven"),
    (r"TECHNISCHE UNIVERSITAE?T MUE?NCHEN", "TU Munich"),
    (r"LUDWIG-MAXIMILIANS-UNIVERSITAE?T", "LMU Munich"),
    (r"TECHNISCHE UNIVERSITAE?T DARMSTADT", "TU Darmstadt"),
    (r"TECHNISCHE UNIVERSITAE?T BERLIN", "TU Berlin"),
    (r"TECHNISCHE UNIVERSITAE?T DRESDEN", "TU Dresden"),
    (r"TECHNISCHE UNIVERSITAE?T WIEN", "TU Wien"),
    (r"RHEINISCH-WESTFAELISCHE TECHNISCHE HOCHSCHULE AACHEN", "RWTH Aachen University"),
    (r"KARLSRUHER INSTITUT FUER TECHNOLOGIE", "Karlsruhe Institute of Technology"),
    (r"UNIVERSITAE?T DES SAARLANDES", "Saarland University"),
    (r"CISPA", "CISPA Helmholtz Center"),
    (r"ALBERT-LUDWIGS-UNIVERSITAE?T FREIBURG", "University of Freiburg"),
    (r"UNIVERSITAE?T ZU KOE?LN", "University of Cologne"),
    (r"RUPRECHT-KARLS-UNIVERSITAE?T HEIDELBERG", "Heidelberg University"),
    (r"RHEINISCHE FRIEDRICH-WILHELMS-UNIVERSITAE?T BONN", "University of Bonn"),
    (r"EBERHARD KARLS UNIVERSITAE?T TUEBINGEN", "University of Tübingen"),
    (r"HUMBOLDT-UNIVERSITAE?T ZU BERLIN", "Humboldt University of Berlin"),
    (r"FREIE UNIVERSITAE?T BERLIN", "Freie Universitaet Berlin"),
    (r"UNIVERSITAE?T KONSTANZ", "University of Konstanz"),
    (r"WEIZMANN INSTITUTE", "Weizmann Institute of Science"),
    (r"TECHNION", "Technion"),
    (r"HEBREW UNIVERSITY", "Hebrew University of Jerusalem"),
    (r"BAR ILAN UNIVERSITY", "Bar - Ilan University"),
    (r"BEN-GURION UNIVERSITY", "Ben - Gurion University of the Negev"),
    (r"KATHOLIEKE UNIVERSITEIT LEUVEN", "KU Leuven"),
    (r"UNIVERSITE LIBRE DE BRUXELLES", "Université libre de Bruxelles"),
    (r"UNIVERSITEIT ANTWERPEN", "University of Antwerp"),
    (r"KOBENHAVNS UNIVERSITET", "University of Copenhagen"),
    (r"DANMARKS TEKNISKE UNIVERSITET", "DTU"),
    (r"AARHUS UNIVERSITET", "Aarhus University"),
    (r"AALBORG UNIVERSITET", "Aalborg University"),
    (r"IT-UNIVERSITETET I KOBENHAVN", "IT University of Copenhagen"),
    (r"UNIVERSITEIT VAN AMSTERDAM", "University of Amsterdam"),
    (r"STICHTING VU", "VU Amsterdam"),
    (r"RADBOUD UNIVERSITEIT", "Radboud University"),
    (r"UNIVERSITEIT LEIDEN", "Leiden University"),
    (r"UNIVERSITEIT UTRECHT", "Utrecht University"),
    (r"UNIVERSITEIT TWENTE", "University of Twente"),
    (r"RIJKSUNIVERSITEIT GRONINGEN", "University of Groningen"),
    (r"CENTRUM WISKUNDE", "CWI"),
    (r"UNIVERSITEIT MAASTRICHT", "Maastricht University"),
    (r"AALTO", "Aalto University"),
    (r"HELSINGIN YLIOPISTO", "University of Helsinki"),
    (r"KUNGLIGA TEKNISKA HOEGSKOLAN", "KTH Royal Institute of Technology"),
    (r"CHALMERS TEKNISKA|GOETEBORGS UNIVERSITET", "Chalmers GU"),
    (r"LUNDS UNIVERSITET", "Lund University"),
    (r"UPPSALA UNIVERSITET", "Uppsala University"),
    (r"INSTITUTE OF SCIENCE AND TECHNOLOGY AUSTRIA", "IST Austria"),
    (r"UNIVERSITAE?T WIEN", "University of Vienna"),
    (r"UNIVERSITAE?T INNSBRUCK", "University of Innsbruck"),
    (r"TECHNISCHE UNIVERSITAE?T GRAZ", "Graz University of Technology"),
    (r"UNIVERSITA DEGLI STUDI DI ROMA LA SAPIENZA", "Sapienza University of Rome"),
    (r"POLITECNICO DI MILANO", "Politecnico di Milano"),
    (r"UNIVERSITA DI PISA", "University of Pisa"),
    (r"UNIVERSITA DEGLI STUDI DI PADOVA", "University of Padova"),
    (r"UNIVERSITA DEGLI STUDI DI TRENTO", "University of Trento"),
    (r"BOCCONI", "Bocconi University"),
    (r"UNIVERSITAT POLITECNICA DE CATALUNYA", "Polytechnic University of Catalonia"),
    (r"IMDEA SOFTWARE", "IMDEA Software Institute"),
    (r"IMDEA NETWORKS", "IMDEA Networks Institute"),
    (r"UNIVERSITE DU LUXEMBOURG", "University of Luxembourg"),
    (r"UNIVERSITY COLLEGE DUBLIN", "University College Dublin"),
    (r"NORGES TEKNISK-NATURVITENSKAPELIGE", "NTNU"),
    (r"UNIWERSYTET WARSZAWSKI", "University of Warsaw"),
    (r"UNIVERZITA KARLOVA", "Charles University"),
    (r"CESKE VYSOKE UCENI TECHNICKE", "Czech Technical University"),
    (r"ECOLE NORMALE SUPERIEURE DE LYON", "Ecole Normale Superieure de Lyon"),
    (r"ECOLE NORMALE SUPERIEURE$", "Ecole Normale Superieure"),
    (r"UNIVERSITE PARIS DAUPHINE|UNIVERSITE PARIS SCIENCES ET LETTRES", "Université Paris Dauphine"),
    (r"EURECOM", "EURECOM"),
]


def host_names(legal: str) -> str:
    """The legal name plus the everyday name CSRankings uses, " | "-joined for the linker."""
    names = [legal]
    upper = legal.upper()
    for pattern, name in HOST_NAMES:
        if re.search(pattern, upper):
            names.append(name)
    # "THE UNIVERSITY OF EDINBURGH" -> "University of Edinburgh"
    plain = re.sub(r"^THE\s+", "", legal, flags=re.I).title().replace(" Of ", " of ")
    if plain.lower() != legal.lower():
        names.append(plain)
    return " | ".join(dict.fromkeys(n for n in names if n))
MIN_END_YEAR = 2015


def zipped(z: zipfile.ZipFile, name: str) -> list[dict]:
    csv.field_size_limit(1 << 30)
    member = next(n for n in z.namelist() if n.endswith(name))
    with z.open(member) as f:
        return list(csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline=""), delimiter=";"))


CORDIS = "https://cordis.europa.eu/data/"
HE_SOURCES = ROOT / "backup" / "erc_he_sources.txt"  # curated: one line per result PDF


def fetch() -> None:
    for name in ("cordis-h2020-erc-pi.xlsx", "cordis-h2020projects-csv.zip", "cordis-HORIZONprojects-csv.zip"):
        # H2020 is closed and doesn't change; Horizon Europe grows
        download(CORDIS + name, SRC / name, max_age_days=365 if "h2020" in name else 30)
    for line in HE_SOURCES.read_text().splitlines():
        if line.strip():
            year, call, url = line.split(maxsplit=2)
            download(url, DATA / "erc_he" / f"erc-{year}-{call}.pdf", max_age_days=3650)  # published once


def main() -> None:
    fetch()
    sheet = next(iter(read_xlsx(SRC / "cordis-h2020-erc-pi.xlsx").values()))
    header = [h.strip() for h in sheet[0]]
    pis = [dict(zip(header, r)) for r in sheet[1:]]
    z = zipfile.ZipFile(SRC / "cordis-h2020projects-csv.zip")
    projects = {p["id"]: p for p in zipped(z, "project.csv")}
    orgs = {(o["projectID"], o["organisationID"]): o for o in zipped(z, "organization.csv")}
    fields: dict[str, list[str]] = {}
    for f in zipped(z, "euroSciVoc.csv"):
        fields.setdefault(f["projectID"], []).append(f["euroSciVocPath"])

    grants, people, seen = [], [], set()
    for pi in pis:
        pid = (pi.get("projectId") or "").strip()
        p = projects.get(pid)
        if not p or not (p.get("endDate") or "")[:4].isdigit() or int(p["endDate"][:4]) < MIN_END_YEAR:
            continue
        paths = fields.get(pid, [])
        cs = any(path.startswith(CS_FIELDS) for path in paths) or CS_WORDS.search(
            f"{p['title']} {p.get('keywords') or ''}")
        if not cs:
            continue
        org = orgs.get((pid, (pi.get("organisationId") or "").strip())) or {}
        country = (org.get("country") or "").lower()
        country = COUNTRY_FIX.get(country, country)
        if pid not in seen:
            seen.add(pid)
            cs_paths = [x.rsplit("/", 1)[-1] for x in paths if x.startswith(CS_FIELDS)]
            grants.append({
                "funder": "erc", "grant_id": pid, "title": p["title"].strip(),
                "abstract": (p.get("objective") or "").strip(),
                "amount": (p.get("ecMaxContribution") or "").replace(",", "."), "currency": "EUR",
                "country": country, "starts": p.get("startDate") or "", "ends": p.get("endDate") or "",
                "url": f"https://cordis.europa.eu/project/id/{pid}",
                "scheme": pi.get("fundingScheme") or p.get("fundingScheme") or "",
                "field": "; ".join(cs_paths[:3]),
            })
        first, last = (pi.get("firstName") or "").strip(), (pi.get("lastName") or "").strip()
        if last:
            people.append({
                "funder": "erc", "grant_id": pid, "full_name": f"{first} {last}".strip(),
                "first_name": first, "last_name": last, "role": "PI",
                "institution": host_names((org.get("name") or "").strip()),
            })
    he_grants, he_people = horizon_europe()
    write("erc", grants + he_grants, people + he_people)


def horizon_europe() -> tuple[list[dict], list[dict]]:
    """Horizon Europe ERC computer-science (PE6) grants from the result PDFs + CORDIS projects."""
    src = DATA / "erc_he"
    he = SRC / "cordis-HORIZONprojects-csv.zip"
    if not HE_SOURCES.exists() or not he.exists():
        print("Horizon Europe ERC: backup/erc_he_sources.txt or the CORDIS Horizon Europe zip missing; skipped")
        return [], []
    z = zipfile.ZipFile(he)
    by_call = {(p["masterCall"].upper(), p["acronym"].strip().lower()): p for p in zipped(z, "project.csv")
               if p["masterCall"].upper().startswith("ERC-")}
    grants, people, unmatched = [], [], 0
    for line in HE_SOURCES.read_text().splitlines():
        if not line.strip():
            continue
        year, call, _url = line.split(maxsplit=2)
        pdf = src / f"erc-{year}-{call}.pdf"
        if not pdf.exists():
            continue
        for row in parse_pdf(pdf):
            if row["panel"] != "PE6" or not row["acronym"]:
                continue
            acronym = row["acronym"].split()[0]  # a cell can catch the start of the title
            master = f"ERC-{year}-{call.upper()}"
            p = by_call.get((master, acronym.lower()))
            if not p and len(acronym) >= 4:
                # in some lists the acronym column starts a character early ("YDRANOS" = "HYDRANOS")
                ends = [v for (m, a), v in by_call.items() if m == master and a.endswith(acronym.lower())]
                p = ends[0] if len(ends) == 1 else None
            if not p or not row["last"]:
                unmatched += 1
                continue
            country = COUNTRY_FIX.get(row["country"].lower(), row["country"].lower())
            grants.append({
                "funder": "erc", "grant_id": p["id"], "title": p["title"].strip(),
                "abstract": (p.get("objective") or "").strip(),
                "amount": (p.get("ecMaxContribution") or "").replace(",", "."), "currency": "EUR",
                "country": country, "starts": p.get("startDate") or "", "ends": p.get("endDate") or "",
                "url": f"https://cordis.europa.eu/project/id/{p['id']}",
                "scheme": f"ERC-{call.upper()}", "field": "PE6 Computer Science and Informatics",
            })
            last = row["last"].title() if row["last"].isupper() else row["last"]
            people.append({
                "funder": "erc", "grant_id": p["id"], "full_name": f"{row['first']} {last}".strip(),
                "first_name": row["first"], "last_name": last, "role": "PI",
                "institution": host_names(row["institution"]),
            })
    # Unmatched rows: list rows the PDF layout garbled, and UK-hosted grants of 2021-2023, which
    # UKRI's Horizon Europe Guarantee funded (they come in through the UKRI import instead).
    print(f"Horizon Europe ERC: {len(grants)} PE6 grants matched to CORDIS, {unmatched} list rows unmatched")
    return grants, people


if __name__ == "__main__":
    main()
