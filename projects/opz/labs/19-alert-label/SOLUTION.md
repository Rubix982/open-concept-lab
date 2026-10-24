# Lab 19 · Solution (spoilers)

## What was wrong

The rule selects `up{job="api"}`. The scrape config's `job_name` is `api-service`,
and Prometheus copies `job_name` into the `job` label of every series it scrapes.
So the only `up` series in the database is `up{job="api-service", instance="api:8019"}`.

`up{job="api"} == 0` matches **no series at all**. An alert rule fires once for
each series its expression returns. No series means no alert. That's true while
the API is up, and still true while it's down. Prometheus can't tell the
difference between "nothing is broken" and "this rule doesn't match anything".

## The fix

Make the rule select what's actually stored:

```yaml
        expr: up{job="api-service"} == 0
```

(Renaming `job_name` to `api` works too, but it renames the series behind every
dashboard and rule that already uses `api-service`. Fix the rule, not the data.)

## The tempting wrong fix

Editing the unit test's input series to `job="api"` makes `promtool` pass, but
the real alert still never fires. The test was right: it describes the data the
way the scrape config produces it. A unit test checks a rule against the data
*you wrote into the test*. It's only as good as that data's match with reality.
That's why `check.sh` also stops the real API.

## Details worth knowing

- **Alert on absence too.** `absent(up{job="api-service"})` fires when the series
  doesn't exist at all: a renamed job, a typo, or the target dropped from service
  discovery. Pairing it with the `== 0` rule covers "down" and "gone".
- **Check rules against live data.** Tools like `pint` (from Cloudflare) query
  Prometheus to confirm each rule's selectors match real series, and flag this
  exact bug in CI.
- **`for:` is a trade-off.** It stops a single failed scrape from paging anyone,
  but adds that much delay to every real alert.
- **What this doesn't cover:** Prometheus itself going down, or Alertmanager not
  delivering. The fix only works if the alerting pipeline is running. The
  deadman's-switch lab (an always-firing watchdog alert) covers that.
