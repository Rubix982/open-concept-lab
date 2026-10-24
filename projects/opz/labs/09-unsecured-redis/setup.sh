#!/usr/bin/env bash
# Builds and starts the app and Redis. Re-run after any change to compose.yaml or app/.
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d --build --force-recreate --remove-orphans
echo "Up. Try: curl localhost:8009/login   then: tools/attacker.sh"
