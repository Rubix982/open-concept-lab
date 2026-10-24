"""Orders API behind NGINX. POST /api/orders takes a JSON order.

Fine for normal traffic. Someone has started sending it very unusual requests.
"""

import json
import os
import resource
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8000"))


def count_items(node: object) -> int:
    """How many line items, however the client nested its bundles."""
    if isinstance(node, list):
        return sum(count_items(x) for x in node)
    if isinstance(node, dict):
        return 1 + sum(count_items(v) for v in node.values() if isinstance(v, (list, dict)))
    return 0


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send(200, {"ok": True})
        elif self.path == "/stats":
            # ru_maxrss is in KB on Linux: the most memory this process has ever used
            peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024
            self._send(200, {"peak_rss_mb": peak_mb, "pid": os.getpid()})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/api/orders":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        order = json.loads(raw)
        self._send(200, {"accepted": True, "items": count_items(order.get("items", []))})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"orders API on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
