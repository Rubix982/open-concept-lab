"""Agence nationale de la recherche (ANR, France) grants -> data/grants/anr_*.csv

Source: data.gouv.fr dataset 60ca2086030c7b7e52e2c02e "ANR_01 Projets ANR DOS et DGDS", projects and
partners since 2010 (ODbL; attribution "Agence nationale de la recherche"). Download into data/anr/:
    projets.csv      <- anr-dgds-depuis-2010-projets-finances-<date>-projets.csv
    partenaires.csv  <- anr-dgds-depuis-2010-projets-finances-<date>-partenaires.csv
plus the research-unit register (RNSR) with each lab's parent institutions and ERC panel:
    rnsr.csv <- https://data.enseignementsup-recherche.gouv.fr/api/explore/v2.1/catalog/datasets/
                fr-esr-structures-recherche-publiques-actives/exports/csv?delimiter=%3B

ANR lists investigators under their lab ("LIP6"); the RNSR code maps the lab to its parent
institutions ("Sorbonne Université", CNRS), and the faculty linker tries each of them.
Computing projects: a computing committee in the decision code (ANR-21-CE23-...) or a partner lab
on ERC panel PE6. ANR gives no end date; projects are assumed to run four years.
"""

import csv
import re

from common import DATA, split_name, write

SRC = DATA / "anr"
CS_COMMITTEES = {"CE23", "CE25", "CE33", "CE39", "CE46", "CE48"}
MIN_START_YEAR = 2012  # four-year projects starting earlier ended before 2016


def rows(name: str) -> list[dict]:
    csv.field_size_limit(1 << 30)
    with (SRC / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def committee(code: str) -> str:
    m = re.match(r"ANR-\d\d-([A-Z]+\d*)-", code)
    return m.group(1) if m else ""


def institutions(unit: dict | None, organisation: str) -> str:
    """Every institution a CSRankings entry might use for an investigator in this lab, " | "-joined:
    the partner organisation, the lab, its parent institutions (university, CNRS, Inria, ...)."""
    names = [organisation.strip()]
    if unit:
        names += [unit["sigle"].strip(), unit["libelle"].strip()]
        names += [re.sub(r"\s*\(?EPE\)?$", "", n.strip()) for n in unit["tutelles"].split(",")]
    inria = any(re.search(r"inria|informatique et (en )?automatique", n, re.I) for n in names)
    if inria:
        names.append("INRIA")
    # CSRankings lists Lille's computing faculty under their lab, CRIStAL, not the university.
    if (inria or (unit or {}).get("code_panel_erc") == "PE6") and any("lille" in n.lower() for n in names):
        names.append("CRIStAL")
    seen, out = set(), []
    for n in names:
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return " | ".join(out)


def main() -> None:
    units = {u["numero_national_de_structure"]: u for u in rows("rnsr.csv")}
    partners: dict[str, list[dict]] = {}
    for p in rows("partenaires.csv"):
        partners.setdefault(p["Projet.Code_Decision"], []).append(p)

    grants, people = [], []
    for r in rows("projets.csv"):
        code = r["Projet.Code_Decision"].strip()
        start = (r["Projet.T0 scientifique"] or "")[:10]
        if not start or int(start[:4]) < MIN_START_YEAR:
            continue
        team = partners.get(code, [])
        pe6 = any((units.get(p["Projet.Partenaire.Code_RNSR"]) or {}).get("code_panel_erc") == "PE6" for p in team)
        if committee(code) not in CS_COMMITTEES and not pe6:
            continue
        doi = (r.get("Projet.DOI") or "").strip()
        grants.append({
            "funder": "anr", "grant_id": code,
            "title": (r["Projet.Titre.Anglais"] or r["Projet.Titre.Francais"]).strip(),
            "abstract": (r["Projet.Resume.Anglais"] or r["Projet.Resume.Francais"] or "").strip(),
            "amount": r["Projet.Montant.AF.Aide_allouee.ANR"] or "", "currency": "EUR", "country": "fr",
            "starts": start, "ends": f"{int(start[:4]) + 4}{start[4:]}",
            "url": f"https://doi.org/{doi}" if doi else "https://anr.fr/Projet-" + code,
            "scheme": r["Programme.Acronyme"] or "", "field": committee(code),
        })
        for p in team:
            last = (p["Projet.Partenaire.Responsable_scientifique.Nom"] or "").strip()
            first = (p["Projet.Partenaire.Responsable_scientifique.Prenom"] or "").strip()
            if not last:
                continue
            last = last.title() if last.isupper() else last
            full, _, _ = split_name(f"{first} {last}")
            org = p["Projet.Partenaire.Nom_organisme"] or ""
            people.append({
                "funder": "anr", "grant_id": code, "full_name": full, "first_name": first, "last_name": last,
                "role": "PI" if p["Projet.Partenaire.Est_coordinateur"] == "True" else "CoI",
                "institution": institutions(units.get(p["Projet.Partenaire.Code_RNSR"]), org),
                "orcid": p["Projet.Partenaire.Responsable_scientifique.ORCID"] or "",
            })
    write("anr", grants, people)


if __name__ == "__main__":
    main()
