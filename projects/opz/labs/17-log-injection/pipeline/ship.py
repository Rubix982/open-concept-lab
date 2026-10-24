"""The log shipper: a small stand-in for Fluent Bit / Vector / Filebeat.

Reads logs/app.log one line at a time and turns each line into one event in
logs/central.jsonl, the store the security team searches. It understands two
line formats:

  - a JSON object per line:  {"time": ..., "level": ..., "msg": ..., <any other fields>}
  - plain text:              2026-10-25 03:12:44,120 INFO <message>

Like a real shipper with no multiline rule, it treats every line as its own
event. You shouldn't need to change this file.
"""

import json
import os
import re
from pathlib import Path

LOG_DIR = Path(os.environ.get("LOG_DIR", Path(__file__).resolve().parent.parent / "logs"))
PLAIN = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) (DEBUG|INFO|WARNING|ERROR|CRITICAL) (.*)$")
KV = re.compile(r"(\w+)=(\S+)")


def parse(line: str) -> dict:
    if line.startswith("{"):
        try:
            event = json.loads(line)
            if isinstance(event, dict):
                return event
        except json.JSONDecodeError:
            pass
    m = PLAIN.match(line)
    if not m:
        return {"level": "UNPARSED", "msg": line}
    time_, level, msg = m.groups()
    event = {"time": time_, "level": level, "msg": msg}
    event.update(dict(KV.findall(msg)))  # pull out user=..., ip=... for searching
    return event


def main() -> None:
    src, dst = LOG_DIR / "app.log", LOG_DIR / "central.jsonl"
    if not src.exists():
        print("no logs/app.log yet")
        return
    with src.open(encoding="utf-8", newline="") as f:
        # split on "\n" only. Python's splitlines() also splits on other characters
        # (\r, \x85, \u2028...), and real shippers don't agree with each other on that.
        lines = [ln for ln in f.read().split("\n") if ln.strip()]
    with dst.open("w", encoding="utf-8") as out:
        for line in lines:
            out.write(json.dumps(parse(line)) + "\n")
    print(f"shipped {len(lines)} events to {dst}")


if __name__ == "__main__":
    main()
