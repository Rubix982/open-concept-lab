# Lab 10 · Solution (spoilers)

## What went wrong

`reports.py` reads the password **once**, when the process starts, into a
global. The file did change. `docker compose exec reports cat
/run/secrets/db_password` shows the new password, but the running process never
looks at the file again. Until revocation, the old password still worked, so
nothing looked wrong. The failure appears only at revocation, which is usually
days after the rotation, when nobody connects the two.

## Fix A: the service re-reads (most robust)

```python
from common import db_login, read_password, serve


def health() -> bool:
    return db_login(read_password())
```

Reading a small file per login costs microseconds. If it ever mattered, cache it
for a few seconds, or re-read only when a login fails and retry once. Don't cache
it for an hour: `check.sh` gives services 10 seconds after revocation, and a
60-second cache fails it.

## Fix B: the runbook restarts consumers

Append to `rotate.sh`:

```bash
docker compose restart reports
```

This works, but only for the consumers the runbook knows about. Ten services
later, someone adds an eleventh and forgets the runbook. Fix A fails safe: a new
service written like `orders` just works.

A middle ground is **reload on a signal** (handle `SIGHUP` by re-reading the
file), which is what nginx, Postgres and HAProxy do. The runbook still has to
send the signal, though.

## Details worth knowing

- **Why two steps:** rotation is *add new → switch every consumer → revoke old*.
  The overlap window is what makes it zero-downtime. Revoking straight away turns
  every slow consumer into an outage. Most managed secret stores (AWS Secrets
  Manager, Vault) support this with two valid versions at once.
- **Know when everyone has switched:** the db can log *which* password each login
  used (by version, never the value), so "zero logins with the old one for an hour"
  is a safe signal to revoke.
- **Bind mounts and inodes:** Compose `secrets:` with `file:` is a bind mount of
  that one file. `rotate.sh` overwrites it *in place*. Tools that write a new file
  and rename it over the old one (many editors, `sed -i`, Kubernetes' atomic
  updates) give it a new inode, and a single-file bind mount keeps showing the
  *old* one. Kubernetes avoids this by mounting a whole directory of symlinks and
  swapping the link. That's also why subPath-mounted secrets never update.
- **Torn reads:** overwriting in place has its own race. For a moment the file is
  empty or half-written, and a service reading it then logs in with a truncated
  password (you may see one 503 right after `rotate.sh`, and `db` logs a refused
  password with an odd ending). Kubernetes' symlink swap fixes both problems at
  once: readers see either the whole old file or the whole new one.
- **Env vars can't be rotated in place at all:** a process's environment is fixed
  at start, so a secret passed as an env var (lab 02) always needs a restart.
- **What this doesn't cover:** connection pools. A pool opened with the old
  password keeps working until the db drops those connections, and then fails
  later, at random. Real rotations also recycle pools.
