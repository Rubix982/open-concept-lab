# Lab 01 · Hardcoded Credentials in Dockerfile

**Time:** ~20 min · **Needs:** Docker · **Cost:** free, all local

## The incident

A teammate shipped `app/` as an image to a shared registry. The service needs an
`API_TOKEN`. They put the token in the Dockerfile and, "to be safe", deleted the
`.env` file in a later step. A week later the token is being used from an IP you
don't recognise. Anyone who could pull the image could read the token.

## Your job

1. **See the leak yourself.** Build the image and find the token *without*
   reading the Dockerfile. Find it in at least two different places.
   ```bash
   docker build -t lab01 app
   ```
   Hints, one at a time if you're stuck:
   - `docker inspect lab01` — read the `Env` section.
   - `docker save lab01 -o lab01.tar`, untar it, and look inside the layer blobs.
     Ask yourself why `rm -f .env` didn't help.
2. **Fix it.** The token must not be in the image at all, and the service must
   still work when the token is supplied at run time.
3. **Prove it.** Run `./check.sh` until it says `LAB PASSED`.
4. **Write the retro** (5 lines, below). This is the part that sticks.

Spoilers live in `SOLUTION.md`. Open it only after `LAB PASSED`, or once you're properly stuck.

## Retro (fill in)

- Where the secret actually lived: In the image, not just a container: in its settings (ENV, visible via docker inspect) and in a file layer (COPY . . pulled in .env)
- Why deleting the file didn't remove it: Layers are append-only; rm adds a new layer that hides the file, but the earlier layer still holds it
- The fix: .dockerignore keeps .env out of the build; the token is supplied at run time (--env-file), so the image holds nothing
- What would have caught this before it shipped: An image secret scan in CI (trivy image --scanners secret); gitleaks for the repo side
- One thing I'd check in any Dockerfile from now on: COPY . . without .dockerignore, and any secret in ENV/ARG
