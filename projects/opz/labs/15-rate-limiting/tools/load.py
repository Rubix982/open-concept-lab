"""Two customers at once: a scraper flooding the API, and Alice using it normally.

    python3 tools/load.py                         # 6 seconds against localhost:8015
    python3 tools/load.py http://127.0.0.1:18015 8

The scraper runs 40 threads in a tight loop with key "key_FAKE_scraper".
Alice sends 5 requests a second with key "key_FAKE_alice" and times each one.
Prints a summary per customer, and the last line is the same summary as JSON.
"""

import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8015"
SECONDS = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
stop = time.monotonic() + SECONDS

scraper: Counter[str] = Counter()
retry_after_seen: list[str] = []
alice_codes: Counter[str] = Counter()
alice_ms: list[float] = []
lock = threading.Lock()


def get(key: str) -> tuple[int, dict[str, str]]:
    req = urllib.request.Request(f"{BASE}/search?q=kettle", headers={"X-API-Key": key})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
            return resp.status, dict(resp.headers)
    except urllib.error.HTTPError as e:
        e.read()
        return e.code, dict(e.headers)
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        return 0, {}


def flood() -> None:
    while time.monotonic() < stop:
        code, headers = get("key_FAKE_scraper")
        with lock:
            scraper[str(code)] += 1
            if code == 429 and "Retry-After" in headers and len(retry_after_seen) < 1:
                retry_after_seen.append(headers["Retry-After"])


def alice() -> None:
    time.sleep(0.5)  # let the flood get going
    while time.monotonic() < stop:
        t0 = time.monotonic()
        code, _ = get("key_FAKE_alice")
        alice_ms.append((time.monotonic() - t0) * 1000)
        alice_codes[str(code)] += 1
        time.sleep(max(0.0, 0.2 - (time.monotonic() - t0)))


threads = [threading.Thread(target=flood) for _ in range(40)] + [threading.Thread(target=alice)]
for t in threads:
    t.start()
for t in threads:
    t.join()

total = sum(scraper.values())
p50 = statistics.median(alice_ms) if alice_ms else 0.0
p95 = statistics.quantiles(alice_ms, n=20)[-1] if len(alice_ms) >= 2 else p50
print(f"scraper: {total} requests, by status: {dict(scraper)}")
print(f"         Retry-After on 429: {retry_after_seen[0] if retry_after_seen else 'none seen'}")
print(f"alice:   {len(alice_ms)} requests, by status: {dict(alice_codes)}, p50 {p50:.0f} ms, p95 {p95:.0f} ms")
print(json.dumps({
    "scraper_total": total, "scraper_429": scraper["429"], "scraper_by_status": dict(scraper),
    "retry_after": retry_after_seen[0] if retry_after_seen else None,
    "alice_by_status": dict(alice_codes), "alice_p50_ms": round(p50, 1), "alice_p95_ms": round(p95, 1),
}))
