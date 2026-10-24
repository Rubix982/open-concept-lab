"""Sales summary service. GET /summary returns totals per region."""

import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pandas as pd

PORT = int(os.environ.get("PORT", "8011"))

SALES = """region,month,amount
north,2026-07,1200
north,2026-08,1350
south,2026-07,980
south,2026-08,1105
west,2026-07,1500
west,2026-08,1420
"""


def summary() -> dict:
    df = pd.read_csv(io.StringIO(SALES))
    return {k: int(v) for k, v in df.groupby("region")["amount"].sum().items()}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            body = b"ok\n"
        elif self.path == "/summary":
            body = (json.dumps(summary()) + "\n").encode()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    print(f"sales summary on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
