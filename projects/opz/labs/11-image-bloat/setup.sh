#!/usr/bin/env bash
# Builds the image (timed) and runs it on localhost:8011.
set -euo pipefail
cd "$(dirname "$0")"
start=$(date +%s)
docker build -t opz-lab11-sales app
echo "build took $(( $(date +%s) - start ))s"
docker rm -f opz-lab11 >/dev/null 2>&1 || true
docker run -d --name opz-lab11 -p 127.0.0.1:8011:8011 opz-lab11-sales >/dev/null
docker image ls opz-lab11-sales
echo "Try: curl localhost:8011/summary"
