#!/usr/bin/env bash
# Builds the current app/ and asks it for the next 9 a.m. New York send time,
# from several fixed "now" instants (including both DST switches), in containers
# with different TZ settings. Passes only when every container gives the same,
# correct UTC instant, whatever the machine's own timezone says.
set -u
cd "$(dirname "$0")"
fail=0

docker build -q -t opz-lab12-scheduler app >/dev/null || { echo "build failed"; exit 1; }

# now (unix seconds) | what "now" is                   | correct next run (UTC)
cases="
1792929600|Sun 25 Oct 2026, 08:00 New York (EDT)|2026-10-25T13:00:00Z
1792933200|Sun 25 Oct 2026, 09:00 New York, just missed it|2026-10-26T13:00:00Z
1772913600|Sat 7 Mar 2026, 15:00 New York; clocks go forward overnight|2026-03-08T13:00:00Z
1793543400|Sun 1 Nov 2026, 09:30 New York; clocks went back last night|2026-11-02T14:00:00Z
"

for tz in UTC America/New_York Asia/Karachi America/Los_Angeles; do
  bad=0
  while IFS='|' read -r t what want; do
    [ -z "$t" ] && continue
    got=$(docker run --rm -e TZ="$tz" -e FAKE_NOW="$t" opz-lab12-scheduler 2>&1 | tail -1)
    if [ "$got" != "$want" ]; then
      [ $bad = 0 ] && printf 'FAIL  TZ=%-20s\n' "$tz"
      echo "        $what: got $got, want $want"
      bad=1
    fi
  done <<< "$cases"
  if [ $bad = 0 ]; then printf 'pass  TZ=%-20s all 4 runs at the right instant\n' "$tz"; else fail=1; fi
done

[ "$fail" = 0 ] && echo "LAB PASSED" || echo "lab not passed yet"
exit $fail
