# Lab 07 · Graceful Shutdown (PID 1 ignores SIGTERM)

**Time:** ~40 min · **Needs:** Docker · **Cost:** free, all local

## The incident

Every deploy of the report service takes ten seconds longer than it should, per
container. While a deploy is running, some users' reports come back half-written
or as a dropped connection. The app logs nothing at all about shutting down.

You saw a hint of this in lab 04: old pods sat in `Terminating` for a while
before they went away.

## Setup

```bash
./setup.sh                          # builds and starts the service on localhost:8087
curl localhost:8087/report          # takes ~3 seconds
time docker stop opz-lab07          # how long does stopping take?
docker inspect -f '{{.State.ExitCode}}' opz-lab07
```

Re-run `./setup.sh` after every change to `app/`.

## Your job

1. **Diagnose.** Why does `docker stop` take exactly ~10 seconds? What does exit
   code 137 tell you? Hints, one at a time if you're stuck:
   - `docker stop` sends SIGTERM, waits (10s by default), then sends SIGKILL.
     Kubernetes does the same with a 30s `terminationGracePeriodSeconds`.
   - `docker exec opz-lab07 cat /proc/1/cmdline | tr '\0' ' '`: which process is PID 1?
   - Linux treats PID 1 specially: a signal with no handler installed is
     **ignored**, not fatal. Python installs no SIGTERM handler.
   - Exit codes above 128 are 128 + the signal number. 137 = 128 + 9.
2. **Fix it.** There's a quick fix that makes the container stop fast. Try it,
   run `./check.sh`, and see what it costs you. Then fix it properly: on SIGTERM
   the service should stop taking new requests, finish the ones in flight, and exit 0.
   - Look at what `ThreadingHTTPServer.shutdown()`, `server_close()` and
     `daemon_threads` do in the Python docs.
   - `shutdown()` blocks until `serve_forever()` returns. What happens if you call
     it from inside a signal handler that is running on that same thread?
3. **Prove it.** `./check.sh` starts a 3-second report, stops the container half a
   second in, and passes only when the report completes, the container is gone
   within 5 seconds, and the exit code is 0.
4. **Write the retro** (below). **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- What `docker stop` / a pod deletion actually sends, and in what order:
- Why PID 1 ignored SIGTERM:
- The quick fix, and what it broke:
- What "graceful" means in three steps:
- What Kubernetes adds on top (readiness, preStop, grace period):
