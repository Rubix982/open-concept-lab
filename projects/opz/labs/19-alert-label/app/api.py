"""The orders API. Serves a few endpoints and Prometheus metrics on /metrics."""

import os
import random
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8019"))
STARTED = time.time()
requests_total = 0


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        global requests_total
        requests_total += 1
        if self.path == "/metrics":
            body = (
                "# HELP orders_requests_total Requests served.\n"
                "# TYPE orders_requests_total counter\n"
                f"orders_requests_total {requests_total}\n"
                "# HELP orders_queue_depth Orders waiting to be packed.\n"
                "# TYPE orders_queue_depth gauge\n"
                f"orders_queue_depth {random.randint(0, 12)}\n"
                "# HELP process_start_time_seconds Start time.\n"
                "# TYPE process_start_time_seconds gauge\n"
                f"process_start_time_seconds {STARTED}\n"
            ).encode()
        elif self.path == "/orders":
            body = b'{"orders": 1204}\n'
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
    print(f"orders API on :{PORT}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
