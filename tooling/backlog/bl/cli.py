"""bl: a small project backlog that lives in your repo (.backlog/backlog.json).

Run `bl -h` for the commands, `bl <command> -h` for each one's options.
"""
import argparse
import json
import os
import sys
import webbrowser

from . import __version__
from .store import Backlog, BacklogError, init, find_root, id_key

# ---- colour ---------------------------------------------------------------------------
COLOURS = {"todo": "37", "doing": "34;1", "blocked": "31;1", "review": "33", "done": "32",
           "parked": "35", "dropped": "90"}
USE_COLOUR = False


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOUR and code else text


def st(status):
    return c(status, COLOURS.get(status, "36"))


def dim(text):
    return c(text, "2")


def bold(text):
    return c(text, "1")


def minibar(d, t, width=10):
    if not t:
        return ""
    full = round(width * d / t)
    return c("█" * full, "32") + dim("░" * (width - full))


# ---- rendering helpers ------------------------------------------------------------------
def line_for(bl, it, depth=0, show_progress=True, show_top=False):
    kids = bl.children(it["id"])
    parts = ["  " * depth + bold(it["id"]), f"[{st(it['status'])}]", it["title"]]
    if kids and show_progress:
        d, t = bl.progress(it["id"])
        parts.append(f"{minibar(d, t)} {d}/{t}")
    if it.get("owner"):
        parts.append(dim(f"@{it['owner']}"))
    if it.get("labels"):
        parts.append(c(" ".join("#" + lb for lb in it["labels"]), "36"))
    waiting = [b for b in it.get("blocked_by", []) if b in bl.items and not bl.closed(bl.items[b])]
    if waiting and not bl.closed(it):
        parts.append(c("blocked by " + ", ".join(waiting), "31"))
    if show_top and it.get("parent"):
        top = bl.top(it["id"])
        parts.append(dim(f"· {top['id']} {top['title']}"))
    return " ".join(parts)


def tree_lines(bl, only_open=False, root=None):
    out = []

    def walk(it, depth):
        if only_open and bl.closed(it):
            return
        out.append(line_for(bl, it, depth))
        for k in bl.children(it["id"]):
            walk(k, depth + 1)

    for it in ([bl.get(root)] if root else bl.roots()):
        walk(it, 0)
    return out


def show_text(bl, it):
    iid = it["id"]
    out = []
    chain = bl.chain(iid)
    if chain:
        out.append(dim(" › ".join(f"{p['id']} {p['title']}" for p in chain)))
    out.append(bold(f"{iid}  {it['title']}"))
    meta = [it["kind"], st(it["status"])]
    if it.get("owner"):
        meta.append("@" + it["owner"])
    meta.append(dim(f"created {it.get('created')} · updated {it.get('updated')}"))
    out.append("  ".join(meta))
    if it.get("labels"):
        out.append("labels: " + ", ".join(it["labels"]))
    kids = bl.children(iid)
    if kids:
        d, t = bl.progress(iid)
        out.append(f"progress: {minibar(d, t)} {d}/{t}")
    def section(title, ids):
        rows = [bl.items[i] for i in ids if i in bl.items]
        if rows:
            out.append("")
            out.append(bold(title))
            for r in rows:
                out.append(f"  {r['id']} [{st(r['status'])}] {r['title']}")
    section("children", [k["id"] for k in kids])
    section("blocked by", it.get("blocked_by", []))
    section("blocks", sorted((o["id"] for o in bl.items.values() if iid in o.get("blocked_by", [])), key=id_key))
    section("linked", it.get("links", []))
    if it.get("refs"):
        out.append("")
        out.append(bold("refs"))
        out += [f"  {r}" for r in it["refs"]]
    if it.get("notes"):
        out.append("")
        out.append(bold("notes"))
        out += [f"  {n}" for n in it["notes"]]
    return out


def split_list(values):
    out = []
    for v in values or []:
        out += [x.strip() for x in v.split(",") if x.strip()]
    return out


# ---- commands --------------------------------------------------------------------------
def cmd_init(a):
    kinds = None
    if a.kinds:
        kinds = []
        for part in split_list([a.kinds]):
            name, _, prefix = part.partition(":")
            kinds.append({"name": name.strip().lower(), "prefix": (prefix or name[:2]).strip().upper()})
        if len({k["prefix"] for k in kinds}) != len(kinds):
            raise BacklogError("each kind needs its own id prefix")
    statuses = split_list([a.statuses]) if a.statuses else None
    bl = init(a.dir or os.getcwd(), a.name, kinds, statuses)
    names = " → ".join(f"{k['name']} ({k['prefix']})" for k in bl.config["kinds"])
    print(f"Started backlog {bold(bl.config['name'])} in {bl.path}")
    print(f"kinds: {names}")
    print(f"statuses: {', '.join(bl.config['statuses'])}")
    top = bl.kinds()[0]
    print(dim(f'next: bl add {top} "First {top}"'))


def cmd_add(a):
    bl = open_backlog(a)
    with bl.edit():
        iid = bl.add(a.kind, a.title, parent=a.parent, status=a.status, owner=a.owner, note=a.note,
                     refs=[bl.rel_ref(r) for r in a.ref or []], labels=split_list(a.label))
        if a.blocked_by:
            bl.set(iid, blocked_by=split_list(a.blocked_by))
    print(iid)


def cmd_set(a):
    bl = open_backlog(a)
    with bl.edit():
        bl.set(a.id, title=a.title, status=a.status, owner=a.owner, note=a.note,
               refs=[bl.rel_ref(r) for r in a.ref or []], unref=a.unref or [], parent=a.parent,
               links=split_list(a.link), unlinks=split_list(a.unlink),
               blocked_by=split_list(a.blocked_by), unblock=split_list(a.unblock),
               labels=split_list(a.label), unlabels=split_list(a.unlabel))
        it = bl.get(a.id)
    print(line_for(bl, it))


def cmd_show(a):
    bl = open_backlog(a)
    it = bl.get(a.id)
    if a.json:
        print(json.dumps(it, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print("\n".join(show_text(bl, it)))


def cmd_tree(a):
    bl = open_backlog(a)
    lines = tree_lines(bl, a.open, a.id)
    print("\n".join(lines) if lines else dim("(empty: add something with `bl add`)"))


def cmd_ls(a):
    bl = open_backlog(a)
    statuses = split_list(a.status)
    for s in statuses:
        bl.check_status(s)
    labels = [x.lower() for x in split_list(a.label)]
    q = " ".join(a.query).lower()
    rows = []
    for it in sorted(bl.items.values(), key=lambda i: (id_key(bl.top(i["id"])["id"]), bl.kinds().index(i["kind"])
                                                        if i["kind"] in bl.kinds() else 99, id_key(i["id"]))):
        if statuses and it["status"] not in statuses:
            continue
        if not statuses and not a.all and bl.closed(it):
            continue
        if a.owner and (it.get("owner") or "").lower() != a.owner.lower():
            continue
        if labels and not all(lb in it.get("labels", []) for lb in labels):
            continue
        if a.kind and it["kind"] != a.kind:
            continue
        if a.epic and bl.top(it["id"])["id"] != bl.get(a.epic)["id"]:
            continue
        if q:
            hay = " ".join([it["id"], it["title"], it.get("owner") or "", " ".join(it.get("labels", [])),
                            " ".join(it.get("notes", []))]).lower()
            if q not in hay:
                continue
        rows.append(it)
    for it in rows:
        print(line_for(bl, it, show_top=True))
    if not rows:
        print(dim("nothing matches"))


def cmd_next(a):
    bl = open_backlog(a)
    items = sorted(bl.items.values(), key=lambda i: (id_key(bl.top(i["id"])["id"]), id_key(i["id"])))
    leafish = lambda it: not bl.children(it["id"]) or all(bl.closed(k) for k in bl.children(it["id"]))
    doing = [i for i in items if i["status"] == "doing"]
    review = [i for i in items if i["status"] == "review"]
    blocked = [i for i in items if i["status"] == "blocked"
               or (not bl.closed(i) and any(b in bl.items and not bl.closed(bl.items[b]) for b in i.get("blocked_by", [])))]
    first = bl.config["statuses"][0]
    ready = [i for i in items if i["status"] == first and leafish(i) and i not in blocked]
    def block(title, rows, limit=None):
        print(bold(title) + dim(f" ({len(rows)})"))
        for it in rows[:limit] if limit else rows:
            print("  " + line_for(bl, it, show_top=True))
        if limit and len(rows) > limit:
            print(dim(f"  … {len(rows) - limit} more (bl ls --status {first})"))
        if not rows:
            print(dim("  none"))
    block("In progress", doing)
    if review:
        block("In review", review)
    if blocked:
        block("Blocked", blocked)
    block("Up next", ready, a.n)


def write_board(bl, out=None):
    from .render import render_static
    out = out or os.path.join(bl.dir, "board.html")
    html = render_static(bl, out)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return out


def cmd_board(a):
    bl = open_backlog(a)
    out = write_board(bl, os.path.abspath(a.out) if a.out else None)
    print(f"wrote {out}")
    if not a.no_open:
        webbrowser.open("file://" + out)


def cmd_serve(a):
    from .server import serve
    bl = open_backlog(a)
    serve(bl, a.port, open_browser=not a.no_open)


def cmd_import(a):
    bl = open_backlog(a)
    src = os.path.abspath(a.path)
    if os.path.isdir(src):
        for cand in (os.path.join(src, ".backlog", "backlog.json"), os.path.join(src, "backlog", "backlog.json"),
                     os.path.join(src, "backlog.json")):
            if os.path.isfile(cand):
                src = cand
                break
    if not os.path.isfile(src):
        raise BacklogError(f"no backlog file at {a.path}")
    with bl.edit():
        mapping = bl.import_file(src)
    renamed = sum(1 for k, v in mapping.items() if k != v)
    print(f"imported {len(mapping)} items from {src}" + (f" ({renamed} given new ids)" if renamed else ""))


def open_backlog(a):
    return Backlog(a.dir) if a.dir else Backlog.find()


# ---- argument parsing --------------------------------------------------------------------
def build_parser():
    ap = argparse.ArgumentParser(prog="bl", description="A small project backlog that lives in your repo.",
                                 epilog="Run `bl <command> -h` for a command's options.")
    ap.add_argument("-C", dest="dir", metavar="DIR", help="use the backlog in DIR instead of searching up from here")
    ap.add_argument("--no-color", action="store_true", help="plain output")
    ap.add_argument("--version", action="version", version=f"bl {__version__}")
    sp = ap.add_subparsers(dest="cmd", metavar="command")
    sp.required = True

    p = sp.add_parser("init", help="start a backlog in this folder (.backlog/backlog.json)")
    p.add_argument("name", nargs="?", help="project name shown in the viewer (default: folder name)")
    p.add_argument("--kinds", help='levels top to bottom as name:PREFIX, e.g. "epic:EP,story:ST,task:TK"')
    p.add_argument("--statuses", help='comma list, first is the starting status, e.g. "todo,doing,done"')
    p.set_defaults(fn=cmd_init)

    p = sp.add_parser("add", help="add an item")
    p.add_argument("kind", help="epic, story, task (or your configured kinds)")
    p.add_argument("title")
    p.add_argument("--parent", "-p", help="the item it sits under")
    p.add_argument("--status", "-s")
    p.add_argument("--owner", "-o")
    p.add_argument("--note", "-n")
    p.add_argument("--ref", "-r", action="append", help="a file or URL (repeatable)")
    p.add_argument("--label", "-l", action="append", help="a label (repeatable or comma list)")
    p.add_argument("--blocked-by", "-b", action="append", help="an item this waits on (repeatable)")
    p.set_defaults(fn=cmd_add)

    p = sp.add_parser("set", help="change an item")
    p.add_argument("id")
    p.add_argument("--title", "-t")
    p.add_argument("--status", "-s")
    p.add_argument("--owner", "-o", help='"" clears it')
    p.add_argument("--note", "-n", help="appended with today's date")
    p.add_argument("--ref", "-r", action="append")
    p.add_argument("--unref", action="append")
    p.add_argument("--parent", "-p", help="move it under another item")
    p.add_argument("--link", action="append", help="relate to another item (both ways)")
    p.add_argument("--unlink", action="append")
    p.add_argument("--blocked-by", "-b", action="append")
    p.add_argument("--unblock", action="append")
    p.add_argument("--label", "-l", action="append")
    p.add_argument("--unlabel", action="append")
    p.set_defaults(fn=cmd_set)

    p = sp.add_parser("show", help="one item in full")
    p.add_argument("id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_show)

    p = sp.add_parser("tree", help="the hierarchy with progress")
    p.add_argument("id", nargs="?", help="only this item's branch")
    p.add_argument("--open", action="store_true", help="hide done and dropped")
    p.set_defaults(fn=cmd_tree)

    p = sp.add_parser("ls", help="a flat, filtered list")
    p.add_argument("query", nargs="*", help="text to look for in id, title, owner, labels, notes")
    p.add_argument("--status", "-s", action="append")
    p.add_argument("--owner", "-o")
    p.add_argument("--label", "-l", action="append")
    p.add_argument("--epic", "-e", help="only items under this top-level item")
    p.add_argument("--kind", "-k")
    p.add_argument("--all", "-a", action="store_true", help="include done and dropped")
    p.set_defaults(fn=cmd_ls)

    p = sp.add_parser("next", help="what's in progress and what to pick up")
    p.add_argument("-n", type=int, default=5, help="how many to-dos to show (default 5)")
    p.set_defaults(fn=cmd_next)

    p = sp.add_parser("board", help="write a read-only HTML viewer and open it")
    p.add_argument("--out", help="where to write it (default .backlog/board.html)")
    p.add_argument("--no-open", action="store_true")
    p.set_defaults(fn=cmd_board)

    p = sp.add_parser("serve", help="the viewer with editing, on localhost")
    p.add_argument("--port", type=int, default=8765, help="0 picks a free port (default 8765)")
    p.add_argument("--no-open", action="store_true")
    p.set_defaults(fn=cmd_serve)

    p = sp.add_parser("import", help="bring in another backlog.json (bl or Janaan format)")
    p.add_argument("path")
    p.set_defaults(fn=cmd_import)
    return ap


def main(argv=None):
    global USE_COLOUR
    argv = list(sys.argv[1:] if argv is None else argv)
    plain = "--no-color" in argv  # accepted anywhere on the line
    argv = [x for x in argv if x != "--no-color"]
    a = build_parser().parse_args(argv)
    USE_COLOUR = sys.stdout.isatty() and not plain and not os.environ.get("NO_COLOR")
    try:
        a.fn(a)
    except BacklogError as e:
        print(f"bl: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
