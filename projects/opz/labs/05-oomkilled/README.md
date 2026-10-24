# Lab 05 · Resource Starvation: Misconfigured Requests & Limits (OOMKilled)

**Time:** ~45 min · **Needs:** Docker, `kind`, `kubectl` · **Cost:** free, all local

## The incident

The report service is fine when it's quiet. Under real use it restarts every
few minutes. Its logs are clean, with no error and no stack trace: the last line is
a normal request, and then it's simply starting again. Users get connection
resets. Someone copied the `resources:` block from another service's manifest.

## Setup

```bash
./setup.sh                                   # kind cluster "opz-lab05" + the service (~1 min first time)
kubectl get pods -w                          # terminal 2: watch
kubectl delete job load --ignore-not-found; kubectl apply -f load/job.yaml   # the load test
kubectl logs job/load                        # how many requests failed
```

`setup.sh` switches kubectl to `kind-opz-lab05`. Re-run it to reset everything.

## Your job

1. **Diagnose with kubectl only.** Hints, one at a time if you're stuck:
   - `kubectl logs deploy/report --previous`: why is there nothing useful here?
   - `kubectl describe pod <pod>`: look at `Last State`, `Reason` and `Exit Code`.
   - Exit code 137 again (lab 07: 128 + 9). Who sent SIGKILL this time, and why?
   - `kubectl get pod <pod> -o jsonpath='{.status.qosClass}'`: what class is it, and what does that mean?
2. **Measure before you change anything.** You can't set a limit from a guess,
   which is how this went wrong in the first place.
   - The app reports its own memory: `kubectl port-forward deploy/report 8080` and `curl localhost:8080/stats`.
   - To measure the real peak, the pod has to survive the load test once. How?
   - (`kubectl top` needs metrics-server, which kind doesn't install. `/stats` is enough here.)
3. **Fix `k8s/deployment.yaml`**, `kubectl apply -f k8s/`. Set requests and
   limits from what you measured. There's more than one right answer: you can
   also change how much memory the app *uses* (read `app/app.py`).
4. **Prove it.** `./check.sh` runs the same load test and passes only when the pod
   survives it, and the numbers fit the measurement: the limit has headroom but
   isn't a blank cheque, and the request covers what the pod really uses.
5. **Write the retro** (below). **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- What a request is for, and what a limit is for:
- Why the logs were clean (who killed the container, and how fast):
- Memory over the limit vs. CPU over the limit, what happens to each:
- Why "just set 1Gi" fails the check, and what it costs a real cluster:
- The QoS class before and after, and why it matters when a node runs short:
