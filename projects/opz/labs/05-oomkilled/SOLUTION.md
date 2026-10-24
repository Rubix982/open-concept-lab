# Lab 05 · Solution (spoilers)

## What was happening

`describe pod` shows:

```
Last State:  Terminated
  Reason:    OOMKilled
  Exit Code: 137
```

The container went over its **memory limit** (128Mi). The kernel's OOM killer
sent SIGKILL instantly, so the app got no chance to log anything. That's why
the logs were clean. Kubernetes then restarted it, and after a few repeats the
pod showed CrashLoopBackOff (lab 04).

The app caches up to 25 reports of 6 MB each: ~150 MB of cache plus ~40 MB for
Python itself, so ~190 MiB at peak, well above 128Mi.

## Measuring

Give the pod room to survive one load test (a temporary 1Gi limit), run the
load, then read `/stats`:

```json
{"rss_mb": 189.6, "peak_rss_mb": 190.2, "cache_entries": 25, "cache_limit": 25}
```

## The fix

```yaml
          resources:
            requests:
              memory: 200Mi    # what it really uses: the scheduler reserves this
              cpu: 50m
            limits:
              memory: 256Mi    # peak + ~30% headroom
```

`check.sh`: zero restarts, limit 1.3x peak, request ≥ peak. Passed.

**The other right answer:** make the app need less. `CACHE_ENTRIES: "10"` keeps
the peak near 100 MiB, so ~128Mi request / 160Mi limit works. That's a trade
(more cache misses, slower reports), and it's the better trade when memory is the
expensive resource.

## Why "just set 1Gi" is wrong

It passes "no restarts", and the check still fails it. The scheduler places pods
by **requests**, not limits. A 32Mi request with a 1Gi limit tells Kubernetes "I
need 32Mi" while the pod really uses 190Mi. Pack a node with pods like that
and it runs out of memory for real. Then the kubelet starts **evicting** pods,
and Burstable pods using more than they requested go first.

## Details worth knowing

- **Requests** = reserved, used for scheduling. **Limits** = the ceiling, enforced
  by the kernel.
- **Memory over the limit → killed** (OOMKilled). **CPU over the limit →
  throttled** (slowed down, never killed). Many teams set CPU requests but no CPU
  limit, because throttling shows up as mysterious latency.
- **QoS classes:** `Guaranteed` (requests = limits for every resource),
  `Burstable` (some requests set), `BestEffort` (none). On a short node,
  BestEffort is evicted first, then Burstable pods over their request.
  Guaranteed is last.
- **In production** you'd watch the real peak over days (Prometheus,
  `container_memory_working_set_bytes`), not one load test. The Vertical Pod
  Autoscaler in recommendation mode does this for you.
- **What this doesn't cover:** a real memory *leak*. If usage climbs forever, no
  limit is right; the limit only decides how often you crash.
