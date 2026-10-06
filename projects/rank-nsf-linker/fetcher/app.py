"""Fetcher: runs the data-fetch scripts for the pipeline (server/db.go, "Fetch ..." steps).

A small HTTP service on :8090, in its own container so the Go server image stays small:
    POST /run?group=<group>[&force=1]   start every source in the group that isn't fresh or running
    GET  /status?group=<group>          the group's sources and their state
The groups in FETCH_DAEMON_GROUPS (default "openalex") also run on their own, as a daemon: a source
is started whenever it is due, and one that stopped at a daily allowance resumes after the reset,
day after day, until it completes; the pipeline loads what has arrived.
Each source is one script (server/scripts/...). A source is skipped while its last complete run is
younger than its max age; a partial run (exit 75: a daily allowance spent) or a failed one runs
again next time. State and the last run's log are kept in data/fetch_state/<source>.json / .log,
so they survive restarts. A source that fails keeps its previous output: the scripts only
replace files when they finish.
Standard library only.
"""

import hashlib
import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(os.environ.get("APP_ROOT", "/app"))
SCRIPTS = ROOT / "server" / "scripts"
STATE = ROOT / "data" / "fetch_state"
PARTIAL = 75
DAY = 86400

# name: (group, script relative to server/scripts, arguments, max age in days, time limit in hours)
SOURCES = {
    # grants and other sources the load steps read
    "nih": ("base", "grants/nih.py", [], 7, 12),
    "ukri": ("base", "grants/ukri.py", [], 14, 6),
    "kaken": ("base", "grants/kaken.py", [], 30, 12),
    "arc": ("base", "grants/arc.py", [], 30, 2),
    "anr": ("base", "grants/anr.py", [], 30, 2),
    "snsf": ("base", "grants/snsf.py", [], 30, 2),
    "erc": ("base", "grants/erc.py", [], 30, 2),
    "marsden": ("base", "grants/marsden.py", [], 30, 1),
    "rgc": ("base", "grants/rgc.py", [], 30, 12),
    "nserc": ("base", "grants/nserc.py", [], 30, 2),
    "nwo": ("base", "grants/nwo.py", [], 14, 4),
    "fwf": ("base", "grants/fwf.py", [], 30, 1),
    "nrf": ("base", "grants/nrf_kr.py", [], 30, 1),
    "daad": ("base", "scholarships/daad.py", [], 7, 1),
    "dblp": ("base", "dblp/fetch.py", [], 30, 3),
    "openalex-awards": ("base", "grants/openalex_awards.py", [], 30, 6),  # national funders, from the CC0 snapshot
    # OpenAlex: inputs exported by the pipeline after the explorer tables are built
    "openalex-works": ("openalex", "openalex/works.py", ["--max-calls", "4000"], 14, 8),
    "openalex-fields": ("openalex", "openalex/fields.py", ["works", "--max-calls", "5000"], 30, 8),
}

# Files a source reads (relative to the app root): when they change, the source is due again however
# fresh its last run (more universities to find researchers at, more DOIs to look up).
INPUTS = {
    "openalex-works": ["data/openalex/dois.txt"],
    "openalex-fields": ["data/openalex/universities.csv", "backup/extra_universities.csv",
                        "backup/openalex_institutions.csv"],
}

lock = threading.Lock()
running: dict[str, threading.Thread] = {}  # started, whether waiting for a slot or running
# A few sources at a time: all at once ran the container out of memory (KAKEN was killed).
slots = threading.Semaphore(int(os.environ.get("FETCH_CONCURRENCY", "3")))


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(name: str) -> dict:
    path = STATE / f"{name}.json"
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {"name": name, "status": "never run"}


def save(name: str, state: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = STATE / f"{name}.json.tmp"
    tmp.write_text(json.dumps(state, indent=1))
    tmp.replace(STATE / f"{name}.json")


def inputs_hash(name: str) -> str:
    h = hashlib.sha1()
    for rel in INPUTS.get(name, []):
        try:
            h.update((ROOT / rel).read_bytes())
        except OSError:
            h.update(b"-")
    return h.hexdigest()


def is_fresh(name: str) -> bool:
    state = load(name)
    max_age = SOURCES[name][3]
    if name in INPUTS and state.get("inputs") != inputs_hash(name):
        return False
    return state.get("status") == "ok" and time.time() - state.get("finished_ts", 0) < max_age * DAY


def capped(args: list[str]) -> list[str]:
    """FETCH_MAX_CALLS lowers every --max-calls (a second stack sharing the API key: the fresh-server
    test), never raises it."""
    cap = os.environ.get("FETCH_MAX_CALLS", "").strip()
    if not cap.isdigit() or "--max-calls" not in args:
        return args
    i = args.index("--max-calls") + 1
    return [*args[:i], str(min(int(args[i]), int(cap))), *args[i + 1:]]


def run(name: str) -> None:
    group, script, args, _max_age, hours = SOURCES[name]
    args = capped(args)
    state = load(name)
    state.update(name=name, group=group, status="queued")
    save(name, state)
    with slots:
        _run(name, group, script, args, hours, state)
    with lock:
        running.pop(name, None)


def _run(name: str, group: str, script: str, args: list[str], hours: float, state: dict) -> None:
    state.update(status="running", started=now(), started_ts=time.time(), inputs=inputs_hash(name))
    save(name, state)
    log = STATE / f"{name}.log"
    code: int | str
    try:
        with log.open("w") as out:
            proc = subprocess.run(["python3", "-u", str(SCRIPTS / script), *args], cwd=(SCRIPTS / script).parent,
                                  stdout=out, stderr=subprocess.STDOUT, timeout=hours * 3600)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = "timeout"
    tail = log.read_text(errors="replace").splitlines()[-5:] if log.exists() else []
    status = "ok" if code == 0 else "partial" if code == PARTIAL else "failed"
    state.update(status=status, exit=code, finished=now(), finished_ts=time.time(), log_tail=tail)
    if status == "ok":
        state["last_ok"] = state["finished"]
    save(name, state)


def start_one(name: str) -> None:
    """Start a source unless it is already running (call with lock held)."""
    if name in running:
        return
    t = threading.Thread(target=run, args=(name,), daemon=True)
    running[name] = t
    t.start()


def start(group: str, force: bool) -> None:
    with lock:
        for name, (g, *_rest) in SOURCES.items():
            if g == group and (force or not is_fresh(name)):
                start_one(name)


def due(name: str, now: float) -> bool:
    """For the daemon: a source to start now. Not when fresh; not when it stopped at a daily allowance
    today (it resumes after the reset at 00:00 UTC, with ten minutes' grace); not within six hours of
    a failure (a broken source shouldn't run every few minutes)."""
    if is_fresh(name):
        return False
    state = load(name)
    midnight = now - now % DAY
    if state.get("status") == "partial" and (state.get("finished_ts", 0) >= midnight or now < midnight + 600):
        return False
    if state.get("status") == "failed" and now - state.get("finished_ts", 0) < 6 * 3600:
        return False
    return True


def daemon(groups: list[str]) -> None:
    """Keeps long fetches going on their own: OpenAlex's spans several daily allowances, so instead of
    waiting on a pipeline run it resumes every day; the pipeline loads whatever has arrived
    (server/fetch.go). Checks every ten minutes."""
    while True:
        with lock:
            for name, (g, *_rest) in SOURCES.items():
                if g in groups and name not in running and due(name, time.time()):
                    print(f"{now()} daemon: starting {name}", flush=True)
                    start_one(name)
        time.sleep(600)


def status(group: str) -> dict:
    with lock:
        busy = set(running)
    out = {}
    for name, (g, *_rest) in SOURCES.items():
        if g != group:
            continue
        s = load(name)
        if s.get("status") in ("running", "queued") and name not in busy:
            s["status"] = "interrupted"  # the container restarted mid-run; it runs again next time
        s["fresh"] = is_fresh(name)
        out[name] = s
    return {"group": group, "running": sorted(n for n in busy if SOURCES[n][0] == group), "sources": out}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        q = parse_qs(url.query)
        if url.path == "/health":
            return self._send(200, {"ok": True})
        if url.path == "/status":
            return self._send(200, status(q.get("group", ["base"])[0]))
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        url = urlparse(self.path)
        q = parse_qs(url.query)
        if url.path == "/run":
            group = q.get("group", ["base"])[0]
            if not any(g == group for g, *_ in SOURCES.values()):
                return self._send(400, {"error": f"unknown group {group}"})
            start(group, q.get("force", ["0"])[0] == "1")
            return self._send(202, status(group))
        self._send(404, {"error": "not found"})

    def log_message(self, fmt: str, *args) -> None:  # one quiet line per request
        print(f"{now()} {self.command} {self.path}", flush=True)


if __name__ == "__main__":
    STATE.mkdir(parents=True, exist_ok=True)
    groups = [g for g in os.environ.get("FETCH_DAEMON_GROUPS", "openalex").split(",") if g]
    if groups:
        threading.Thread(target=daemon, args=(groups,), daemon=True).start()
    print(f"fetcher on :8090, {len(SOURCES)} sources; daemon for: {', '.join(groups) or 'none'}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
