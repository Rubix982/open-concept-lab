#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose down --remove-orphans >/dev/null 2>&1
LAB16_PROJECT=opz-lab16-check docker compose down --remove-orphans >/dev/null 2>&1
docker rmi opz-lab16-app >/dev/null 2>&1
echo "removed"
