# Lab 19 · Alert Not Fired Due to Misconfigured Label

**Time:** ~30 min · **Needs:** Docker Compose · **Cost:** free, all local

## The incident

The orders API was down for 40 minutes on Saturday. Prometheus was running the
whole time, and so was the `ApiDown` alert rule, which was reviewed and approved
in PR #212. Nobody got paged. A customer emailed support.

Prometheus didn't crash, and the rule didn't error out. It just never fired.

## Setup

```bash
./setup.sh                          # the API on :8019, Prometheus on :9019
open http://localhost:9019          # Alerts tab, Status > Targets, Graph
docker compose stop api             # simulate the outage
docker compose start api            # and recover
```

After editing anything in `prometheus/`, re-run `./setup.sh` so Prometheus reloads it.

## Your job

1. **Reproduce it.** Stop the API, wait a minute, and look at the Alerts tab.
   Then work out why it stays green. Hints, one at a time if you're stuck:
   - In the Graph tab, run the rule's expression exactly as written in
     `prometheus/rules.yml`. What comes back while the API is down? While it's up?
   - Now run just `up`. What labels does the API's series actually have?
   - Where does the `job` label come from? Look in `prometheus/prometheus.yml`.
   - What's the difference between "the query returned 0" and "the query returned nothing"?
2. **Fix it**, so the alert fires when the API goes down.
3. **Make the unit test pass.** `prometheus/tests/rules_test.yml` feeds the rule
   fake data and states what should fire. Its command is at the top of the file.
   It's labelled the way the scrape config labels things, so it fails right now.
   Ask yourself which side is wrong before editing either one.
4. **Prove it.** `./check.sh` runs the unit test, then stops the real API and waits
   up to 40 seconds for `ApiDown` to fire. Passing the unit test alone isn't enough.
5. **Write the retro** (below). `./teardown.sh` when done.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why the rule passed review:
- Why an empty result looks exactly like "everything is fine":
- What `promtool test rules` proves, and what it can't:
- One way to write the alert that would have caught this mistake itself:
- What else could silently empty a query like this (renames, relabels, a new exporter)?
