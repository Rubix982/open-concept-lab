#!/usr/bin/env bash
cd "$(dirname "$0")"
docker compose -p opz-lab13 down >/dev/null 2>&1
OPZ_PORT=18013 docker compose -p opz-lab13-check down >/dev/null 2>&1
docker rm -f opz-lab13-nopw opz-lab13-weak >/dev/null 2>&1
docker rmi opz-lab13-opsboard >/dev/null 2>&1
echo "removed"
