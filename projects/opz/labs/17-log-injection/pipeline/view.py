"""What the on-call engineer sees: central events, one per line, in a terminal.

    python3 pipeline/view.py                 # everything
    python3 pipeline/view.py login           # events whose message contains "login"
"""

import json
import os
import sys
from pathlib import Path

LOG_DIR = Path(os.environ.get("LOG_DIR", Path(__file__).resolve().parent.parent / "logs"))


def show(value: object) -> str:
    return str(value)


def main() -> None:
    needle = sys.argv[1] if len(sys.argv) > 1 else ""
    path = LOG_DIR / "central.jsonl"
    if not path.exists():
        sys.exit("nothing shipped yet: run python3 pipeline/ship.py")
    for line in path.read_text(encoding="utf-8").splitlines():
        event = json.loads(line)
        msg = event.get("msg", "")
        if needle in msg:
            extras = " ".join(f"{k}={show(v)}" for k, v in event.items() if k not in ("time", "level", "msg"))
            print(f"{event.get('time', '?')}  {event.get('level', '?'):8} {show(msg)}  {extras}")


if __name__ == "__main__":
    main()
