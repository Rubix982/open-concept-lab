#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose down -v --remove-orphans && echo "removed"
