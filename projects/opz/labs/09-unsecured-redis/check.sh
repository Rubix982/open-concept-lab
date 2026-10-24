#!/usr/bin/env bash
# Checks the running stack (./setup.sh first). Passes only when Redis can't be
# reached from outside the app's network, refuses unauthenticated clients on the
# inside, and the app still works through it.
set -u
cd "$(dirname "$0")"
fail=0
CLI="docker run --rm redis:7.4-alpine redis-cli"

docker inspect opz-lab09-redis >/dev/null 2>&1 || { echo "Redis container opz-lab09-redis isn't running: ./setup.sh"; exit 1; }

# 1. From outside: a container on no shared network, aimed at the host.
reply=$($CLI -h host.docker.internal -p 6309 PING 2>&1 | tr -d '\r')
if [ "$reply" = PONG ]; then echo "FAIL  reachable from outside the app network (host port 6309 answered PONG)"; fail=1
else echo "pass  not reachable from outside the app network"; fi
ports=$(docker port opz-lab09-redis 2>/dev/null)
if [ -n "$ports" ]; then echo "FAIL  Redis still publishes a host port: $ports"; fail=1
else echo "pass  no host ports published for Redis"; fi

# 2. From inside the app's own network, with no credentials.
net=$(docker inspect -f '{{range $k, $v := .NetworkSettings.Networks}}{{$k}} {{end}}' opz-lab09-redis | awk '{print $1}')
reply=$(docker run --rm --network "$net" redis:7.4-alpine redis-cli -h opz-lab09-redis PING 2>&1 | tr -d '\r')
case "$reply" in
  PONG) echo "FAIL  unauthenticated client on the app network got PONG"; fail=1 ;;
  *NOAUTH*|*WRONGPASS*|*"Authentication required"*) echo "pass  unauthenticated client refused ($reply)" ;;
  *) echo "FAIL  couldn't test auth on the app network: $reply"; fail=1 ;;
esac

# 3. The app still works.
a=$(curl -fs localhost:8009/visit); b=$(curl -fs localhost:8009/login)
if [[ $a == *visits* && $b == *session* ]]; then echo "pass  app still reads and writes Redis"
else echo "FAIL  app broken: /visit -> ${a:-no answer}, /login -> ${b:-no answer}"; fail=1; fi

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
