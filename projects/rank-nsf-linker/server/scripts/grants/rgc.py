"""Hong Kong Research Grants Council (RGC) computing projects -> data/grants/rgc_*.csv

Source: RGC's public project enquiry (https://cerg1.ugc.edu.hk/cergprod/scrrm00541.jsp), panel
Engineering, subject "Computing Science & Information Technology" (E2), award years 2015 onward.
RGC publishes no reuse licence, so only facts are kept — investigators, title, institution, amount,
years, status and a link to the project page — never the abstract. One request a second; every
page is cached in data/rgc/, so a rerun fetches only what is missing.
"""

import html
import http.cookiejar
import re
import time
import urllib.parse
import urllib.request
from datetime import date

from common import DATA, split_name, write
from fetchlib import refreshed_cache

CACHE = DATA / "rgc"
BASE = "https://cerg1.ugc.edu.hk/cergprod/"
UA = {"User-Agent": "advisor-atlas/1.0 (non-commercial research explorer)"}
# Result pages belong to the search session the POST starts, so requests share cookies.
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
YEARS = range(2015, date.today().year + 1)


def get(url: str, cache_name: str, data: bytes | None = None) -> str:
    path = CACHE / cache_name
    if path.exists():
        return path.read_text(encoding="utf-8")
    req = urllib.request.Request(url, data=data, headers=UA, method="POST" if data else "GET")
    for attempt in range(4):
        try:
            with OPENER.open(req, timeout=120) as resp:
                text = resp.read().decode("utf-8", errors="replace")
            break
        except OSError as e:
            if attempt == 3:
                raise SystemExit(f"RGC request failed: {e}")
            time.sleep(15 * (attempt + 1))
    path.write_text(text, encoding="utf-8")
    time.sleep(1.1)  # one request a second
    return text


SEARCH_FORM = {"mode": "search", "page": "1", "sScheme": "1", "panel": "E", "subject": "E2", "institution": "",
               "proj_id": "", "proj_title": "", "isname": "", "ioname": "", "fromAwardYear": "", "toAwardYear": "",
               "sStatus": ""}


def list_page(year: int, page: int) -> str:
    """Page 1 is the search form; later pages are the page's own "go to page" form (frm_goToPage)."""
    if page == 1:
        form = {**SEARCH_FORM, "Year": str(year)}
    else:
        form = {"subject": "E2", "panel": "E", "scheme": "1", "sScheme": "1", "sStatus": "", "proj_id": "",
                "Old_proj_id": "", "proj_title": "", "isname": "", "ioname": "", "institution": "",
                "Year": str(year), "pages": str(page), "mode": "search"}
    return get(BASE + "scrrm00541.jsp", f"list-{year}-{page:03d}.html", urllib.parse.urlencode(form).encode())


def detail_url(proj_id: str, year: int) -> str:
    return BASE + "scrrm00542.jsp?" + urllib.parse.urlencode(
        {"proj_id": proj_id, "old_proj_id": "null", "proj_title": "", "isname": "", "ioname": "",
         "institution": "", "subject": "E2", "pages": "1", "year": str(year)})


def fields(page: str) -> dict[str, str]:
    """Label -> value from a detail page ("Institution :" followed by its value)."""
    body = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    lines = [html.unescape(x).strip() for x in re.sub(r"<[^>]+>", "\n", body).splitlines()]
    lines = [x for x in lines if x]
    out, label = {}, None
    for line in lines:
        if line.endswith(":") and len(line) < 60:
            label = line.rstrip(" :")
            out[label] = ""
        elif label is not None:
            out[label] = f"{out[label]}; {line}" if out[label] else line  # several co-investigators
    return out


def person(raw: str) -> tuple[str, str, str]:
    """'Prof Chan, Antoni B.' -> ('Antoni B. Chan', 'Antoni B.', 'Chan')."""
    raw = re.sub(r"^(Prof|Professor|Dr|Ir|Mr|Ms|Mrs|Miss)\.?\s+", "", raw.strip(), flags=re.I)
    if "," in raw:
        last, first = [x.strip() for x in raw.split(",", 1)]
        last = last.title() if last.isupper() else last
        return f"{first} {last}".strip(), first, last
    return split_name(raw)


def main() -> None:
    # Pages only make sense together (a search session's results; pages that shift as projects
    # are added): refreshed whole every 28 days, the previous copy kept until that succeeds.
    with refreshed_cache(CACHE, 28):
        fetch_all()


def fetch_all() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    grants, people = [], []
    for year in YEARS:
        first = list_page(year, 1)
        pages = max([1] + [int(p) for p in re.findall(r"goToPage\([^)]*'(\d+)'\)", first)])
        ids = []
        for page in range(1, pages + 1):
            text = first if page == 1 else list_page(year, page)
            ids += re.findall(r'NAME="proj_id" value="([^"]+)"', text)
        ids = list(dict.fromkeys(ids))
        print(f"{year}: {len(ids)} projects")
        for pid in ids:
            f = fields(get(detail_url(pid, year), f"project-{pid}.html"))
            title = f.get("Project Title(English)", "").split("; ")[0].strip()
            if not title:
                continue
            end = ""
            m = re.match(r"(\d{1,2})-(\d{1,2})-(\d{4})", f.get("Completion Date", ""))
            if m:
                end = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
            ex = re.match(r"(\d{4})", f.get("Exercise Year", ""))
            start = f"{int(ex.group(1)) + 1}-01-01" if ex else ""  # projects start in the year after the exercise
            institution = f.get("Institution", "")
            grants.append({
                "funder": "rgc", "grant_id": pid, "title": title, "abstract": "",
                "amount": f.get("Fund Approved", "").replace(",", ""), "currency": "HKD", "country": "hk",
                "starts": start, "ends": end, "url": detail_url(pid, year),
                "scheme": f.get("Funding Scheme", ""), "field": f.get("Subject Area", ""),
            })
            pi = f.get("Principal Investigator(English)", "")
            if pi:
                full, first_name, last = person(pi)
                people.append({"funder": "rgc", "grant_id": pid, "full_name": full, "first_name": first_name,
                               "last_name": last, "role": "PI", "institution": institution})
            cois = f.get("Co - Investigator(s)", "")
            for raw in re.split(r"\s*;\s*|\s{2,}", cois):
                if raw and not raw.lower().startswith(("panel", "n/a")) and "," in raw:
                    full, first_name, last = person(raw)
                    people.append({"funder": "rgc", "grant_id": pid, "full_name": full, "first_name": first_name,
                                   "last_name": last, "role": "CoI", "institution": institution})
    write("rgc", grants, people)


if __name__ == "__main__":
    main()
