"""A small service that refuses to start with bad config."""
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

VALID_MODES = {"prod", "dev"}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} {fmt % args}", flush=True)


if __name__ == "__main__":
    mode = os.environ.get("APP_MODE", "")
    if mode not in VALID_MODES:
        print(f"fatal: APP_MODE={mode!r} is not one of {sorted(VALID_MODES)}", flush=True)
        sys.exit(1)
    port = int(os.environ.get("PORT", "8080"))
    print(f"starting in {mode} mode on :{port}", flush=True)
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
