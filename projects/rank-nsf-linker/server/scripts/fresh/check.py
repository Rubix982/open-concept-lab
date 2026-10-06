"""Fresh-server test: compare the fresh stack (docker-compose.fresh.yaml, started from an empty data/)
with the live one, and say whether the fresh one got through on its own.

    python3 server/scripts/fresh/check.py

Prints each pipeline step's status, each fetch source's state, and row counts side by side (fresh /
live / share). Passes when every step up to "Fetch OpenAlex Data" completed, no fetch failed, and the
main tables hold at least 90% of the live rows (OpenAlex can trail: the fresh stack spends few calls).
Standard library only.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LIVE = "pg17-local"
FRESH = "atlas-fresh-postgres-1"
COUNTS = [
    ("universities", "SELECT count(*) FROM explorer_universities"),
    ("US R1 universities", "SELECT count(*) FROM explorer_universities WHERE carnegie = 'R1'"),
    ("Pakistani universities", "SELECT count(*) FROM explorer_universities WHERE country = 'pk'"),
    ("people", "SELECT count(*) FROM explorer_faculty"),
    ("people from OpenAlex", "SELECT count(*) FROM explorer_faculty WHERE source = 'openalex'"),
    ("NSF awards", "SELECT count(*) FROM award"),
    ("other funders' grants", "SELECT count(*) FROM funder_grants"),
    ("funders", "SELECT count(DISTINCT funder) FROM funder_grants"),
    ("all grants (Funding tab)", "SELECT count(*) FROM explorer_grants"),
    ("papers and grants searchable", "SELECT count(*) FROM explorer_work_docs"),
    ("research areas", "SELECT count(DISTINCT area) FROM research_area_venues"),
]
MUST_MATCH = {"universities", "US R1 universities", "Pakistani universities", "NSF awards",
              "other funders' grants", "funders", "all grants (Funding tab)"}


def psql(container: str, sql: str) -> str:
    r = subprocess.run(["docker", "exec", "-e", "PGPASSWORD=postgres", container, "psql", "-h", "localhost",
                        "-U", "postgres", "-d", "rank-nsf-linker", "-AtF", "|", "-c", sql],
                       capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def main() -> None:
    ok = True
    print("Pipeline steps (fresh):")
    steps = psql(FRESH, "SELECT pipeline_name, status FROM pipeline_status WHERE pipeline_name LIKE 'step_%' "
                        "ORDER BY substring(pipeline_name from 'step_(\\d+)')::int, pipeline_name")
    if not steps:
        sys.exit("the fresh stack's database isn't reachable: is it running (make fresh-test)?")
    latest: dict[str, str] = {}
    for line in steps.splitlines():
        name, status = line.split("|")
        latest[name.split("_", 2)[2]] = status  # the step number moves when steps are added
    for name, status in latest.items():
        print(f"  {status:12} {name}")
        if status != "completed" and name not in ("Embed Explorer Work", "Embed Grants"):
            ok = False

    print("\nFetch sources (fresh):")
    for p in sorted((ROOT / "fresh" / "data" / "fetch_state").glob("*.json")):
        s = json.loads(p.read_text())
        print(f"  {s.get('status', '?'):11} {p.stem}  {(s.get('log_tail') or [''])[-1][:90]}")
        if s.get("status") == "failed":
            ok = False

    print(f"\n{'':32}{'fresh':>10}{'live':>10}{'share':>8}")
    for label, sql in COUNTS:
        f, l = psql(FRESH, sql), psql(LIVE, sql)
        fv, lv = int(f or 0), int(l or 0)
        share = fv / lv if lv else 1.0
        flag = ""
        if label in MUST_MATCH and share < 0.9:
            ok, flag = False, "  <- short"
        print(f"  {label:30}{fv:>10,}{lv:>10,}{share:>8.0%}{flag}")
    print("\nfresh-server test:", "PASSED" if ok else "NOT YET (see above)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
