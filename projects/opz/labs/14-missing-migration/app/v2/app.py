"""Users service, v2: users now have a timezone.

    GET  /healthz       {"version": "v1"}
    GET  /users/<id>    one user
    POST /users         {"name": ..., "email": ..., "timezone": ...}
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psycopg

VERSION = "v2"
DB = os.environ["DATABASE_URL"]


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send(200, {"version": VERSION})
            return
        if not self.path.startswith("/users/"):
            self._send(404, {"error": "not found"})
            return
        try:
            with psycopg.connect(DB) as conn:
                row = conn.execute(
                    "SELECT id, name, email, timezone FROM users WHERE id = %s",
                    (int(self.path.rsplit("/", 1)[1]),),
                ).fetchone()
        except Exception as e:
            self._send(500, {"error": str(e).strip()})
            return
        if row is None:
            self._send(404, {"error": "no such user"})
        else:
            self._send(200, {"id": row[0], "name": row[1], "email": row[2], "timezone": row[3]})

    def do_POST(self) -> None:
        if self.path != "/users":
            self._send(404, {"error": "not found"})
            return
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"{}")
        try:
            with psycopg.connect(DB) as conn:
                (new_id,) = conn.execute(
                    "INSERT INTO users (name, email, timezone) VALUES (%s, %s, %s) RETURNING id",
                    (body.get("name", "anon"), body.get("email", "anon@example.com"), body.get("timezone", "UTC")),
                ).fetchone()
        except Exception as e:
            self._send(500, {"error": str(e).strip()})
            return
        self._send(201, {"id": new_id})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{VERSION} {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"users service {VERSION} on :8080", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
