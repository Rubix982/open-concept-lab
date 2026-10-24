#!/usr/bin/env bash
# Creates ./secrets from secrets.example/ (resetting any rotations) and starts
# the stack: db, orders, billing, reports, and a status page on localhost:8010.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p secrets
cp secrets.example/db_password.txt secrets.example/db_valid_passwords.txt secrets/
docker compose up -d --build --force-recreate
for _ in $(seq 1 30); do curl -fs localhost:8010 >/dev/null 2>&1 && break; sleep 0.5; done
echo "Status: $(curl -s localhost:8010)"
