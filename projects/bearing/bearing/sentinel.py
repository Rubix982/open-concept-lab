"""Watch one or more projects for a long time, and report only what CHANGED.

    python -m bearing --sentinel ~/code/open-concept-lab/ai/edit-slice ~/code/janaan
    python -m bearing --sentinel <paths...> --interval 2h --notify
    python -m bearing --digest            # what it has seen, newest first

**Differential by design, and that is the whole reason it works.** A watcher that reports
its full state on every pass trains you to skim it, and a skimmed watcher is off. So the
sentinel stores the last answer to every check and reports three things:

    NEW      a check that was fine and is now uncomfortable      <- the only alarm
    GONE     a check that was uncomfortable and is now fine      <- worth knowing, briefly
    Nd       a check uncomfortable for N days, unchanged         <- nagging, see below

The third is the one people underestimate. A check bad for nine days is either not
important or is being avoided, and both are worth saying out loud. It is reported with its
age so the distinction is yours to make.

It has no taste — see README. It reports CHANGE, never importance, and a project can pass
every check while pointed somewhere that does not matter.

Crash-safe: state is written after every pass, so a restart resumes rather than re-alarming
on everything it already told you about.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import date, datetime

from .checks import run_all
from .record import load

STATE = os.path.expanduser("~/.bearing-sentinel.json")
DIGEST = os.path.expanduser("~/.bearing-digest.md")


def _load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _save_state(s: dict) -> None:
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=1)
    os.replace(tmp, STATE)        # atomic: a killed sentinel never leaves half a state


def notify(title: str, body: str) -> None:
    """A desktop notification, best-effort and never fatal. Off unless --notify."""
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification {json.dumps(body[:200])} '
                        f'with title {json.dumps(title[:60])}'],
                       capture_output=True, timeout=10)
    except Exception:
        pass


def pass_once(paths: list[str], state: dict, want_notify: bool) -> list[str]:
    """One sweep. Returns the lines worth a person's attention, which may be none."""
    today = date.today().isoformat()
    lines: list[str] = []
    for path in paths:
        try:
            rec = load(path)
        except Exception as exc:
            lines.append(f"  !! {os.path.basename(path)}: could not read — {exc}")
            continue
        if not rec.ok():
            continue
        prev = state.setdefault(rec.name, {})
        changes: list[str] = []
        for c in run_all(rec):
            q = c["q"]
            was = prev.get(q, {})
            first_bad = was.get("since")
            if c["bad"] and not was.get("bad"):
                changes.append(f"  NEW   {q}")
                changes.append(f"        {c['say'][:150]}")
                prev[q] = {"bad": True, "since": today}
            elif c["bad"]:
                days = (datetime.fromisoformat(today)
                        - datetime.fromisoformat(first_bad or today)).days
                if days >= 7:
                    changes.append(f"  {days}d    {q}  (unchanged — not important, "
                                   f"or being avoided?)")
                prev[q] = {"bad": True, "since": first_bad or today}
            elif was.get("bad"):
                changes.append(f"  GONE  {q}")
                prev[q] = {"bad": False, "since": None}
            else:
                prev[q] = {"bad": False, "since": None}
        if changes:
            lines.append(f"\n### {rec.name}")
            lines += changes
    if lines and want_notify:
        head = next((x.strip() for x in lines if x.strip().startswith("NEW")), None)
        notify("bearing", head or "something changed in a watched project")
    return lines


def append_digest(lines: list[str]) -> None:
    with open(DIGEST, "a", encoding="utf-8") as fh:
        fh.write(f"\n## {datetime.now():%Y-%m-%d %H:%M}\n" + "\n".join(lines) + "\n")


def read_digest(n: int = 60) -> str:
    try:
        with open(DIGEST, encoding="utf-8") as fh:
            body = fh.read().strip().split("\n")
    except OSError:
        return ("Nothing yet. Start it with:\n"
                "    python -m bearing --sentinel <project> [<project>...] --interval 2h")
    return "\n".join(body[-n:])


def run(paths: list[str], interval_s: float, want_notify: bool, once: bool) -> int:
    paths = [os.path.abspath(os.path.expanduser(p)) for p in paths]
    print(f"bearing sentinel · {len(paths)} project(s) · every "
          f"{interval_s / 3600:.1f}h · digest at {DIGEST}")
    print("  " + "\n  ".join(os.path.basename(p) for p in paths))
    print("\nReports only what CHANGED. Silence means nothing moved — which is\n"
          "information, and is why this can be left running.\n", flush=True)
    while True:
        state = _load_state()
        try:
            lines = pass_once(paths, state, want_notify)
        except Exception as exc:                       # a sweep must never kill the loop
            lines = [f"  !! sentinel error, continuing: {type(exc).__name__}: {exc}"]
        _save_state(state)
        stamp = f"[{datetime.now():%Y-%m-%d %H:%M}]"
        if lines:
            append_digest(lines)
            print(stamp + "\n" + "\n".join(lines) + "\n", flush=True)
        else:
            print(f"{stamp} no change", flush=True)
        if once:
            return 0
        time.sleep(interval_s)
