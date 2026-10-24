# Lab 13 · Forgotten Default Credentials

**Time:** ~30 min · **Needs:** Docker Compose · **Cost:** free, all local

## The incident

Opsboard is the ops team's admin dashboard: it can restart servers, deploy, and
read secrets. It was deployed from its image with the vendor's quick-start, which
says:

> Log in with **admin / admin**, then change the password.

Nobody changed it. Last night someone logged in from an IP nobody recognises,
first try, no failed attempts. Default credentials are published in the vendor
docs, so they're the first thing every attacker and every scanner tries.

(Opsboard is a stand-in for any real product with a default login: routers,
Grafana, Jenkins, database images, IoT cameras. Here, `app/` plays the vendor
image and you own both it and `compose.yaml`.)

## Setup

```bash
./setup.sh                              # Opsboard on http://localhost:8013
python3 tools/try_defaults.py           # an attacker's first minute
```

Log in by hand:
```bash
curl -s -X POST localhost:8013/login -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"admin"}'
```

## Your job

1. **Find it the way an attacker would.** Run `tools/try_defaults.py`. Then read
   `load_password()` in `app/opsboard.py`: under what conditions does the default
   apply?
2. **Fix it in two places.** Hints, one at a time if you're stuck:
   - *Your deployment:* give Opsboard a real password. It should be generated, not
     chosen (`python3 -c "import secrets; print(secrets.token_urlsafe(24))"`),
     live in `secrets/admin_password.txt` (already in `.gitignore`), and reach the
     container without going through an environment variable. Lab 02 did this.
   - *The image itself:* fixing your compose file protects you, but not the next
     team who deploys this image with the quick-start. What should the app do when
     no password is configured, instead of falling back?
   - Someone will set the password to `admin` to "get it working". Should that
     start?
3. **Prove it.** `./check.sh` runs your compose file on port 18013 and passes only
   when no default login works, the password in `secrets/admin_password.txt` logs
   in and is 16+ characters, and the image refuses to start with no password or
   with `admin`.
4. **Write the retro** (below). `./teardown.sh` removes everything.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- How long would admin/admin have survived on the internet, and why:
- Why fixing only `compose.yaml` isn't enough:
- "Refuse to start" vs. "generate a password at first start": what each costs:
- How I'd find default credentials in a stack I didn't build:
- What a strong password still doesn't protect against here:
