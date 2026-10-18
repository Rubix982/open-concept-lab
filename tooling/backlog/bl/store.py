"""The backlog file: finding it, reading it, changing it safely, writing it back.

Everything that changes the backlog goes through a `Backlog` method, so the CLI and
the web server follow the same rules. Writes happen under a file lock and through a
temporary file, so a CLI edit and a browser edit never overwrite each other.
"""
import contextlib
import datetime
import json
import os
import re
import tempfile

try:
    import fcntl
except ImportError:  # Windows: no advisory lock, the atomic rename still applies
    fcntl = None

DIRNAME = ".backlog"
FILENAME = "backlog.json"
VERSION = 1

DEFAULT_KINDS = [
    {"name": "epic", "prefix": "EP"},
    {"name": "story", "prefix": "ST"},
    {"name": "task", "prefix": "TK"},
]
DEFAULT_STATUSES = ["todo", "doing", "blocked", "review", "done", "parked", "dropped"]
DEFAULT_DONE = ["done"]
DEFAULT_IGNORED = ["dropped"]  # left out of progress counts
ITEM_LISTS = ("notes", "refs", "blocked_by", "links", "labels")


class BacklogError(Exception):
    """A user-facing problem: bad id, wrong parent, no backlog found."""


def today():
    return datetime.date.today().isoformat()


def find_root(start=None):
    """Walk up from `start` (default: cwd) to the folder that holds .backlog/backlog.json."""
    here = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isfile(os.path.join(here, DIRNAME, FILENAME)):
            return here
        up = os.path.dirname(here)
        if up == here:
            raise BacklogError("no backlog here or in any parent folder (run `bl init` to start one)")
        here = up


def id_key(iid):
    """Sort ids naturally: EP-2 before EP-10."""
    m = re.match(r"^(.*?)-(\d+)$", iid)
    return (m.group(1), int(m.group(2))) if m else (iid, 0)


def new_data(name, kinds=None, statuses=None):
    kinds = kinds or [dict(k) for k in DEFAULT_KINDS]
    statuses = statuses or list(DEFAULT_STATUSES)
    done = [s for s in DEFAULT_DONE if s in statuses] or [statuses[-1]]
    ignored = [s for s in DEFAULT_IGNORED if s in statuses]
    return {
        "version": VERSION,
        "config": {"name": name, "kinds": kinds, "statuses": statuses, "done": done, "ignored": ignored},
        "next": {k["prefix"]: 1 for k in kinds},
        "items": {},
    }


def _pretty(v, ind, expand=False):
    """JSON with sorted keys; short lists and small objects stay on one line."""
    one = json.dumps(v, sort_keys=True, ensure_ascii=False)
    if not isinstance(v, (dict, list)) or not v or (not expand and len(one) + ind <= 88 and (isinstance(v, list) or len(v) <= 3)):
        return one
    pad = " " * (ind + 2)
    if isinstance(v, list):
        body = ",\n".join(pad + _pretty(x, ind + 2) for x in v)
        return "[\n" + body + "\n" + " " * ind + "]"
    body = ",\n".join(f"{pad}{json.dumps(k, ensure_ascii=False)}: {_pretty(v[k], ind + 2)}" for k in sorted(v))
    return "{\n" + body + "\n" + " " * ind + "}"


def dumps(data):
    """Readable, diff-friendly JSON: sorted keys, items in id order, one item per block."""
    head = {k: v for k, v in data.items() if k != "items"}
    lines = ["{"]
    for k in sorted(head):
        lines.append(f"  {json.dumps(k)}: {_pretty(head[k], 2)},")
    items = data["items"]
    ids = sorted(items, key=lambda i: (kind_rank(data, items[i].get("kind")), id_key(i)))
    if not ids:
        lines.append('  "items": {}')
    else:
        lines.append('  "items": {')
        for n, iid in enumerate(ids):
            body = _pretty(items[iid], 4, expand=True)
            comma = "," if n < len(ids) - 1 else ""
            lines.append(("\n" if n else "") + f"    {json.dumps(iid)}: {body}{comma}")
        lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def kind_rank(data, kind):
    for n, k in enumerate(data["config"]["kinds"]):
        if k["name"] == kind:
            return n
    return 99


def init(folder, name=None, kinds=None, statuses=None):
    folder = os.path.abspath(folder)
    path = os.path.join(folder, DIRNAME, FILENAME)
    if os.path.exists(path):
        raise BacklogError(f"there is already a backlog at {path}")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = new_data(name or os.path.basename(folder), kinds, statuses)
    _write(path, data)
    return Backlog(folder)


def _write(path, data):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".backlog-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(dumps(data))
    os.replace(tmp, path)


class Backlog:
    """One project's backlog. Use `with bl.edit() as data:` for changes, or the helpers below."""

    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.dir = os.path.join(self.root, DIRNAME)
        self.path = os.path.join(self.dir, FILENAME)
        self.data = None
        self.load()

    @classmethod
    def find(cls, start=None):
        return cls(find_root(start))

    # ---- reading and writing -------------------------------------------------
    def load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            raise BacklogError(f"no backlog at {self.path}")
        except json.JSONDecodeError as e:
            raise BacklogError(f"{self.path} is not valid JSON: {e}")
        self._normalise()
        return self.data

    def version(self):
        """Changes whenever the file changes; the browser polls this."""
        try:
            st = os.stat(self.path)
            return f"{st.st_mtime_ns}-{st.st_size}"
        except FileNotFoundError:
            return "missing"

    @contextlib.contextmanager
    def edit(self):
        """Lock, reload the latest file, let the caller change it, write it back atomically."""
        with open(os.path.join(self.dir, ".lock"), "a") as lock:
            if fcntl:
                fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                self.load()
                yield self.data
                _write(self.path, self.data)
            finally:
                if fcntl:
                    fcntl.flock(lock, fcntl.LOCK_UN)

    def _normalise(self):
        d = self.data
        d.setdefault("version", VERSION)
        cfg = d.setdefault("config", {})
        cfg.setdefault("name", os.path.basename(self.root))
        cfg.setdefault("kinds", [dict(k) for k in DEFAULT_KINDS])
        cfg.setdefault("statuses", list(DEFAULT_STATUSES))
        cfg.setdefault("done", [s for s in DEFAULT_DONE if s in cfg["statuses"]])
        cfg.setdefault("ignored", [s for s in DEFAULT_IGNORED if s in cfg["statuses"]])
        d.setdefault("next", {})
        for k in cfg["kinds"]:
            d["next"].setdefault(k["prefix"], 1)
        d.setdefault("items", {})
        for it in d["items"].values():
            for key in ITEM_LISTS:
                it.setdefault(key, [])
            it.setdefault("owner", None)
            it.setdefault("parent", None)

    # ---- config helpers -----------------------------------------------------
    @property
    def config(self):
        return self.data["config"]

    @property
    def items(self):
        return self.data["items"]

    def kinds(self):
        return [k["name"] for k in self.config["kinds"]]

    def kind(self, name):
        for k in self.config["kinds"]:
            if k["name"] == name:
                return k
        raise BacklogError(f"unknown kind {name!r} (kinds: {', '.join(self.kinds())})")

    def parent_kind(self, kind):
        names = self.kinds()
        i = names.index(self.kind(kind)["name"])
        return names[i - 1] if i else None

    def child_kind(self, kind):
        names = self.kinds()
        i = names.index(self.kind(kind)["name"])
        return names[i + 1] if i + 1 < len(names) else None

    def get(self, iid):
        it = self.items.get(iid) or self.items.get(iid.upper())
        if not it:
            raise BacklogError(f"no such item {iid}")
        return it

    def check_status(self, status):
        if status not in self.config["statuses"]:
            raise BacklogError(f"unknown status {status!r} (statuses: {', '.join(self.config['statuses'])})")

    # ---- queries ------------------------------------------------------------
    def children(self, iid):
        return sorted((it for it in self.items.values() if it.get("parent") == iid), key=lambda it: id_key(it["id"]))

    def roots(self):
        return sorted((it for it in self.items.values() if not it.get("parent")),
                      key=lambda it: (kind_rank(self.data, it["kind"]), id_key(it["id"])))

    def chain(self, iid):
        out, it = [], self.get(iid)
        while it.get("parent") and it["parent"] in self.items:
            it = self.items[it["parent"]]
            out.insert(0, it)
        return out

    def top(self, iid):
        c = self.chain(iid)
        return c[0] if c else self.get(iid)

    def progress(self, iid):
        """(done, total) over an item's leaves; an item with no children counts itself."""
        kids = self.children(iid)
        if not kids:
            s = self.get(iid)["status"]
            if s in self.config["done"]:
                return 1, 1
            return (0, 0) if s in self.config["ignored"] else (0, 1)
        d = t = 0
        for k in kids:
            a, b = self.progress(k["id"])
            d, t = d + a, t + b
        return d, t

    def closed(self, it):
        return it["status"] in self.config["done"] or it["status"] in self.config["ignored"]

    # ---- changes (call inside `edit()`) --------------------------------------
    def add(self, kind, title, parent=None, status=None, owner=None, note=None, refs=(), labels=()):
        k = self.kind(kind)
        title = (title or "").strip()
        if not title:
            raise BacklogError("an item needs a title")
        want = self.parent_kind(kind)
        if want:
            p = self.items.get(parent or "") or self.items.get((parent or "").upper())
            if not p or p["kind"] != want:
                raise BacklogError(f"a {kind} needs a parent {want} (got {parent or 'none'})")
            parent = p["id"]
        elif parent:
            raise BacklogError(f"a {kind} is top level and takes no parent")
        status = status or self.config["statuses"][0]
        self.check_status(status)
        pre = k["prefix"]
        n = self.data["next"].get(pre, 1)
        while f"{pre}-{n}" in self.items:  # never reuse an id, even after a hand edit
            n += 1
        iid = f"{pre}-{n}"
        self.data["next"][pre] = n + 1
        self.items[iid] = {
            "id": iid, "kind": kind, "title": title, "parent": parent, "status": status,
            "owner": owner or None, "created": today(), "updated": today(),
            "notes": [], "refs": [], "blocked_by": [], "links": [], "labels": [],
        }
        it = self.items[iid]
        if note:
            it["notes"].append(f"{today()}: {note.strip()}")
        for r in refs or ():
            if r and r not in it["refs"]:
                it["refs"].append(r)
        for lb in labels or ():
            self._label(it, lb)
        return iid

    def set(self, iid, *, title=None, status=None, owner=None, note=None, refs=(), unref=(),
            parent=None, links=(), unlinks=(), blocked_by=(), unblock=(), labels=(), unlabels=(),
            set_labels=None):
        it = self.get(iid)
        iid = it["id"]
        if title is not None:
            if not title.strip():
                raise BacklogError("the title can't be empty")
            it["title"] = title.strip()
        if status is not None:
            self.check_status(status)
            it["status"] = status
        if owner is not None:
            it["owner"] = owner.strip() or None  # "" clears it
        if parent is not None:
            self.move(iid, parent)
        for other in links or ():
            o = self.get(other)
            if o["id"] == iid:
                raise BacklogError("an item can't link to itself")
            for a, b in ((it, o["id"]), (o, iid)):
                if b not in a["links"]:
                    a["links"].append(b)
            o["updated"] = today()
        for other in unlinks or ():
            o = self.get(other)
            for a, b in ((it, o["id"]), (o, iid)):
                if b in a["links"]:
                    a["links"].remove(b)
        for other in blocked_by or ():
            o = self.get(other)
            if o["id"] == iid:
                raise BacklogError("an item can't block itself")
            if o["id"] not in it["blocked_by"]:
                it["blocked_by"].append(o["id"])
        for other in unblock or ():
            o = self.get(other)
            if o["id"] in it["blocked_by"]:
                it["blocked_by"].remove(o["id"])
        for r in refs or ():
            if r and r not in it["refs"]:
                it["refs"].append(r)
        for r in unref or ():
            if r in it["refs"]:
                it["refs"].remove(r)
        if set_labels is not None:
            it["labels"] = []
            labels = list(set_labels)
        for lb in labels or ():
            self._label(it, lb)
        for lb in unlabels or ():
            lb = lb.strip().lower()
            if lb in it["labels"]:
                it["labels"].remove(lb)
        if note:
            it["notes"].append(f"{today()}: {note.strip()}")
        it["updated"] = today()
        return iid

    def move(self, iid, parent):
        it = self.get(iid)
        want = self.parent_kind(it["kind"])
        if not want:
            raise BacklogError(f"a {it['kind']} is top level and can't move under anything")
        p = self.get(parent)
        if p["kind"] != want:
            raise BacklogError(f"a {it['kind']} sits under a {want}, not under a {p['kind']} ({p['id']})")
        it["parent"] = p["id"]

    @staticmethod
    def _label(it, label):
        label = label.strip().lower()
        if label and label not in it["labels"]:
            it["labels"].append(label)

    def rel_ref(self, path, cwd=None):
        """Store a ref relative to the project root when it names a real file from the cwd."""
        if re.match(r"^[a-z]+://", path):
            return path
        full = os.path.abspath(os.path.join(cwd or os.getcwd(), path))
        if os.path.exists(full) and (full + os.sep).startswith(self.root + os.sep):
            return os.path.relpath(full, self.root)
        return path

    # ---- import ---------------------------------------------------------------
    def import_file(self, src_path):
        """Bring in another backlog.json (this tool's format or Janaan's). Returns {old id: new id}.

        Into an empty backlog the ids are kept. Into one that already has items, the
        imported items get fresh ids and every reference to them is rewritten."""
        with open(src_path, encoding="utf-8") as f:
            src = json.load(f)
        if not isinstance(src, dict) or not isinstance(src.get("items"), dict):
            raise BacklogError(f"{src_path} doesn't look like a backlog (no 'items' object)")
        items = {iid: dict(it, id=iid) for iid, it in src["items"].items()}
        cfg = self.config
        # kinds and statuses the source uses must exist here
        src_kinds = {k["name"]: k for k in src.get("config", {}).get("kinds", [])}
        for it in items.values():
            kind = it.get("kind")
            if kind not in self.kinds():
                prefix = src_kinds.get(kind, {}).get("prefix") or it["id"].rsplit("-", 1)[0]
                raise BacklogError(f"the import uses kind {kind!r} ({prefix}) which this backlog doesn't have "
                                   f"(kinds: {', '.join(self.kinds())})")
            st = it.get("status") or cfg["statuses"][0]
            it["status"] = st
            if st not in cfg["statuses"]:
                cfg["statuses"].append(st)
        keep = not self.items
        mapping = {}
        if keep:
            for iid in items:
                mapping[iid] = iid
        else:
            order = sorted(items, key=lambda i: (kind_rank(self.data, items[i]["kind"]), id_key(i)))
            for iid in order:
                pre = self.kind(items[iid]["kind"])["prefix"]
                n = self.data["next"].get(pre, 1)
                while f"{pre}-{n}" in self.items or f"{pre}-{n}" in mapping.values():
                    n += 1
                mapping[iid] = f"{pre}-{n}"
                self.data["next"][pre] = n + 1
        for old, it in items.items():
            new = mapping[old]
            out = {
                "id": new, "kind": it["kind"], "title": it.get("title") or "(untitled)",
                "parent": mapping.get(it.get("parent")) if it.get("parent") else None,
                "status": it["status"], "owner": it.get("owner") or None,
                "created": it.get("created") or today(), "updated": it.get("updated") or today(),
            }
            for key in ITEM_LISTS:
                vals = list(it.get(key) or [])
                if key in ("blocked_by", "links"):
                    vals = [mapping[v] for v in vals if v in mapping]
                out[key] = vals
            if not keep and old != new:
                out["notes"].append(f"{today()}: imported from {os.path.basename(src_path)} as {old}")
            for extra, v in it.items():  # keep any fields we don't know about
                if extra not in out and extra != "id":
                    out[extra] = v
            self.items[new] = out
        if keep:  # carry the id counters over so ids are never reused
            for pre, n in (src.get("next") or {}).items():
                self.data["next"][pre] = max(self.data["next"].get(pre, 1), int(n))
            for iid in self.items:
                pre, n = id_key(iid)
                if pre in self.data["next"]:
                    self.data["next"][pre] = max(self.data["next"][pre], n + 1)
        # parent rules still hold?
        for new in mapping.values():
            it = self.items[new]
            want = self.parent_kind(it["kind"])
            p = self.items.get(it["parent"]) if it["parent"] else None
            if (want and (not p or p["kind"] != want)) or (not want and p):
                it["notes"].append(f"{today()}: import: parent {it['parent']} doesn't fit a {it['kind']}; check it")
        return mapping
