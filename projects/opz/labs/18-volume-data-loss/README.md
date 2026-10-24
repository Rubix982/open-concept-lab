# Lab 18 · Silent Data Loss from Wrong Volume Mount

**Time:** ~40 min · **Needs:** Docker, `kind`, `kubectl` · **Cost:** free, all local

## The incident

The notes service keeps its data in SQLite "on a volume", per the manifest. It
passed review and testing. Then two things happened in one week:

- The app crashed once (it happens) and came back **empty**.
- After that was "fixed", a node was drained for maintenance, the pod moved, and
  everything was gone **again**.

There are two bugs, layered like lab 04: fixing the first reveals the second.

## Setup

```bash
./setup.sh                                  # kind cluster "opz-lab18" + the service
kubectl port-forward svc/notes 8018:8080    # terminal 2
curl -s -XPOST localhost:8018/notes -d 'buy milk'
curl -s localhost:8018/notes
curl -s -XPOST localhost:8018/crash         # simulate a crash; wait for the restart, re-run port-forward
kubectl delete pod -l app=notes             # simulate a node drain moving the pod
```

## Your job

1. **Find bug 1** (data lost on a crash). Hints, one at a time:
   - `curl localhost:8018/notes` tells you where the database file is.
   - `kubectl describe pod`: where is the volume mounted? Are those the same place?
   - A container's own filesystem is thrown away when it restarts. Only volumes survive.
2. **Find bug 2** (data lost when the pod moves).
   - Read about volume types: how long does an `emptyDir` live? A container? A pod?
   - `kubectl get storageclass`: kind ships one. What uses it?
   - `kubectl get pvc,pv` before and after your fix.
3. **Fix `k8s/deployment.yaml`**, `kubectl apply -f k8s/`. If Kubernetes refuses
   to change something in place, `kubectl delete deployment notes` first.
4. **Prove it.** `./check.sh` writes a note, crashes the app, then deletes the
   pod, and passes only when the note survives both.
5. **Write the retro** (below). **Clean up:** `./teardown.sh`.

Spoilers live in `SOLUTION.md`.

## Retro (fill in)

- Bug 1, and why "it's on a volume" was wrong:
- Bug 2: how long an emptyDir lives, and what outlives a pod:
- PVC vs. PV vs. StorageClass, one line each:
- Why a database usually runs as a StatefulSet, not a Deployment:
- What a PVC still doesn't protect against:
