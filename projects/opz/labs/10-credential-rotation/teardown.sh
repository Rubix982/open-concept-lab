#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose down --remove-orphans >/dev/null 2>&1
docker compose -p opz-lab10-check down --remove-orphans >/dev/null 2>&1
docker rmi opz-lab10-app >/dev/null 2>&1
echo "removed"
