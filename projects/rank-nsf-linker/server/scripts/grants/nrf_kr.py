"""NRF (National Research Foundation of Korea) projects -> data/grants/nrf_*.csv

Source: data.go.kr dataset 3049029, "한국연구재단_이알앤디_과제정보" (NRF R&D project information), a CSV
in CP949 refreshed yearly; licence 이용허락범위: 제한 없음 (no restrictions). The dataset page names the
current file (atchFileId), so it is read first. Only part of NRF's projects (selected 2023 onward,
mostly humanities and social sciences); no amounts, end dates or abstracts, and titles in Korean.
Dates: Korea's academic year starts in March, so a project starts in March of its selection year;
the end is estimated at three years (most NRF basic-research projects run one to five). Projects
marked classified (보안과제여부 = Y) are left out.
People: the principal investigator, romanised (Revised Romanization, with the usual English spellings
of surnames: 김 Kim, 이 Lee, 박 Park); given names vary in English ("Sung-Hoon" for 성훈), so fewer link
than for other funders. Institutions: OpenAlex's English name for the Korean one (its alternative
names), from the institutions snapshot.
"""

import csv
import hashlib
import io
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA, UA, download, write  # noqa: E402
from fetchlib import openalex_snapshot, snapshot_records  # noqa: E402

PAGE = "https://www.data.go.kr/data/3049029/fileData.do"
FILE = "https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId={}&fileDetailSn=1&insertDataPrcus=N"
SRC = DATA / "nrf"
HANGUL = re.compile(r"[가-힣]")

INITIALS = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj", "ch", "k", "t", "p", "h"]
VOWELS = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe", "yo", "u", "wo", "we", "wi",
          "yu", "eu", "ui", "i"]
FINALS = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t",
          "ng", "t", "t", "k", "t", "p", "t"]
SURNAMES = {
    "김": "Kim", "이": "Lee", "박": "Park", "최": "Choi", "정": "Jung", "강": "Kang", "조": "Cho", "윤": "Yoon",
    "장": "Jang", "임": "Lim", "한": "Han", "오": "Oh", "서": "Seo", "신": "Shin", "권": "Kwon", "황": "Hwang",
    "안": "Ahn", "송": "Song", "류": "Ryu", "유": "Yoo", "홍": "Hong", "전": "Jeon", "고": "Ko", "문": "Moon",
    "양": "Yang", "손": "Son", "배": "Bae", "백": "Baek", "허": "Heo", "남": "Nam", "심": "Shim", "노": "Noh",
    "하": "Ha", "곽": "Kwak", "성": "Sung", "차": "Cha", "주": "Joo", "우": "Woo", "구": "Koo", "민": "Min",
    "나": "Na", "진": "Jin", "지": "Ji", "엄": "Um", "채": "Chae", "원": "Won", "천": "Chun", "방": "Bang",
    "공": "Kong", "현": "Hyun", "함": "Ham", "변": "Byun", "염": "Yeom", "여": "Yeo", "추": "Choo", "도": "Do",
    "소": "So", "석": "Seok", "선": "Sun", "설": "Seol", "마": "Ma", "길": "Gil", "연": "Yeon", "표": "Pyo",
    "명": "Myung", "기": "Ki", "반": "Ban", "왕": "Wang", "금": "Keum", "옥": "Ok", "육": "Yook", "인": "In",
    "맹": "Maeng", "제": "Je", "모": "Mo", "탁": "Tak", "국": "Kook", "은": "Eun", "편": "Pyeon", "용": "Yong",
    "경": "Kyung", "봉": "Bong", "태": "Tae", "형": "Hyung", "두": "Doo", "동": "Dong", "승": "Seung",
    "남궁": "Namgung", "황보": "Hwangbo", "제갈": "Jegal", "선우": "Sunwoo", "독고": "Dokgo", "서문": "Seomun",
}


def romanize(text: str) -> str:
    """Revised Romanization, syllable by syllable: '성훈' -> 'seonghun'."""
    out = []
    for ch in text:
        code = ord(ch) - 0xAC00
        if 0 <= code < 11172:
            out.append(INITIALS[code // 588] + VOWELS[(code % 588) // 28] + FINALS[code % 28])
        else:
            out.append(ch)
    return "".join(out)


def split_name(name: str) -> tuple[str, str]:
    """'김성훈' -> ('Seonghun', 'Kim'); two-syllable surnames ('남궁') when listed."""
    name = name.strip()
    n = 2 if name[:2] in SURNAMES and len(name) > 2 else 1
    family, given = name[:n], name[n:]
    return romanize(given).capitalize(), SURNAMES.get(family) or romanize(family).capitalize()


def korean_names() -> dict[str, str]:
    """Korean institution name -> OpenAlex's English one (alternative names in Hangul), for Korea."""
    best: dict[str, tuple[int, str]] = {}
    for r in snapshot_records(openalex_snapshot("institutions")):
        if r.get("country_code") != "KR" or not r.get("display_name"):
            continue
        for n in r.get("display_name_alternatives") or []:
            if HANGUL.search(n):
                works = r.get("works_count") or 0
                if n not in best or works > best[n][0]:
                    best[n.strip()] = (works, r["display_name"])
    return {n: v[1] for n, v in best.items()}


def main() -> None:
    SRC.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(PAGE, headers=UA), timeout=120) as r:
        page = r.read().decode("utf-8", errors="replace")
    m = re.search(r"atchFileId=(FILE_\d+)", page)
    if not m:
        sys.exit("data.go.kr: the dataset page no longer names its file")
    dest = SRC / "nrf_projects.csv"
    download(FILE.format(m.group(1)), dest, max_age_days=30)
    rows = list(csv.DictReader(io.StringIO(dest.read_bytes().decode("cp949", errors="replace"))))
    english = korean_names()
    grants, people, seen = [], [], set()
    for row in rows:
        if row.get("보안과제여부", "").strip() == "Y" or not row.get("과제명", "").strip():
            continue
        year = (row.get("선정년도") or row.get("사업년도") or "").strip()
        title, pi, inst_ko = row["과제명"].strip(), row.get("연구책임자명", "").strip(), row.get("주관기관명", "").strip()
        # no project number in the file: the researcher number, year and title identify a project
        gid = f"{year}-{row.get('연구자번호', '').strip()}-" + hashlib.sha1(title.encode()).hexdigest()[:8]
        if gid in seen:
            continue
        seen.add(gid)
        grants.append({
            "funder": "nrf", "grant_id": gid, "title": title, "abstract": "", "amount": "", "currency": "KRW",
            "country": "kr", "starts": f"{year}-03-01" if year.isdigit() else "",
            "ends": f"{int(year) + 3}-02-28" if year.isdigit() else "", "url": PAGE,
            "scheme": (row.get("세부사업명") or row.get("소사업명") or "").strip(), "field": "",
        })
        if pi and HANGUL.search(pi):
            first, last = split_name(pi)
            en = english.get(inst_ko)
            people.append({"funder": "nrf", "grant_id": gid, "full_name": f"{first} {last}", "first_name": first,
                           "last_name": last, "role": "PI",
                           "institution": f"{en} | {inst_ko}" if en else inst_ko, "orcid": ""})
    named = sum(1 for p in people if " | " in p["institution"])
    print(f"NRF: {len(grants)} projects; {named} of {len(people)} institutions named in English")
    write("nrf", grants, people)


if __name__ == "__main__":
    main()
