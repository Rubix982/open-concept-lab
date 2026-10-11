"""The same tiny service as Lab 01, now run with Docker Compose."""
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


def load_token() -> str:
    # The token arrives as a mounted file; the environment only holds its path.
    path = os.environ.get("API_TOKEN_FILE", "/run/secrets/api_token")
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        ok = bool(load_token())
        self.send_response(200 if ok else 503)
        self.end_headers()
        self.wfile.write(b"ready\n" if ok else b"no API_TOKEN\n")


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
