# Lab 16 · DoS Attack via Large JSON Body

**Time:** ~40 min · **Needs:** Docker Compose (pulls `nginx:1.27-alpine`, `python:3.12-slim`) · **Cost:** free, all local

## The incident

The orders API sits behind NGINX. Since last night, it keeps falling over:
requests fail with `502 Bad Gateway`, and the app container's restart count
keeps going up. Nobody is sending much traffic, just a few strange requests.

A few weeks ago someone turned off NGINX's upload limit because "large uploads
were failing with 413".

The app container has a 256 MB memory limit. That's part of the incident (it's
what gets the app killed), and it also means this lab can't hurt your Mac.

## Setup

```bash
./setup.sh                                  # NGINX on localhost:8016 -> app:8000
curl -s localhost:8016/healthz
docker compose ps                           # note the app's status
```

`tools/attack.py` sends requests through NGINX:

```bash
python3 tools/attack.py normal              # an ordinary order
python3 tools/attack.py big 150             # a valid order, 150 MB of padding
python3 tools/attack.py nested 100000       # only 200 KB, but 100,000 brackets deep
python3 tools/attack.py nested 800          # tiny, 800 deep
```

Watch while you attack: `docker compose logs -f app` in one terminal,
`docker stats opz-lab16-app-1` in another, and
`docker inspect -f '{{.RestartCount}}' opz-lab16-app-1` afterwards.

## Your job

1. **Break it first.** Run each attack. For each one, write down what actually
   failed: memory, or something else? (The `nested` ones are not about memory.)
2. **Fix it at both layers**, in `nginx/default.conf` and `app/app.py`, then
   `./setup.sh` again. Hints, one at a time if you're stuck:
   - NGINX turned off its own protection. What's the directive, and what's a sane
     value for a JSON orders API?
   - The proxy isn't enough on its own: something inside the network can call the
     app directly. Where can the app learn the body size *before* reading the body?
   - What should the app answer when the body is too big? There's a status code
     made for it.
   - The `nested` attacks crash Python's recursion, once in `json.loads` and once
     in `count_items`. Catching the error is one fix. Refusing anything deeper than
     an order could ever be, before parsing, is a better one.
3. **Prove it.** `./check.sh` builds your current code as a separate copy on port
   18016 and passes only when big bodies get 413 (from NGINX *and* from the app
   directly), deep nesting gets 400, the app never restarts, and its peak memory
   stays under 100 MB.
4. **Write the retro** (below), then `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- What killed the app on the 150 MB request, and why it was a restart, not an error:
- Why the nested attacks broke it without using much memory:
- Why the limit belongs at the proxy *and* in the app:
- Why the app can refuse a huge body without reading it:
- What these limits don't stop:
