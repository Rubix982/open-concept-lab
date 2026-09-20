"""Generate the public evidence ledger from the repo's own shared surfaces.

An audit on 2026-09-20 found 80 of 91 records invisible on the site: the narrative and the
review packet carry the highlights, and everything else existed only in the repo. A
hand-written index would drift within a day, so this is generated and regenerated.

    python agents/engineer/workspace/build_ledger.py

Writes web/notebook/edit-slice/ledger.md. Commit the output.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT.parents[1] / "web" / "notebook" / "edit-slice" / "ledger.md"


def first_sentence(text: str, limit: int = 155) -> str:
    """One clause of plain prose, with markdown emphasis and links stripped."""
    body = re.sub(r'^_Date:[^\n]*\n', '', text.strip(), flags=re.M)
    body = re.sub(r'^\s*[|>#\-].*$', '', body, flags=re.M)      # tables, quotes, headings
    body = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', body)         # links
    body = re.sub(r'[*_`]', '', body)
    # MDX parses the output, so anything that can open a JSX tag or an expression has to
    # be escaped. A "<->" in one entry broke the whole build; generated text can contain
    # anything, so escape rather than fix cases as they appear.
    body = (body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace("{", "&#123;").replace("}", "&#125;"))
    body = " ".join(body.split())
    if not body:
        return "—"
    cut = body[:limit]
    return (cut if len(body) <= limit else cut.rsplit(" ", 1)[0] + "…")


def parse_entries(path: Path) -> list[dict]:
    text = path.read_text()
    out = []
    parts = re.split(r'\n## \[', text)
    for p in parts[1:]:
        tid, rest = p.split("]", 1)
        lines = rest.split("\n")
        title = (lines[0].strip().lstrip(":").strip()
                 .replace("<", "&lt;").replace(">", "&gt;")
                 .replace("{", "&#123;").replace("}", "&#125;"))
        # The gist must come from the BODY, not from the line the title is on, or every
        # row restates its own title before saying anything.
        body = "\n".join(lines[1:])
        date = (re.search(r'_Date:\s*([0-9-]+)', rest) or [None, "—"])[1]
        kind, _, short = title.partition(":")
        if not short.strip():
            kind, short = "Note", title
        out.append({"id": tid.strip(), "title": short.strip(), "kind": kind.strip(),
                    "date": date, "gist": first_sentence(body)})
    return out


def parse_threads(path: Path) -> list[dict]:
    text = path.read_text()
    out = []
    for b in re.split(r'\n### ', text)[1:]:
        head = b.split("\n")[0]
        tid = head.split("·")[0].strip()
        title = (head.split("·", 1)[1].strip() if "·" in head else head)
        title = (title.replace("<", "&lt;").replace(">", "&gt;")
                      .replace("{", "&#123;").replace("}", "&#125;"))
        st = re.search(r'\*\*Status:\*\*\s*(.+)', b)
        parent = re.search(r'\*\*Parent:\*\*\s*(.+)', b)
        q = re.search(r'\*\*Question:\*\*\s*(.+?)(?=\n\*\*|\Z)', b, re.S)
        out.append({"id": tid, "title": title,
                    "status": (st.group(1).strip() if st else "?"),
                    "parent": (parent.group(1).strip() if parent else "—"),
                    "gist": first_sentence(q.group(1) if q else "", 130)})
    return out


def main() -> None:
    log = setup("build_ledger", config={"output": str(OUT)})
    dec = parse_entries(ROOT / "agents/shared/decisions.md")
    fnd = parse_entries(ROOT / "agents/shared/findings.md")
    thr = parse_threads(ROOT / "threads.md")
    log.info("parsed %d decisions, %d findings, %d threads", len(dec), len(fnd), len(thr))

    def status_key(s: str) -> str:
        s = s.lower()
        for k in ("answered", "dropped", "parked", "active", "open"):
            if s.startswith(k):
                return k
        return "open"

    groups: dict[str, list] = {}
    for t in thr:
        groups.setdefault(status_key(t["status"]), []).append(t)

    L = []
    L.append("---")
    L.append("title: Evidence ledger")
    L.append("sidebar_label: Evidence ledger")
    L.append("sidebar_position: 3")
    L.append("description: Every decision, finding and thread in the edit-slice record, "
             "generated from the repository so it cannot drift from it.")
    L.append("---")
    L.append("")
    L.append("# Evidence ledger")
    L.append("")
    L.append("_Generated from `agents/shared/decisions.md`, `agents/shared/findings.md` and "
             "`threads.md` by `build_ledger.py`. Regenerated rather than edited._")
    L.append("")
    L.append("The [paper](./review) argues a claim and the [narrative](/writing/five-days) "
             "tells the story. This is the complete record behind both — including the "
             "entries that went nowhere, which are the majority.")
    L.append("")
    L.append(f"**{len(dec)} decisions · {len(fnd)} findings · {len(thr)} threads "
             f"({', '.join(f'{len(v)} {k}' for k, v in sorted(groups.items()))})**")
    L.append("")
    L.append("## Decisions and results")
    L.append("")
    L.append("Engineering decisions and experiment outcomes. Each states its falsification "
             "before the run, and corrections keep their own entry rather than editing the "
             "original.")
    L.append("")
    L.append("| id | date | kind | what it settled |")
    L.append("| --- | --- | --- | --- |")
    for e in dec:
        L.append(f"| `{e['id']}` | {e['date']} | {e['kind']} | "
                 f"**{e['title']}** — {e['gist']} |")
    L.append("")
    L.append("## Findings")
    L.append("")
    L.append("Literature reads and measurements that are not decisions. Two of these closed "
             "whole directions at the prior-art gate.")
    L.append("")
    L.append("| id | date | finding |")
    L.append("| --- | --- | --- |")
    for e in fnd:
        L.append(f"| `{e['id']}` | {e['date']} | **{e['title']}** — {e['gist']} |")
    L.append("")
    L.append("_Confidence levels and full evidence are in the repository entries; these "
             "are one-line pointers, not summaries._")
    L.append("")
    L.append("## Threads")
    L.append("")
    L.append("Open questions, tracked as a tree. A thread is a unit of *inquiry*; a ticket "
             "is a unit of *work*. Parked is not dropped — a parked thread carries enough "
             "context to resume cold.")
    L.append("")
    for key, label in (("open", "Open"), ("active", "Active"), ("answered", "Answered"),
                       ("parked", "Parked"), ("dropped", "Dropped")):
        rows = groups.get(key, [])
        if not rows:
            continue
        L.append(f"### {label} ({len(rows)})")
        L.append("")
        L.append("| id | question | parent | status |")
        L.append("| --- | --- | --- | --- |")
        for t in rows:
            st = t["status"].replace("|", "/")
            L.append(f"| `{t['id']}` | **{t['title']}** — {t['gist']} | {t['parent']} | {st} |")
        L.append("")

    OUT.write_text("\n".join(L) + "\n")
    log.info("wrote %s (%d lines)", OUT, len(L))


if __name__ == "__main__":
    main()
