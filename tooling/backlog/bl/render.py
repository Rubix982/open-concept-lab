"""Fill the single-file viewer (viewer.html) with a backlog."""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def page(bl, mode, ref_base):
    """mode: "static" (read-only, data baked in) or "live" (talks to `bl serve`)."""
    with open(os.path.join(HERE, "viewer.html"), encoding="utf-8") as f:
        tpl = f.read()
    boot = {
        "mode": mode,
        "refBase": ref_base,
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data": bl.data if mode == "static" else None,
    }
    blob = json.dumps(boot, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    title = bl.config.get("name") or "Backlog"
    esc = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return tpl.replace("/*BOOT*/null", blob).replace("{{title}}", esc)


def render_static(bl, out_path):
    """Refs become links relative to wherever the HTML file is written."""
    rel = os.path.relpath(bl.root, os.path.dirname(os.path.abspath(out_path)))
    base = "" if rel == "." else rel.replace(os.sep, "/") + "/"
    return page(bl, "static", base)
