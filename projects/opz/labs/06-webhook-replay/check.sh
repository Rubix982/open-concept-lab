#!/usr/bin/env bash
# Starts a fresh copy of the shop on a side port and attacks it. Passes only when
# forged, tampered, stale and replayed webhooks are all refused, a fresh signed
# one ships its order exactly once, and signatures are compared in constant time.
set -u
cd "$(dirname "$0")"
PORT=18086
export SHOP_URL="http://127.0.0.1:$PORT/webhook"
export LAST_EVENT="$(mktemp)"
fail=0

PORT=$PORT python3 app/server.py >.check.log 2>&1 & srv=$!
trap 'kill $srv 2>/dev/null; wait $srv 2>/dev/null; rm -f "$LAST_EVENT"' EXIT
for _ in $(seq 1 30); do curl -fs "127.0.0.1:$PORT/orders" >/dev/null && break; sleep 0.2; done

status() { python3 tools/send.py "$@" | sed -E 's/.*HTTP ([0-9]+).*/\1/'; }
shipments() { curl -fs "127.0.0.1:$PORT/orders" | python3 -c "import json,sys; print(json.load(sys.stdin)['$1']['shipments'])"; }

expect_refused() {  # name, order, send args...
  local name=$1 order=$2; shift 2
  local code; code=$(status "$@")
  if [[ $code == 4* ]] && [ "$(shipments "$order")" = 0 ]; then echo "pass  $name refused ($code), nothing shipped"
  else echo "FAIL  $name accepted (HTTP $code, $order shipments: $(shipments "$order"))"; fail=1; fi
}

expect_refused "forged signature   " ord_1002 forge ord_1002
expect_refused "tampered body      " ord_1003 tamper ord_1003
expect_refused "stale (10 min old) " ord_1002 stale ord_1002

code=$(status fresh ord_1001)
if [[ $code == 2* ]] && [ "$(shipments ord_1001)" = 1 ]; then echo "pass  fresh signed event accepted, shipped once"
else echo "FAIL  fresh signed event: HTTP $code, ord_1001 shipments: $(shipments ord_1001)"; fail=1; fi

status replay >/dev/null; status replay >/dev/null
n=$(shipments ord_1001)
if [ "$n" = 1 ]; then echo "pass  replayed twice, still shipped once"
else echo "FAIL  replayed twice, ord_1001 shipped $n times"; fail=1; fi

if grep -q "compare_digest" app/server.py; then echo "pass  constant-time signature compare"
else echo "FAIL  signature not compared with hmac.compare_digest"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
