#!/usr/bin/env bash
# Builds the current app/, starts it, begins a 3-second /report request, and
# stops the container half a second in (like a deploy would). Passes only when
# the in-flight report still completes AND the container exits within 5 seconds
# of being asked, instead of waiting out Docker's 10-second kill timer.
set -u
cd "$(dirname "$0")"
NAME=opz-lab07-check
PORT=18087
fail=0

docker build -q -t opz-lab07-report app >/dev/null || { echo "build failed"; exit 1; }
docker rm -f $NAME >/dev/null 2>&1
docker run -d --name $NAME -p $PORT:8087 opz-lab07-report >/dev/null
trap 'docker rm -f $NAME >/dev/null 2>&1' EXIT
for _ in $(seq 1 50); do curl -fs "localhost:$PORT/healthz" >/dev/null && break; sleep 0.2; done

out=$(mktemp)
curl -s -m 15 "localhost:$PORT/report" >"$out" 2>/dev/null & req=$!
sleep 0.5
start=$(python3 -c 'import time; print(time.time())')
docker stop -t 10 $NAME >/dev/null
took=$(python3 -c "import time; print(round(time.time() - $start, 1))")
wait $req

if grep -q "report:" "$out"; then echo "pass  in-flight report finished"
else echo "FAIL  in-flight report was cut off"; fail=1; fi

if python3 -c "import sys; sys.exit(0 if $took < 5 else 1)"; then echo "pass  container stopped in ${took}s"
else echo "FAIL  container took ${took}s to stop (Docker gave up and SIGKILLed it?)"; fail=1; fi

code=$(docker inspect -f '{{.State.ExitCode}}' $NAME)
if [ "$code" = 0 ]; then echo "pass  exited cleanly (code 0)"
else echo "FAIL  exit code $code (137 = killed by SIGKILL, 143 = died on SIGTERM without cleanup)"; fail=1; fi

rm -f "$out"
[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
