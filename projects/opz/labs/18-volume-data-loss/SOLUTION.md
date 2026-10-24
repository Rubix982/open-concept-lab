# Lab 18 · Solution (spoilers)

## Bug 1: the volume is mounted somewhere the app doesn't write

The manifest mounts the volume at `/data`, but the app writes to its default,
`/app/data/notes.db` (`GET /notes` says so). That path is in the container's
own writable layer, which is thrown away whenever the container restarts. The
volume sat empty the whole time.

Fix one side to match the other. Either set `DB_PATH=/data/notes.db`, or mount
at `/app/data`.

## Bug 2: emptyDir lives exactly as long as the pod

With bug 1 fixed the data survives crashes, because a container restart keeps the
pod, and `emptyDir` belongs to the pod. Deleting or rescheduling the pod (a node
drain, an eviction, a `rollout restart`, a new image) deletes the `emptyDir` with
it. For weeks it looks persistent, until the first reschedule.

Fix: a PersistentVolumeClaim.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: notes-data
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests:
      storage: 100Mi
---
# in the Deployment:
spec:
  strategy:
    type: Recreate        # a ReadWriteOnce volume can't be shared by old and new pod
  template:
    spec:
      containers:
        - name: notes
          env:
            - name: DB_PATH
              value: /data/notes.db
          volumeMounts:
            - name: data
              mountPath: /data
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: notes-data
```

## How the pieces fit

- **PVC** (claim): "I need 100Mi, mountable read-write by one node." Lives in your namespace.
- **PV** (volume): the actual storage. Usually created on demand to satisfy a claim.
- **StorageClass**: *how* to create PVs: which provisioner, disk type, reclaim
  policy. kind's `standard` class makes directories on the node (local-path);
  on a cloud it would create an EBS/Azure disk.

## Details worth knowing

- **`strategy: Recreate`.** The default rolling update starts the new pod before
  stopping the old one. With a ReadWriteOnce disk on a real cloud, the new pod can
  hang waiting for a disk the old pod still holds.
- **StatefulSets** exist for this: stable pod names (`notes-0`), one PVC per
  replica from `volumeClaimTemplates`, and ordered start/stop. A Deployment with
  `replicas: 2` and one RWO PVC is a bug waiting for a second node.
- **What a PVC doesn't protect against:** deleting the PVC (the default
  `reclaimPolicy: Delete` deletes the data too), disk failure, or bad writes.
  Persistence isn't backup. On kind specifically, local-path storage lives on one
  node, so losing that node loses the data.
- **SQLite on network storage** is a known foot-gun (file locking). Real
  databases want block storage, and usually one writer.
