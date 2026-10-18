"""`bl serve`: the viewer with editing, on 127.0.0.1 only.

  GET  /                  the viewer (live mode)
  GET  /api/backlog       {"data": ..., "version": ...}
  GET  /api/version       {"version": ...}   (the page polls this to pick up CLI edits)
  POST /api/add           {"kind", "title", "parent"?, "status"?, "owner"?, "note"?, "labels"?}
  POST /api/set           {"id", "title"?, "status"?, "owner"?, "note"?, "parent"?, "labels"? (full list),
                           "link"?, "unlink"?, "blocked_by"?, "unblock"?, "ref"?, "unref"?}
  GET  /files/<path>      a file from the project, for refs

Every POST re-reads the file under a lock, applies one change and writes it back, so
an edit from the CLI in between is never lost. POSTs must be JSON from this origin.
"""
import http.server
import json
import mimetypes
import os
import threading
import urllib.parse
import webbrowser

from .render import page
from .store import BacklogError


def make_handler(bl):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "bl"

        def log_message(self, fmt, *args):  # quiet; errors still reach the client
            pass

        def send(self, code, body, ctype="application/json; charset=utf-8"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body, ensure_ascii=False)
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def state(self):
            return {"data": bl.data, "version": bl.version()}

        def do_GET(self):
            path = urllib.parse.urlparse(self.path).path
            if path in ("/", "/index.html"):
                bl.load()
                return self.send(200, page(bl, "live", "files/"), "text/html; charset=utf-8")
            if path == "/api/backlog":
                try:
                    bl.load()
                except BacklogError as e:
                    return self.send(500, {"error": str(e)})
                return self.send(200, self.state())
            if path == "/api/version":
                return self.send(200, {"version": bl.version()})
            if path.startswith("/files/"):
                return self.file(urllib.parse.unquote(path[len("/files/"):]))
            return self.send(404, {"error": "not found"})

        def file(self, rel):
            full = os.path.realpath(os.path.join(bl.root, rel))
            if not (full + os.sep).startswith(os.path.realpath(bl.root) + os.sep) or os.sep + ".git" in full:
                return self.send(403, {"error": "outside the project"})
            if os.path.isdir(full):
                names = sorted(os.listdir(full))
                links = "".join(f'<li><a href="{urllib.parse.quote(n)}{"/" if os.path.isdir(os.path.join(full, n)) else ""}">'
                                f'{n}</a></li>' for n in names)
                return self.send(200, f"<!doctype html><meta charset=utf-8><ul>{links}</ul>", "text/html; charset=utf-8")
            if not os.path.isfile(full):
                return self.send(404, {"error": f"no file {rel}"})
            ctype = mimetypes.guess_type(full)[0] or "text/plain"
            if ctype.startswith("text/") or ctype in ("application/json", "application/javascript"):
                ctype = ("text/plain" if ctype == "text/html" else ctype) + "; charset=utf-8"  # never run project HTML here
            with open(full, "rb") as f:
                self.send(200, f.read(), ctype)

        def do_POST(self):
            path = urllib.parse.urlparse(self.path).path
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            if origin and urllib.parse.urlparse(origin).netloc != host:
                return self.send(403, {"error": "cross-origin request refused"})
            if not (self.headers.get("Content-Type") or "").startswith("application/json"):
                return self.send(415, {"error": "send JSON"})
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                if not isinstance(body, dict):
                    raise ValueError("expected an object")
            except ValueError as e:
                return self.send(400, {"error": f"bad JSON: {e}"})
            try:
                with bl.edit():
                    if path == "/api/add":
                        iid = bl.add(body.get("kind"), body.get("title"), parent=body.get("parent"),
                                     status=body.get("status"), owner=body.get("owner"), note=body.get("note"),
                                     refs=one_or_many(body.get("ref")), labels=one_or_many(body.get("labels")))
                    elif path == "/api/set":
                        if not body.get("id"):
                            raise BacklogError("which item? (id missing)")
                        labels = body.get("labels")
                        iid = bl.set(body["id"], title=body.get("title"), status=body.get("status"),
                                     owner=body.get("owner"), note=body.get("note"), parent=body.get("parent"),
                                     refs=one_or_many(body.get("ref")), unref=one_or_many(body.get("unref")),
                                     links=one_or_many(body.get("link")), unlinks=one_or_many(body.get("unlink")),
                                     blocked_by=one_or_many(body.get("blocked_by")),
                                     unblock=one_or_many(body.get("unblock")),
                                     set_labels=one_or_many(labels) if labels is not None else None)
                    else:
                        raise LookupError
            except LookupError:
                return self.send(404, {"error": "not found"})
            except BacklogError as e:
                bl.load()
                return self.send(400, {"error": str(e)})
            return self.send(200, dict(self.state(), id=iid))

    return Handler


def one_or_many(v):
    if v is None or v == "":
        return []
    return [v] if isinstance(v, str) else list(v)


class Server(http.server.HTTPServer):
    """One request at a time: requests are tiny, and it keeps the shared backlog object simple."""
    allow_reuse_address = True


def make_server(bl, port=0):
    return Server(("127.0.0.1", port), make_handler(bl))


def serve(bl, port=8765, open_browser=True):
    try:
        srv = make_server(bl, port)
    except OSError:
        srv = make_server(bl, 0)  # the usual port is taken: pick a free one
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"Serving {bl.config.get('name')} at {url}  (editing {bl.path})", flush=True)
    print("Ctrl-C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.3, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        srv.server_close()
