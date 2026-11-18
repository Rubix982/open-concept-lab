"""Put the sweep's shortlist into the reading ledger, so none of it is lost.

`citation_sweep.py` leaves about a hundred papers in a JSON file. A JSON file
is not a ledger: nothing counts them, nothing shows what is still unread, and
the project's own rule is that a surfaced line of inquiry gets an id even when
nobody is following it today. This moves them into `web/data/papers.yml`, where
the reading page already counts `to-read` against `read`.

**Every entry lands unread and uncitable.** `status: to-read` and
`verified: false`, which in that file means the entry came from a secondhand
note and must not be cited yet — true here, because a keyword screen read a
title and an abstract and nothing else.

**`gives_me` is not invented.** That field holds the one thing its owner goes
back to a paper for, and a script cannot know it. What goes in instead is why
the paper is on the list: which screen matched and on which words. Replacing
that line with a real one is what reading the paper means.

Authors are fetched for the shortlist only, because the sweep's own cache does
not hold them and re-pulling 3,780 records to get a hundred names would be
rude to a shared quota.

    python3 ai/edit-reach/tools/sweep_intake.py --dry-run
    python3 ai/edit-reach/tools/sweep_intake.py

Appends to web/data/papers.yml. Papers already in that file are skipped, by
arXiv id first and by title when there is no arXiv id.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SWEEP = ROOT / "results" / "R-004-sweep.json"
CACHE = ROOT / "results" / "R-004-rome-citers.json"
PAPERS = REPO / "web" / "data" / "papers.yml"

BATCH = "https://api.semanticscholar.org/graph/v1/paper/batch"
UA = "edit-reach-citation-sweep/1.0 (research literature screen)"

#: Where each screen's papers belong on the reading page. The page groups by
#: both, so a stub with neither would be filed under nothing and disappear —
#: which is the failure this script exists to prevent.
SHELF = {
    "contamination": ("Evaluating edits", "Ripple effects and multi-hop"),
    "pre-edit screen": ("Evaluating edits", "Predicting an edit's reach"),
    "rank-one structure": ("Knowledge editing", "Rank-one edits and their structure"),
}

#: Words too common to tell two citation ids apart.
STOP = {
    "a", "an", "the", "of", "for", "and", "in", "on", "to", "with", "via", "is",
    "are", "can", "we", "it", "its", "be", "by", "at", "from", "into", "when",
    "how", "what", "does", "do", "large", "language", "models", "model", "llm",
    "llms", "knowledge", "editing", "edits", "edit", "towards", "evaluation",
    "evaluating", "study", "analysis", "new", "more", "their", "this", "that",
}


def ascii_fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_title(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", ascii_fold(s or "").lower()).strip()


def post(url: str, body: dict, tries: int = 8) -> list:
    wait = 2.0
    data = json.dumps(body).encode()
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(
            url, data=data,
            headers={"User-Agent": UA, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == tries:
                raise
            print(f"    {e.code}; waiting {wait:.0f}s", file=sys.stderr)
        time.sleep(wait)
        wait = min(wait * 1.7, 120)
    raise RuntimeError("unreachable")


def existing_keys() -> tuple[set[str], set[str], set[str]]:
    """What the ledger already holds: ids, arXiv numbers, normalised titles."""
    text = PAPERS.read_text()
    ids = set(re.findall(r"^([A-Za-z0-9_]+):\s*$", text, re.M))
    arx = set(re.findall(r"arxiv\.org/abs/([0-9.]+)", text))
    titles = {norm_title(m) for m in re.findall(r"^  title: (.+)$", text, re.M)}
    return ids, arx, titles


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    sweep = json.loads(SWEEP.read_text())
    if not CACHE.is_file():
        sys.exit(f"{CACHE.relative_to(REPO)} is not here. Run citation_sweep.py first;\n"
                 "it is gitignored because one command rebuilds it.")
    by_title = {norm_title(p.get("title")): p
                for p in json.loads(CACHE.read_text())["citers"] if p.get("title")}

    # One row per paper, carrying every screen that matched it.
    shortlist: dict[str, dict] = {}
    for question, rows in sweep["hits"].items():
        for r in rows:
            key = norm_title(r["title"])
            e = shortlist.setdefault(key, {**r, "screens": {}})
            e["screens"][question] = r["matched"]

    ids, arx, titles = existing_keys()
    fresh = [e for k, e in shortlist.items()
             if k not in titles and (e.get("arxiv") or "") not in arx]
    print(f"shortlist {len(shortlist)} · already in the ledger "
          f"{len(shortlist) - len(fresh)} · new {len(fresh)}")
    if not fresh:
        return

    # Authors, for the shortlist only.
    wanted = [e for e in fresh if by_title.get(norm_title(e["title"]), {}).get("paperId")]
    authors: dict[str, list[str]] = {}
    for i in range(0, len(wanted), 400):
        chunk = wanted[i:i + 400]
        got = post(f"{BATCH}?fields=authors,externalIds",
                   {"ids": [by_title[norm_title(e["title"])]["paperId"] for e in chunk]})
        for e, rec in zip(chunk, got):
            if rec:
                authors[norm_title(e["title"])] = [
                    x.get("name", "") for x in (rec.get("authors") or [])]
        time.sleep(2.0)
    print(f"authors for {len(authors)} of {len(fresh)}")

    out, used = [], set(ids)
    for e in sorted(fresh, key=lambda r: -r["cited_by"]):
        names = authors.get(norm_title(e["title"]), [])
        last = ascii_fold(names[0].split()[-1]).lower() if names else "anon"
        last = re.sub(r"[^a-z]", "", last) or "anon"
        word = next((w for w in norm_title(e["title"]).split()
                     if w not in STOP and len(w) > 3), "paper")
        base = f"{last}{e['year'] or 'nd'}{word}"
        cid, n = base, 2
        while cid in used:
            cid, n = f"{base}{n}", n + 1
        used.add(cid)

        field, area = SHELF[next(iter(e["screens"]))]
        why = "; ".join(f"the {q} screen on {', '.join(w[:4])}"
                        for q, w in e["screens"].items())
        author_line = ", ".join(names[:6]) + (" et al." if len(names) > 6 else "")
        out.append(f"""
{cid}:
  title: {json.dumps(e['title'])}
  authors: {json.dumps(author_line or 'unknown')}
  year: {e['year'] or 'null'}
  venue: {json.dumps(e['venue'] or 'Preprint')}
  url: {('https://arxiv.org/abs/' + e['arxiv']) if e.get('arxiv') else 'null'}
  status: to-read
  relevance: medium
  field: {json.dumps(field)}
  area: {json.dumps(area)}
  verified: false
  projects: [edit-slice, rome-neighbors]
  gives_me: {json.dumps('TODO(read) - matched by ' + why + ' in [T-014]; cited ' + str(e['cited_by']) + ' times. Relevance is a placeholder: an unread paper has none assessed. Replace this line with what the paper gives, once its methods have been read.')}""")

    block = "\n".join(out) + "\n"
    if a.dry_run:
        print(block[:1400])
        print(f"… {len(out)} entries, not written (--dry-run)")
        return
    PAPERS.write_text(PAPERS.read_text().rstrip("\n") + "\n" + block)
    print(f"appended {len(out)} entries to {PAPERS.relative_to(REPO)}")
    print("All to-read and verified: false. None of them may be cited yet.")


if __name__ == "__main__":
    main()
