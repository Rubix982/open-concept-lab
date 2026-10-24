"""Public product-search API.

Every search queries the database, and the database has 4 connections. When all
4 are busy, requests wait in line for one, whoever sent them.
"""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB_CONNECTIONS = threading.BoundedSemaphore(4)
QUERY_SECONDS = 0.025


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            body = b'{"ok": true}'
        elif self.path.startswith("/search"):
            with DB_CONNECTIONS:          # wait for a free connection
                time.sleep(QUERY_SECONDS)  # the query
            body = json.dumps({"results": ["blue kettle", "green kettle"]}).encode()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        pass  # nginx logs every request already


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
    server.request_queue_size = 256
    print("search API on :8080", flush=True)
    server.serve_forever()
