#!/usr/bin/env bash
# Runs the same load test against the current deployment, then passes only when:
# the pod survived it with zero restarts (no OOMKill), memory requests and limits
# are both set, and they're based on what the pod really used: the limit sits
# above the measured peak with some headroom, but not absurdly above it, and the
# request covers most of the peak.
set -u
cd "$(dirname "$0")"
K="kubectl --context kind-opz-lab05"
fail=0

$K get deployment report >/dev/null 2>&1 || { echo "no report deployment: run ./setup.sh"; exit 1; }
$K rollout status deployment/report --timeout=90s >/dev/null 2>&1

echo "      running the load test (up to 3 min)..."
$K delete job load --ignore-not-found >/dev/null 2>&1
$K apply -f load/job.yaml >/dev/null
$K wait --for=condition=complete job/load --timeout=180s >/dev/null 2>&1 \
  || $K wait --for=condition=failed job/load --timeout=5s >/dev/null 2>&1
failed=$($K logs job/load 2>/dev/null | sed -nE 's/done: ([0-9]+) failed requests/\1/p')
if [ "$failed" = 0 ]; then echo "pass  load test: every request answered"
else echo "FAIL  load test: ${failed:-?} requests failed (pod died mid-test?)"; fail=1; fi

pod=$($K get pods -l app=report --no-headers -o custom-columns=N:.metadata.name,D:.metadata.deletionTimestamp | awk '$2=="<none>"{print $1; exit}')
restarts=$($K get pod "$pod" -o jsonpath='{.status.containerStatuses[0].restartCount}')
reason=$($K get pod "$pod" -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}')
if [ "$restarts" = 0 ]; then echo "pass  zero restarts under load"
else echo "FAIL  $restarts restarts under load (last: ${reason:-?})"; fail=1; fi

stats=$($K exec "$pod" -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/stats').read().decode())" 2>/dev/null)
req=$($K get deployment report -o jsonpath='{.spec.template.spec.containers[0].resources.requests.memory}')
lim=$($K get deployment report -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}')

python3 - "$stats" "$req" "$lim" <<'PY' || fail=1
import json, re, sys
stats, req, lim = sys.argv[1], sys.argv[2], sys.argv[3]
UNITS = {"": 1, "k": 1e3, "M": 1e6, "G": 1e9, "Ki": 2**10, "Mi": 2**20, "Gi": 2**30}
def mib(q: str) -> float | None:
    m = re.fullmatch(r"([0-9.]+)([A-Za-z]*)", q or "")
    return float(m.group(1)) * UNITS.get(m.group(2), 0) / 2**20 if m and m.group(2) in UNITS else None
ok = True
try:
    peak = json.loads(stats)["peak_rss_mb"]
except Exception:
    print("FAIL  couldn't read /stats from the pod"); sys.exit(1)
r, l = mib(req), mib(lim)
print(f"      measured peak {peak:.0f} MiB; request {req or 'unset'}, limit {lim or 'unset'}")
if r is None or l is None:
    print("FAIL  memory request and limit must both be set"); sys.exit(1)
if l >= peak * 1.2: print(f"pass  limit leaves headroom above the peak ({l/peak:.1f}x)")
else: print(f"FAIL  limit only {l/peak:.2f}x the measured peak; one busy moment away from OOMKill"); ok = False
if l <= peak * 4: print("pass  limit is based on usage, not a blank cheque")
else: print(f"FAIL  limit is {l/peak:.1f}x the peak; that memory is promised to nobody else on the node"); ok = False
if r >= peak * 0.8: print("pass  request covers the real working set")
else: print(f"FAIL  request {r:.0f} MiB is far below the {peak:.0f} MiB the pod really uses; the scheduler will overpack the node"); ok = False
sys.exit(0 if ok else 1)
PY

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
