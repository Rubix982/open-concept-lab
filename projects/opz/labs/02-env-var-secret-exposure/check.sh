#!/usr/bin/env bash
# Passes only when the running service works AND the token can't be read from
# its metadata, its environment, the compose config, or the image.
set -uo pipefail
cd "$(dirname "$0")"
SECRET="sk-lab02"
fail=0
dc() { docker compose "$@"; }
trap 'dc down -v >/dev/null 2>&1' EXIT

dc up -d --build --wait >/dev/null 2>&1 || dc up -d --build >/dev/null || { echo "compose up failed"; exit 1; }
sleep 2
cid=$(dc ps -q api)

if curl -fs localhost:18082 >/dev/null; then echo "pass  service is ready"
else echo "FAIL  service isn't ready (does the app still find its token?)"; fail=1; fi

if docker inspect "$cid" | grep -q "$SECRET"; then
  echo "FAIL  token visible in container metadata (docker inspect <container>)"; fail=1
else echo "pass  container metadata clean"; fi

if docker exec "$cid" env | grep -q "$SECRET"; then
  echo "FAIL  token in the process environment (docker exec ... env, inherited by every child process)"; fail=1
else echo "pass  process environment clean"; fi

if dc config 2>/dev/null | grep -q "$SECRET"; then
  echo "FAIL  token printed by docker compose config"; fail=1
else echo "pass  compose config clean"; fi

img=$(docker inspect "$cid" --format '{{.Image}}')
if docker inspect "$img" | grep -q "$SECRET" || docker history --no-trunc "$img" | grep -q "$SECRET"; then
  echo "FAIL  token in the image (Lab 01 regression)"; fail=1
else echo "pass  image clean"; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
