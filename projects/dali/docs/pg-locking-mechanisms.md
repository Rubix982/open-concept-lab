# `pg_locks` sample outputs (realistic examples)

> Notes: `pg_locks` columns include `locktype, database, relation, page, tuple, virtualxid, transactionid, classid, objid, objsubid, virtualtransaction, pid, mode, granted, fastpath`. Use `pg_locks` together with `pg_stat_activity` for human-friendly context. ([PostgreSQL][1])

---

## Example A — Simple row-level locks (two transactions touching different rows)

Query to run:

```sql
-- show locks and the associated queries
SELECT l.pid, a.usename, a.query, l.locktype, l.relation::regclass AS relation,
       l.page, l.tuple, l.virtualtransaction, l.mode, l.granted
FROM pg_locks l
LEFT JOIN pg_stat_activity a ON l.pid = a.pid
WHERE l.locktype IN ('tuple','transactionid');
```

Simulated `pg_locks` output:

```
 pid  | usename |            query             | locktype |  relation  | page | tuple | virtualtransaction |           mode           | granted
------+---------+------------------------------+----------+------------+------+------+--------------------+--------------------------+---------
 4103 | app usr | UPDATE accounts SET ...      | tuple    | accounts   |  123 |    4 | 3/45               | RowExclusiveLock         | t
 4103 | app usr | UPDATE accounts SET ...      | transactionid |        |      |      |                    | ExclusiveLock            | t
 4238 | worker  | SELECT id FROM jobs ... FOR UPDATE SKIP LOCKED | tuple | jobs |  56  |   2 | 3/52 | RowExclusiveLock | t
```

Interpretation:

* `pid=4103` holds a row-level (`tuple`) and transactionid lock while performing an `UPDATE` on `accounts`. `mode = RowExclusiveLock` on tuples is common for updates.
* `pid=4238` shows a worker that locked a row in `jobs` (useful for job-queue patterns with `SKIP LOCKED`).
* `granted = t` means the lock is held; `f` would mean the session is waiting. See docs for what each `locktype`/`mode` means. ([PostgreSQL][1])

---

## Example B — Blocking scenario: one session waiting on a table-level lock

Reproduce scenario:

1. Session A:

   ```sql
   BEGIN;
   LOCK TABLE orders IN ACCESS EXCLUSIVE MODE;
   -- hold the lock (do not COMMIT)
   ```

2. Session B:

   ```sql
   -- tries to read/write the same table and will wait
   SELECT * FROM orders WHERE id=1 FOR UPDATE;
   ```

Query to inspect:

```sql
SELECT l.pid, a.query, l.locktype, l.relation::regclass AS relation, l.mode, l.granted
FROM pg_locks l
LEFT JOIN pg_stat_activity a ON l.pid = a.pid
WHERE l.relation IS NOT NULL
ORDER BY l.relation, l.granted;
```

Simulated `pg_locks` output:

```
 pid  |            query                  | locktype  | relation |           mode            | granted
------+-----------------------------------+-----------+----------+---------------------------+---------
 5010 | LOCK TABLE orders IN ACCESS...    | relation  | orders   | AccessExclusiveLock       | t
 5231 | SELECT * FROM orders ... FOR UPDATE | relation  | orders   | RowExclusiveLock          | f
 5231 | SELECT * FROM orders ... FOR UPDATE | tuple     | orders   | RowExclusiveLock          | f
```

Interpretation:

* `pid=5010` holds an `AccessExclusiveLock` on `orders` (blocks nearly all access) — typical from `LOCK TABLE ... ACCESS EXCLUSIVE`, `DROP TABLE`, `TRUNCATE`.
* `pid=5231` is waiting (`granted = f`) for the lock; you can identify blockers using `pg_blocking_pids()` or by joining `pg_locks` with `pg_stat_activity`. The docs recommend `pg_blocking_pids()` for easy identification. ([PostgreSQL][1])

---

## Example C — Advisory locks (application-level)

How to acquire:

```sql
-- session-level (survives transaction rollback)
SELECT pg_advisory_lock(1001);

-- transaction-scoped (released at COMMIT/ROLLBACK)
BEGIN;
SELECT pg_advisory_xact_lock(42);
-- ... work ...
COMMIT;
```

Inspect advisory locks:

```sql
SELECT pid, locktype, classid, objid, objsubid, virtualtransaction, mode, granted
FROM pg_locks
WHERE locktype = 'advisory';
```

Simulated `pg_locks` output:

```
 pid  | locktype  | classid | objid | objsubid | virtualtransaction |        mode        | granted
------+-----------+---------+-------+----------+--------------------+--------------------+---------
 6120 | advisory  |    0    |  1001 |    0     | 3/77               | ExclusiveLock      | t
 6125 | advisory  |    0    |  42   |    0     | 3/81               | ExclusiveLock      | t
```

Interpretation:

* Advisory locks appear in `pg_locks` with `locktype = 'advisory'`. They are application-managed and very useful for coarse-grained coordination without touching table rows. See the advisory-lock functions in the docs. ([PostgreSQL][2])

---

## Example D — Combined blocking tree (joined with `pg_stat_activity`)

Useful diagnostic query (community-common pattern):

```sql
WITH blocked AS (
  SELECT pid AS blocked_pid, relation
  FROM pg_locks WHERE NOT granted
),
blocking AS (
  SELECT pid AS blocking_pid, relation
  FROM pg_locks WHERE granted
)
SELECT b.blocked_pid, a_blocked.query AS blocked_query,
       br.blocking_pid, a_blocking.query AS blocking_query
FROM blocked b
JOIN blocking br ON b.relation = br.relation
LEFT JOIN pg_stat_activity a_blocked ON a_blocked.pid = b.blocked_pid
LEFT JOIN pg_stat_activity a_blocking ON a_blocking.pid = br.blocking_pid
ORDER BY b.blocked_pid;
```

This gives a readable mapping of who’s waiting and who’s blocking them. The PostgreSQL docs also suggest `pg_blocking_pids()` as an easier helper. ([PostgreSQL][1])

---

# Quick-run commands you’ll want in runbooks

* Show everything (raw):

```sql
SELECT * FROM pg_locks;
```

* Human-friendly locks + query text:

```sql
SELECT l.pid, a.usename, a.client_addr, a.query, l.locktype, l.mode, l.relation::regclass AS relation, l.page, l.tuple, l.granted
FROM pg_locks l
LEFT JOIN pg_stat_activity a ON l.pid = a.pid
ORDER BY l.relation, l.granted DESC;
```

* Identify blockers for a PID:

```sql
SELECT pg_blocking_pids(<target_pid>);
```

Then inspect `pg_stat_activity` rows returned to see queries. The docs recommend `pg_blocking_pids()` for identifying blocking process(es). ([PostgreSQL][1])

---

# Official PostgreSQL documentation (primary references)

* `pg_locks` system view — *Viewing locks (pg\_locks)*. Explains columns and recommended usage. ([PostgreSQL][1])
* `27.3 Viewing Locks` — monitoring locks and best practices (how to see outstanding locks). ([PostgreSQL][3])
* `13.3 Explicit Locking` — explains `FOR UPDATE`, `FOR SHARE`, advisory locks, and locking semantics. ([PostgreSQL][2])
* `LOCK` SQL command docs — `LOCK TABLE` modes and descriptions (AccessExclusive, Share, etc.). ([PostgreSQL][4])
* `pg_blocking_pids()` / system info functions — helper to find blocking processes. ([PostgreSQL][5])

(If you want direct links pasted as raw URLs I can list them — I included the official doc pages above as citations which you can click.)

---

# Small checklist for using these outputs safely

1. **Don’t kill pids blindly.** Inspect the query text in `pg_stat_activity` first.
2. **Short transactions win.** Long-running transactions cause most lock headaches.
3. **Use `SKIP LOCKED` for workers.** Avoids waiting on locked tuples.
4. **Use `pg_blocking_pids()`** to quickly find blocking PIDs (recommended in docs). ([PostgreSQL][1])

## References

[1]: https://www.postgresql.org/docs/current/view-pg-locks.html?utm_source=chatgpt.com "Documentation: 17: 52.12. pg_locks - PostgreSQL"
[2]: https://www.postgresql.org/docs/current/explicit-locking.html?utm_source=chatgpt.com "Documentation: 17: 13.3. Explicit Locking - PostgreSQL"
[3]: https://www.postgresql.org/docs/current/monitoring-locks.html?utm_source=chatgpt.com "Documentation: 17: 27.3. Viewing Locks - PostgreSQL"
[4]: https://www.postgresql.org/docs/current/sql-lock.html?utm_source=chatgpt.com "Documentation: 17: LOCK - PostgreSQL"
[5]: https://www.postgresql.org/docs/9.6/functions-info.html?utm_source=chatgpt.com "Documentation: 9.6: System Information Functions - PostgreSQL"
