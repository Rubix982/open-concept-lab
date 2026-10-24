# Lab 14 · Post-Deployment Failure Due to Missing Migration

**Time:** ~45 min · **Needs:** Docker Compose (Postgres runs in a container) · **Cost:** free, all local

## The incident

The users service is on v1. v2 shows each user's local time, so it reads a new
`users.timezone` column. Migration `002_add_timezone.up.sql` that adds the column
was written and merged with the code.

Friday's deploy of v2 returned a 500 on every request. Someone rolled back to v1,
then ran the migration by hand "to be ready for next time", and now **v1** started
failing too. Two outages from one column.

## Setup

```bash
./setup.sh                          # Postgres with migration 001, the v1 app on localhost:8014
curl -s localhost:8014/users/1
python3 tools/traffic.py            # terminal 2: steady GET/POST traffic; Ctrl-C prints a summary
```

The pieces:
- `deploy.sh v2` / `deploy.sh v1` is the deploy pipeline (and the rollback).
- `docker compose run --rm migrate` applies any migrations not yet applied.
  `docker compose run --rm migrate 001` stops after 001.
- `docker compose exec db psql -U shop -c '\d users'` shows the table.

## Your job

1. **Break it first.** With traffic running, `./deploy.sh v2`. Watch the 5xx lines.
   Then try the "fix it by hand" route: run the migration, and roll back with
   `./deploy.sh v1`. What happens to v1 now? (`./setup.sh` resets everything.)
2. **Fix the pipeline and the migration** so that deploying v2 and rolling back to
   v1 both work, with no failed requests during either. Hints, one at a time:
   - Who runs migrations today? What should run them, and **when**: before the new
     code starts or after?
   - While a migration runs, the *old* code is still serving. Read v1's INSERT.
     Does it still work after migration 002?
   - After a rollback, the schema stays migrated. Rolling the schema back too is
     risky (it can drop data). So the old code has to work on the new schema.
   - What does Postgres put in a new `NOT NULL` column for rows that already exist,
     and for rows inserted by code that doesn't mention it?
   - You can change `deploy.sh` and `migrations/002_add_timezone.up.sql`.
     Leave the app code alone: v1 is what's in production, and v2 is correct.
3. **Prove it.** `./check.sh` builds a separate copy on v1 (port 18014), then runs
   **your** `deploy.sh` to v2 and back to v1, both under steady traffic. It passes
   only when each deploy lands and nothing gets a 5xx. It takes about 40 seconds.
4. **Write the retro** (below).
5. **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why v2 failed on Friday:
- Why the hand-run migration then broke v1:
- Migrate before or after the new code, and why:
- What makes a migration "backward compatible":
- Expand, then deploy, then contract — what would the "contract" step be here, and when is it safe?
