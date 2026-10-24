#!/usr/bin/env bash
# Builds a separate copy of production (project opz-lab14-check, port 18014) on
# v1 with migration 001, then runs YOUR ./deploy.sh twice under steady traffic:
# forward to v2, then back to v1. Passes only when each deploy lands on the
# right version and no request gets a 5xx, during or after either deploy.
set -u
cd "$(dirname "$0")"
export COMPOSE_PROJECT_NAME=opz-lab14-check APP_PORT=18014
BASE="http://127.0.0.1:$APP_PORT"
fail=0

cleanup() { docker compose down -v --remove-orphans >/dev/null 2>&1; }
trap cleanup EXIT
cleanup
echo "      starting v1 with migration 001..."
docker build -q -t opz-lab14-app:v1 app/v1 >/dev/null || { echo "build of v1 failed"; exit 1; }
docker compose up -d --wait db >/dev/null 2>&1
docker compose run --rm migrate 001 >/dev/null 2>&1 || { echo "migration 001 failed"; exit 1; }
APP_VERSION=v1 docker compose up -d --wait app >/dev/null 2>&1

version() { curl -fs "$BASE/healthz" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin)['version'])" 2>/dev/null; }

deploy_under_traffic() {  # target version
  local target=$1 out
  out=$(mktemp)
  python3 tools/traffic.py "$BASE" >"$out" 2>&1 & local t=$!
  sleep 1
  ./deploy.sh "$target" >.check.log 2>&1 || echo "      (deploy.sh $target exited nonzero, see .check.log)"
  for _ in $(seq 1 40); do [ "$(version)" = "$target" ] && break; sleep 0.25; done
  sleep 3   # keep traffic going on the new version for a while
  kill -TERM $t; wait $t 2>/dev/null
  local summary; summary=$(tail -1 "$out")
  local errors; errors=$(echo "$summary" | python3 -c "import json,sys; print(json.load(sys.stdin)['server_errors'])" 2>/dev/null || echo "?")
  local now; now=$(version)

  if [ "$now" = "$target" ]; then echo "pass  deploy to $target: now running $target"
  else echo "FAIL  deploy to $target: running '${now:-nothing}'"; fail=1; fi
  if [ "$errors" = 0 ]; then echo "pass  deploy to $target: no 5xx under traffic"
  else
    echo "FAIL  deploy to $target: $errors requests got a 5xx"
    echo "$summary" | python3 -c "import json,sys; print('        last:', json.load(sys.stdin)['last_error'])" 2>/dev/null
    fail=1
  fi
  rm -f "$out"
}

deploy_under_traffic v2
deploy_under_traffic v1

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
