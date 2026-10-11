# Lab 04 · Debugging a CrashLoopBackOff Pod

**Time:** ~30 min · **Needs:** Docker, `kind`, `kubectl` · **Cost:** free, all local

## The incident

A teammate deployed `greeter` to Kubernetes and went to lunch. The pod shows
`CrashLoopBackOff`, and the restart count keeps climbing. The app worked on their laptop.

There are **two** problems. Fixing the first reveals the second. That's typical
of real CrashLoopBackOff debugging: each fix lets the pod get one step further.

## Setup

```bash
./setup.sh             # creates a local kind cluster "opz-lab04" and deploys the broken app (~1 min first time)
kubectl get pods -w    # watch it crash; Ctrl-C to stop
```

`setup.sh` switches kubectl to the `kind-opz-lab04` context.

## Your job

1. **Diagnose without reading the YAML first.** Use only `kubectl` to find out
   why it crashes. Hints, one at a time if you're stuck:
   - `kubectl logs deploy/greeter` — what does the app say before it dies?
   - `kubectl logs <pod> --previous` — the logs of the run that just crashed.
   - `kubectl describe pod <pod>` — read the **Events** at the bottom, and `Last State` / `Exit Code`.
   - `kubectl get configmap greeter-config -o yaml`
2. **Fix both problems** by editing `k8s/` and running `kubectl apply -f k8s/`.
   If a fix doesn't seem to take effect, try `kubectl rollout restart deployment/greeter`.
   Don't delete the liveness probe; fix it.
3. **Prove it.** Run `./check.sh` until it says `LAB PASSED`. It watches the pod
   for 20 seconds, because "Running" right after a restart proves nothing.
4. **Write the retro** (below).
5. **Clean up:** `./teardown.sh` deletes the cluster.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- What CrashLoopBackOff actually means (what is backing off?): Not an error itself. The container keeps exiting, so Kubernetes waits longer before each restart (10s, 20s, 40s… up to 5 min). The cause is always elsewhere: logs or events.
- Bug 1 — how I found it, and the fix: `kubectl logs deploy/greeter` said `APP_MODE='production' is not one of ['dev', 'prod']`. A bad setting, not a code bug, so no new image: fix the ConfigMap to `APP_MODE: prod`, `kubectl apply`, `kubectl rollout restart` (pods read env values only when the container starts).
- Bug 2 — how I found it, and why the logs didn't show it: The pod ran and the app logged a clean start, but the restart count kept climbing. `kubectl describe pod` events: `Liveness probe failed: HTTP probe failed with statuscode: 404`. The probe asked for `/health`, the app serves `/healthz`. The logs couldn't show it because Kubernetes did the killing, not the app.
- Logs vs. describe/events — what each one is for: Logs are what the app said (why it chose to exit). Events are what Kubernetes did: started, probed, killed, OOM-killed. When Kubernetes kills a healthy app, only the events show it.
- Why a wrong liveness probe is worse than no probe at all: With no probe a healthy app just runs; a wrong probe kills a healthy app over and over, taking a working service down. Liveness checks only "is the process alive"; readiness handles "can I take traffic" (it removes the pod from traffic without killing it).
- Incident playbook: Roll back (`kubectl rollout undo`) if an earlier version worked → capture logs and describe output before anything deletes the pods → scale to zero only if each restart does harm (migrations, emails, poison queue messages) → diagnose → fix → scale back up.
