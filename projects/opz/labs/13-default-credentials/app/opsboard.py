"""Opsboard: an admin dashboard for the ops team (pretend it's a vendor image).

Vendor docs: "Log in with admin / admin, then change the password." Nobody did.

    POST /login   {"username": ..., "password": ...}  -> 200 {"session": ...} or 401
    GET  /        dashboard summary (needs "Authorization: Bearer <session>")
"""

import hmac
import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8000"))
ADMIN_USER = os.environ.get("ADMIN_USER", "admin")


def load_password() -> str:
    path = os.environ.get("ADMIN_PASSWORD_FILE")
    if path:
        with open(path) as f:
            return f.read().strip()
    password = os.environ.get("ADMIN_PASSWORD")
    if password:
        return password
    print("warning: no admin password configured, using the default", flush=True)
    return "admin"


ADMIN_PASSWORD = load_password()
sessions: set[str] = set()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        if self.path != "/login":
            self._send(404, {"error": "not found"})
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
            user, password = str(body["username"]), str(body["password"])
        except (ValueError, KeyError):
            self._send(400, {"error": "send username and password"})
            return
        ok_user = hmac.compare_digest(user.encode(), ADMIN_USER.encode())
        ok_pass = hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
        if not (ok_user and ok_pass):
            self._send(401, {"error": "bad credentials"})
            return
        session = secrets.token_urlsafe(24)
        sessions.add(session)
        self._send(200, {"session": session})

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send(200, {"ok": True})
            return
        if self.path != "/":
            self._send(404, {"error": "not found"})
            return
        if self.headers.get("Authorization", "").removeprefix("Bearer ") not in sessions:
            self._send(401, {"error": "log in first"})
            return
        self._send(200, {"servers": 14, "alerts": 2, "can": ["restart", "deploy", "read secrets"]})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"opsboard on :{PORT}, admin user {ADMIN_USER!r}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
