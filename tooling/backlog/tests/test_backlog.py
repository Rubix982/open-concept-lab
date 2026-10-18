"""Run from tooling/backlog:  python3 -m unittest discover -s tests -v"""
import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bl import cli, store  # noqa: E402
from bl.server import make_server  # noqa: E402
from bl.store import Backlog, BacklogError  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def run(*args, cwd):
    """Run the CLI in `cwd`; return (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(args))
    finally:
        os.chdir(old)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.realpath(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def raw(self):
        with open(os.path.join(self.dir, ".backlog", "backlog.json")) as f:
            return json.load(f)


class TestInitAndFind(Base):
    def test_init_creates_file_with_defaults(self):
        code, out, _ = run("init", "My project", cwd=self.dir)
        self.assertEqual(code, 0)
        d = self.raw()
        self.assertEqual(d["config"]["name"], "My project")
        self.assertEqual([k["prefix"] for k in d["config"]["kinds"]], ["EP", "ST", "TK"])
        self.assertIn("blocked", d["config"]["statuses"])
        self.assertEqual(d["items"], {})

    def test_init_twice_fails(self):
        run("init", cwd=self.dir)
        code, _, err = run("init", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("already", err)

    def test_custom_kinds_and_statuses(self):
        run("init", "--kinds", "goal:G,step:S", "--statuses", "open,wip,shipped", cwd=self.dir)
        bl = Backlog(self.dir)
        self.assertEqual(bl.kinds(), ["goal", "step"])
        with bl.edit():
            g = bl.add("goal", "A goal")
            s = bl.add("step", "A step", parent=g, status="wip")
        self.assertEqual((g, s), ("G-1", "S-1"))
        self.assertEqual(bl.config["done"], ["shipped"])

    def test_find_root_walks_up(self):
        run("init", cwd=self.dir)
        deep = os.path.join(self.dir, "a", "b", "c")
        os.makedirs(deep)
        self.assertEqual(store.find_root(deep), self.dir)
        code, out, _ = run("add", "epic", "From deep inside", cwd=deep)
        self.assertEqual((code, out.strip()), (0, "EP-1"))

    def test_no_backlog_is_a_clear_error(self):
        code, _, err = run("tree", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("bl init", err)


class TestItems(Base):
    def setUp(self):
        super().setUp()
        run("init", "T", cwd=self.dir)
        run("add", "epic", "Epic one", cwd=self.dir)
        run("add", "story", "Story one", "-p", "EP-1", "-l", "ui,Core", "-o", "ana", cwd=self.dir)
        run("add", "task", "Task one", "-p", "ST-1", "-n", "first note", cwd=self.dir)

    def test_add_fields(self):
        it = self.raw()["items"]["ST-1"]
        self.assertEqual(it["labels"], ["ui", "core"])
        self.assertEqual(it["owner"], "ana")
        self.assertEqual(it["status"], "todo")
        tk = self.raw()["items"]["TK-1"]
        self.assertTrue(tk["notes"][0].endswith(": first note"))
        self.assertRegex(tk["notes"][0], r"^\d{4}-\d{2}-\d{2}: ")

    def test_parent_rules(self):
        code, _, err = run("add", "task", "Orphan", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("needs a parent story", err)
        code, _, err = run("add", "task", "Wrong level", "-p", "EP-1", cwd=self.dir)
        self.assertEqual(code, 1)
        code, _, err = run("add", "epic", "Top", "-p", "EP-1", cwd=self.dir)
        self.assertEqual(code, 1)
        code, _, err = run("set", "TK-1", "-p", "EP-1", cwd=self.dir)
        self.assertEqual(code, 1)

    def test_move(self):
        run("add", "story", "Story two", "-p", "EP-1", cwd=self.dir)
        code, _, _ = run("set", "TK-1", "-p", "ST-2", cwd=self.dir)
        self.assertEqual(code, 0)
        self.assertEqual(self.raw()["items"]["TK-1"]["parent"], "ST-2")

    def test_set_and_notes_append(self):
        run("set", "TK-1", "-s", "doing", "-n", "second", "-t", "Renamed", "-l", "x", cwd=self.dir)
        it = self.raw()["items"]["TK-1"]
        self.assertEqual((it["status"], it["title"], it["labels"]), ("doing", "Renamed", ["x"]))
        self.assertEqual(len(it["notes"]), 2)
        self.assertTrue(it["notes"][1].endswith("second"))
        run("set", "TK-1", "--unlabel", "x", "-o", "", cwd=self.dir)
        it = self.raw()["items"]["TK-1"]
        self.assertEqual((it["labels"], it["owner"]), ([], None))

    def test_bad_status(self):
        code, _, err = run("set", "TK-1", "-s", "finished", cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("unknown status", err)

    def test_links_both_ways_and_blockers(self):
        run("add", "story", "Story two", "-p", "EP-1", cwd=self.dir)
        run("set", "ST-1", "--link", "ST-2", "-b", "ST-2", cwd=self.dir)
        items = self.raw()["items"]
        self.assertEqual(items["ST-1"]["links"], ["ST-2"])
        self.assertEqual(items["ST-2"]["links"], ["ST-1"])
        self.assertEqual(items["ST-1"]["blocked_by"], ["ST-2"])
        run("set", "ST-2", "--unlink", "ST-1", cwd=self.dir)
        run("set", "ST-1", "--unblock", "ST-2", cwd=self.dir)
        items = self.raw()["items"]
        self.assertEqual((items["ST-1"]["links"], items["ST-2"]["links"], items["ST-1"]["blocked_by"]), ([], [], []))
        code, _, _ = run("set", "ST-1", "--link", "ST-1", cwd=self.dir)
        self.assertEqual(code, 1)
        code, _, _ = run("set", "ST-1", "--link", "ST-99", cwd=self.dir)
        self.assertEqual(code, 1)

    def test_ids_never_reused(self):
        d = self.raw()
        del d["items"]["TK-1"]  # someone deletes an item by hand
        with open(os.path.join(self.dir, ".backlog", "backlog.json"), "w") as f:
            json.dump(d, f)
        _, out, _ = run("add", "task", "Another", "-p", "ST-1", cwd=self.dir)
        self.assertEqual(out.strip(), "TK-2")

    def test_progress_and_views(self):
        run("add", "task", "Task two", "-p", "ST-1", "-s", "done", cwd=self.dir)
        run("add", "task", "Task three", "-p", "ST-1", "-s", "dropped", cwd=self.dir)
        bl = Backlog(self.dir)
        self.assertEqual(bl.progress("EP-1"), (1, 2))
        _, out, _ = run("tree", cwd=self.dir)
        self.assertIn("1/2", out)
        _, out, _ = run("tree", "--open", cwd=self.dir)
        self.assertNotIn("Task two", out)
        _, out, _ = run("ls", "--label", "ui", cwd=self.dir)
        self.assertIn("ST-1", out)
        self.assertNotIn("TK-1", out)
        _, out, _ = run("ls", "first", cwd=self.dir)
        self.assertIn("TK-1", out)
        _, out, _ = run("next", cwd=self.dir)
        self.assertIn("TK-1", out)
        _, out, _ = run("show", "tk-1", "--json", cwd=self.dir)
        self.assertEqual(json.loads(out)["id"], "TK-1")

    def test_file_is_readable_and_stable(self):
        path = os.path.join(self.dir, ".backlog", "backlog.json")
        text = read(path)
        self.assertLess(text.index('"EP-1"'), text.index('"ST-1"'))
        self.assertLess(text.index('"ST-1"'), text.index('"TK-1"'))
        bl = Backlog(self.dir)
        self.assertEqual(store.dumps(bl.data), text)  # writing again changes nothing

    def test_board_export(self):
        code, out, _ = run("board", "--no-open", cwd=self.dir)
        self.assertEqual(code, 0)
        html = read(os.path.join(self.dir, ".backlog", "board.html"))
        self.assertIn('"mode": "static"', html)
        self.assertIn("Story one", html)
        self.assertNotIn("/*BOOT*/", html)
        self.assertIn('"refBase": "../"', html)


class TestImport(Base):
    JANAAN = {
        "next": {"EP": 3, "ST": 5, "TK": 2},
        "items": {
            "EP-1": {"id": "EP-1", "kind": "epic", "title": "Critic", "parent": None, "status": "doing", "owner": None,
                     "created": "2026-10-01", "updated": "2026-10-02", "notes": ["2026-10-01: hi"], "refs": [],
                     "blocked_by": []},
            "ST-4": {"id": "ST-4", "kind": "story", "title": "Standard", "parent": "EP-1", "status": "done",
                     "owner": "claude", "created": "2026-10-01", "updated": "2026-10-01", "notes": [],
                     "refs": ["docs/standard.md"], "blocked_by": [], "links": ["TK-1"]},
            "TK-1": {"id": "TK-1", "kind": "task", "title": "Write it", "parent": "ST-4", "status": "todo",
                     "owner": None, "created": "2026-10-01", "updated": "2026-10-01", "notes": [], "refs": [],
                     "blocked_by": ["ST-4"], "links": ["ST-4"]},
        },
    }

    def src(self):
        p = os.path.join(self.dir, "old.json")
        with open(p, "w") as f:
            json.dump(self.JANAAN, f)
        return p

    def test_import_into_empty_keeps_ids(self):
        run("init", cwd=self.dir)
        code, out, _ = run("import", self.src(), cwd=self.dir)
        self.assertEqual(code, 0, out)
        d = self.raw()
        self.assertEqual(set(d["items"]), {"EP-1", "ST-4", "TK-1"})
        self.assertEqual(d["items"]["TK-1"]["labels"], [])
        self.assertEqual(d["items"]["EP-1"]["links"], [])
        self.assertEqual(d["next"], {"EP": 3, "ST": 5, "TK": 2})
        _, out, _ = run("add", "story", "New", "-p", "EP-1", cwd=self.dir)
        self.assertEqual(out.strip(), "ST-5")

    def test_import_into_nonempty_renumbers_and_rewires(self):
        run("init", cwd=self.dir)
        run("add", "epic", "Existing", cwd=self.dir)
        run("import", self.src(), cwd=self.dir)
        d = self.raw()["items"]
        self.assertEqual(d["EP-2"]["title"], "Critic")
        self.assertEqual(d["ST-1"]["parent"], "EP-2")
        self.assertEqual(d["TK-1"]["parent"], "ST-1")
        self.assertEqual(d["TK-1"]["blocked_by"], ["ST-1"])
        self.assertEqual(d["ST-1"]["links"], ["TK-1"])
        self.assertIn("imported from old.json as ST-4", d["ST-1"]["notes"][-1])

    def test_import_unknown_kind_fails(self):
        run("init", "--kinds", "goal:G", cwd=self.dir)
        code, _, err = run("import", self.src(), cwd=self.dir)
        self.assertEqual(code, 1)
        self.assertIn("kind", err)


class TestServer(Base):
    def setUp(self):
        super().setUp()
        run("init", "Served", cwd=self.dir)
        run("add", "epic", "E", cwd=self.dir)
        run("add", "story", "S", "-p", "EP-1", cwd=self.dir)
        with open(os.path.join(self.dir, "notes.md"), "w") as f:
            f.write("hello")
        self.srv = make_server(Backlog(self.dir), 0)
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def get(self, path):
        with urllib.request.urlopen(self.url + path) as r:
            return r.status, r.read().decode()

    def post(self, path, body, headers=None):
        req = urllib.request.Request(self.url + path, data=json.dumps(body).encode(), method="POST",
                                     headers=dict({"Content-Type": "application/json"}, **(headers or {})))
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            with e:
                return e.code, json.loads(e.read())

    def test_page_and_state(self):
        code, html = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn('"mode": "live"', html)
        code, body = self.get("/api/backlog")
        self.assertEqual(json.loads(body)["data"]["items"]["ST-1"]["title"], "S")

    def test_edit_round_trip(self):
        code, body = self.post("/api/set", {"id": "ST-1", "status": "doing", "title": "S2", "labels": ["a", "b"],
                                            "note": "from the browser"})
        self.assertEqual(code, 200, body)
        it = self.raw()["items"]["ST-1"]
        self.assertEqual((it["status"], it["title"], it["labels"]), ("doing", "S2", ["a", "b"]))
        self.assertTrue(it["notes"][-1].endswith("from the browser"))
        code, body = self.post("/api/add", {"kind": "task", "title": "T", "parent": "ST-1"})
        self.assertEqual((code, body["id"]), (200, "TK-1"))
        code, body = self.post("/api/set", {"id": "TK-1", "link": "EP-1", "blocked_by": "ST-1"})
        self.assertEqual(self.raw()["items"]["EP-1"]["links"], ["TK-1"])

    def test_cli_edit_between_browser_edits_is_kept(self):
        _, before = self.get("/api/version")
        run("set", "ST-1", "-o", "cli-user", cwd=self.dir)
        _, after = self.get("/api/version")
        self.assertNotEqual(before, after)
        self.post("/api/set", {"id": "ST-1", "status": "review"})
        it = self.raw()["items"]["ST-1"]
        self.assertEqual((it["owner"], it["status"]), ("cli-user", "review"))

    def test_errors_and_guards(self):
        code, body = self.post("/api/add", {"kind": "task", "title": "orphan"})
        self.assertEqual(code, 400)
        self.assertIn("parent", body["error"])
        code, body = self.post("/api/set", {"id": "ST-1", "status": "x"})
        self.assertEqual(code, 400)
        code, _ = self.post("/api/set", {"id": "ST-1", "status": "done"}, {"Origin": "http://evil.example"})
        self.assertEqual(code, 403)
        self.assertEqual(self.raw()["items"]["ST-1"]["status"], "todo")

    def test_files(self):
        code, body = self.get("/files/notes.md")
        self.assertEqual((code, body), (200, "hello"))
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/files/../../etc/passwd")
        cm.exception.close()
        self.assertIn(cm.exception.code, (403, 404))


if __name__ == "__main__":
    unittest.main()
