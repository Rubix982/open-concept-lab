"""Status page: asks each service for /health and shows the answers.

    curl -s localhost:8010     ->  {"orders": 200, "billing": 200, "reports": 200}
"""

import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICES = ["orders", "billing", "reports"]


def probe(name: str) -> int:
    try:
        with urllib.request.urlopen(f"http://{name}:8000/health", timeout=3) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError:
        return 0  # not reachable


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = (json.dumps({s: probe(s) for s in SERVICES}) + "\n").encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8010), Handler).serve_forever()
