# Lab 12 · Pod Crash on Timezone Mismatch

**Time:** ~30 min · **Needs:** Docker · **Cost:** free, all local

## The incident

The daily digest email must reach the New York sales team at **9:00 a.m. New
York time**. On the developer's laptop in New York, `scheduler.py` gets it right.
Since it moved into a container, the digest arrives at 5 a.m. in summer and 4 a.m.
in winter.

Someone already tried `-e TZ=America/New_York`. Nothing changed. A second attempt
using `zoneinfo` crashed the container on start. The image was recently moved
from `python:3.12-slim` to plain `alpine:3` "to save space".

`scheduler.py` prints the next send time as a UTC instant. `FAKE_NOW=<unix seconds>`
lets you pretend "now" is any moment, so you don't have to wait for 9 a.m.

## Setup

```bash
./setup.sh
docker run --rm opz-lab12-scheduler                              # next run, from the container
docker run --rm -e TZ=America/New_York opz-lab12-scheduler       # "the fix" that didn't work
TZ=America/New_York python3 app/scheduler.py                     # the laptop, where it works
```

Pick a moment: `FAKE_NOW=1792929600` is Sunday 25 Oct 2026, 08:00 in New York,
so the right answer is that same morning, `2026-10-25T13:00:00Z`.

## Your job

1. **Explain the difference first.** Same code, same moment: why does the laptop
   say 13:00Z and the container say something else? Hints, one at a time:
   - `datetime.fromtimestamp(t)` with no second argument gives a *naive* datetime
     in... whose timezone? Where does Python get that from?
   - Run `docker run --rm -e TZ=America/New_York opz-lab12-scheduler date` (any
     command works after the image name). Then `ls /usr/share/zoneinfo` the same
     way. Why is `TZ` being ignored?
2. **Fix it so the answer doesn't depend on the machine at all.** Hints:
   - "9 a.m." means nothing without saying *where*. The code should name New York
     itself, not inherit it from whoever runs it.
   - Do the arithmetic in that named zone, then convert to UTC. Keep "now" in UTC.
   - When the code names a zone and the container crashes, read the error. What
     does Python need to look a zone up, and what did the move to Alpine remove?
3. **Prove it.** `./check.sh` asks the container for the next run from four
   fixed moments, including both daylight-saving switches, under `TZ=UTC`,
   `America/New_York`, `Asia/Karachi` and `America/Los_Angeles`. It passes only
   when every one gives the same correct UTC instant. (Baking `ENV TZ=...` into
   the image doesn't count: the check overrides it.)
4. **Write the retro** (below). `./teardown.sh` removes the image.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why it worked on the laptop:
- Why `-e TZ=America/New_York` changed nothing in the container:
- Naive vs. aware datetimes, in one line each:
- The rule for where times live (storage, comparison, display):
- What the two daylight-saving test cases would have caught that the others don't:
