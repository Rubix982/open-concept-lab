"""A tiny service that needs an API token to talk to an upstream."""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        token = os.environ.get("API_TOKEN", "")
        ok = bool(token)
        self.send_response(200 if ok else 503)
        self.end_headers()
        self.wfile.write(b"ready\n" if ok else b"no API_TOKEN\n")


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
