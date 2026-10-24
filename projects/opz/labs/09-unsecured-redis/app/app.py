"""Visit counter and session store, backed by Redis.

    GET /visit   counts a visit, returns the total
    GET /login   creates a session token (stored in Redis) and returns it

Connection settings come from the environment:
    REDIS_HOST, REDIS_PORT          where Redis is
    REDIS_USERNAME                  optional ACL user
    REDIS_PASSWORD_FILE             optional path to a file holding the password
"""

import json
import os
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import redis

password = None
if path := os.environ.get("REDIS_PASSWORD_FILE"):
    with open(path) as f:
        password = f.read().strip()

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),
    port=int(os.environ.get("REDIS_PORT", "6379")),
    username=os.environ.get("REDIS_USERNAME") or None,
    password=password,
    decode_responses=True,
)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        try:
            if self.path == "/visit":
                self._send(200, {"visits": r.incr("visits")})
            elif self.path == "/login":
                token = "sess_FAKE_" + secrets.token_hex(12)
                r.setex(f"session:{token}", 3600, json.dumps({"user": "user_42", "role": "customer"}))
                self._send(200, {"session": token})
            else:
                self._send(404, {"error": "not found"})
        except redis.RedisError as e:
            self._send(503, {"error": f"redis: {e}"})


if __name__ == "__main__":
    print("app on :8009", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8009), Handler).serve_forever()
