# Lab 04 · Solution (spoilers)

## What CrashLoopBackOff means

It's not an error in itself. It's Kubernetes saying "this container keeps exiting,
so I'm waiting longer before each restart": 10s, 20s, 40s… up to 5 minutes.
The real cause is always somewhere else: the app's logs, or the pod's events.

## Bug 1: bad config (found in the logs)

```
kubectl logs <pod> --previous
fatal: APP_MODE='production' is not one of ['dev', 'prod']
```
The app exits with code 1 on start. `describe` shows `Last State: Terminated, Exit Code: 1`.

Fix in `k8s/configmap.yaml`:
```yaml
  APP_MODE: prod
```
Then `kubectl apply -f k8s/` and `kubectl rollout restart deployment/greeter`.
Pods read `envFrom` values when their container starts. Changing a ConfigMap does
not update a running process's environment, so a restart is the reliable way to
pick up the new value.

## Bug 2: liveness probe on the wrong path (found in events)

After Bug 1 the pod starts, logs `starting in prod mode`, then gets killed every
few seconds anyway. The logs look healthy, apart from the probe's own requests
returning 404. `describe pod` says it plainly:
```
Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 404
Normal   Killing    Container greeter failed liveness probe, will be restarted
```
The app serves `/healthz`; the probe asks for `/health`. Fix in `k8s/deployment.yaml`:
```yaml
          livenessProbe:
            httpGet:
              path: /healthz
```

## Logs vs. events

- **Logs** are what the **app** said. They tell you why the app chose to exit.
- **Events** (`describe`) are what **Kubernetes** did: scheduled, pulled, started,
  probed, killed, OOM-killed. When Kubernetes kills a healthy app, only events show it.

## Why a wrong liveness probe is worse than none

With no probe, a healthy app just runs. A wrong liveness probe kills a **healthy**
app over and over: it takes a working service down. Common safer patterns:
- a liveness probe that checks only "is the process alive" (not the database etc.),
  with generous timing
- a **readiness** probe for "can I take traffic right now". A failing readiness
  probe removes the pod from load balancing but doesn't kill it
- a **startupProbe** for slow-starting apps, so liveness doesn't kill them mid-boot

## Bonus thing you may have noticed

Old pods sit in `Terminating` for ~30s. Python running as PID 1 in a container
ignores SIGTERM by default, so Kubernetes waits out the 30s grace period, then
sends SIGKILL. Fixes: handle SIGTERM in the app, or run under a tiny init
(`docker run --init`, or `tini`). That's a good future lab.
