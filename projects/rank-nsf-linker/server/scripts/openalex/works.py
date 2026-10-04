"""OpenAlex works for the explorer's papers, looked up by DOI -> data/openalex/works.csv

Source: OpenAlex API (https://api.openalex.org, data CC0). Key: OPENALEX_API_KEY in server/.env.
Input: data/openalex/dois.txt, one lower-case DOI per line, exported from the database:
    docker exec -e PGPASSWORD=postgres pg17-local psql -h localhost -U postgres -d rank-nsf-linker -tAc \\
      "SELECT DISTINCT lower(substring(url from 'doi\\.org/(.+)$')) FROM explorer_work_docs
       WHERE kind = 'paper' AND url ~* 'doi\\.org/'" > data/openalex/dois.txt
Output columns: doi, openalex_id, abstract, topic, subfield, field, cited_by.

Abstracts are only used to improve semantic matching; the explorer does not display them.
DOIs are looked up 50 per request, at most a few requests a second. Each response is cached in
data/openalex/works/ together with the DOIs it asked for, so a rerun (interrupted, or with a changed
DOI list) only requests DOIs never asked before. Pass --max-calls N to cap this run's API calls.
"""

import csv
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "openalex"
CACHE = DATA / "works"
API = "https://api.openalex.org/works"
BATCH = 50
PAUSE = 0.25  # seconds between calls
FIELDS = "id,doi,abstract_inverted_index,primary_topic,cited_by_count"


def api_key() -> str:
    for line in (ROOT / "server" / ".env").read_text().splitlines():
        if line.startswith("OPENALEX_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENALEX_API_KEY is not set in server/.env")


def abstract(inverted: dict | None) -> str:
    if not inverted:
        return ""
    words: dict[int, str] = {}
    for word, positions in inverted.items():
        for p in positions:
            words[p] = word
    return " ".join(words[i] for i in sorted(words))


def fetch(batch: list[str], key: str, show_limits: bool = False) -> bytes:
    query = urllib.parse.urlencode({
        "filter": "doi:" + "|".join(batch), "per_page": BATCH, "select": FIELDS, "api_key": key,
    })
    req = urllib.request.Request(f"{API}?{query}", headers={"User-Agent": "advisor-atlas/1.0 (non-commercial)"})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                if show_limits:  # usage against the daily allowance (headers carry no key)
                    print("  rate limits:", {k: v for k, v in resp.headers.items() if "limit" in k.lower()})
                return resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                wait = 30 * (attempt + 1)
                print(f"  HTTP {e.code}; waiting {wait} s")
                time.sleep(wait)
                continue
            raise SystemExit(f"OpenAlex refused the request: HTTP {e.code}")  # no URL: it carries the key
        except (TimeoutError, OSError) as e:
            print(f"  {type(e).__name__}; retrying")
            time.sleep(15 * (attempt + 1))
    raise SystemExit("OpenAlex kept failing; stopping (rerun to resume)")


def main() -> None:
    max_calls = int(sys.argv[sys.argv.index("--max-calls") + 1]) if "--max-calls" in sys.argv else None
    dois = sorted({d.strip().lower() for d in (DATA / "dois.txt").read_text().splitlines() if d.strip()})
    # DOIs with commas or pipes cannot go in an OR filter
    dois = [d for d in dois if "," not in d and "|" not in d]
    CACHE.mkdir(parents=True, exist_ok=True)
    key = api_key()
    asked: set[str] = set()
    for path in CACHE.glob("*.json"):
        try:
            asked.update(json.loads(path.read_text()).get("requested", []))
        except ValueError:
            pass
    todo = [d for d in dois if d not in asked]
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]
    print(f"{len(dois)} DOIs, {len(asked)} already asked; {len(batches)} batches to request")
    calls = 0
    for batch in batches:
        if max_calls is not None and calls >= max_calls:
            print(f"stopped after {calls} calls (--max-calls); rerun to continue")
            break
        body = json.loads(fetch(batch, key, show_limits=calls == 0))
        name = hashlib.sha1("|".join(batch).encode()).hexdigest()[:16]
        (CACHE / f"{name}.json").write_text(json.dumps({"requested": batch, "results": body.get("results", [])}))
        calls += 1
        if calls % 200 == 0:
            print(f"  {calls}/{len(batches)} batches")
        time.sleep(PAUSE)

    rows = {}
    for path in sorted(CACHE.glob("*.json")):
        for w in json.loads(path.read_text()).get("results", []):
            doi = (w.get("doi") or "").lower().removeprefix("https://doi.org/")
            if not doi:
                continue
            t = w.get("primary_topic") or {}
            rows[doi] = {
                "doi": doi, "openalex_id": (w.get("id") or "").rsplit("/", 1)[-1],
                "abstract": abstract(w.get("abstract_inverted_index")),
                "topic": t.get("display_name") or "",
                "subfield": (t.get("subfield") or {}).get("display_name") or "",
                "field": (t.get("field") or {}).get("display_name") or "",
                "cited_by": w.get("cited_by_count") or 0,
            }
    with (DATA / "works.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["doi", "openalex_id", "abstract", "topic", "subfield", "field", "cited_by"])
        w.writeheader()
        w.writerows(rows.values())
    with_abstract = sum(1 for r in rows.values() if r["abstract"])
    print(f"data/openalex/works.csv: {len(rows)} works, {with_abstract} with an abstract")


if __name__ == "__main__":
    main()
