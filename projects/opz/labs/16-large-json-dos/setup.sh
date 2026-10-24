#!/usr/bin/env bash
# Builds and starts NGINX + the orders API on localhost:8016.
# Re-run after changing app/ or nginx/ (it rebuilds and recreates what changed).
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d --build
echo "Up. curl -s localhost:8016/healthz   and see tools/attack.py"
