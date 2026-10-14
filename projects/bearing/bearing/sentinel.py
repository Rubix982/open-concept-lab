"""Watch one or more projects for a long time, and report only what CHANGED.

    python -m bearing --sentinel ~/code/open-concept-lab/ai/edit-slice <private-project>
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
    """One sweep. Returns the lines worth a person's attention, which may be none.

    It also refreshes a STANDING snapshot — what is uncomfortable right now, per project,
    with the age of each. The change log alone answers "what moved"; it cannot answer
    "where do things stand", and someone checking twice a day needs both. Keeping them
    separate is what stops the standing summary from becoming the repetition that trains
    skimming.
    """
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
        standing = [{"q": c["q"], "say": c["say"][:150],
                     "since": prev.get(c["q"], {}).get("since")}
                    for c in run_all(rec) if c["bad"]]
        state.setdefault("_standing", {})[rec.name] = {
            "at": datetime.now().isoformat(timespec="minutes"), "bad": standing}
        if changes:
            lines.append(f"\n### {rec.name}")
            lines += changes
    if lines and want_notify:
        head = next((x.strip() for x in lines if x.strip().startswith("NEW")), None)
        notify("bearing", head or "something changed in a watched project")
    return lines


def append_heartbeat(state: dict) -> None:
    n = sum(len(v.get("bad", [])) for v in state.get("_standing", {}).values())
    with open(DIGEST, "a", encoding="utf-8") as fh:
        fh.write(f"- {datetime.now():%Y-%m-%d %H:%M} · no change · "
                 f"{n} standing\n")


def append_digest(lines: list[str]) -> None:
    with open(DIGEST, "a", encoding="utf-8") as fh:
        fh.write(f"\n## {datetime.now():%Y-%m-%d %H:%M}\n" + "\n".join(lines) + "\n")


def read_digest(n: int = 50) -> str:
    """Two parts, because they answer different questions.

    AS OF NOW  where things stand, with ages — the question someone returning after a
               day actually has
    WHAT MOVED the change log — the question the alarms answer

    The standing section is regenerated from state rather than replayed from the log, so
    it is current even if every sweep since has been quiet.
    """
    out: list[str] = []
    standing = _load_state().get("_standing", {})
    if standing:
        out.append("AS OF NOW")
        out.append("=" * 60)
        today = date.today()
        for proj, info in sorted(standing.items()):
            bad = info.get("bad", [])
            out.append(f"\n{proj}  ({len(bad)} uncomfortable · swept {info.get('at','?')})")
            for b in bad:
                age = ""
                if b.get("since"):
                    try:
                        d = (today - date.fromisoformat(b["since"])).days
                        age = f"  [{d}d]" if d else "  [today]"
                    except ValueError:
                        pass
                out.append(f"  !{age} {b['q']}")
                out.append(f"       {b['say']}")
            if not bad:
                out.append("  nothing")
        out.append("")

    try:
        with open(DIGEST, encoding="utf-8") as fh:
            body = [x for x in fh.read().strip().split("\n") if x.strip()]
    except OSError:
        return "\n".join(out) or (
            "Nothing yet. Start it with:\n"
            "    python -m bearing --sentinel <project> [<project>...] --interval 2h")
    out.append("WHAT MOVED  (newest last)")
    out.append("=" * 60)
    out += body[-n:]
    return "\n".join(out)


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
            # A quiet sweep still leaves a mark. Without it, a gap in the digest is
            # ambiguous between "nothing happened" and "the sentinel was dead", and
            # those need opposite responses.
            append_heartbeat(state)
            print(f"{stamp} no change", flush=True)
        if once:
            return 0
        time.sleep(interval_s)
