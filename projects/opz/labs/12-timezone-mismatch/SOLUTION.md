# Lab 12 · Solution (spoilers)

## What was wrong

Two problems, stacked:

1. **The code never says "New York".** `datetime.fromtimestamp(t)` returns a
   *naive* datetime in the **process's local timezone**. On the laptop that's New
   York, so "9 a.m. local" happens to mean the right thing. In a container, local
   is UTC, so the digest goes out at 09:00 UTC, which is 5 a.m. in New York (4 a.m.
   in winter).
2. **The image has no timezone database.** Plain Alpine doesn't ship
   `/usr/share/zoneinfo`. Without it, the C library can't resolve
   `TZ=America/New_York`, so it silently falls back to UTC. That's why setting `TZ`
   changed nothing. It's also why `ZoneInfo("America/New_York")` crashes with
   `ZoneInfoNotFoundError`: Python looks in the same place.

`python:3.12-slim` happened to include `tzdata`. Moving to `alpine:3` took it away,
and nobody noticed, because the code never asked for a zone by name.

## The fix

Name the zone in code, keep "now" in UTC, and convert only at the edges:

```python
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SEND_HOUR = 9
BUSINESS_TZ = ZoneInfo("America/New_York")


def now() -> datetime:
    return datetime.fromtimestamp(float(os.environ.get("FAKE_NOW", time.time())), timezone.utc)


def next_run(current: datetime) -> datetime:
    local = current.astimezone(BUSINESS_TZ)
    target = datetime.combine(local.date(), datetime.min.time().replace(hour=SEND_HOUR), BUSINESS_TZ)
    if target <= local:
        target = datetime.combine(local.date() + timedelta(days=1), target.timetz())
    return target.astimezone(timezone.utc)
```

And give the image the database:

```dockerfile
RUN apk add --no-cache python3 tzdata
```

(Or `pip install tzdata`: Python's `zoneinfo` falls back to that package when the
system has none. That travels with the app instead of the image.)

## Why the half-fixes fail

- **`ENV TZ=America/New_York` in the Dockerfile, plus tzdata:** it works until
  someone runs the container with a different `TZ`: a platform default, another
  team's base image, a Kubernetes cluster in another region. The check overrides
  `TZ` for this reason. The code's meaning shouldn't depend on an environment variable.
- **`ZoneInfo` without tzdata:** the right code with a missing file. It crashes on
  start, which is at least loud.

## Details worth knowing

- **The rule:** store and compare in UTC; convert to a *named* zone only to
  answer a human question ("9 a.m. in New York") or to display.
- **Never use fixed offsets like `-05:00` for a place.** New York is −5 in winter
  and −4 in summer. The DST test cases catch code that hard-codes one of them.
- **Adding `timedelta(days=1)` to a local time across a DST switch** is the classic
  next bug. Adding a day to an aware datetime keeps the wall-clock time, which is
  usually what a human schedule wants. Adding 24 hours of UTC doesn't.
- **What this doesn't cover:** times that don't exist (02:30 on the spring-forward
  night) or happen twice (01:30 in the fall). A job scheduled then needs a
  decision; look up `fold` in the `datetime` docs. And cron in a container runs
  in the container's local time, so `0 9 * * *` has the same bug as this code.
- **The tz database changes.** Countries change their DST rules with little
  notice, so an image built two years ago can be wrong today. That's another
  reason to rebuild base images regularly.
