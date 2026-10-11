#!/usr/bin/env bash
# Passes only when the image carries no trace of the secret AND the service
# still works when the token is supplied at run time.
set -uo pipefail
cd "$(dirname "$0")"
SECRET="sk-lab01"
IMG="opz-lab01:check"
fail=0

docker build -q -t "$IMG" app >/dev/null || { echo "build failed"; exit 1; }

if docker history --no-trunc "$IMG" | grep -q "$SECRET"; then
  echo "FAIL  secret visible in image history (docker history --no-trunc)"; fail=1
else echo "pass  history clean"; fi

if docker inspect "$IMG" --format '{{json .Config.Env}}' | grep -q "$SECRET"; then
  echo "FAIL  secret in image config env (docker inspect)"; fail=1
else echo "pass  config env clean"; fi

tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
docker save "$IMG" -o "$tmp/img.tar" && tar -xf "$tmp/img.tar" -C "$tmp"
found=0
while IFS= read -r f; do
  if gzip -t "$f" 2>/dev/null; then gzip -dc "$f" | grep -aq "$SECRET" && found=1
  else grep -aq "$SECRET" "$f" && found=1; fi
done < <(find "$tmp" -type f ! -name img.tar)
if [ "$found" = 1 ]; then
  echo "FAIL  secret in a filesystem layer (deleting a file later does not remove it)"; fail=1
else echo "pass  layers clean"; fi

cid=$(docker run -d -p 18080:8080 -e API_TOKEN=runtime-token "$IMG")
sleep 2
if curl -fs localhost:18080 >/dev/null; then echo "pass  service works with a run-time token"
else echo "FAIL  service doesn't come up ready when given API_TOKEN at run time"; fail=1; fi
docker rm -f "$cid" >/dev/null

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
