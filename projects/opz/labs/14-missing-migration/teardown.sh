#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose down -v --remove-orphans
COMPOSE_PROJECT_NAME=opz-lab14-check docker compose down -v --remove-orphans 2>/dev/null
docker rmi opz-lab14-app:v1 opz-lab14-app:v2 2>/dev/null
echo removed
