"""Load test: asks for 40 different reports, three times over. Runs as a Job in the cluster."""

import sys
import time
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://report:8080"
failures = 0
for rnd in range(3):
    for i in range(40):
        try:
            urllib.request.urlopen(f"{BASE}/report?id={i}", timeout=10).read()
        except Exception as e:  # a killed pod shows up here as a refused/reset connection
            failures += 1
            print(f"round {rnd} report {i}: {e}", flush=True)
            time.sleep(1)
print(f"done: {failures} failed requests", flush=True)
