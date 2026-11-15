"""Census the committed logs for readings the result files overwrote.

A runner writes one JSON per ticket, so running it twice leaves one file and two
logs. `run_e006.py` was run twice on 1 November, four minutes apart, and the
second run overwrote the first: the committed JSON holds one session and reports
that the values partition cleanly by GPU. Both logs survive, and together they
show the partition holding *within* a session while the value a given GPU
returns changes *between* them.

That is only recoverable because the logs were committed. It is the logging rule
paying for itself, and it is the reason this script reads `logs/` rather than
`results/`.

    python3 ai/edit-reach/tools/log_census.py

Writes results/E-017-log-census.json.

**Not a rebuild of [E-012].** That census counted readings at a resolution these
logs do not preserve: most lines carry the floor median to four decimals and the
effect is at 1e-06. This counts what the logs do carry — a content hash of the
raw keys, and the device that served them.
"""
from __future__ import annotations

import json
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
LOGS = ROOT / "logs"
OUT = ROOT / "results" / "E-017-log-census.json"

#: `  0  sig 3896ee28446f8156  gpu 0     runtime  1.66s ...`, with floor
#: appearing only once the format was widened mid-day.
READING = re.compile(
    r"\s(?P<ticket>[A-Z]-\d+)\s+(?P<n>\d+)\s+sig\s+(?P<sig>[0-9a-f]{8,})\s+"
    r"gpu\s+(?P<gpu>\S+)(?:.*?floor\s+(?P<floor>[0-9.]+))?"
)


def main() -> None:
    sessions: dict[str, dict] = {}
    for path in sorted(LOGS.glob("*.log")):
        rows = []
        for line in path.read_text(errors="replace").splitlines():
            m = READING.search(line)
            if m:
                rows.append({
                    "reading": int(m.group("n")),
                    "signature": m.group("sig"),
                    "gpu": m.group("gpu"),
                    "floor": float(m.group("floor")) if m.group("floor") else None,
                })
        if rows:
            sessions[path.name] = {"ticket": rows[0] and path.name.split("-")[0],
                                   "readings": len(rows), "rows": rows}

    by_gpu_per_session = {}
    for name, s in sessions.items():
        g = defaultdict(set)
        for r in s["rows"]:
            g[r["gpu"]].add(r["signature"])
        by_gpu_per_session[name] = {k: sorted(v) for k, v in sorted(g.items())}

    # the point: a device's value within one session, against across sessions
    across = defaultdict(set)
    for name, g in by_gpu_per_session.items():
        for gpu, sigs in g.items():
            across[gpu].update(sigs)

    stable_within = all(len(sigs) == 1
                        for g in by_gpu_per_session.values() for sigs in g.values())
    stable_across = all(len(v) == 1 for v in across.values())

    doc = {
        "ticket": "E-017",
        "source": "committed logs under ai/edit-reach/logs/",
        "why": ("a runner writes one JSON per ticket, so a second run overwrites the "
                "first; the logs keep both"),
        "sessions_with_device_readings": len(sessions),
        "readings": sum(s["readings"] for s in sessions.values()),
        "distinct_signatures": len({r["signature"] for s in sessions.values()
                                    for r in s["rows"]}),
        "devices": sorted(across),
        "one_value_per_device_within_a_session": stable_within,
        "one_value_per_device_across_sessions": stable_across,
        "signatures_by_device_per_session": by_gpu_per_session,
        "signatures_by_device_over_all_sessions": {k: sorted(v) for k, v in sorted(across.items())},
        "note": ("Not a rebuild of [E-012]: these logs carry the floor median to four "
                 "decimals and that census worked at 1e-06."),
        "sessions": sessions,
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT.parent.parent)}")
    print(f"  {doc['sessions_with_device_readings']} sessions, {doc['readings']} readings, "
          f"{doc['distinct_signatures']} distinct values over devices {doc['devices']}")
    print(f"  one value per device within a session: {stable_within}")
    print(f"  one value per device across sessions : {stable_across}")


if __name__ == "__main__":
    main()
