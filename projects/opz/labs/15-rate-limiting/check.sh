#!/usr/bin/env bash
# Starts its own copy (project opz-lab15-check, port 18015) with the current
# nginx/nginx.conf, then runs tools/load.py: a 40-thread scraper and Alice at
# 5 requests/second, for 8 seconds. Passes only when the scraper is turned away
# with 429 + Retry-After, while Alice never is and stays fast.
set -u
cd "$(dirname "$0")"
export COMPOSE_PROJECT_NAME=opz-lab15-check PROXY_PORT=18015
BASE="http://127.0.0.1:$PROXY_PORT"
fail=0

trap 'docker compose down --remove-orphans >/dev/null 2>&1' EXIT
docker compose up -d --build --force-recreate >/dev/null 2>&1 || { echo "compose up failed (nginx.conf syntax? try: docker compose logs proxy)"; exit 1; }
for _ in $(seq 1 50); do curl -fs "$BASE/healthz" >/dev/null && break; sleep 0.2; done
curl -fs "$BASE/healthz" >/dev/null || { echo "proxy not answering: docker compose -p opz-lab15-check logs proxy"; exit 1; }

echo "      flooding for 8s..."
out=$(python3 tools/load.py "$BASE" 8)
echo "$out" | sed '$d' | sed 's/^/      /'
j=$(echo "$out" | tail -1)
field() { echo "$j" | python3 -c "import json,sys; v=json.load(sys.stdin)$1; print(v)"; }

total=$(field "['scraper_total']"); s429=$(field "['scraper_429']")
if python3 -c "import sys; sys.exit(0 if $total > 0 and $s429 / $total >= 0.5 else 1)"; then
  echo "pass  scraper mostly gets 429 ($s429 of $total)"
else echo "FAIL  scraper got 429 on $s429 of $total requests (by status: $(field "['scraper_by_status']"))"; fail=1; fi

ra=$(field "['retry_after']")
if [ "$ra" != "None" ]; then echo "pass  429s carry Retry-After: $ra"
else echo "FAIL  no Retry-After header on the 429s"; fail=1; fi

ok=$(field "['alice_by_status'].get('200', 0)")
astat=$(field "['alice_by_status']")
if [ "$astat" = "{'200': $ok}" ] && [ "$ok" -gt 0 ]; then echo "pass  alice: every request succeeded ($ok)"
else echo "FAIL  alice was not always served: $astat"; fail=1; fi

p95=$(field "['alice_p95_ms']")
if python3 -c "import sys; sys.exit(0 if $p95 < 150 else 1)"; then echo "pass  alice p95 latency ${p95} ms (< 150)"
else echo "FAIL  alice p95 latency ${p95} ms (normal is ~30; the flood is slowing everyone)"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
