"""Shared bits for the three services: a tiny HTTP server and a db login."""

import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable

DB_URL = os.environ.get("DB_URL", "http://db:7000/auth")
PASSWORD_FILE = os.environ.get("DB_PASSWORD_FILE", "/run/secrets/db_password")


def read_password() -> str:
    with open(PASSWORD_FILE) as f:
        return f.read().strip()


def db_login(password: str) -> bool:
    req = urllib.request.Request(DB_URL, method="POST", headers={"X-Db-Password": password})
    try:
        with urllib.request.urlopen(req, timeout=3):
            return True
    except urllib.error.HTTPError:
        return False


def serve(name: str, health: Callable[[], bool]) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            ok = self.path == "/health" and health()
            self.send_response(200 if ok else 503)
            self.end_headers()
            self.wfile.write(f"{name}: {'ok' if ok else 'db login failed'}\n".encode())

        def log_message(self, fmt: str, *args: object) -> None:
            pass

    print(f"{name} listening on :8000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
