"""bearing — where a research project is pointed, measured from its own record.

    python -m bearing <project-path> [--adapter agentic|pipeline] [--json]

It measures drift. It has no taste, and it must not pretend to: see README.md, and the
author's own Compass, which is explicit that connecting work to real need is a habit and
that building a tracking system for THAT is itself the trap.
"""
from __future__ import annotations

import argparse
import json
import sys

from .checks import run_all
from .record import ADAPTERS, load


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bearing", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--adapter", choices=sorted(ADAPTERS))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    rec = load(a.project, a.adapter)
    if not rec.ok():
        print(f"bearing: found no record under {rec.root}\n"
              f"  adapters: {', '.join(sorted(ADAPTERS))}\n"
              f"  configure one in .bearing.json, or write ~30 lines in record.py",
              file=sys.stderr)
        return 2
    res = run_all(rec)
    if a.json:
        print(json.dumps({"project": rec.name, "checks": res}, indent=1, default=str))
        return 0

    bad = [x for x in res if x["bad"]]
    print(f"\n{rec.name} — {len(rec.work)} work, {len(rec.questions)} questions, "
          f"{len(rec.results)} results")
    print(f"{len(bad)} of {len(res)} questions have an uncomfortable answer.\n")
    for x in res:
        print(f"{'!!' if x['bad'] else '  '}  {x['q']}")
        print(f"      {x['say']}")
        if x["bad"] and x.get("why"):
            print(f"      asked because: {x['why']}")
        if x.get("soft"):
            print("      (heuristic — evidence in --json; disagree freely)")
        print()
    print("bearing measures drift, not direction. A project can pass every question\n"
          "and still be pointed somewhere that does not matter.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
