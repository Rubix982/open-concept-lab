"""Accounts service. POST /signup and POST /login take form fields.

Every line it logs goes to logs/app.log, which the log shipper
(pipeline/ship.py) forwards to the central store that the security team
searches and alerts on.
"""

import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

PORT = int(os.environ.get("PORT", "8017"))
LOG_DIR = Path(os.environ.get("LOG_DIR", Path(__file__).resolve().parent.parent / "logs"))
LOG_DIR.mkdir(exist_ok=True)

handler = logging.FileHandler(LOG_DIR / "app.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
log = logging.getLogger("accounts")
log.addHandler(handler)
log.setLevel(logging.INFO)

users: dict[str, str] = {"admin": "FAKE-admin-password-lab17"}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, text: str) -> None:
        data = (text + "\n").encode()
        self.send_response(code)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode()).items()}
        username, password = form.get("username", ""), form.get("password", "")
        ip = self.client_address[0]

        if self.path == "/signup":
            if not username or username in users:
                log.warning(f"signup rejected user={username} ip={ip}")
                self._send(400, "username taken or empty")
                return
            users[username] = password
            log.info(f"signup user={username} ip={ip}")
            self._send(201, "welcome")
        elif self.path == "/login":
            if users.get(username) == password:
                log.info(f"login succeeded user={username} ip={ip}")
                self._send(200, "ok")
            else:
                log.warning(f"login failed user={username} ip={ip}")
                self._send(401, "nope")
        else:
            self._send(404, "not found")

    def log_message(self, fmt: str, *args: object) -> None:
        pass  # request lines aren't part of the audit log


if __name__ == "__main__":
    print(f"accounts service on 127.0.0.1:{PORT}, logging to {LOG_DIR / 'app.log'}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
