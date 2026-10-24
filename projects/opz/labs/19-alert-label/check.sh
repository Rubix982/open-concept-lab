#!/usr/bin/env bash
# Passes only when the rule's unit test passes, the alert stays quiet while the
# API is up, and the alert actually fires within ~40s of the API going down.
set -u
cd "$(dirname "$0")"
PROM=http://localhost:9019
fail=0

if docker run --rm -v "$PWD/prometheus:/etc/prometheus:ro" --entrypoint promtool \
     prom/prometheus:v2.53.2 test rules /etc/prometheus/tests/rules_test.yml >.check.log 2>&1
then echo "pass  rule unit test (promtool test rules)"
else echo "FAIL  rule unit test; see .check.log"; fail=1; fi

docker compose up -d >/dev/null 2>&1
docker compose start api >/dev/null 2>&1
docker compose restart prometheus >/dev/null 2>&1   # pick up rule edits
trap 'docker compose start api >/dev/null 2>&1' EXIT

alert_state() {  # prints firing / pending / none
  curl -fs "$PROM/api/v1/alerts" | python3 -c '
import json, sys
alerts = [a for a in json.load(sys.stdin)["data"]["alerts"] if a["labels"].get("alertname") == "ApiDown"]
states = {a["state"] for a in alerts}
print("firing" if "firing" in states else "pending" if "pending" in states else "none")'
}

for _ in $(seq 1 30); do
  curl -fs "$PROM/api/v1/query?query=up" 2>/dev/null | grep -q '"value"' && break; sleep 1
done
sleep 6   # a few scrapes and evaluations with the API up

s=$(alert_state)
if [ "$s" = none ]; then echo "pass  ApiDown quiet while the API is up"
else echo "FAIL  ApiDown is $s while the API is up"; fail=1; fi

echo "      stopping the API, waiting up to 40s for ApiDown to fire..."
docker compose stop api >/dev/null 2>&1
fired=no
for _ in $(seq 1 40); do
  [ "$(alert_state)" = firing ] && { fired=yes; break; }; sleep 1
done
if [ "$fired" = yes ]; then echo "pass  ApiDown fired after the API went down"
else echo "FAIL  API down for 40s and ApiDown never fired"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
