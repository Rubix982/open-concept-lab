# Lab 02 · Solution (spoilers)

## Why environment variables leak

- **`docker inspect <container>`** prints the container's full config, `Env` included,
  to anyone who can talk to the Docker daemon. People paste that output into tickets and chats.
- **Child processes inherit the environment.** Every shell, subprocess and library
  the app launches gets a copy. Crash reporters and debug pages (e.g. Django's
  debug page, Spring's `/actuator/env`) often dump the environment.
- **`docker compose config`** expands `env_file` and prints the values. A CI job that
  runs it for debugging writes the token into the build log.

## Fix

Put the token in its own file, e.g. `api_token.txt` (just the value, no `KEY=`),
keep it out of git and the image, and delete `.env`.

`compose.yaml`:
```yaml
name: opz-lab02

services:
  api:
    build: ./app
    ports:
      - "18082:8080"
    environment:
      API_TOKEN_FILE: /run/secrets/api_token   # a path, not the secret
    secrets:
      - api_token

secrets:
  api_token:
    file: ./api_token.txt
```

`app/app.py`, replacing `load_token`:
```python
def load_token() -> str:
    path = os.environ.get("API_TOKEN_FILE", "/run/secrets/api_token")
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""
```

Compose mounts the file at `/run/secrets/api_token`. `inspect`, `env` and
`compose config` now show only the path.

## What it still doesn't protect against

Anyone who can `docker exec` into the container can still `cat /run/secrets/api_token`.
Docker access is effectively root on the host, and root can read the app's memory anyway.
The fix removes the *accidental* leaks: pasted inspect output, inherited
environments, crash dumps, CI logs. Stopping a deliberate insider takes
short-lived tokens and a secret manager, which is a later lab.

## Where this goes next

- **Kubernetes:** same idea. Mount a `Secret` as a volume rather than using `env: valueFrom`.
- **Swarm:** `docker secret create` keeps the secret encrypted in the cluster's own
  store and mounts it in memory (tmpfs), never on disk.
- **Rotation:** a mounted file can be updated without rebuilding the image. An app
  that re-reads the file can pick up a new token without a restart.
