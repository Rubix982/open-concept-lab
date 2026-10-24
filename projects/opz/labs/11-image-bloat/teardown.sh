#!/usr/bin/env bash
docker rm -f opz-lab11 opz-lab11-check >/dev/null 2>&1
docker rmi opz-lab11-sales opz-lab11-verify opz-lab11-check >/dev/null 2>&1
echo "removed (the build cache stays; 'docker builder prune' clears it)"
