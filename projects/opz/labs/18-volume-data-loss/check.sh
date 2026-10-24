#!/usr/bin/env bash
# Writes a note, then (1) crashes the app so the container restarts, and
# (2) deletes the pod so Kubernetes makes a new one. Passes only when the note
# is still there after both.
set -u
cd "$(dirname "$0")"
K="kubectl --context kind-opz-lab18"
fail=0

$K get svc notes >/dev/null 2>&1 || { echo "no notes service: run ./setup.sh"; exit 1; }

pod() { $K get pods -l app=notes --no-headers -o custom-columns=N:.metadata.name,D:.metadata.deletionTimestamp | awk '$2=="<none>"{print $1; exit}'; }
ready() { $K wait --for=condition=Ready pod -l app=notes --timeout=90s >/dev/null 2>&1; }
call() {  # method path [body] -- runs curl-equivalent inside the pod
  $K exec "$(pod)" -- python -c "
import sys, urllib.request
req = urllib.request.Request('http://localhost:8080$2', method='$1', data=sys.argv[1].encode() if len(sys.argv) > 1 else None)
print(urllib.request.urlopen(req, timeout=5).read().decode())" ${3:+"$3"} 2>/dev/null
}
has_note() { call GET /notes | grep -q "$1"; }

ready
note="check-$(date +%s)"
call POST /notes "$note" >/dev/null
if has_note "$note"; then echo "pass  wrote a note"
else echo "FAIL  couldn't write a note"; echo "lab not passed yet"; exit 1; fi

# 1. Crash: same pod, new container.
before=$($K get pod "$(pod)" -o jsonpath='{.status.containerStatuses[0].restartCount}')
call POST /crash >/dev/null
for _ in $(seq 1 60); do
  now=$($K get pod "$(pod)" -o jsonpath='{.status.containerStatuses[0].restartCount}' 2>/dev/null)
  [ "${now:-0}" -gt "$before" ] && break; sleep 1
done
ready; sleep 1
if has_note "$note"; then echo "pass  note survived a container crash"
else echo "FAIL  note gone after the container restarted"; fail=1; fi

# 2. Reschedule: delete the pod, as a node drain would.
old=$(pod)
$K delete pod "$old" --wait=true >/dev/null 2>&1
for _ in $(seq 1 90); do p=$(pod); [ -n "$p" ] && [ "$p" != "$old" ] && break; sleep 1; done
ready; sleep 1
if has_note "$note"; then echo "pass  note survived the pod being deleted and recreated"
else echo "FAIL  note gone after the pod was recreated ($(pod))"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
