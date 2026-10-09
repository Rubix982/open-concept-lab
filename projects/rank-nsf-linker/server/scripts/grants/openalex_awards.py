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
    "nsfc_kd": ("nsfc", "NSFC (China)", "cn", "no reuse terms published: facts and a link only"),
    "grb_most_projects": ("nstc", "NSTC (Taiwan)", "tw", "Government Data Open License v1"),
    "grb_nstc_projects": ("nstc", "NSTC (Taiwan)", "tw", "Government Data Open License v1"),
    "cihr_opendata": ("cihr", "CIHR (Canada)", "ca", "Open Government Licence - Canada"),
    "sshrc_opendata": ("sshrc", "SSHRC (Canada)", "ca", "Open Government Licence - Canada"),
    "fapesp_bv": ("fapesp", "FAPESP (Brazil)", "br", "CC BY (São Paulo open-data catalogue; medium confidence)"),
    "fct": ("fct", "FCT (Portugal)", "pt", "no reuse terms published: facts and a link only"),
    "anid_github": ("anid", "ANID (Chile)", "cl", "CC0 (GitHub open data)"),
    "research_council_norway_project_bank": ("rcn", "Research Council of Norway", "no", "NLOD 2.0"),
    "nhmrc": ("nhmrc", "NHMRC (Australia)", "au", "CC BY 4.0"),
    "trdizin_tubitak_projects": ("tubitak", "TÜBİTAK (Turkey)", "tr", "no reuse terms published: facts and a link only"),
    "swedish_research_council": ("vr", "Swedish Research Council", "se", "open, may be used publicly; credit SweCRIS"),
    "swecris_vinnova": ("vinnova", "Vinnova (Sweden)", "se", "open, may be used publicly; credit SweCRIS"),
    "formas": ("formas", "Formas (Sweden)", "se", "open, may be used publicly; credit SweCRIS"),
    "forte": ("forte", "Forte (Sweden)", "se", "open, may be used publicly; credit SweCRIS"),
    "ncn_ranking_lists": ("ncn", "NCN (Poland)", "pl", "reuse under Poland's 2016 reuse act: credit NCN and the retrieval date"),
    "fwo_fris": ("fwo", "FWO (Flanders, Belgium)", "be", "Flemish open-data licence (Modellicentie Gratis Hergebruik): credit FRIS"),
    "isf_grant_search": ("isf", "Israel Science Foundation", "il", "unverified (site unreachable): facts and a link only"),
    "sfi_open_data": ("sfi", "Research Ireland (SFI)", "ie", "CC BY 4.0"),
    "wellcome_trust": ("wellcome", "Wellcome", "gb", "CC BY 4.0 (360Giving)"),
    "amed_amedfind": ("amed", "AMED (Japan)", "jp", "quoting allowed with source and URL (non-commercial)"),
    "zonmw_projects_jsonapi": ("zonmw", "ZonMw (Netherlands)", "nl", "no reuse terms published: facts and a link only"),
    "forskningsportal_dk": ("dff", "Independent Research Fund Denmark", "dk", "no licence named: facts and a link only; credit Research Portal Denmark"),
    "portal_fis_isciii": ("isciii", "ISCIII (Spain)", "es", "reproduction needs ISCIII's permission: facts and a link only, no abstracts"),
    "nafosted": ("nafosted", "NAFOSTED (Vietnam)", "vn", "no reuse terms published: facts and a link only"),
    "icmr_approved_projects": ("icmr", "ICMR (India)", "in", "may be reproduced free of charge, source acknowledged"),
    "nsf_sri_lanka_gmis": ("nsf-lk", "NSF Sri Lanka", "lk", "copying content not allowed: facts and a link only, no abstracts"),
    "hec_pakistan_nrpu": ("hec", "HEC NRPU (Pakistan)", "pk", "no reuse terms published: facts and a link only"),
    # China's provincial natural science foundations, as one funder
    **{p: ("cn-prov", "Provincial science foundations (China)", "cn", "unverified")
       for p in ("zhejiang_nsf", "hunan_nsf", "fujian_nsf", "guangdong_nsf", "shanghai_nsf", "shandong_nsf",
                 "hainan_nsf", "chongqing_nsf", "heilongjiang_nsf")},
}
# Funders whose investigators are named in Chinese characters: mainland researchers write their
# names in pinyin, Taiwanese ones in Wade-Giles (see taiwan_name).
PINYIN = {"nsfc", "cn-prov"}
WADE_GILES = {"nstc"}
FROM_YEAR = 2015  # grants running in 2015 or later, as for KAKEN; HEC's list has no dates and stays
# Sources whose terms don't allow reproducing their texts: titles and facts with a link, no abstracts.
NO_ABSTRACTS = {"isciii", "nsf-lk"}
# NCN's lists carry no dates, but each id starts with NCN's call edition ("21_OPUS_12243"): edition E
# opens in March/June/September/December of 2011 + (E-1)//4 and results come about nine months later.
# Projects then run up to the programme's longest duration (months, from NCN's call pages).
NCN_MONTHS = {"OPUS": 48, "OPUS LAP": 48, "PRELUDIUM": 36, "PRELUDIUM BIS": 48, "SONATA": 36, "SONATA BIS": 60,
              "MAESTRO": 60, "HARMONIA": 36, "SONATINA": 36, "ETIUDA": 12, "FUGA": 36, "SYMFONIA": 60,
              "POLONEZ": 24, "POLONEZ BIS": 24, "UWERTURA": 12}


def ncn_dates(gid: str) -> tuple[str, str]:
    """Estimated start and end for an NCN id: '21_OPUS_12243' -> ('2016-12-01', '2020-12-01')."""
    m = re.match(r"(\d+)_(.+)_\d+$", gid)
    if not m:
        return "", ""
    edition, programme = int(m.group(1)), m.group(2).replace("-", " ").strip().upper()
    opens_month = 12 * (2011 + (edition - 1) // 4) + [3, 6, 9, 12][(edition - 1) % 4] - 1
    start = opens_month + 9
    end = start + NCN_MONTHS.get(programme, 36)
    return f"{start // 12}-{start % 12 + 1:02d}-01", f"{end // 12}-{end % 12 + 1:02d}-01"


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


COMPOUND_SURNAMES = {"欧阳", "歐陽", "司马", "司馬", "上官", "诸葛", "諸葛", "张简", "張簡", "范姜", "长孙", "長孫",
                     "尉迟", "尉遲", "万俟", "萬俟", "东方", "東方", "夏侯", "皇甫", "公孙", "公孫", "慕容", "令狐"}


def split_chinese(given: str, family: str) -> tuple[str, str]:
    """Some funders give the whole name in one field ('王采蕎'): the surname is its first character, or
    its first two for compound surnames ('歐陽')."""
    if given or not CJK.search(family) or len(family) < 2 or "·" in family:
        return given, family
    n = 2 if family[:2] in COMPOUND_SURNAMES and len(family) > 2 else 1
    return family[n:], family[:n]


def pinyin_name(given: str, family: str) -> tuple[str, str]:
    """('燎原', '董') -> ('Liaoyuan', 'Dong'): how mainland researchers write their names in English."""
    if lazy_pinyin is None or not CJK.search(given + family):
        return given, family
    given, family = split_chinese(given, family)
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


# Taiwan: researchers write their names in Wade-Giles without apostrophes ("Chen-Yu Lee", "Kuo",
# "Hsieh"), so names are read in pinyin and converted syllable by syllable; surnames whose usual
# spelling differs from the rule are listed.
TW_SURNAMES = {"李": "Lee", "張": "Chang", "郭": "Kuo", "何": "Ho", "羅": "Lo", "葉": "Yeh", "游": "Yu",
               "呂": "Lu", "盧": "Lu", "余": "Yu", "于": "Yu", "俞": "Yu", "尤": "Yu", "簡": "Chien",
               "曾": "Tseng", "單": "Shan", "區": "Ou", "歐陽": "Ouyang", "張簡": "Changchien",
               "阮": "Juan", "黎": "Li", "卓": "Cho", "粘": "Nien"}
WG_INITIALS = [("zh", "ch"), ("ch", "ch"), ("sh", "sh"), ("b", "p"), ("p", "p"), ("d", "t"), ("t", "t"),
               ("g", "k"), ("k", "k"), ("z", "ts"), ("c", "ts"), ("s", "s"), ("r", "j"), ("j", "ch"),
               ("q", "ch"), ("x", "hs"), ("m", "m"), ("f", "f"), ("n", "n"), ("l", "l"), ("h", "h"),
               ("y", "y"), ("w", "w"), ("", "")]


def wade_giles(syllable: str) -> str:
    """One pinyin syllable (no tones) in Taiwanese-style Wade-Giles: 'zhi' -> 'chih', 'xue' -> 'hsueh',
    'guo' -> 'kuo', 'cong' -> 'tsung', 'qian' -> 'chien'."""
    p = syllable.lower().replace("v", "u")
    if p == "yi":
        return "yi"  # Taiwanese names: "Hsin-Yi", not the textbook "Hsin-I"
    if p == "you":
        return "yu"
    if p in ("ye", "yan"):
        return {"ye": "yeh", "yan": "yen"}[p]
    if p in ("zi", "ci", "si"):
        return {"zi": "tzu", "ci": "tzu", "si": "ssu"}[p]
    ini, wg_ini = next((i, w) for i, w in WG_INITIALS if p.startswith(i))
    fin = p[len(ini):]
    if ini in ("zh", "ch", "sh", "r") and fin == "i":
        fin = "ih"
    elif fin == "e" and ini in ("g", "k", "h"):
        fin = "o"
    elif fin == "uo" and ini not in ("g", "k", "h", "sh"):
        fin = "o"
    elif fin == "ui" and ini in ("g", "k"):
        fin = "uei"
    fin = re.sub(r"ong$", "ung", fin)
    fin = re.sub(r"ian$", "ien", fin)
    fin = re.sub(r"ie$", "ieh", fin)
    fin = re.sub(r"ue$", "ueh", fin)
    return wg_ini + fin


def taiwan_name(given: str, family: str) -> tuple[str, str]:
    """('采蕎', '王') -> ('Tsai-chiao', 'Wang')."""
    if lazy_pinyin is None or not CJK.search(given + family):
        return given, family
    given, family = split_chinese(given, family)
    syllables = [wade_giles(x) for x in lazy_pinyin(given, style=Style.NORMAL) if x.strip()]
    first = "-".join(syllables).capitalize() if syllables else given
    last = TW_SURNAMES.get(family) or "".join(wade_giles(x) for x in lazy_pinyin(family, style=Style.NORMAL)).capitalize()
    return first, last


def institution(r: dict, lead: dict | None) -> str:
    """OpenAlex's English names for the awarded institution, most specific first ("Institute of High
    Energy Physics | Chinese Academy of Sciences"), else the funder's own spelling."""
    names = [i["display_name"] for i in r.get("institution_awarded") or [] if i.get("display_name")]
    if names:
        return " | ".join(dict.fromkeys(names))
    own = (((lead or {}).get("affiliation") or {}).get("name") or "").strip()
    # "Universidade de São Paulo (USP). Faculdade de ..." (FAPESP): the university first, then the full name
    if (m := re.match(r"(.+?\))\. ", own)):
        return f"{m.group(1)} | {own}"
    return own


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
        if abstract.startswith("Principal investigator:") or funder in NO_ABSTRACTS:  # HEC: it repeats the PI
            abstract = ""
        start, end = r.get("start_date") or "", r.get("end_date") or ""
        if funder == "ncn" and not start:
            start, end = ncn_dates((r.get("funder_award_id") or "").strip())
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
            given, family = (pinyin_name(*name) if funder in PINYIN
                             else taiwan_name(*name) if funder in WADE_GILES else name)
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
