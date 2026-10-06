"""KAKEN (JSPS Grants-in-Aid for Scientific Research, Japan) informatics projects -> data/grants/kaken_*.csv

Source: KAKEN OpenSearch API (https://kaken.nii.ac.jp/opensearch/), application id CINII_APP_ID in
server/.env. Terms of use (https://support.nii.ac.jp/en/cinii/terms): non-profit use; no bursty
access (one request every few seconds here, every page cached in data/kaken/); API only; credit
"Created by Advisor Atlas, based on KAKEN (NII)" with a link to each project. Only facts are kept
(title, investigators, institution, amount, years, link) — no report text.

Projects: research field "Informatics" (the pre-2018 classification) and every review section under
Broad Section J (informatics, 2018 onward: "Medium-sized Section 60:...", "Basic Section 60050:
Software-related", ...; names from KAKEN's review-section master), ending in 2015 or later.
Names: KAKEN's English member record gives family and given names for most investigators; otherwise
the katakana reading is romanised (Hepburn) so names compare with CSRankings' romaji spellings.
Institutions are in Japanese; KAKEN's institution master (data/kaken/institution_master_kakenhi.xml,
https://bitbucket.org/niijp/grants_masterxml_kaken) gives their English names.
"""

import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from common import DATA, download, secret, write
from fetchlib import refetch_or_keep

ROOT = Path(__file__).resolve().parents[3]
CACHE = DATA / "kaken"
API = "https://kaken.nii.ac.jp/opensearch/"
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)"}
PAGE = 500
PAUSE = 3.0  # seconds between requests
FROM_YEAR = 2015
PAGE_MAX_AGE = 28  # days: pages are fetched again monthly (new and updated projects)
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def app_id() -> str:
    return secret("CINII_APP_ID")


def review_sections() -> list[str]:
    """English names of Broad Section J and every section under it, from the review-section master."""
    path = CACHE / "review_section_master_kakenhi.xml"
    if not path.exists():
        sys.exit("data/kaken/review_section_master_kakenhi.xml missing: its download failed")
    names = []
    for el in ET.parse(path).getroot().iter("review_section"):
        mext = next((c.text for c in el.findall("code") if c.get("type") == "mext"), "")
        en = next((n.text for n in el.findall("name") if n.get("lang") == "en"), "")
        if en and (mext == "J" or re.match(r"6[012](\d{3})?$", mext or "")):
            names.append(en.strip())
    return sorted(set(names))


def fetch_page(query: str, start: int, key: str) -> bytes:
    slug = "informatics" if query == "Informatics" else re.sub(r"[^0-9A-Za-z]+", "-", query)[:60]
    path = CACHE / f"{slug}-{FROM_YEAR}-{start:06d}.xml"

    def fetch() -> str:
        q = urllib.parse.urlencode({"appid": key, "format": "xml", "rw": PAGE, "st": start, "lang": "en",
                                    "qd": query, "s1": FROM_YEAR, "o1": 3})
        req = urllib.request.Request(f"{API}?{q}", headers=UA)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    body = resp.read()
                break
            except OSError as e:
                if attempt == 3:
                    raise SystemExit(f"KAKEN page {start} failed: {type(e).__name__}")  # no URL: it has the key
                time.sleep(30 * (attempt + 1))
        time.sleep(PAUSE)
        return body.decode("utf-8")

    return refetch_or_keep(path, PAGE_MAX_AGE, fetch).encode("utf-8")


# Katakana -> Hepburn romaji (digraphs first).
KANA = {
    "キャ": "kya", "キュ": "kyu", "キョ": "kyo", "シャ": "sha", "シュ": "shu", "ショ": "sho", "チャ": "cha",
    "チュ": "chu", "チョ": "cho", "ニャ": "nya", "ニュ": "nyu", "ニョ": "nyo", "ヒャ": "hya", "ヒュ": "hyu",
    "ヒョ": "hyo", "ミャ": "mya", "ミュ": "myu", "ミョ": "myo", "リャ": "rya", "リュ": "ryu", "リョ": "ryo",
    "ギャ": "gya", "ギュ": "gyu", "ギョ": "gyo", "ジャ": "ja", "ジュ": "ju", "ジョ": "jo", "ビャ": "bya",
    "ビュ": "byu", "ビョ": "byo", "ピャ": "pya", "ピュ": "pyu", "ピョ": "pyo", "ジェ": "je", "ティ": "ti",
    "ディ": "di", "ファ": "fa", "フィ": "fi", "フェ": "fe", "フォ": "fo", "ウィ": "wi", "ウェ": "we",
    "ア": "a", "イ": "i", "ウ": "u", "エ": "e", "オ": "o", "カ": "ka", "キ": "ki", "ク": "ku", "ケ": "ke",
    "コ": "ko", "サ": "sa", "シ": "shi", "ス": "su", "セ": "se", "ソ": "so", "タ": "ta", "チ": "chi",
    "ツ": "tsu", "テ": "te", "ト": "to", "ナ": "na", "ニ": "ni", "ヌ": "nu", "ネ": "ne", "ノ": "no",
    "ハ": "ha", "ヒ": "hi", "フ": "fu", "ヘ": "he", "ホ": "ho", "マ": "ma", "ミ": "mi", "ム": "mu",
    "メ": "me", "モ": "mo", "ヤ": "ya", "ユ": "yu", "ヨ": "yo", "ラ": "ra", "リ": "ri", "ル": "ru",
    "レ": "re", "ロ": "ro", "ワ": "wa", "ヲ": "o", "ン": "n", "ガ": "ga", "ギ": "gi", "グ": "gu",
    "ゲ": "ge", "ゴ": "go", "ザ": "za", "ジ": "ji", "ズ": "zu", "ゼ": "ze", "ゾ": "zo", "ダ": "da",
    "ヂ": "ji", "ヅ": "zu", "デ": "de", "ド": "do", "バ": "ba", "ビ": "bi", "ブ": "bu", "ベ": "be",
    "ボ": "bo", "パ": "pa", "ピ": "pi", "プ": "pu", "ペ": "pe", "ポ": "po", "ヴ": "vu",
    "ァ": "a", "ィ": "i", "ゥ": "u", "ェ": "e", "ォ": "o",
}


def romaji(kana: str) -> str:
    """'シラド' -> 'shirado', 'ヒロカズ' -> 'hirokazu'. Long vowels are dropped ('オオノ' -> 'ono'),
    as in most romaji spellings of names."""
    out, i = [], 0
    kana = kana.replace("ー", "")
    while i < len(kana):
        if kana[i] == "ッ" and i + 1 < len(kana):  # double the next consonant
            nxt = KANA.get(kana[i + 1:i + 3]) or KANA.get(kana[i + 1], "")
            out.append(nxt[:1])
            i += 1
            continue
        two = KANA.get(kana[i:i + 2])
        if two:
            out.append(two)
            i += 2
            continue
        out.append(KANA.get(kana[i], ""))
        i += 1
    word = "".join(out)
    word = re.sub(r"ou", "o", word)  # Tōkyō -> Tokyo, Satou -> Sato
    word = re.sub(r"([ou])\1", r"\1", word)  # Oono -> Ono, Ryuu -> Ryu
    return word


def text(el, path: str) -> str:
    found = el.find(path)
    return (found.text or "").strip() if found is not None and found.text else ""


def summary(award, lang: str):
    for s in award.findall("summary"):
        if s.get(XML_LANG) == lang:
            return s
    return None


def institution_names() -> dict[str, str]:
    """Japanese institution name -> English, from KAKEN's master data (later tables win)."""
    names: dict[str, str] = {}
    path = CACHE / "institution_master_kakenhi.xml"
    if not path.exists():
        print("data/kaken/institution_master_kakenhi.xml missing: institutions stay in Japanese")
        return names
    for inst in ET.parse(path).getroot().iter("institution"):
        ja = en = ""
        for n in inst.findall("name"):
            if n.get("lang") == "ja":
                ja = (n.text or "").strip()
            elif n.get("lang") == "en":
                en = (n.text or "").strip()
        if ja and en:
            names[ja] = en
    return names


MASTERS = "https://bitbucket.org/niijp/grants_masterxml_kaken/raw/master/"


def main() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    # KAKEN's master data (review sections, institutions' English names), refreshed monthly
    for name in ("review_section_master_kakenhi.xml", "institution_master_kakenhi.xml"):
        download(MASTERS + name, CACHE / name, max_age_days=30)
    english_institution = institution_names()
    key = app_id()

    # One page at a time: the cached pages are about 1 GB of XML, and parsing them all at once ran
    # the fetcher out of memory.
    def pages():
        for query in ["Informatics"] + review_sections():
            first = ET.fromstring(fetch_page(query, 1, key))
            total = int(text(first, "totalResults") or 0)
            print(f"  {query}: {total}")
            yield first
            for start in range(1 + PAGE, total + 1, PAGE):
                yield ET.fromstring(fetch_page(query, start, key))

    seen_numbers = set()
    grants, people = [], []
    for page in pages():
        for award in page.findall("grantAward"):
            number = award.get("awardNumber") or ""
            en, ja = summary(award, "en"), summary(award, "ja")
            if not number or ja is None or number in seen_numbers:
                continue
            seen_numbers.add(number)
            title = text(en, "title") if en is not None else ""
            title = title or text(ja, "title")
            # Ongoing projects carry their period only as attributes (no endFiscalYear element yet)
            period = ja.find("periodOfAward")
            start = end = ""
            if period is not None:
                start = text(period, "startFiscalYear") or period.get("searchStartFiscalYear") or ""
                end = text(period, "endFiscalYear") or period.get("searchEndFiscalYear") or ""
            if end and int(end) < FROM_YEAR:
                continue  # the API's period filter needs both ends, so older projects come back too
            amount = ja.find("overallAwardAmount")
            grants.append({
                "funder": "kaken", "grant_id": number, "title": title, "abstract": "",
                "amount": text(amount, "totalCost") if amount is not None else "", "currency": "JPY",
                "country": "jp",
                "starts": f"{start}-04-01" if start else "",  # Japanese fiscal years start in April
                "ends": f"{int(end) + 1}-03-31" if end else "",
                "url": text(award, "urlList/url") or f"https://kaken.nii.ac.jp/grant/KAKENHI-PROJECT-{number}/",
                "scheme": text(en, "category") if en is not None else text(ja, "category"),
                "field": "; ".join(r.text.strip() for r in (en if en is not None else ja).findall("review_section") if r.text),
            })
            english_members = {}
            if en is not None:
                for em in en.findall("member"):
                    english_members[em.get("sequence")] = em
            for m in ja.findall("member"):
                role = "PI" if m.get("role") == "principal_investigator" else "CoI"
                pn = m.find("personalName")
                if pn is None:
                    continue
                em = english_members.get(m.get("sequence"))
                last = text(em, "personalName/familyName") if em is not None else ""
                first_name = text(em, "personalName/givenName") if em is not None else ""
                if not (re.search(r"[A-Za-z]", last) and re.search(r"[A-Za-z]", first_name)):
                    fam, giv = pn.find("familyName"), pn.find("givenName")
                    if fam is None or giv is None or not fam.get("yomi") or not giv.get("yomi"):
                        continue
                    last, first_name = romaji(fam.get("yomi")).title(), romaji(giv.get("yomi")).title()
                last = last.title() if last.isupper() else last
                inst_ja = text(m, "institution")
                inst = english_institution.get(inst_ja, "")
                people.append({
                    "funder": "kaken", "grant_id": number, "full_name": f"{first_name} {last}".strip(),
                    "first_name": first_name, "last_name": last, "role": role,
                    "institution": " | ".join(x for x in (inst, inst_ja) if x),
                })
    write("kaken", grants, people)


if __name__ == "__main__":
    main()
