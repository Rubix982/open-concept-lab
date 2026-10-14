"""The overnight loop: preflight, run, triage, report, next. Escalate on surprise only.

    python3 tools/watch.py                 # work the queue once, then stop
    python3 tools/watch.py --loop          # keep going; re-read the queue after each job
    python3 tools/watch.py --dry           # show what it would do

Ported from a private production pipeline of mine/batch.py. What this loop owns, and what it does
not, is the whole design:

  it owns     running pre-registered work, gating it, recovering it, reporting it, and
              deciding when to wake a person
  it does NOT choose what to run next, judge whether a result is real, write a record
              entry, close a ticket, or touch the write-up

[T-065] found that every narrowing in this project came from choosing WHICH held-fixed
dimension to vary — judgement, and the step that has reliably produced the results. And
[E-025], [E-026] and [R-012] each cost a withdrawn claim to interpreting a result too
eagerly. A loop that did either would manufacture that failure faster than a person can
catch it, and would do so while producing a large, internally consistent body of work
nobody has read — which the write-up already names as this project's real risk.

So the loop drafts. A person ratifies.

ESCALATION — the loop stops and writes out/reports/ESCALATION.md when:
  * preflight refuses                   (the code is wrong; running wastes a night)
  * triage reports an UNSORTED line     (a failure class nobody has diagnosed)
  * the verdict is not in `expect`      (the result is a surprise; surprises are the point)
  * a job exceeds its wall-clock budget (the [E-033] hang: 144h in RECEIVED, no exception)
Anything else is logged and the queue continues.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = os.path.join(ROOT, ".venv/bin/python")
QUEUE = os.path.join(ROOT, "tools/queue.json")
OUT = os.path.join(ROOT, "out", "reports")
#: A job that outlives this is the [E-033] shape — alive, no exception, no progress.
DEFAULT_BUDGET_H = 6.0


def log(msg: str) -> None:
    print(f"[{dt.datetime.now():%H:%M:%S}] {msg}", flush=True)


def escalate(job: dict, why: str, detail: str) -> None:
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "ESCALATION.md")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"\n## {dt.datetime.now():%Y-%m-%d %H:%M} · {job.get('ticket', '?')} · {why}\n\n"
                 f"{detail}\n\n"
                 f"Queue stopped. Nothing after this job was run.\n")
    log(f"ESCALATED — {why}. Written to {os.path.relpath(path, ROOT)}")


def run_job(job: dict, dry: bool) -> tuple[bool, str]:
    tid = job.get("ticket", "?")
    runner = os.path.join(ROOT, job["runner"])
    args = [str(x) for x in job.get("args", [])]
    budget = float(job.get("budget_h", DEFAULT_BUDGET_H))

    log(f"{tid}: preflight")
    pre = [PY, os.path.join(ROOT, "tools/preflight.py"), runner,
           "--model", job.get("model", "meta-llama/Llama-3.1-8B")]
    if dry:
        log(f"  would run: {' '.join(pre)}")
        log(f"  would run: {PY} {runner} {' '.join(args)}")
        return True, "dry"
    r = subprocess.run(pre, capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"**preflight refused.**\n\n```\n{r.stdout[-1200:]}\n```"

    log(f"{tid}: running (budget {budget}h)")
    t0 = time.time()
    try:
        rr = subprocess.run([PY, runner, *args], timeout=budget * 3600,
                            capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return False, (f"**exceeded its {budget}h budget.** This is the [E-033] shape — a "
                       f"job alive with no exception and no progress. Check whether NDIF "
                       f"is holding it in RECEIVED.")
    mins = (time.time() - t0) / 60
    log(f"{tid}: finished in {mins:.0f} min")

    # The runner's stderr is the ONLY place an uncaught traceback goes — `logs.setup`
    # writes the run log, not the crash. It was captured and discarded until [E-038] died
    # at 1300 of 2578 entries and this loop reported "ok": the traceback had been read
    # into a variable nobody looked at, so the cause is permanently unknowable for that
    # run. Persist it before deciding anything.
    if rr.stderr or rr.stdout:
        crash = os.path.join(ROOT, "logs", f"{tid.lower()}-stderr.log")
        with open(crash, "w", encoding="utf-8") as fh:
            fh.write(f"=== returncode {rr.returncode} ===\n--- stderr ---\n{rr.stderr}"
                     f"\n--- stdout ---\n{rr.stdout}")

    # And the return code was never checked. Preflight's was; the experiment's was not,
    # so a crash, a kill and a clean exit were indistinguishable to this loop.
    if rr.returncode != 0:
        return False, (f"**the runner exited {rr.returncode}.** It did not finish, and "
                       f"this loop previously reported such a run as ok. Its stderr is in "
                       f"`logs/{tid.lower()}-stderr.log`.\n\n```\n"
                       f"{(rr.stderr or '(empty)')[-1200:]}\n```")

    # The log glob comes from the RUNNER's basename, not the ticket id. They coincide
    # only when a ticket has its own runner — [E-038] reuses `run_e037.py` with different
    # arguments, so `run_e038*.log` matched nothing, the verdict scan had no files to read,
    # and `expect` was checked against an empty list. Triage got the right file only by
    # accident: called with no paths it falls back to the newest log, which happened to be
    # the right one. Two consumers, one silently correct for the wrong reason.
    stem = os.path.basename(runner).replace(".py", "")
    logs = sorted(__import__("glob").glob(
        os.path.join(ROOT, "logs", f"{stem}*.log")), key=os.path.getmtime)[-2:]
    if not logs:
        return False, (f"**no log file found for `{stem}`.** The runner wrote nothing this "
                       f"loop can read, so neither triage nor the verdict check ran. "
                       f"Nothing about this run has been verified.")
    tri = subprocess.run([PY, os.path.join(ROOT, "tools/triage.py"), "--json", *logs],
                         capture_output=True, text=True)
    unsorted_n, unsorted_lines = 0, []
    if tri.returncode == 0 and tri.stdout.strip():
        t = json.loads(tri.stdout)
        unsorted_n = t.get("counts", {}).get("UNSORTED", 0)
        unsorted_lines = [ln for _, ln in (t.get("unsorted") or [])[:5]]

    subprocess.run([PY, os.path.join(ROOT, "tools/report.py"), tid],
                   capture_output=True, text=True)

    if unsorted_n:
        return False, (f"**{unsorted_n} unsorted log line(s)** — a failure class not yet "
                       f"diagnosed.\n\n```\n" + "\n".join(unsorted_lines) + "\n```\n\n"
                       "Add a cause to `tools/triage.py` once you know what it is.")

    # Both verdict forms. The regex matched `VERDICT: X` only, while [E-037] onward
    # report two arms and write `ARM A · X` — so `verdicts` came back empty for every
    # such run, `expect` had nothing to compare against, and the escalate-on-surprise
    # rule was silently inert. This is the SAME divergence that broke `triage.py` this
    # morning; that consumer was fixed and this one was not, which is the actual lesson:
    # a verdict string with two consumers needs one definition, not two regexes.
    verdicts = []
    for lg in logs:
        with open(lg, encoding="utf-8", errors="replace") as fh:
            verdicts += re.findall(r"(?:VERDICT:|ARM [A-Z] ·) ([A-Z][A-Z _-]*)", fh.read())
    verdicts = [v.strip() for v in verdicts if v.strip()]
    if not verdicts:
        return False, ("**the run produced no verdict line.** Every runner here ends with "
                       "one, so its absence means the run did not reach its report — or "
                       "that the verdict format has drifted from what this loop matches. "
                       "Either way `expect` had nothing to check and the surprise rule "
                       "was inert.")
    expect = {v.upper() for v in job.get("expect", [])}
    surprises = [v.strip() for v in verdicts if expect and v.strip().upper() not in expect]
    if surprises:
        return False, (f"**verdict not in `expect`.** Got {sorted(set(surprises))}, "
                       f"expected one of {sorted(expect)}.\n\nThis is a surprise, and "
                       f"surprises are the reason to run anything. Read "
                       f"`out/reports/{tid}.html`, then write the entry yourself — the "
                       f"loop does not interpret results.")
    log(f"{tid}: ok — verdict {verdicts or ['(none)']}, report written")
    return True, ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    while True:
        with open(QUEUE, encoding="utf-8") as fh:
            jobs = json.load(fh).get("jobs", [])
        todo = [j for j in jobs if not j.get("done")]
        if not todo:
            log("queue empty — nothing pre-registered to run")
            return 0
        log(f"{len(todo)} job(s) queued")
        for job in todo:
            ok, detail = run_job(job, a.dry)
            if not ok and detail != "dry":
                escalate(job, detail.split(".")[0].strip("*"), detail)
                return 2
        if not a.loop:
            return 0
        log("queue worked; sleeping 15 min before re-reading it")
        time.sleep(900)


if __name__ == "__main__":
    raise SystemExit(main())
