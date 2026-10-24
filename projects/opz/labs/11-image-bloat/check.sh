#!/usr/bin/env bash
# Builds a copy of app/, then changes ONE line of app.py and builds again, timing
# the second build. Passes only when that code-only rebuild takes under 15s,
# the image is under 700 MB with no compiler in it, and the service still works.
set -u
cd "$(dirname "$0")"
IMG=opz-lab11-verify
NAME=opz-lab11-check
PORT=18011
fail=0

# A throwaway copy of app/ inside the lab folder. (A mktemp dir under
# /var/folders made Docker Desktop's build client hang after finishing.)
ctx=.check-ctx
rm -rf "$ctx"; mkdir "$ctx"
trap 'docker rm -f $NAME >/dev/null 2>&1; rm -rf "$ctx"' EXIT
cp -R app/. "$ctx/"

echo "      first build (slow the first time, that's fine)..."
docker build --progress=plain -t $IMG "$ctx" >.check.log 2>&1 || { echo "FAIL  build failed, see .check.log"; exit 1; }

echo "# touched by check.sh at $(date +%s)" >> "$ctx/app.py"
echo "      rebuilding after a one-line code change..."
start=$(python3 -c 'import time; print(time.time())')
docker build --progress=plain -t $IMG "$ctx" >>.check.log 2>&1 || { echo "FAIL  rebuild failed, see .check.log"; exit 1; }
took=$(python3 -c "import time; print(round(time.time() - $start, 1))")
if python3 -c "import sys; sys.exit(0 if $took < 15 else 1)"; then echo "pass  code-only rebuild took ${took}s"
else echo "FAIL  code-only rebuild took ${took}s (dependencies reinstalled?)"; fail=1; fi

# Unpacked size, as `docker image ls` shows it (inspect's .Size can be the compressed size).
size=$(docker image ls $IMG --format '{{.Size}}' | head -1)
mb=$(python3 -c "
import re, sys
n, unit = re.fullmatch(r'([0-9.]+)\s*([kMG]?B)', sys.argv[1]).groups()
print(int(float(n) * {'B': 1e-6, 'kB': 1e-3, 'MB': 1, 'GB': 1000}[unit]))" "$size")
if [ "$mb" -lt 700 ]; then echo "pass  image is ${mb} MB"
else echo "FAIL  image is ${mb} MB (should be under 700)"; fail=1; fi

tools=$(docker run --rm --entrypoint sh $IMG -c 'for t in gcc cc g++ make; do command -v $t; done' 2>/dev/null)
if [ -z "$tools" ]; then echo "pass  no compilers or make in the final image"
else echo "FAIL  build tools in the final image: $(echo $tools)"; fail=1; fi

docker rm -f $NAME >/dev/null 2>&1
docker run -d --name $NAME -p 127.0.0.1:$PORT:8011 $IMG >/dev/null
for _ in $(seq 1 40); do curl -fs "localhost:$PORT/healthz" >/dev/null && break; sleep 0.25; done
if curl -fs "localhost:$PORT/summary" | grep -q '"west": 2920'; then echo "pass  /summary still correct"
else echo "FAIL  /summary doesn't answer correctly"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
