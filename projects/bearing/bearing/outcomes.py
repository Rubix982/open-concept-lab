"""What each check has actually caught. Checks earn their place from outcomes, not priors.

    python -m bearing <project> --record <check> caught|false-positive|ignored ["note"]
    python -m bearing <project> --track

A check is added because someone believed it would help. That belief is a prior, and
priors about which checks matter are exactly what this project's record shows to be
unreliable: `preflight`'s first cache rule, `bearing`'s first `still_checking`, and the
first `unchecked_universal` were each written with confidence and each cried wolf.

So the track record is kept, and it is kept per check:

    caught          it surfaced something real that was then acted on
    false-positive  it fired and was wrong
    ignored         it fired and nobody did anything

A check with no `caught` after many firings is overhead, and `--track` says so out loud.
This is the falsification clause from edit-slice's harness ticket — *"if three runs pass
with no caught defect, the harness is overhead"* — made mechanical, so it gets checked
rather than quietly accreted.

Outcomes live in `.bearing-outcomes.json` beside the project, because what a check catches
is a property of the project it runs on, not of the check.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import date

VERDICTS = ("caught", "false-positive", "ignored")


def _path(root: str) -> str:
    return os.path.join(root, ".bearing-outcomes.json")


def load(root: str) -> list[dict]:
    try:
        with open(_path(root), encoding="utf-8") as fh:
            return json.load(fh).get("outcomes", [])
    except Exception:
        return []


def record(root: str, check: str, verdict: str, note: str = "") -> str:
    if verdict not in VERDICTS:
        return f"verdict must be one of {', '.join(VERDICTS)}"
    rows = load(root)
    rows.append({"check": check, "verdict": verdict, "note": note,
                 "date": date.today().isoformat()})
    with open(_path(root), "w", encoding="utf-8") as fh:
        json.dump({"_": "what each bearing check has actually caught here",
                   "outcomes": rows}, fh, indent=1)
    return f"recorded: {check} -> {verdict}"


def track(root: str, check_names: list[str]) -> str:
    rows = load(root)
    per: dict[str, Counter] = {}
    for r in rows:
        per.setdefault(r["check"], Counter())[r["verdict"]] += 1

    out = [f"track record over {len(rows)} recorded outcome(s)", "=" * 64, ""]
    if not rows:
        out.append("  Nothing recorded yet. A check's value is unknown until someone says")
        out.append("  whether it helped:")
        out.append("")
        out.append("      python -m bearing <project> --record <check> caught \"why\"")
        return "\n".join(out)

    out.append(f"  {'check':<30}{'caught':>8}{'false+':>8}{'ignored':>9}  verdict")
    for name in check_names:
        c = per.get(name, Counter())
        fired = sum(c.values())
        if not fired:
            out.append(f"  {name:<30}{'—':>8}{'—':>8}{'—':>9}  never fired")
            continue
        if c["caught"]:
            v = "earns its place"
        elif c["false-positive"] >= 2:
            v = "CRYING WOLF — fix or delete"
        elif fired >= 3:
            v = "OVERHEAD — fired, never helped"
        else:
            v = "too early to say"
        out.append(f"  {name:<30}{c['caught']:>8}{c['false-positive']:>8}"
                   f"{c['ignored']:>9}  {v}")
    out.append("")
    out.append("  A check with no `caught` after several firings is overhead. That is the")
    out.append("  falsification clause, made mechanical so it gets checked rather than")
    out.append("  quietly accreted.")
    return "\n".join(out)
