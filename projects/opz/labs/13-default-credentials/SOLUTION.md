# Lab 13 · Solution (spoilers)

## What was wrong

`load_password()` fell back to `"admin"` when nothing was configured, and printed
a warning nobody reads. The compose file configured nothing. So the dashboard
that can deploy and read secrets was protected by a password printed in its own
docs.

## Fix 1: your deployment

Generate the password, keep it out of git, and mount it as a file:

```bash
mkdir -p secrets
python3 -c "import secrets; print(secrets.token_urlsafe(24))" > secrets/admin_password.txt
```

```yaml
services:
  opsboard:
    build: ./app
    image: opz-lab13-opsboard
    ports:
      - "${OPZ_PORT:-8013}:8000"
    environment:
      ADMIN_PASSWORD_FILE: /run/secrets/admin_password
    secrets:
      - admin_password

secrets:
  admin_password:
    file: ./secrets/admin_password.txt
```

That's enough to pass the first three checks, and it's where most teams stop.

## Fix 2: the image

The real bug is that an insecure state is *possible*. Remove the default, and
refuse to start rather than run with a weak password:

```python
def load_password() -> str:
    ...  # file, then env, as before
    return ""


KNOWN_DEFAULTS = {"admin", "password", "changeme", "admin123", "root", "toor"}
MIN_LENGTH = 16

ADMIN_PASSWORD = load_password()
if not ADMIN_PASSWORD:
    sys.exit("refusing to start: set ADMIN_PASSWORD_FILE (or ADMIN_PASSWORD). There is no default.")
if ADMIN_PASSWORD.lower() in KNOWN_DEFAULTS or len(ADMIN_PASSWORD) < MIN_LENGTH:
    sys.exit(f"refusing to start: the admin password is a known default or shorter than {MIN_LENGTH} characters.")
```

A container that exits with a clear message is a five-minute annoyance at deploy
time. A dashboard with `admin/admin` is an incident.

## Details worth knowing

- **Refuse vs. generate.** The other safe pattern is to generate a random
  password on first start and print it once to the logs (Jenkins does this; so
  does Grafana's `admin` reset). It's friendlier, but the password now lives in
  your log system, and a restart with a fresh volume makes a new one. Refusing
  forces the decision onto whoever deploys it, which is where it belongs.
- **Finding defaults in a stack you didn't build:** list every image and
  appliance, look up each one's documented default login, and try them. Scanners
  (nmap's `http-default-accounts` script, Nuclei's default-login templates) do
  exactly what `try_defaults.py` does, just with longer lists.
- **What this doesn't cover:**
  - **Brute force.** The login has no rate limit or lockout, so even a strong
    password only makes guessing slow, not impossible to try.
  - **Exposure.** An admin dashboard usually shouldn't be on a public port at
    all. Put it behind a VPN or SSO, and the password becomes the second lock,
    not the only one.
  - **One shared admin account.** Nobody can tell who did what. Real users with
    their own logins (and MFA) fix that; this lab doesn't.
