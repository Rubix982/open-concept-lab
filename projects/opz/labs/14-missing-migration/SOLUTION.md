# Lab 14 · Solution (spoilers)

## What was wrong

Two separate mistakes, and each one caused one outage.

1. **Nothing ran the migration.** `deploy.sh` started v2 against a schema that
   didn't have `timezone` yet, so every query that mentioned it failed.
2. **The migration broke the old code.** `ADD COLUMN timezone text NOT NULL`
   with no default:
   - fails outright on a table that already has rows, because existing rows would
     hold NULL;
   - if you "fix" that by adding the column, backfilling and then setting NOT NULL,
     v1's `INSERT INTO users (name, email)` now violates the constraint. Every
     signup fails on v1, both while the migration runs and after any rollback.

## The fix

**The pipeline runs migrations first, then swaps the code** (`deploy.sh`):

```bash
docker compose run --rm migrate          # schema first...
APP_VERSION="$VERSION" docker compose up -d --wait app   # ...then code
```

`set -e` matters here: if the migration fails, the deploy stops and v1 keeps
running on an unchanged schema. That's a non-event instead of an outage.

**The migration is additive and old-code-safe** (`002_add_timezone.up.sql`):

```sql
ALTER TABLE users ADD COLUMN timezone text NOT NULL DEFAULT 'UTC';
```

The default fills existing rows and any row v1 inserts without mentioning the
column. Since Postgres 11 this doesn't rewrite the table, so it's instant even on
a big one.

## Expand → deploy → contract

The general pattern for schema changes with zero downtime:

1. **Expand:** add things (columns with defaults, new tables, new indexes) so old
   and new code both work. Run it before the deploy.
2. **Deploy** the new code. Rollback is now just "deploy the old code"; the schema
   needs no change.
3. **Contract**, in a *later* release, once you're sure you won't roll back past
   it: remove what the old code needed. Here that might be dropping the default.
   A rename is the classic hard case: add the new column, write both, backfill,
   switch reads, stop writing the old one, then drop it. That's several releases
   for one rename.

## Details worth knowing

- **Down migrations are rarely the rollback plan.** `002_add_timezone.down.sql`
  exists, but running it after v2 has been live throws away every timezone users
  set. Roll back code, not schema.
- **Locks.** Some `ALTER TABLE`s take a lock that blocks all reads and writes
  while they run: adding a column with a *volatile* default, changing a column's
  type, or `CREATE INDEX` without `CONCURRENTLY`. On a big table that's an outage
  even when the SQL is "correct". Use `SET lock_timeout` in migrations so they fail
  fast instead of queueing behind a long query and blocking everyone behind them.
- **Several replicas, one migration.** With many app instances, don't let each
  one migrate on startup; they race. Run it once, as a pipeline step or a
  Kubernetes Job or init step that only one instance runs.
- **What this doesn't cover:** the few seconds while Compose swaps the container,
  when connections are refused. `tools/traffic.py` counts those as "unreachable",
  not as failures. Closing that gap needs two instances behind a load balancer
  with a rolling deploy, plus lab 07's graceful shutdown.
