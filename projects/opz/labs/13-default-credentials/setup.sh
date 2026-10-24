#!/usr/bin/env bash
# Builds and starts Opsboard on localhost:8013. Re-run after changing app/ or compose.yaml.
set -euo pipefail
cd "$(dirname "$0")"
docker compose -p opz-lab13 up -d --build
echo "Running on http://localhost:8013. Try: python3 tools/try_defaults.py"
