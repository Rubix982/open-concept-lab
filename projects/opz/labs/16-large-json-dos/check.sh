#!/usr/bin/env bash
# Builds the current app/ and nginx/ as a separate project on port 18016 and
# attacks it. Passes only when oversized bodies get 413 (at NGINX, and at the app
# itself before it reads them), deeply nested JSON gets 400, the app never
# restarts, its peak memory stays small, and normal orders still work.
set -u
cd "$(dirname "$0")"
export LAB16_PROJECT=opz-lab16-check LAB16_PORT=18016
fail=0

docker compose up -d --build --force-recreate >.check.log 2>&1 || { echo "compose failed, see .check.log"; exit 1; }
trap 'docker compose down >/dev/null 2>&1' EXIT
for _ in $(seq 1 50); do curl -fs "localhost:$LAB16_PORT/healthz" >/dev/null && break; sleep 0.2; done
APP=$(docker compose ps -q app)

attack() { python3 tools/attack.py "$@" | sed -E 's/.*HTTP ([0-9]+).*/\1/'; }
expect() {  # label, allowed codes (regex), attack args...
  local label=$1 ok=$2; shift 2
  local code; code=$(attack "$@")
  if [[ $code =~ ^($ok)$ ]]; then echo "pass  $label -> $code"
  else echo "FAIL  $label -> ${code:-no answer} (want $ok)"; fail=1; fi
}

expect "normal order               " 200 normal
expect "150 MB body through NGINX  " 413 big 150
expect "nested 100,000 deep        " "400|413" nested 100000
expect "nested 800 deep (small)    " 400 nested 800

# Straight at the app, skipping NGINX: claim a 150 MB body, send almost none of it.
# A careful app answers 413 from the header alone instead of waiting to read it.
code=$(docker compose exec -T app python - <<'PY'
import socket
s = socket.create_connection(("127.0.0.1", 8000), timeout=4)
s.sendall(b"POST /api/orders HTTP/1.1\r\nHost: app\r\nContent-Type: application/json\r\n"
          b"Content-Length: 157286400\r\n\r\n{\"items\":")
try:
    print(s.recv(64).split()[1].decode())
except (socket.timeout, IndexError):
    print("timeout")
PY
)
if [ "$code" = 413 ]; then echo "pass  app itself refuses a 150 MB Content-Length (413, nothing read)"
else echo "FAIL  app itself, 150 MB Content-Length -> $code (want 413 before reading the body)"; fail=1; fi

expect "normal order, after attacks" 200 normal

restarts=$(docker inspect -f '{{.RestartCount}}' "$APP")
if [ "$restarts" = 0 ]; then echo "pass  app never restarted"
else echo "FAIL  app restarted $restarts time(s) (killed for running out of memory)"; fail=1; fi

peak=$(curl -fs "localhost:$LAB16_PORT/stats" | python3 -c "import json,sys; print(json.load(sys.stdin)['peak_rss_mb'])")
if [ -n "$peak" ] && [ "$peak" -lt 100 ]; then echo "pass  app peak memory ${peak} MB"
else echo "FAIL  app peak memory ${peak:-?} MB (want under 100)"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
