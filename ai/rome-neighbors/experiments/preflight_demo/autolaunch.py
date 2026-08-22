"""
Auto-launch the preflight demo when NDIF recovers.

NDIF is intermittently degraded. This probes with one cheap trace every
PROBE_EVERY seconds; the moment a probe succeeds, it runs the demo (which is
checkpointed, so it resumes from disk). Bounded by MAX_WAIT so it never spins
forever. Safe to run in the background.

Usage:
    python experiments/preflight_demo/autolaunch.py
"""

import subprocess
import sys
import time
from pathlib import Path

from ripplekit import reps

PROBE_EVERY = 180      # seconds between health probes
MAX_WAIT = 3 * 3600    # give up after 3h
HERE = Path(__file__).resolve().parent


t0 = time.time()
attempt = 0
while time.time() - t0 < MAX_WAIT:
    attempt += 1
    print(f"[{time.strftime('%H:%M:%S')}] probe #{attempt} ...", flush=True)
    if reps.probe_once(timeout=20):   # single bounded attempt (no 5x retries)
        print("NDIF healthy → launching demo run", flush=True)
        rc = subprocess.call([sys.executable, str(HERE / "run.py")])
        print(f"demo run exited rc={rc}", flush=True)
        sys.exit(rc)
    time.sleep(PROBE_EVERY)

print("gave up — NDIF still degraded after MAX_WAIT", flush=True)
sys.exit(2)
