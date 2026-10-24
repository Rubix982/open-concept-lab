# Lab 11 · Escalating Build Times Due to Dependency Bloat

**Time:** ~30 min · **Needs:** Docker · **Cost:** free, all local

## The incident

The sales-summary service is about 40 lines of Python. Every time anyone changes
one of those lines, CI spends a minute or more on `apt-get` and reinstalling
pandas. The image is nearly a gigabyte, and a security scan flagged that it ships
`gcc` and `make` to production, where nothing compiles anything.

## Setup

```bash
./setup.sh                        # builds (timed) and runs it on localhost:8011
curl -s localhost:8011/summary
```

Now feel the problem: change one string in `app/app.py` (say, the startup
message) and run `./setup.sh` again. Watch which build steps run again.

## Your job

1. **Diagnose.** Read the build output and `docker history opz-lab11-sales`.
   Hints, one at a time if you're stuck:
   - Docker caches each instruction as a layer. When one layer changes, every
     layer *after* it is rebuilt, even if its own instruction didn't change.
   - Which instruction changes when `app.py` changes? What comes after it?
   - Run `docker run --rm opz-lab11-sales sh -c 'command -v gcc make'`. Which
     line put them there, and does anything at run time use them?
   - Do numpy and pandas need a compiler to install on this machine? Look at the
     `pip install` output: does it say `.whl` or `.tar.gz`?
2. **Fix `app/Dockerfile`** so a code change rebuilds in seconds, and the final
   image is small and has no build tools. Look up **multi-stage builds**.
3. **Prove it.** `./check.sh` builds a copy of `app/`, changes one line, rebuilds
   and times it (under 15s), checks the image is under 700 MB (it starts near 1 GB) with no
   `gcc`/`cc`/`g++`/`make`, and that `/summary` still answers.
4. **Write the retro** (below).
5. **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Why a one-line code change reinstalled every package:
- The order of instructions that keeps the cache useful:
- What the multi-stage build keeps out of the final image, and why that matters:
- Image size and rebuild time, before and after:
- When would you actually need a compiler in the build stage?
