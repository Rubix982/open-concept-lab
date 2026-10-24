"""Daily digest scheduler.

The digest email must go out at 9:00 a.m. New York time, every day: that's when
the sales team in New York starts work. This prints when the next send is due.

    python scheduler.py              # next run, from the real clock
    FAKE_NOW=<unix seconds> python scheduler.py   # pretend "now" is that instant

Output is one line: the next run as a UTC timestamp, e.g. 2026-10-26T13:00:00Z.
The mailer process sleeps until that instant and then sends.
"""

import os
import time
from datetime import datetime, timedelta, timezone

SEND_HOUR = 9  # 9 a.m. New York


def now() -> datetime:
    return datetime.fromtimestamp(float(os.environ.get("FAKE_NOW", time.time())))


def next_run(current: datetime) -> datetime:
    target = current.replace(hour=SEND_HOUR, minute=0, second=0, microsecond=0)
    if target <= current:
        target += timedelta(days=1)
    return target


if __name__ == "__main__":
    run_at = next_run(now())
    print(datetime.fromtimestamp(run_at.timestamp(), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
