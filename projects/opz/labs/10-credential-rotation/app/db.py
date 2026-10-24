"""Stand-in for the database. It only does logins.

POST /auth with header "X-Db-Password". Accepted passwords live in
/run/db/valid_passwords.txt, one per line, re-read on every login, so the DBA
can add a new password and later revoke the old one without a restart.
"""

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VALID = Path(os.environ.get("VALID_PASSWORDS_FILE", "/run/db/valid_passwords.txt"))


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        given = self.headers.get("X-Db-Password", "")
        valid = {line.strip() for line in VALID.read_text().splitlines() if line.strip()}
        ok = given in valid
        self.send_response(200 if ok else 401)
        self.end_headers()
        self.wfile.write(b"ok\n" if ok else b"FATAL: password authentication failed\n")
        if not ok:
            print(f"login refused (password ending ...{given[-4:]})", flush=True)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    print("db listening on :7000", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 7000), Handler).serve_forever()
