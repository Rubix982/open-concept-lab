# Lab 10 · Credential Rotations Not Propagated

**Time:** ~30 min · **Needs:** Docker Compose · **Cost:** free, all local

## The incident

Security policy says the database password is rotated every quarter. This
quarter the DBA ran the runbook (`rotate.sh`), waited, and revoked the old
password (`revoke.sh`). Within seconds, reports stopped loading. Orders and
billing were fine. All three services read the same secret file.

## Setup

```bash
./setup.sh               # copies secrets.example/ to secrets/, starts the stack
curl -s localhost:8010   # status page: {"orders": 200, "billing": 200, "reports": 200}
```

The stack:
- `db`, a stand-in database that only does logins. It accepts any password listed in `secrets/db_valid_passwords.txt`.
- `orders`, `billing` and `reports`, which each log in on every health check, using the password in the secret file `secrets/db_password.txt`.
- `status`, which asks all three on port 8010.

Reproduce the incident:

```bash
./rotate.sh              # step 1: add a new password; services' file gets it
curl -s localhost:8010   # all fine (old and new both work right now)
./revoke.sh              # step 2: the db forgets the old password
curl -s localhost:8010   # ...
```

`./setup.sh` resets everything to the starting state.

If a service shows a single 503 *right* after `rotate.sh` and is fine a second
later, that's a different (smaller) bug: it read the file while it was being
rewritten. `SOLUTION.md` explains it; it isn't the incident.

## Your job

1. **Diagnose.** Why does one service fail when all three read the same file?
   Hints, one at a time if you're stuck:
   - `docker compose exec reports cat /run/secrets/db_password`. Is the file wrong?
   - `docker compose logs db`. Which password ending is being refused?
   - Compare `app/reports.py` with `app/orders.py`. *When* does each one read the file?
2. **Fix it** so a rotation reaches every service without anyone watching. You
   have two places you could fix it, and either is fine:
   - the **service** (`app/reports.py`), so it notices the new password, or
   - the **runbook** (`rotate.sh`), so it makes services pick up the new password.
   Think about which one you'd trust at 3 a.m. with ten services instead of three.
3. **Prove it.** `./check.sh` runs its own copy (status on port 18010), runs your
   `rotate.sh`, waits 5 seconds, revokes the old password **itself** (so you can't
   pass by never revoking), and checks all three services still answer.
4. **Write the retro** (below).
5. **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why reports kept the old password even though the file changed:
- The fix I chose (service or runbook), and why:
- Why the runbook has two steps with a wait between them:
- How would you know every consumer has switched before revoking?
- What changes if the secret is an env var instead of a file? (lab 02)
