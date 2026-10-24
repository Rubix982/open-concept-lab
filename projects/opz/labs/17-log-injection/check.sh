#!/usr/bin/env bash
# Runs a fresh accounts service on a side port with its own log folder, signs up
# one honest user and two malicious usernames, ships the logs, and inspects the
# central store and the viewer. Passes only when each signup is exactly one event,
# each malicious username is kept whole and exact inside a field, no forged
# "login succeeded" event exists, and the viewer prints no raw control characters.
set -u
cd "$(dirname "$0")"
export LOG_DIR="$(mktemp -d)" ACCOUNTS_URL="http://127.0.0.1:18017"
fail=0

PORT=18017 python3 app/server.py >.check.log 2>&1 & srv=$!
trap 'kill $srv 2>/dev/null; wait $srv 2>/dev/null; rm -rf "$LOG_DIR"' EXIT
for _ in $(seq 1 30); do curl -s -o /dev/null "$ACCOUNTS_URL/" && break; sleep 0.2; done

python3 tools/attack.py honest >/dev/null
python3 tools/attack.py forge >/dev/null
python3 tools/attack.py hide >/dev/null
python3 pipeline/ship.py >/dev/null
python3 pipeline/view.py >"$LOG_DIR/view.out" 2>&1

python3 - "$LOG_DIR" <<'PY' || fail=1
import json, sys
from pathlib import Path
sys.path.insert(0, "tools")
from attack import payloads

d = Path(sys.argv[1])
events = [json.loads(l) for l in (d / "central.jsonl").read_text().splitlines()]
p = payloads()
ok = True

def strings(e):
    return [v for v in e.values() if isinstance(v, str)]

def report(good, text):
    global ok
    print(("pass  " if good else "FAIL  ") + text)
    ok &= good

report(len(events) == 4, f"4 events in the store: 2 honest + 1 per malicious signup (found {len(events)})")

maria = [e for e in events if "maria" in strings(e)]
report(len(maria) == 2, f"honest signup and login are 2 events with user field 'maria' (found {len(maria)})")

for name, prefix in (("forge", "eve"), ("hide", "dave")):
    touched = [e for e in events if any(prefix in v for v in strings(e)) or e.get("level") == "UNPARSED"]
    exact = [e for e in touched if p[name] in strings(e)]
    report(len(touched) == 1 and len(exact) == 1,
           f"'{name}' username: {len(touched)} event(s), {len(exact)} holding it exactly in one field (want 1 and 1)")

forged = [e for e in events if "admin" in strings(e) and "succeeded" in json.dumps(e)]
report(not forged, f"no forged 'login succeeded user=admin' event (found {len(forged)})")

raw = (d / "view.out").read_bytes()
report(b"\x1b" not in raw and b"\r" not in raw,
       "viewer prints control characters escaped, not raw" if b"\x1b" not in raw and b"\r" not in raw
       else "viewer prints raw control characters (ESC / carriage return) to the terminal")
sys.exit(0 if ok else 1)
PY

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
