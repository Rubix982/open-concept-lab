"""Notes service: a tiny SQLite-backed API.

    POST /notes   body = the note text; stores it
    GET  /notes   all notes, oldest first
    POST /crash   simulates the process crashing (exits immediately)
"""

import json
import os
import socket
import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer

DB_PATH = os.environ.get("DB_PATH", "/app/data/notes.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
db.commit()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path == "/notes":
            rows = db.execute("SELECT text FROM notes ORDER BY id").fetchall()
            self._send(200, {"pod": socket.gethostname(), "db": DB_PATH, "notes": [r[0] for r in rows]})
        elif self.path == "/healthz":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path == "/crash":
            print("crashing on purpose", flush=True)
            os._exit(1)
        if self.path != "/notes":
            self._send(404, {"error": "not found"})
            return
        text = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode()
        db.execute("INSERT INTO notes (text) VALUES (?)", (text,))
        db.commit()
        self._send(201, {"stored": text})


if __name__ == "__main__":
    print(f"notes service on :8080, database at {DB_PATH}", flush=True)
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
