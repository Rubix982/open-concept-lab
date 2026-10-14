"""The re-entry brief: what changed, and the one thing that needs you.

    python -m bearing <project> --brief

Written for the case this project was actually built for — a person with an hour a week,
not a day. Twice in one session the author came back and asked "what happened in between?",
and both times the answer had to be reconstructed by hand from logs and commits.

**The scarce resource is not time at the laptop. It is context reload.** An hour that
starts with forty minutes of remembering where things were is twenty minutes of research.
This page exists to make that five, so the hour is spent deciding.

It is deliberately ordered to be read top-down and abandoned at any point:

    1  what needs you           decisions only a person can make, nothing else
    2  what moved               since you were last here
    3  what the record says     drift, from bearing's own checks
    4  what is waiting          queued, blocked, or priced-and-unrun

Nothing here interprets a result. A brief that told you what your findings meant would be
the thing the loop is forbidden from doing, wearing a friendlier format.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime

from .checks import run_all
from .record import Record


def _git(root: str, *args: str) -> str:
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root,
                             capture_output=True, text=True).stdout.strip() or root
        return subprocess.run(["git", *args], cwd=top,
                              capture_output=True, text=True).stdout
    except Exception:
        return ""


def since_last_visit(r: Record, since: str) -> list[str]:
    out = _git(r.root, "log", "--oneline", f"--since={since}", "--", r.root)
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def needs_you(r: Record, drift: list[dict]) -> list[tuple[str, str]]:
    """Decisions a person must make. Ordered by what goes stale fastest.

    A thread marked active is a question someone started and left; an uncomfortable drift
    check is a direction the record cannot correct on its own. Neither is a task — both
    are decisions, which is why they are the only things in section 1.
    """
    out: list[tuple[str, str]] = []
    for q in r.questions:
        if q.status.strip().lower().startswith("active"):
            out.append(("an active question, left open",
                        f"{q.id} · {q.title[:88]}"))
    for d in drift:
        if d["bad"]:
            out.append(("the record disagrees with itself", f"{d['q']} — {d['say'][:120]}"))
    blocked = [w for w in r.work if "blocked" in w.status.lower()]
    for b in blocked:
        out.append(("blocked work", f"{b.id} · {b.title[:88]}"))
    return out


def render(r: Record, since: str = "7.days") -> str:
    drift = run_all(r)
    commits = since_last_visit(r, since)
    mine = needs_you(r, drift)

    L: list[str] = []
    L.append(f"{r.name} — re-entry brief · {datetime.now():%Y-%m-%d %H:%M}")
    L.append("=" * 72)

    L.append("\n1 · NEEDS YOU")
    if not mine:
        L.append("    Nothing. No active question, no drift, nothing blocked.")
    else:
        L.append(f"    {len(mine)} thing(s). Everything below this section can wait.\n")
        for kind, what in mine[:6]:
            L.append(f"    · {what}")
            L.append(f"      ({kind})")
    L.append("")

    L.append(f"2 · WHAT MOVED  (last {since.replace('.', ' ')})")
    if not commits:
        L.append("    Nothing committed. If something was running, it did not finish.")
    else:
        L.append(f"    {len(commits)} commit(s):")
        for c in commits[:8]:
            L.append(f"      {c[:96]}")
        if len(commits) > 8:
            L.append(f"      … and {len(commits) - 8} more")
    L.append("")

    L.append("3 · WHAT THE RECORD SAYS")
    bad = [d for d in drift if d["bad"]]
    L.append(f"    {len(bad)} of {len(drift)} drift checks uncomfortable.")
    for d in bad:
        L.append(f"      ! {d['q']}")
        L.append(f"        {d['say'][:110]}")
    if not bad:
        L.append("      Every check passes. (bearing has no taste — see README.)")
    L.append("")

    L.append("4 · WHAT IS WAITING")
    openq = [q for q in r.questions if not q.done
             and not q.status.strip().lower().startswith("active")]
    openw = [w for w in r.work if not w.done]
    L.append(f"    {len(openq)} open question(s), {len(openw)} unfinished item(s).")
    for q in openq[:5]:
        L.append(f"      {q.id} · {q.title[:80]}")
    priced = next((d for d in drift if "priced" in d["q"].lower()), None)
    if priced and priced["bad"]:
        L.append(f"\n    priced and still unrun: {priced['say'][:130]}")
    L.append("")

    L.append("-" * 72)
    L.append("Nothing above interprets a result. Section 1 is the only part that is")
    L.append("yours; sections 2-4 are so you can trust that and stop reading.")
    return "\n".join(L)
