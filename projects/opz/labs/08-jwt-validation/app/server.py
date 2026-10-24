"""Orders API. Every request needs "Authorization: Bearer <token>".

    GET /me              who the token says you are
    GET /admin/refunds   issue refunds; needs role "admin"
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from auth import InvalidToken, decode

PORT = int(os.environ.get("PORT", "8088"))


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            self._send(401, {"error": "missing token"})
            return
        try:
            claims = decode(auth.removeprefix("Bearer "))
        except InvalidToken as e:
            self._send(401, {"error": str(e)})
            return

        if self.path == "/me":
            self._send(200, {"sub": claims.get("sub"), "role": claims.get("role")})
        elif self.path == "/admin/refunds":
            if claims.get("role") != "admin":
                self._send(403, {"error": "admins only"})
                return
            self._send(200, {"refunded": ["ord_1001", "ord_1002"], "by": claims.get("sub")})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"GET {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


if __name__ == "__main__":
    print(f"orders API on 127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
