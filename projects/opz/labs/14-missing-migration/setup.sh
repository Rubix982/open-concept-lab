#!/usr/bin/env bash
# Starts production as it is today: Postgres with migration 001 only, and the v1
# app on localhost:8014. Re-run any time to reset (it wipes the database).
set -euo pipefail
cd "$(dirname "$0")"
docker compose down -v --remove-orphans >/dev/null 2>&1 || true
docker build -q -t opz-lab14-app:v1 app/v1 >/dev/null
docker compose up -d --wait db
docker compose run --rm migrate 001
APP_VERSION=v1 docker compose up -d --wait app
echo "Production is on v1: curl localhost:8014/users/1"
