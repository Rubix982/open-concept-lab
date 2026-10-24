"""Report service. GET /report takes ~3 seconds to build a report.

Deploys stop this container and start a new one. Users say reports sometimes
fail halfway during deploys, and deploys are slow.
"""

import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8087"))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            body = b"ok\n"
        elif self.path == "/report":
            time.sleep(3)  # pretend to query and render
            body = b"report: 1,204 orders, 3 refunds\n"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"report service on :{PORT} (pid {os.getpid()})", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
