#!/usr/bin/env bash
# Builds the image and starts the report service on localhost:8087.
# Re-run after every change to app/ (it replaces the running container).
set -euo pipefail
cd "$(dirname "$0")"
docker build -q -t opz-lab07-report app >/dev/null
docker rm -f opz-lab07 >/dev/null 2>&1 || true
docker run -d --name opz-lab07 -p 8087:8087 opz-lab07-report >/dev/null
echo "Running: curl localhost:8087/report   then try: time docker stop opz-lab07"
