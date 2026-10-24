#!/usr/bin/env bash
# Runs its own copy of the stack (project opz-lab10-check, status on port 18010,
# throwaway secrets), then does a full rotation: ./rotate.sh, a 5-second pause,
# revoke the old password, and give services 10 more seconds. Passes only when
# the db really refuses the old password and all three services still answer.
set -u
cd "$(dirname "$0")"
export COMPOSE_PROJECT_NAME=opz-lab10-check STATUS_PORT=18010
export SECRETS_DIR; SECRETS_DIR=$(mktemp -d)
fail=0
cp secrets.example/db_password.txt secrets.example/db_valid_passwords.txt "$SECRETS_DIR/"
chmod 644 "$SECRETS_DIR"/*
trap 'docker compose down --remove-orphans >/dev/null 2>&1; rm -rf "$SECRETS_DIR"' EXIT

docker compose up -d --build --force-recreate >.check.log 2>&1 || { echo "compose up failed, see .check.log"; exit 1; }
status() { curl -s "localhost:$STATUS_PORT"; }
all_ok() { python3 -c "import json,sys; d=json.loads(sys.argv[1]); sys.exit(0 if d and all(v==200 for v in d.values()) else 1)" "$1" 2>/dev/null; }

for _ in $(seq 1 40); do s=$(status); all_ok "$s" && break; sleep 0.5; done
if all_ok "$s"; then echo "pass  all three services up before rotation"
else echo "FAIL  not healthy even before rotating: $s"; exit 1; fi

old=$(tr -d '[:space:]' < "$SECRETS_DIR/db_password.txt")
./rotate.sh >/dev/null || { echo "FAIL  rotate.sh failed"; exit 1; }
sleep 5
# Revoke the old password ourselves, so skipping revocation can't pass the check.
grep -vx "$old" "$SECRETS_DIR/db_valid_passwords.txt" > "$SECRETS_DIR/.v" || true
cat "$SECRETS_DIR/.v" > "$SECRETS_DIR/db_valid_passwords.txt"

code=$(docker compose exec -T db python -c "
import urllib.request, urllib.error
r = urllib.request.Request('http://localhost:7000/auth', method='POST', headers={'X-Db-Password': '$old'})
try: urllib.request.urlopen(r); print(200)
except urllib.error.HTTPError as e: print(e.code)")
if [ "$code" = 401 ]; then echo "pass  old password revoked (db refuses it)"
else echo "FAIL  db still accepts the old password ($code)"; fail=1; fi

for _ in $(seq 1 20); do s=$(status); all_ok "$s" && break; sleep 0.5; done
for svc in orders billing reports; do
  c=$(python3 -c "import json,sys; print(json.loads(sys.argv[1]).get('$svc'))" "$s" 2>/dev/null)
  if [ "$c" = 200 ]; then printf 'pass  %-8s still answering after revocation\n' "$svc"
  else printf 'FAIL  %-8s %s after revocation (still using the old password?)\n' "$svc" "$c"; fail=1; fi
done

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
