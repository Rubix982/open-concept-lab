#!/usr/bin/env bash
# Starts a fresh copy of the API on a side port. Passes only when expired,
# wrong-audience, unsigned (alg none) and tampered tokens are all refused,
# and a fresh honest token still works.
set -u
cd "$(dirname "$0")"
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
PORT=18088
fail=0

PORT=$PORT $PY app/server.py >.check.log 2>&1 & srv=$!
trap 'kill $srv 2>/dev/null; wait $srv 2>/dev/null' EXIT
for _ in $(seq 1 30); do curl -s -o /dev/null "127.0.0.1:$PORT/me" && break; sleep 0.2; done

code() {  # kind, path
  curl -s -o /dev/null -w '%{http_code}' "127.0.0.1:$PORT$2" \
    -H "Authorization: Bearer $($PY tools/mint.py "$1")"
}

c=$(code valid /me)
if [ "$c" = 200 ]; then echo "pass  fresh honest token accepted"
else echo "FAIL  fresh honest token got $c (should be 200)"; fail=1; fi

for case in "expired /me" "wrong-aud /me" "none /admin/refunds" "tampered /admin/refunds"; do
  set -- $case
  c=$(code "$1" "$2")
  if [ "$c" = 401 ]; then printf 'pass  %-9s token refused on %s\n' "$1" "$2"
  else printf 'FAIL  %-9s token got %s on %s (should be 401)\n' "$1" "$c" "$2"; fail=1; fi
done

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
