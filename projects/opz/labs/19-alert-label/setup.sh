#!/usr/bin/env bash
# Starts the orders API and Prometheus. Re-run after editing prometheus/ so
# Prometheus reloads its config and rules.
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d
docker compose restart prometheus >/dev/null
echo "API:        http://localhost:8019/orders"
echo "Prometheus: http://localhost:9019  (Alerts tab, Status > Targets, Graph)"
