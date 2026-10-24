"""Try the well-known default logins against a dashboard, like an attacker's
first minute would. Lists like this ship with every scanner.

    python3 tools/try_defaults.py                       # localhost:8013
    python3 tools/try_defaults.py http://127.0.0.1:18013
"""

import json
import sys
import urllib.error
import urllib.request

URL = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8013").rstrip("/") + "/login"
DEFAULTS = [
    ("admin", "admin"), ("admin", "password"), ("admin", "changeme"), ("admin", "admin123"),
    ("root", "root"), ("root", "toor"), ("administrator", "administrator"), ("user", "user"),
]


def try_login(user: str, password: str) -> int:
    req = urllib.request.Request(
        URL, method="POST", headers={"Content-Type": "application/json"},
        data=json.dumps({"username": user, "password": password}).encode(),
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


found = [(u, p) for u, p in DEFAULTS if try_login(u, p) == 200]
for u, p in found:
    print(f"OPEN  {u} / {p}")
print(f"tried {len(DEFAULTS)} default logins, {len(found)} worked")
sys.exit(1 if found else 0)
