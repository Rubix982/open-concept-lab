# Lab 02 · Secret Exposed Through Environment Variables

**Time:** ~30 min · **Needs:** Docker (with Compose) · **Cost:** free, all local

## The incident

Lab 01 is fixed: the image holds no token, and Compose passes it in at run time
from `.env`. Then the service misbehaves. A support engineer with Docker access
on the host runs `docker inspect` on the container to debug it and pastes the
full output into a ticket. The token is in that output in plain text, and now
it's in the ticket system, its search index and its email notifications.

The image was clean, but the running container still showed the token to anyone who looked.

## Your job

1. **See the leak yourself.** Start it and find the token in three places,
   without opening `.env`:
   ```bash
   docker compose up -d --build
   ```
   Hints, one at a time if you're stuck:
   - `docker inspect $(docker compose ps -q api)` — search the output.
   - `docker compose exec api env` — every program the app starts inherits this list.
   - `docker compose config` — what would a CI log show if a job printed this?
2. **Fix it.** The token should reach the app as a **file** mounted into the
   container, not as an environment variable. The app has to change too: right
   now `load_token()` only reads the environment.
   Look up: Compose `secrets:` (top-level and per-service), and the `_FILE`
   convention used by the official Postgres and MySQL images.
3. **Prove it.** Run `./check.sh` until it says `LAB PASSED`. It also confirms
   the image is still clean, so Lab 01's fix can't quietly come undone.
4. **Write the retro** (below).

When you're done: `docker compose down`.
Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- The three places the token showed up, and who can see each: Before the fix, the token itself appeared in (1) `docker inspect` (anyone with Docker access on the host, and anyone reading pasted output in tickets/chats), (2) `env` inside the container (the app and every program it starts), (3) `docker compose config` (anyone reading a CI log where it ran). After the fix all three show only the path, and knowing the path is not the secret.
- Why a file is safer than an environment variable: Env vars are pushed: copied into every child process, inspect output and crash dump by default. A file is pulled: only code that deliberately opens it gets the token.
- What the fix still does NOT protect against: Anyone who can `docker exec` into the container can `cat` the file, and the token still sits in plain text on the host's disk (`api_token.txt`). It stops accidental leaks, not a deliberate insider.
- The fix: Compose `secrets:` mounts the token as a file at `/run/secrets/api_token`; the environment only holds its path (`API_TOKEN_FILE`); the app reads the file.
- One thing I'd check in any compose file from now on: `env_file:` or `environment:` carrying a secret value.
