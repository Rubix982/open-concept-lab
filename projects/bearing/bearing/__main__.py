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
    ap.add_argument("--brief", action="store_true",
                    help="re-entry brief: what changed, and what needs you")
    ap.add_argument("--since", default="7.days")
    ap.add_argument("--lessons", action="store_true",
                    help="rules earned by being wrong, with their incidents")
    ap.add_argument("--record", nargs="+", metavar=("CHECK VERDICT", "NOTE"),
                    help="log what a check actually did: caught | false-positive | ignored")
    ap.add_argument("--track", action="store_true",
                    help="which checks have earned their place here")
    a = ap.parse_args(argv)

    if a.lessons:
        from .lessons import render
        print(render())
        return 0

    rec = load(a.project, a.adapter)
    if not rec.ok():
        print(f"bearing: found no record under {rec.root}\n"
              f"  adapters: {', '.join(sorted(ADAPTERS))}\n"
              f"  configure one in .bearing.json, or write ~30 lines in record.py",
              file=sys.stderr)
        return 2
    if a.record:
        from .outcomes import record as log_outcome
        chk, verdict, *note = a.record
        print(log_outcome(rec.root, chk, verdict, " ".join(note)))
        return 0

    if a.track:
        from .checks import CHECKS
        from .outcomes import track
        print(track(rec.root, [c.__name__ for c in CHECKS]))
        return 0

    if a.brief:
        from .brief import render
        print(render(rec, a.since))
        return 0

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
