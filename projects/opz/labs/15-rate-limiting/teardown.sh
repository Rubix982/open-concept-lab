#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose down --remove-orphans
COMPOSE_PROJECT_NAME=opz-lab15-check docker compose down --remove-orphans 2>/dev/null
docker rmi opz-lab15-api 2>/dev/null
echo removed
