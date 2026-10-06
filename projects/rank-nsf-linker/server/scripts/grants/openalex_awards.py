"""National research funders via OpenAlex awards -> data/grants/<funder>_*.csv (one pair per funder)

OpenAlex collects award data from about 250 funder sources (each award's `provenance`) and publishes
them as a free CC0 snapshot (s3://openalex/data/jsonl/awards/, ~4.4 GB gzipped JSON lines, updated
monthly; no API calls, so the daily allowance is untouched). This keeps the sources in SOURCES: national
funders not loaded by their own importer, whose awards name a lead investigator. OpenAlex's CC0 does not
lift a funder's own terms; each source's terms are noted in SOURCES.

    openalex_awards.py            download what changed, then write the CSVs
    openalex_awards.py stats      per provenance: awards, with a lead investigator, top countries
                                  (to choose SOURCES)

Snapshot files are kept in data/openalex_awards/ and downloaded again only when the manifest lists a
different size. S3's IPv4 route can be very slow from some networks; the dual-stack endpoint is tried
first. Standard library, plus pypinyin for Chinese names (fetcher/requirements.txt).
"""

import collections
import csv
import re
import sys
from pathlib import Path

from common import write
from fetchlib import ROOT, openalex_snapshot, snapshot_records as records


# provenance: (funder key, name students see, country of the funder, terms as published by the funder).
# National research funders (and Wellcome) with lead investigators in OpenAlex, not loaded by their own
# importer (NSF, NIH, NSERC, KAKEN, SNSF, ARC, ANR, RGC, NWO, Marsden, UKRI and ERC are). Left out:
# Mexico's SNII (a researcher registry, not grants), fellowships and prizes (Humboldt, Guggenheim...),
# mixed sources (crossref_work, datacite), provincial Chinese NSFs (later).
SOURCES: dict[str, tuple[str, str, str, str]] = {
    "nsfc_kd": ("nsfc", "NSFC (China)", "cn", "unverified: no published reuse terms found"),
    "grb_most_projects": ("nstc", "NSTC (Taiwan)", "tw", "Government Data Open License v1"),
    "grb_nstc_projects": ("nstc", "NSTC (Taiwan)", "tw", "Government Data Open License v1"),
    "cihr_opendata": ("cihr", "CIHR (Canada)", "ca", "Open Government Licence - Canada"),
    "sshrc_opendata": ("sshrc", "SSHRC (Canada)", "ca", "Open Government Licence - Canada"),
    "fapesp_bv": ("fapesp", "FAPESP (Brazil)", "br", "unverified"),
    "fct": ("fct", "FCT (Portugal)", "pt", "unverified"),
    "anid_github": ("anid", "ANID (Chile)", "cl", "CC0 (GitHub open data)"),
    "research_council_norway_project_bank": ("rcn", "Research Council of Norway", "no", "NLOD 2.0"),
    "nhmrc": ("nhmrc", "NHMRC (Australia)", "au", "unverified (Australian government data, usually CC BY)"),
    "trdizin_tubitak_projects": ("tubitak", "TÜBİTAK (Turkey)", "tr", "unverified"),
    "swedish_research_council": ("vr", "Swedish Research Council", "se", "open, may be used publicly; credit SweCRIS"),
    "swecris_vinnova": ("vinnova", "Vinnova (Sweden)", "se", "open, may be used publicly; credit SweCRIS"),
    "formas": ("formas", "Formas (Sweden)", "se", "open, may be used publicly; credit SweCRIS"),
    "forte": ("forte", "Forte (Sweden)", "se", "open, may be used publicly; credit SweCRIS"),
    "ncn_ranking_lists": ("ncn", "NCN (Poland)", "pl", "unverified (published ranking lists)"),
    "fwo_fris": ("fwo", "FWO (Flanders, Belgium)", "be", "unverified (FRIS)"),
    "isf_grant_search": ("isf", "Israel Science Foundation", "il", "unverified"),
    "sfi_open_data": ("sfi", "Research Ireland (SFI)", "ie", "CC BY 4.0"),
    "wellcome_trust": ("wellcome", "Wellcome", "gb", "CC BY 4.0 (360Giving)"),
    "amed_amedfind": ("amed", "AMED (Japan)", "jp", "unverified"),
    "zonmw_projects_jsonapi": ("zonmw", "ZonMw (Netherlands)", "nl", "unverified"),
    "forskningsportal_dk": ("dff", "Independent Research Fund Denmark", "dk", "unverified"),
    "portal_fis_isciii": ("isciii", "ISCIII (Spain)", "es", "unverified"),
    "nafosted": ("nafosted", "NAFOSTED (Vietnam)", "vn", "unverified"),
    "icmr_approved_projects": ("icmr", "ICMR (India)", "in", "unverified"),
    "nsf_sri_lanka_gmis": ("nsf-lk", "NSF Sri Lanka", "lk", "unverified"),
    "hec_pakistan_nrpu": ("hec", "HEC NRPU (Pakistan)", "pk", "unverified (HEC's public list)"),
}
# Funders whose investigators are named in Chinese characters and whose researchers write their
# names in pinyin (mainland China); Taiwan's use other romanisations, so their names stay as given.
PINYIN = {"nsfc"}
FROM_YEAR = 2015  # grants running in 2015 or later, as for KAKEN; HEC's list has no dates and stays


def person(p: dict | None) -> tuple[str, str] | None:
    if not p:
        return None
    given, family = (p.get("given_name") or "").strip(), (p.get("family_name") or "").strip()
    return (given, family) if family else None


def stats(paths: list[Path]) -> None:
    n, lead, titled = collections.Counter(), collections.Counter(), collections.Counter()
    countries: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    funders: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for r in records(paths):
        pv = r.get("provenance") or "?"
        n[pv] += 1
        titled[pv] += bool(r.get("display_name"))
        li = r.get("lead_investigator")
        if person(li):
            lead[pv] += 1
        aff = (li or {}).get("affiliation") or {}
        countries[pv][aff.get("country") or "-"] += 1
        funders[pv][(r.get("funder") or {}).get("display_name") or "-"] += 1
    print("provenance\tawards\ttitled\twith_lead\tcountries\tfunders")
    for pv, c in n.most_common():
        print(f"{pv}\t{c}\t{titled[pv]}\t{lead[pv]}\t"
              f"{', '.join(f'{k}:{v}' for k, v in countries[pv].most_common(3))}\t"
              f"{'; '.join(k for k, _ in funders[pv].most_common(2))}")


CJK = re.compile(r"[\u3400-\u9fff]")
# Surnames read differently from the character's usual reading, and the usual English spellings.
SURNAMES = {"曾": "zeng", "单": "shan", "解": "xie", "区": "ou", "仇": "qiu", "朴": "piao", "查": "zha",
            "盖": "ge", "乐": "yue", "覃": "qin", "缪": "miao", "长孙": "zhangsun", "尉迟": "yuchi",
            "万俟": "moqi", "华": "hua", "任": "ren", "沈": "shen", "秘": "bi", "繁": "po", "阚": "kan"}
try:
    from pypinyin import Style, lazy_pinyin
except ImportError:  # fetcher/requirements.txt; without it names stay in characters (and don't link)
    lazy_pinyin = None


def pinyin_name(given: str, family: str) -> tuple[str, str]:
    """('燎原', '董') -> ('Liaoyuan', 'Dong'): how mainland researchers write their names in English."""
    if lazy_pinyin is None or not CJK.search(given + family):
        return given, family
    def read(text: str) -> str:
        return "".join(lazy_pinyin(text, style=Style.NORMAL)).replace("v", "u")  # 吕 lv -> Lu
    full = (family + given) if "·" in given + family else ""
    if full:  # Uyghur and other transliterated names ("买提明·苏莱曼"): first and last part
        parts = [read(p).capitalize() for p in full.split("·") if p]
        return " ".join(parts[:-1]), parts[-1]
    fam = SURNAMES.get(family) or read(family)
    return read(given).capitalize(), fam.capitalize()


def chinese_names() -> dict[str, str]:
    """Chinese name (simplified or traditional, 4+ characters) -> OpenAlex's English display name, for
    institutions in China, Taiwan, Hong Kong and Macau; a name two institutions share goes to the one
    with more works."""
    best: dict[str, tuple[int, str]] = {}
    for r in records(openalex_snapshot("institutions")):
        if r.get("country_code") not in ("CN", "TW", "HK", "MO") or not r.get("display_name"):
            continue
        names = [a for a in r.get("display_name_alternatives") or [] if CJK.search(a)]
        works = r.get("works_count") or 0
        for n in {n.strip() for n in names if n and len(n.strip()) >= 4}:
            if n not in best or works > best[n][0]:
                best[n] = (works, r["display_name"])
    names = {n: v[1] for n, v in best.items()}
    # Most Taiwanese universities have no traditional-character name in OpenAlex: a curated list
    curated = ROOT / "backup" / "zh_institutions.csv"
    if curated.exists():
        names.update({r["chinese"]: r["english"] for r in csv.DictReader(curated.open(encoding="utf-8"))})
    return names


def institution(r: dict, lead: dict | None) -> str:
    """OpenAlex's English names for the awarded institution, most specific first ("Institute of High
    Energy Physics | Chinese Academy of Sciences"), else the funder's own spelling."""
    names = [i["display_name"] for i in r.get("institution_awarded") or [] if i.get("display_name")]
    if names:
        return " | ".join(dict.fromkeys(names))
    return (((lead or {}).get("affiliation") or {}).get("name") or "").strip()


def build(paths: list[Path]) -> None:
    grants: dict[str, list[dict]] = collections.defaultdict(list)
    people: dict[str, list[dict]] = collections.defaultdict(list)
    for r in records(paths):
        src = SOURCES.get(r.get("provenance") or "")
        title = (r.get("display_name") or "").strip()
        lead = r.get("lead_investigator")
        if not src or not title or not person(lead):
            continue
        funder, _name, country, _terms = src
        gid = (r.get("funder_award_id") or r["id"].rsplit("/", 1)[-1]).strip()
        inst = institution(r, lead)
        host = next((i.get("country_code") for i in r.get("institution_awarded") or [] if i.get("country_code")), None)
        abstract = (r.get("description") or "").strip()
        if abstract.startswith("Principal investigator:"):  # HEC: the description repeats the PI
            abstract = ""
        start, end = r.get("start_date") or "", r.get("end_date") or ""
        last_year = r.get("end_year") or (int(end[:4]) if end else None) or r.get("start_year")
        if last_year and int(last_year) < FROM_YEAR:
            continue
        grants[funder].append({
            "funder": funder, "grant_id": gid, "title": title, "abstract": abstract,
            "amount": r.get("amount") or "", "currency": r.get("currency") or "",
            "starts": start or (f"{r['start_year']}-01-01" if r.get("start_year") else ""),
            "ends": end or (f"{r['end_year']}-12-31" if r.get("end_year") else ""),
            "url": r.get("landing_page_url") or r["id"], "country": (host or country).lower(),
            "scheme": r.get("funder_scheme") or "",
            "field": ((r.get("primary_topic") or {}).get("field") or {}).get("display_name") or "",
        })
        team = [("PI", lead)] + [("CoI", p) for p in [r.get("co_lead_investigator")] + (r.get("investigators") or [])]
        seen = set()
        for role, p in team:
            name = person(p)
            if not name or name in seen:
                continue
            seen.add(name)
            given, family = pinyin_name(*name) if funder in PINYIN else name
            aff = ((p.get("affiliation") or {}).get("name") or "").strip()
            people[funder].append({
                "funder": funder, "grant_id": gid, "full_name": f"{given} {family}".strip(),
                "first_name": given, "last_name": family, "role": role,
                "institution": inst if role == "PI" else (aff or inst),
                "orcid": (p.get("orcid") or "").rsplit("/", 1)[-1],
            })
    # Institutions still in characters: OpenAlex's English name for the longest known Chinese name
    # they start with ("國立臺灣大學電機工程學系" -> National Taiwan University).
    zh = chinese_names()
    lengths = sorted({len(k) for k in zh}, reverse=True)
    def english(name: str) -> str | None:
        for n in lengths:
            if n <= len(name) and (hit := zh.get(name[:n])):
                return hit
        return None
    fixed = left = 0
    for rows in people.values():
        for p in rows:
            if CJK.search(p["institution"]):
                if hit := english(p["institution"]):
                    p["institution"], fixed = f"{hit} | {p['institution']}", fixed + 1
                else:
                    left += 1
    print(f"  institutions in characters: {fixed} named in English, {left} not found")
    for funder in sorted({v[0] for v in SOURCES.values()}):
        write(funder, grants[funder], people[funder])


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    paths = openalex_snapshot("awards")
    if cmd == "stats":
        stats(paths)
    elif cmd != "download":
        build(paths)


if __name__ == "__main__":
    main()
