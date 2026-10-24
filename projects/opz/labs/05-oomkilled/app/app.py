"""Report service. GET /report?id=N builds report N (slow) and caches it in memory.

    GET /report?id=N   a report (~6 MB), from cache if we've built it before
    GET /stats         memory use: current and peak RSS, cache size
    GET /healthz       liveness
"""

import json
import os
import resource
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

CACHE_ENTRIES = int(os.environ.get("CACHE_ENTRIES", "25"))
REPORT_BYTES = 6 * 1024 * 1024
cache: OrderedDict[int, bytes] = OrderedDict()


def build_report(report_id: int) -> bytes:
    line = f"report {report_id}: lots of rows\n".encode()
    return (line * (REPORT_BYTES // len(line) + 1))[:REPORT_BYTES]


def current_rss_mb() -> float:
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) / 1024
    return 0.0


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        url = urlparse(self.path)
        if url.path == "/healthz":
            self._send(200, b"ok\n", "text/plain")
        elif url.path == "/stats":
            peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB on Linux
            body = {"rss_mb": round(current_rss_mb(), 1), "peak_rss_mb": round(peak_mb, 1),
                    "cache_entries": len(cache), "cache_limit": CACHE_ENTRIES}
            self._send(200, json.dumps(body).encode(), "application/json")
        elif url.path == "/report":
            report_id = int(parse_qs(url.query).get("id", ["0"])[0])
            if report_id in cache:
                cache.move_to_end(report_id)
            else:
                cache[report_id] = build_report(report_id)
                while len(cache) > CACHE_ENTRIES:
                    cache.popitem(last=False)
            self._send(200, f"report {report_id}: {len(cache[report_id])} bytes\n".encode(), "text/plain")
        else:
            self._send(404, b"not found\n", "text/plain")

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    print(f"report service on :8080, cache up to {CACHE_ENTRIES} reports", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
