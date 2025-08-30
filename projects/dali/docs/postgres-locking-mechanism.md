# PostgreSQL Locking Levels — Complete Guide

## Overview of PostgreSQL Locking

PostgreSQL uses several locking mechanisms to protect data integrity while allowing concurrency. Locks operate at different granularities and for different purposes:

1. **Table-level locks** — coordinate DDL and broad DML operations (coarse-grained)
2. **Page-level locks** — internal protection of physical pages/blocks (medium-grained, mostly internal)
3. **Row-level locks** — protect individual tuples for transactional correctness (fine-grained)

PostgreSQL also relies on **MVCC (Multi-Version Concurrency Control)** so most reads do **not** block writes and most writes do **not** block reads. Locks come into play for modifications that must be serialized or when explicit locking is requested.

---

## 1. Table-Level Locks

### When to use

* Schema changes (`ALTER TABLE`, `DROP TABLE`)
* Bulk operations that must exclude concurrent DML (`TRUNCATE`, `CLUSTER`, `REINDEX`, `VACUUM FULL`)
* To do coarse-grained application-level coordination (rare — prefer advisory locks)

### Lock modes (summary)

| Mode                     | Description / Typical use                              | Blocks (examples)                      |
| ------------------------ | ------------------------------------------------------ | -------------------------------------- |
| `ACCESS SHARE`           | Normal reads (`SELECT`)                                | Does **not** block other reads         |
| `ROW SHARE`              | `SELECT ... FOR UPDATE` acquires this on table         | blocks some DDL                        |
| `ROW EXCLUSIVE`          | DML: `INSERT`, `UPDATE`, `DELETE`                      | conflicts with stronger locks          |
| `SHARE UPDATE EXCLUSIVE` | `VACUUM`-type internal maintenance                     | prevents `ACCESS EXCLUSIVE`            |
| `SHARE`                  | Some concurrent operations that must prevent exclusive | blocks `EXCLUSIVE`, `ACCESS EXCLUSIVE` |
| `SHARE ROW EXCLUSIVE`    | Stronger than `SHARE`                                  | blocks many writes                     |
| `EXCLUSIVE`              | DDL operations                                         | blocks most \*/                        |
| `ACCESS EXCLUSIVE`       | Strongest — e.g., `DROP TABLE`, `TRUNCATE`             | blocks all other access                |

> Example: `LOCK TABLE orders IN ACCESS EXCLUSIVE MODE;` will block other sessions from reading or writing `orders` until the lock is released.

### Examples

```sql
-- Acquire an exclusive lock (blocks other sessions)
BEGIN;
LOCK TABLE products IN EXCLUSIVE MODE;
-- perform operations that must be serialized with respect to the whole table
COMMIT;
```

Check table locks:

```sql
SELECT pid, locktype, relation::regclass AS table, mode, granted
FROM pg_locks
JOIN pg_stat_activity USING (pid)
WHERE locktype = 'relation';
```

### Performance characteristics

* **Scope:** entire table (all rows)
* **Concurrency:** low when held
* **Typical use:** DDL and heavy maintenance
* **Note:** PostgreSQL does **not** perform automatic lock escalation (unlike some RDBMS). Table locks are explicit or implied by specific commands.

---

## 2. Page-Level Locks

### What they are

* PostgreSQL stores table/index data in 8KB pages (blocks).
* Page-level locking is used internally to protect the physical contents of a page during writes and index updates.
* These locks are **short-lived** and managed by the storage layer; they're not commonly manipulated by applications.

### When they matter

* High write contention where many sessions update rows that happen to be stored on the same page.
* Bulk inserts/updates that concentrate activity in a small number of pages.
* Index operations that modify index pages.

### How to observe / infer

* There is no direct `pg_locks` entry labelled “page” for application-level inspection; instead you infer contention from:

  * `pg_stat_activity` wait events (e.g., `BufferPin`, `IO` related waits)
  * Elevated `lock` or `wait` times and hot pages as revealed by `pg_buffercache` and buffer statistics
* `EXPLAIN (ANALYZE, BUFFERS)` can show buffer reads/writes, helping locate hot pages.

### Performance characteristics

* **Scope:** single block (8KB)
* **Concurrency:** medium — multiple sessions can operate on different pages concurrently
* **Typical impact:** localized hotspots when many rows co-locate on the same page

### Practical tip

* If many updates hit the same page, consider:

  * spreading insert patterns (fillfactor, randomizing PKs)
  * re-clustering data
  * partitioning to reduce hotspotting

---

## 3. Row-Level Locks

### When to use

* Transactional updates and deletes on specific rows
* `SELECT ... FOR UPDATE`, `FOR NO KEY UPDATE`, `FOR SHARE`, `FOR KEY SHARE` to explicitly lock rows
* Optimistic concurrency can avoid locks, but row locks are used for pessimistic concurrency

### Row-lock varieties and meanings

| Clause              | Prevents                                                            | Typical use                                               |
| ------------------- | ------------------------------------------------------------------- | --------------------------------------------------------- |
| `FOR UPDATE`        | Prevents other transactions from `UPDATE` or `DELETE` on those rows | Strong row-level exclusion (e.g., update balances)        |
| `FOR NO KEY UPDATE` | Similar to `FOR UPDATE` but weaker for FK checks                    | When preventing updates but allowing some FK changes      |
| `FOR SHARE`         | Allows reads but prevents updates/deletes                           | Shared intent to read with assurance others won't delete  |
| `FOR KEY SHARE`     | Weaker than `FOR SHARE`, used for FK checks                         | Allows some concurrent changes but blocks destructive ops |

### Examples

```sql
-- Classic locking for account transfer
BEGIN;
SELECT balance FROM accounts WHERE id = 101 FOR UPDATE;
UPDATE accounts SET balance = balance - 50 WHERE id = 101;
COMMIT;

-- Worker queue pattern:
BEGIN;
WITH job AS (
  SELECT id FROM jobs WHERE state = 'pending'
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
UPDATE jobs SET state = 'running' FROM job WHERE jobs.id = job.id RETURNING jobs.*;
COMMIT;
```

`SKIP LOCKED` is useful for job-queue workers to avoid waiting on locked rows. `NOWAIT` causes immediate error if any targeted row is locked.

### How row locks are stored

* Row locks are tracked in `pg_locks` as `tuple` locks with `classid`/`objid` info — you can query `pg_locks` to see which tuples are locked and whether the lock is `granted`.

### Performance characteristics

* **Scope:** single tuple
* **Concurrency:** high — different rows can be modified concurrently
* **Typical impact:** minimal blocking if transactions are kept short and access patterns avoid hot rows

---

## MVCC and Locks — short primer

* PostgreSQL’s MVCC means **readers don’t block writers** and **writers don’t block readers** (reads see a snapshot).
* Locks are primarily for:

  * Preventing concurrent conflicting writes to the **same** row
  * Coordinating DDL and maintenance operations
  * Explicit transactional intent (`FOR UPDATE`, advisory locks)
* Even with MVCC, conflicts occur when two transactions try to modify the same tuple (one will wait or be aborted).

---

## Advisory Locks (Application-level locks)

### What they are

* Lightweight locks allocated by application using integer keys — not tied to rows/tables.
* Useful for coordinating resources outside the database or when you want custom lock semantics.

### Functions

* `pg_advisory_lock(bigint)` — session-level exclusive lock
* `pg_advisory_xact_lock(bigint)` — transaction-scoped exclusive lock
* `pg_try_advisory_lock(bigint)` — try-lock (non-blocking)
* `pg_advisory_unlock(bigint)` — release

### Example

```sql
-- Acquire an advisory lock keyed by a numeric id (session-level)
SELECT pg_advisory_lock(12345);

-- Release
SELECT pg_advisory_unlock(12345);

-- Transaction-scoped advisory lock (automatically released at COMMIT/ROLLBACK)
BEGIN;
SELECT pg_advisory_xact_lock(42);
-- do protected work
COMMIT;
```

Advisory locks are a good alternative to heavy table locks for app-level coordination.

---

## Monitoring locks & diagnosing blocking

### Basic view of locks

```sql
SELECT pid, usename, application_name, client_addr, locktype, mode, granted,
       relation::regclass AS table, virtualtransaction, query, state
FROM pg_locks l
LEFT JOIN pg_stat_activity a ON l.pid = a.pid
ORDER BY granted DESC, pid;
```

### Find who is blocking whom (blocking tree)

```sql
-- Shows blocked and blocking PIDs with their queries
WITH blocked AS (
  SELECT pid AS blocked_pid, relation, mode
  FROM pg_locks WHERE NOT granted
),
blocking AS (
  SELECT pid AS blocking_pid, relation, mode
  FROM pg_locks WHERE granted
)
SELECT bl.blocked_pid,
       a_blocked.query AS blocked_query,
       br.blocking_pid,
       a_blocking.query AS blocking_query
FROM blocked bl
JOIN blocking br ON bl.relation = br.relation
LEFT JOIN pg_stat_activity a_blocked ON a_blocked.pid = bl.blocked_pid
LEFT JOIN pg_stat_activity a_blocking ON a_blocking.pid = br.blocking_pid
ORDER BY bl.blocked_pid;
```

### Quick helper: direct blockers for a PID

```sql
SELECT pg_blocking_pids(<target_pid>);
-- then inspect pg_stat_activity for those PIDs
```

### Lock waits and wait\_event

Look at `pg_stat_activity.wait_event_type` and `wait_event` to see what waits look like (e.g., `Lock`, `BufferPin`, etc).

---

## Deadlocks

### Detection & behavior

* PostgreSQL detects deadlocks automatically (after `deadlock_timeout`, default 1s) and aborts **one** of the transactions to break the cycle.
* The aborted transaction receives a `deadlock detected` error and must retry (application should handle retries).

### Example deadlock scenario

Session A:

```sql
BEGIN;
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
-- waits later to update id = 2
```

Session B:

```sql
BEGIN;
UPDATE accounts SET balance = balance - 5 WHERE id = 2;
-- now tries to update id = 1 -> deadlock
```

### Prevention guidelines

* Access tables/rows in **consistent order** across transactions.
* Keep transactions **short** and avoid user interaction within transactions.
* Use `NOWAIT` or `SKIP LOCKED` where appropriate to avoid waiting.
* Implement retry logic in application for operations that may abort due to deadlocks.

---

## Tuning locking behavior

* `lock_timeout` — abort waiting for a lock after given time (useful to fail-fast rather than block forever).

  ```sql
  SET lock_timeout = '5s';
  ```

* `deadlock_timeout` — server setting controlling how long to wait before deadlock check (tweak with care).
* `statement_timeout` — kills a statement taking too long (can help with stuck locks indirectly).
* `max_locks_per_transaction` — tune only if your workload uses a very large number of distinct locks (e.g., many partitions touched in a single transaction).

---

## Common patterns & real-world examples

### 1) Order processing example — pessimistic locking

```sql
BEGIN;
SELECT id FROM inventory WHERE product_id = 99 FOR UPDATE;
-- ensure no two processes decrement stock for same row concurrently
UPDATE inventory SET qty = qty - 1 WHERE product_id = 99;
COMMIT;
```

### 2) Job queue workers — `SKIP LOCKED`

Workers pick a job without waiting if another worker already locked it:

```sql
BEGIN;
SELECT id FROM jobs WHERE state = 'pending' FOR UPDATE SKIP LOCKED LIMIT 1;
-- mark running, process, then COMMIT
```

### 3) Optimistic concurrency with versioning (avoid locks)

```sql
UPDATE accounts
SET balance = new_balance, xmin_version = xmin_version + 1
WHERE id = 1 AND xmin_version = :expected_version;
-- check rowcount to know if update succeeded; otherwise retry
```

### 4) Application-level coordination — advisory locks

```sql
-- lock on resource id 100
SELECT pg_advisory_xact_lock(100);
-- do work; lock released at transaction end
```

---

## Troubleshooting checklist

1. Are transactions too long? (long-running idle transactions hold locks)
2. Is row hot-spotting happening (many updates to same PK)? Consider partitioning or rebalancing.
3. Are you using `SELECT FOR UPDATE` unnecessarily? Prefer `FOR KEY SHARE` / `FOR NO KEY UPDATE` when appropriate.
4. Use `EXPLAIN (ANALYZE, BUFFERS)` and `pg_stat_activity` to find waits and hotspots.
5. Implement retry logic for deadlock-prone operations.
6. Use `SKIP LOCKED` for worker queues, avoiding blocking.

---

## Decision matrix — pick a lock style

| Need                                 | Use                                                  |
| ------------------------------------ | ---------------------------------------------------- |
| Protect single-row updates in OLTP   | Row-level locks (`FOR UPDATE`)                       |
| Implement worker queue               | `FOR UPDATE SKIP LOCKED`                             |
| Coordinate DDL / schema changes      | Table-level locks (`LOCK TABLE` or implicit via DDL) |
| Protect arbitrary app-level resource | Advisory locks (`pg_advisory_*`)                     |
| Avoid blocking other readers         | Rely on MVCC; avoid explicit locks                   |
| Avoid waiting on locks (fail fast)   | `SET lock_timeout` and/or `NOWAIT`                   |

---

## Monitoring & useful queries (quick list)

* Current locks and statements:

```sql
SELECT l.pid, a.usename, a.query, l.locktype, l.mode, l.granted
FROM pg_locks l JOIN pg_stat_activity a USING (pid)
ORDER BY l.granted DESC;
```

* Blocking chain (simple):

```sql
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.query AS blocked_query,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.query AS blocking_query
FROM pg_locks blocked_locks
JOIN pg_locks blocking_locks
  ON blocked_locks.locktype = blocking_locks.locktype
  AND blocked_locks.database IS NOT DISTINCT FROM blocking_locks.database
  AND blocked_locks.relation IS NOT DISTINCT FROM blocking_locks.relation
  AND blocked_locks.page IS NOT DISTINCT FROM blocking_locks.page
  AND blocked_locks.tuple IS NOT DISTINCT FROM blocking_locks.tuple
  AND blocked_locks.virtualxid IS NOT DISTINCT FROM blocking_locks.virtualxid
  AND blocked_locks.transactionid IS NOT DISTINCT FROM blocking_locks.transactionid
  AND blocked_locks.pid != blocking_locks.pid
JOIN pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted AND blocking_locks.granted;
```

* Find sessions waiting on locks:

```sql
SELECT pid, usename, state, wait_event_type, wait_event, query
FROM pg_stat_activity
WHERE wait_event_type IS NOT NULL;
```

---

## Interview-style questions (practice)

1. Explain how MVCC changes the way locks are used in PostgreSQL.
2. What is the difference between `FOR UPDATE` and `FOR NO KEY UPDATE`? When would you use each?
3. How does PostgreSQL detect and handle deadlocks? How should applications react?
4. What are advisory locks and when are they a good idea?
5. How do `SKIP LOCKED` and `NOWAIT` change locking semantics for `SELECT FOR UPDATE`?
6. Does PostgreSQL do lock escalation? Explain.

---

## Final recommendations / best practices

* Keep transactions short and avoid interactive steps while a transaction is open.
* Prefer row-level locking for OLTP; avoid table locks unless strictly necessary.
* Use `SKIP LOCKED` for worker queues to reduce contention.
* Use advisory locks for coarse-grained app coordination instead of table locks when possible.
* Monitor `pg_locks`, `pg_stat_activity`, and query plans to identify hot pages/rows.
* Implement retry/backoff for transactions that may deadlock or be aborted.
* Consider schema and data-layout changes (partitioning/clustering) if page-level hotspotting is observed.
