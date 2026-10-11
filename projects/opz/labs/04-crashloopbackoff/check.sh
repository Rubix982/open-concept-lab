#!/usr/bin/env bash
# Passes only when the greeter runs stably: ready, zero restarts over a
# 20-second window, answering on /healthz, with its liveness probe still in place.
set -u
cd "$(dirname "$0")"
K="kubectl --context kind-opz-lab04"
fail=0

$K get deployment greeter >/dev/null 2>&1 || { echo "no greeter deployment: run ./setup.sh"; exit 1; }

if [ -z "$($K get deployment greeter -o jsonpath='{.spec.template.spec.containers[0].livenessProbe}')" ]; then
  echo "FAIL  liveness probe removed (fix the probe, don't delete it)"; fail=1
else echo "pass  liveness probe still in place"; fi

# Give a fresh rollout up to 60s to come up. Not a verdict on its own: a crashing
# container with no readiness probe counts as Ready for an instant on each start.
$K wait --for=condition=Ready pod -l app=greeter --timeout=60s >/dev/null 2>&1
$K rollout status deployment/greeter --timeout=60s >/dev/null 2>&1

echo "      watching for 20s..."; sleep 20
# Current pods only: skip ones already shutting down after a rollout.
pods=$($K get pods -l app=greeter --no-headers \
  -o custom-columns=NAME:.metadata.name,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,DELETING:.metadata.deletionTimestamp \
  | awk '$4 == "<none>" {print $1, $2, $3}')
bad=$(echo "$pods" | awk 'NF && ($2 != "true" || $3 != "0")')
if [ -n "$pods" ] && [ -z "$bad" ]; then echo "pass  pod ready with 0 restarts"
else echo "FAIL  pod not stable:"; echo "$pods" | sed 's/^/        /'; fail=1; fi

$K port-forward deployment/greeter 18084:8080 >/dev/null 2>&1 & pf=$!
sleep 2
if curl -fs localhost:18084/healthz >/dev/null; then echo "pass  /healthz answers"
else echo "FAIL  /healthz doesn't answer"; fail=1; fi
kill $pf 2>/dev/null

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
