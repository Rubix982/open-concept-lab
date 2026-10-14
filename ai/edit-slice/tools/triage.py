"""Every warning and error a run logged, sorted by cause, so a run's failures are triaged by
code rather than read through by a person each time.

    python3 tools/triage.py                      # the newest log
    python3 tools/triage.py logs/run_e033-*.log  # specific logs
    python3 tools/triage.py --all                # every log in logs/
    python3 tools/triage.py --json               # for report.py

Ported from ~/code/janaan/tools/pipeline/ledger.py, which does this for a critic's concerns.
The idea that transfers is the last line of its docstring: a concern matching no cause is
listed as "unsorted", and **that is what needs a person**. Everything else is a failure mode
we have already diagnosed, and a count of it is enough.

Each CAUSE carries the record entry that diagnosed it, so a line in a log at 3am points at
the decision that explains it rather than at a stack trace.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: (id, cause, where it was diagnosed, pattern). Order matters — first match wins, so the
#: specific sits above the general.
CAUSES: list[tuple[str, str, str, str]] = [
    ("flaky-node", "NDIF rejected the trace; a retry lands on a good node",
     "[O-007]/[O-008] — 3 of 6 on an identical unchanged call",
     r"is not whitelisted|flaky node"),
    ("cross-device", "a sum spanned two GPUs of a sharded model",
     "[E-033] — compute_v_batch's decay term, invisible below 70B",
     r"Expected all tensors to be on the same device|cuda:\d+ and cuda:\d+"),
    ("hang", "a job sat in RECEIVED or RUNNING without failing",
     "[E-033] — 135h and 144h, no exception ever raised",
     r"RemoteTimeout|exceeded \d+s with no response"),
    ("oom-split", "a batch was too large and was split",
     "remote.score_pairs — shared hosts enforce a per-process budget",
     r"batch split|auto-split|halving to \d+"),
    ("transport", "a socket dropped mid-call",
     "remote._is_transport_error — the httpx.ConnectTimeout incident",
     r"transport failure|ConnectionError|ConnectTimeout|packet queue is empty"),
    ("parked", "a whole chunk failed and the run parked before retrying",
     "the runners' stall loop — an outage, not a code fault",
     r"parking \d+"),
    ("gate-refused", "a pre-registered gate or verdict refused the run",
     "working as designed — the number is the finding",
     r"GATE FAILED|VERDICT: (?:INFEASIBLE|UNMATCHED|NOT INTERPRETABLE|UNDERPOWERED)|CONTROL FAILS"),
    ("confound-fired", "a pre-registered confound check fired",
     "working as designed — read the entry, not the log",
     r"CONFOUND \d+ FIRES|uninterpretable|NOT MATCHED"),
    # Added after the first run over every log: 15 lines came back unsorted and most were
    # not failures at all. They are scientific conclusions and scope caveats logged at
    # WARNING, which is this project's own doing — `logs.setup` reserves WARNING for
    # "retries / auto-splits / skipped items" and the runners have been using it for
    # nulls, verdicts and [O-004] scope notes besides. Until that is separated at the
    # source, they are classified here so the unsorted list means what it says.
    ("verdict", "a pre-registered verdict or null branch fired",
     "working as designed — the entry in decisions.md is the finding",
     r"VERDICT:|NULL branch|DEGENERATE:|is NOT supported"),
    ("scope-caveat", "a scope limit the run states about its own number",
     "[O-004] — existence never a rate; read beside the result",
     r"existence claim|EXISTENCE-grade|is NOT a rate|not attributable to scale|"
     r"INSTRUCTION-TUNED|deferring \d+"),
    ("transport-ws", "the websocket closed with a server-side status",
     "same class as `transport`; 1011 is the server giving up mid-call",
     r"close status: (?:1006|1011|1012|1013)"),
    ("legacy-untyped", "a failure logged before `retrying` recorded exception messages",
     "fixed 2026-09-20 — the type alone could not say which class fired",
     r"failed \(NNsightException: Traceback"),
]


def triage(paths: list[str]) -> dict:
    counts: Counter = Counter()
    unsorted_lines: list[tuple[str, str]] = []
    per_file: dict[str, Counter] = {}
    for p in paths:
        c: Counter = Counter()
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not re.search(r"\b(WARNING|ERROR|CRITICAL)\b", line):
                    continue
                line = line.rstrip()
                for cid, _, _, pat in CAUSES:
                    if re.search(pat, line, re.I):
                        c[cid] += 1
                        counts[cid] += 1
                        break
                else:
                    counts["UNSORTED"] += 1
                    unsorted_lines.append((os.path.basename(p), line[:300]))
        per_file[os.path.basename(p)] = c
    return {"counts": dict(counts), "unsorted": unsorted_lines,
            "per_file": {k: dict(v) for k, v in per_file.items()},
            "files": len(paths)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.logs:
        paths = sorted({p for g in a.logs for p in glob.glob(g)})
    else:
        every = sorted(glob.glob(os.path.join(ROOT, "logs", "*.log")),
                       key=os.path.getmtime, reverse=True)
        paths = every if a.all else every[:1]
    if not paths:
        print("no logs matched")
        return 1

    r = triage(paths)
    if a.json:
        print(json.dumps(r, indent=1))
        return 0

    known = {cid: (cause, where) for cid, cause, where, _ in CAUSES}
    print(f"{len(paths)} log(s)\n")
    width = max((len(k) for k in r["counts"]), default=10)
    for cid, n in sorted(r["counts"].items(), key=lambda kv: -kv[1]):
        if cid == "UNSORTED":
            continue
        cause, where = known[cid]
        print(f"  {cid:<{width}}  {n:>5}  {cause}")
        print(f"  {'':<{width}}         diagnosed: {where}")
    n_unsorted = r["counts"].get("UNSORTED", 0)
    print()
    if not n_unsorted:
        print("  UNSORTED      0  — every failure is one we have already diagnosed.")
        return 0
    # The whole point of the tool. A known failure needs a count; an unknown one needs a
    # person, and it is the only thing here worth being woken for.
    print(f"  UNSORTED  {n_unsorted:>5}  <- THIS is what needs a person")
    seen = set()
    for fname, line in r["unsorted"]:
        key = re.sub(r"\d+", "#", line)[:120]
        if key in seen:
            continue
        seen.add(key)
        print(f"      {fname}: {line}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
