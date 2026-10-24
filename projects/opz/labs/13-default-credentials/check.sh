#!/usr/bin/env bash
# Starts the stack from your compose.yaml on port 18013 and passes only when:
#   - no documented default login works,
#   - the password in secrets/admin_password.txt does work, and is not weak,
#   - the image refuses to start with no password configured, or with "admin".
set -u
cd "$(dirname "$0")"
export OPZ_PORT=18013
P="docker compose -p opz-lab13-check"
URL="http://127.0.0.1:$OPZ_PORT"
fail=0

$P up -d --build >/dev/null 2>&1 || { echo "FAIL  docker compose up failed:"; $P up -d --build 2>&1 | tail -5; exit 1; }
trap '$P down >/dev/null 2>&1; docker rm -f opz-lab13-nopw opz-lab13-weak >/dev/null 2>&1' EXIT
for _ in $(seq 1 50); do curl -fs "$URL/healthz" >/dev/null && break; sleep 0.2; done

login() {  # user, password -> HTTP status
  python3 -c 'import json,sys; print(json.dumps({"username": sys.argv[1], "password": sys.argv[2]}))' "$1" "$2" \
    | curl -s -o /dev/null -w '%{http_code}' -X POST "$URL/login" -H 'Content-Type: application/json' --data-binary @-
}

if python3 tools/try_defaults.py "$URL" >/dev/null; then echo "pass  none of the default logins work"
else echo "FAIL  a default login works:"; python3 tools/try_defaults.py "$URL" | grep OPEN | sed 's/^/        /'; fail=1; fi

if [ ! -s secrets/admin_password.txt ]; then
  echo "FAIL  no secrets/admin_password.txt, so the check can't log in as the real admin"; fail=1
else
  pw=$(tr -d '\n' < secrets/admin_password.txt)
  c=$(login admin "$pw")
  if [ "$c" = 200 ]; then echo "pass  the configured password logs in"
  else echo "FAIL  the password in secrets/admin_password.txt doesn't log in (HTTP $c)"; fail=1; fi
  if [ ${#pw} -ge 16 ]; then echo "pass  configured password is ${#pw} characters"
  else echo "FAIL  configured password is only ${#pw} characters (want 16+, generated)"; fail=1; fi
fi

refuses() {  # container name, extra docker args... -> 0 if it exits nonzero within 5s
  local name=$1; shift
  docker rm -f "$name" >/dev/null 2>&1
  docker run -d --name "$name" "$@" opz-lab13-opsboard >/dev/null
  sleep 5
  local running code
  running=$(docker inspect -f '{{.State.Running}}' "$name")
  code=$(docker inspect -f '{{.State.ExitCode}}' "$name")
  docker rm -f "$name" >/dev/null 2>&1
  [ "$running" = false ] && [ "$code" != 0 ]
}

if refuses opz-lab13-nopw; then echo "pass  image refuses to start with no password configured"
else echo "FAIL  image starts with no password configured (falls back to a default?)"; fail=1; fi

if refuses opz-lab13-weak -e ADMIN_PASSWORD=admin; then echo "pass  image refuses to start with ADMIN_PASSWORD=admin"
else echo "FAIL  image starts with ADMIN_PASSWORD=admin"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
