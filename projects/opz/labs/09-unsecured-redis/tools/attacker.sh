#!/usr/bin/env bash
# What someone on your network sees. Runs redis-cli from a throwaway container
# that is NOT on the app's network, aimed at your machine's published port.
# Usage: tools/attacker.sh [redis command...]     default: KEYS *
args=("$@"); [ ${#args[@]} -eq 0 ] && args=(KEYS '*')
docker run --rm redis:7.4-alpine redis-cli -h host.docker.internal -p 6309 "${args[@]}"
