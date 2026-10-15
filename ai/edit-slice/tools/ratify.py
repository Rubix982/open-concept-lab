"""What an unattended session did, and what still needs a person. One page.

    python3 tools/ratify.py              # write out/RATIFY.md
    python3 tools/ratify.py --stdout     # print it

Written because the lab ran unattended for an hour and then stopped for ten, and the
account of what happened was spread across a ticket file, a thread ledger, a decisions
log and fourteen commits. On return a person should read ONE page and know three things:
what ran, what it found, and what needs their judgement.

The loop's failure mode is a confident wrong record. An unread confident wrong record is
how a body of work rots from the inside, so every autonomously-written entry is marked
`_Unratified_` and listed here until a person removes the marker.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(*a: str) -> str:
    try:
        return subprocess.run(a, cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return ""


def unratified() -> list[tuple[str, str]]:
    """(id, first line) for every record entry still carrying the marker."""
    out = []
    for name in ("decisions.md", "findings.md"):
        p = os.path.join(ROOT, "agents", "shared", name)
        if not os.path.exists(p):
            continue
        cur, head = None, ""
        for ln in open(p, encoding="utf-8"):
            m = re.match(r"^## \[([^\]]+)\] (.*)", ln)
            if m:
                cur, head = m.group(1), m.group(2).strip()
            elif "_Unratified_" in ln and cur:
                out.append((cur, head))
                cur = None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stdout", action="store_true")
    ap.add_argument("--since", default="12 hours ago")
    a = ap.parse_args()

    commits = _run("git", "log", f"--since={a.since}", "--format=%h %s")
    n_commits = len([x for x in commits.splitlines() if x.strip()])
    esc = os.path.join(ROOT, "out", "reports", "ESCALATION.md")
    queue = json.load(open(os.path.join(ROOT, "tools", "queue.json"), encoding="utf-8"))
    jobs = [j["ticket"] for j in queue.get("jobs", [])]

    tick = []
    for role in ("orchestrator", "researcher", "engineer", "documentor"):
        p = os.path.join(ROOT, "agents", role, "tickets.md")
        if not os.path.exists(p):
            continue
        cur = None
        for ln in open(p, encoding="utf-8"):
            m = re.match(r"^### ([ORED]-\d+[a-z]?) · (.*)", ln)
            if m:
                cur = m.groups()
            elif cur and ln.startswith("**Status:**"):
                if ln.split("**Status:**")[1].strip().split()[0] in ("open", "in-progress"):
                    tick.append(cur)
                cur = None

    threads = []
    tp = os.path.join(ROOT, "threads.md")
    if os.path.exists(tp):
        cur = None
        for ln in open(tp, encoding="utf-8"):
            m = re.match(r"^### (T-\d+) · (.*)", ln)
            if m:
                cur = m.groups()
            elif cur and ln.startswith("**Status:**"):
                if ln.split("**Status:**")[1].strip().split()[0] in ("open", "active"):
                    threads.append(cur)
                cur = None

    unr = unratified()
    L = ["# What ran while you were away", "",
         f"_Generated {datetime.now():%Y-%m-%d %H:%M} · covering the last {a.since}_", ""]

    L += ["## Needs your judgement", ""]
    if os.path.exists(esc):
        L += ["- **An escalation is open** — `out/reports/ESCALATION.md`. The queue is "
              "stopped until it is cleared.", ""]
    if unr:
        L += [f"- **{len(unr)} record entr{'y' if len(unr) == 1 else 'ies'} drafted and "
              f"not ratified.** Read, then delete the `_Unratified_` line:", ""]
        L += [f"  - `[{i}]` {h}" for i, h in unr]
        L.append("")
    # A proposed change to what the project ASSERTS about itself. The loop may raise one
    # and may never apply it — [T-099] is the first, and the reason it is a separate file
    # rather than a commit is that a charter edit should not arrive disguised as routine.
    prop = os.path.join(ROOT, "out", "RATIFY_PROPOSALS.md")
    if os.path.exists(prop):
        n = len(re.findall(r"^# ", open(prop, encoding="utf-8").read(), re.M))
        L += [f"- **{n} proposed amendment(s) to the project's own claims** — "
              f"`out/RATIFY_PROPOSALS.md`. The loop raised these and may not apply them. "
              f"Each says what measurement prompted it and what it changes downstream.", ""]

    # A drafted outward message is the one artifact the loop may produce but never act
    # on, so it is surfaced explicitly rather than left to be noticed in a commit.
    pkt = os.path.join(ROOT, "notes", "natalie-packet.md")
    if os.path.exists(pkt) and "Not sent, and not to be sent" in open(pkt, encoding="utf-8").read():
        L += ["- **A covering message is drafted and unsent** — `notes/natalie-packet.md`, "
              "the 2026-10-15 update. The loop may draft it and may not send it. Sending "
              "is your decision and nothing else will make it.", ""]
    if not os.path.exists(esc) and not unr:
        L += ["- Nothing else. Every entry has been ratified and no escalation is open.", ""]

    L += ["## State", "",
          f"- **{n_commits} commits** in the window",
          f"- **queue:** {', '.join(jobs) if jobs else 'EMPTY — the loop has no work and '
                                                      'will go to its generative phase'}",
          f"- **open tickets:** {', '.join(t[0] for t in tick) if tick else 'none'}",
          f"- **open threads:** {', '.join(t[0] for t in threads) if threads else 'none'}",
          ""]

    if threads:
        L += ["## Open questions", ""]
        L += [f"- **{i}** · {t}" for i, t in threads]
        L.append("")

    if commits:
        L += ["## Commits", "", "```", commits, "```", ""]

    L += ["---", "",
          "_The loop drafts; a person ratifies. See `LOOP.md` for what it may and may not "
          "do._"]

    text = "\n".join(L)
    if a.stdout:
        print(text)
    else:
        os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
        with open(os.path.join(ROOT, "out", "RATIFY.md"), "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"written out/RATIFY.md — {len(unr)} unratified, "
              f"{'escalation OPEN' if os.path.exists(esc) else 'no escalation'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
