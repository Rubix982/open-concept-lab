#!/usr/bin/env bash
# Starts the API behind nginx on localhost:8015. Re-run after editing
# nginx/nginx.conf (or run: docker compose exec proxy nginx -s reload).
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d --build --force-recreate
for _ in $(seq 1 50); do curl -fs localhost:8015/healthz >/dev/null && break; sleep 0.2; done
echo "Up: curl -H 'X-API-Key: key_FAKE_alice' 'localhost:8015/search?q=kettle'"
