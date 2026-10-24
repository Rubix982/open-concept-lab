"""Steady user traffic: alternates GET /users/1 and POST /users until stopped
(Ctrl-C or SIGTERM), then prints a one-line summary.

    python3 tools/traffic.py                 # against localhost:8014
    python3 tools/traffic.py http://127.0.0.1:18014
"""

import json
import signal
import sys
import time
import urllib.error
import urllib.request
from collections import Counter

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8014"
signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))

counts: Counter[str] = Counter()
last_error = ""


def call(method: str, path: str, body: dict | None = None) -> None:
    global last_error
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            counts[f"{resp.status // 100}xx"] += 1
    except urllib.error.HTTPError as e:
        counts[f"{e.code // 100}xx"] += 1
        if e.code >= 500:
            last_error = f"{method} {path}: {e.read().decode()[:160]}"
            print(f"5xx  {last_error}", flush=True)
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        counts["unreachable"] += 1  # container being swapped; not this lab's problem


try:
    n = 0
    while True:
        if n % 2:
            call("POST", "/users", {"name": f"load{n}", "email": f"load{n}@example.com"})
        else:
            call("GET", "/users/1")
        n += 1
        time.sleep(0.05)
except KeyboardInterrupt:
    pass
print(json.dumps({"ok": counts["2xx"], "server_errors": counts["5xx"],
                  "unreachable": counts["unreachable"], "last_error": last_error}))
