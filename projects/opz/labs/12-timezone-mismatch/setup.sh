#!/usr/bin/env bash
# Builds the scheduler image. Re-run after every change to app/.
set -euo pipefail
cd "$(dirname "$0")"
docker build -q -t opz-lab12-scheduler app >/dev/null
echo "Built. Try: docker run --rm opz-lab12-scheduler"
echo "     and: docker run --rm -e TZ=America/New_York opz-lab12-scheduler"
