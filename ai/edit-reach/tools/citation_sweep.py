"""Sweep the papers that cite ROME, and write the result down.

[T-014] answered three positioning questions from a web-search pass, and its
own provenance line says so: *one sweep pass, English-language web search*.
That is the weakest line in the repository. Every other number here comes from
a script reading data, and can be re-run.

This makes the sweep the same kind of object. It pulls every paper citing ROME
from Semantic Scholar, caches the raw response so a re-run costs nothing, and
screens titles and abstracts against the three questions. What it prints is a
count and a shortlist, so "I read some titles" becomes "4,000 screened, 37
matched, here they are" — and three months from now the same command shows only
what is new.

**It does not decide anything.** A keyword screen over titles and abstracts
cannot tell whether a paper did the thing; the project rule is that such a
verdict needs the methods section, not the prose. The shortlist is a reading
list, and marking an entry as checked is a human act.

**No key, and no email.** Semantic Scholar serves these endpoints
unauthenticated, at a rate limit shared across every anonymous caller, which is
why this retries and caches rather than hurrying. OpenAlex would be the other
source and now requires a key, which means registering an address; that is a
decision for the person whose address it is, not for this script. The
User-Agent names the tool and nothing else.

    python3 ai/edit-reach/tools/citation_sweep.py            # cached if present
    python3 ai/edit-reach/tools/citation_sweep.py --refresh  # re-fetch
    python3 ai/edit-reach/tools/citation_sweep.py --since 2026

Writes results/R-004-rome-citers.json (the cache) and
results/R-004-sweep.json (the screened shortlist).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "R-004-rome-citers.json"
OUT = ROOT / "results" / "R-004-sweep.json"

API = "https://api.semanticscholar.org/graph/v1"
SEED = "arXiv:2202.05262"          # Meng et al., ROME
FIELDS = "title,abstract,year,venue,citationCount,externalIds"
PAGE = 500
UA = "edit-reach-citation-sweep/1.0 (research literature screen)"

#: The three questions [T-014] asked, as the words a paper would have to use.
#: Each is a *screen*, not a verdict: it decides what gets read, nothing else.
#:
#: `must` and `also` are both required, `any` needs one hit. The first run of
#: this screen returned 426 papers for the contamination question, which is
#: roughly a third of everything that cites ROME and is not a reading list. The
#: fix is a third required word rather than a longer `any`: a paper that matters
#: here is about editing, about an evaluation set, *and* suspicious of it. A
#: screen that returns everything has not failed safe, it has stopped screening.
QUESTIONS: dict[str, dict[str, list[str]]] = {
    "contamination": {
        "must": ["edit"],
        "also": ["benchmark", "evaluation", "dataset", "test set", "multi-hop",
                 "multihop", "ripple", "mquake", "counterfact"],
        "any": ["contamina", "leak", "shortcut", "spurious", "artifact",
                "surface form", "lexical", "overlap", "mention", "flaw",
                "pitfall", "misleading", "overestimat", "inflat", "illusion"],
    },
    "pre-edit screen": {
        "must": ["edit"],
        "also": [],
        "any": ["before the edit", "pre-edit", "without applying", "prior to editing",
                "predict the effect", "predict which", "anticipat", "a priori",
                "estimate the impact", "forecast"],
    },
    "rank-one structure": {
        "must": [],
        "also": [],
        "any": ["rank-one", "rank one", "low-rank update", "closed-form edit",
                "update direction", "key vector", "projection coefficient",
                "delivered fraction"],
    },
}


def fetch(url: str, tries: int = 12) -> dict:
    """One GET, with the backoff an unauthenticated shared quota requires."""
    wait = 2.0
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == tries:
                raise
            print(f"    {e.code}; waiting {wait:.0f}s", file=sys.stderr)
        except urllib.error.URLError as e:
            if attempt == tries:
                raise
            print(f"    {e.reason}; waiting {wait:.0f}s", file=sys.stderr)
        time.sleep(wait)
        wait = min(wait * 1.7, 120)
    raise RuntimeError("unreachable")


def save(rows: list[dict], offset: int | None) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(
        {"seed": SEED, "fetched": time.strftime("%Y-%m-%d"), "n": len(rows),
         "next_offset": offset, "citers": rows}, indent=1))


def pull_citers() -> list[dict]:
    """Every paper citing the seed, a page at a time, checkpointed.

    The unauthenticated quota is shared across every anonymous caller of this
    API, so a 429 says nothing about this script and waiting is the only
    response. Each page is written as it arrives and `next_offset` records
    where to resume, so an interrupted sweep costs the pages it already has
    rather than the whole thing.
    """
    rows: list[dict] = []
    offset = 0
    if CACHE.is_file():
        held = json.loads(CACHE.read_text())
        if held.get("next_offset") is not None:
            rows, offset = held["citers"], held["next_offset"]
            print(f"  resuming at {offset} with {len(rows)} already held", file=sys.stderr)
    while True:
        q = urllib.parse.urlencode({"fields": FIELDS, "offset": offset, "limit": PAGE})
        page = fetch(f"{API}/paper/{SEED}/citations?{q}")
        batch = [c["citingPaper"] for c in page.get("data", []) if c.get("citingPaper")]
        rows.extend(batch)
        nxt = page.get("next")
        save(rows, nxt)
        print(f"  {len(rows)} citers", file=sys.stderr)
        if nxt is None or not batch:
            break
        offset = nxt
        time.sleep(3.0)       # the shared quota is a courtesy as much as a limit
    save(rows, None)
    return rows


def screen(rows: list[dict]) -> dict[str, list[dict]]:
    hits: dict[str, list[dict]] = {k: [] for k in QUESTIONS}
    for p in rows:
        text = " ".join(filter(None, [p.get("title"), p.get("abstract")])).lower()
        if not text:
            continue
        for name, spec in QUESTIONS.items():
            if any(m not in text for m in spec["must"]):
                continue
            if spec["also"] and not any(w in text for w in spec["also"]):
                continue
            matched = [w for w in spec["any"] if w in text]
            if matched:
                hits[name].append({
                    "title": p.get("title"),
                    "year": p.get("year"),
                    "venue": p.get("venue") or "",
                    "cited_by": p.get("citationCount") or 0,
                    "arxiv": (p.get("externalIds") or {}).get("ArXiv"),
                    "matched": matched,
                })
    for name in hits:
        hits[name].sort(key=lambda r: (-(r["cited_by"]), -(r["year"] or 0)))
    return hits


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-fetch instead of using the cache")
    ap.add_argument("--since", type=int, default=0, help="only screen papers from this year on")
    a = ap.parse_args()

    held = json.loads(CACHE.read_text()) if CACHE.is_file() else None
    complete = held is not None and held.get("next_offset") is None
    if complete and not a.refresh:
        rows = held["citers"]
        print(f"cache: {len(rows)} citers, fetched {held.get('fetched')}")
    else:
        if a.refresh and CACHE.is_file():
            CACHE.unlink()
        print(f"fetching citers of {SEED} …")
        rows = pull_citers()
        print(f"wrote {CACHE.relative_to(ROOT)}")

    pool = [p for p in rows if (p.get("year") or 0) >= a.since] if a.since else rows
    with_abstract = sum(1 for p in pool if p.get("abstract"))
    hits = screen(pool)

    OUT.write_text(json.dumps({
        "seed": SEED, "screened": len(pool), "with_abstract": with_abstract,
        "since": a.since or None, "questions": {k: len(v) for k, v in hits.items()},
        "hits": hits,
    }, indent=1))

    print(f"\nscreened {len(pool)} citers "
          f"({with_abstract} had an abstract to read; a title-only entry can "
          f"only match on its title)")
    for name, rowset in hits.items():
        print(f"\n{name}  —  {len(rowset)} to read")
        for r in rowset[:12]:
            ax = f"  arXiv:{r['arxiv']}" if r["arxiv"] else ""
            print(f"  {r['cited_by']:>5}  {r['year']}  {(r['title'] or '')[:88]}{ax}")
        if len(rowset) > 12:
            print(f"  … and {len(rowset) - 12} more in {OUT.relative_to(ROOT)}")
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    print("A match is a reading list, not a verdict. The project rule is that a "
          "positioning verdict rests on a methods section.")


if __name__ == "__main__":
    main()
