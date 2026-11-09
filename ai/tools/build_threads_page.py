"""Generate a project's threads page — the backlog a paper was reached through.

A reader meeting a paper cannot see what was asked, in what order, or what came
back the other way. That history lives in `CARD.md`, `threads.md` and the ticket
files, and `ai/CLAUDE.md` forbids any of its vocabulary from entering the
argument: *card*, *thread*, *ticket* and *run* describe how the work is
organised, not what it found.

So it gets its own page beside the paper rather than a section inside it. The
paper stays readable without it; this page says so in its first line.

    python ai/tools/build_threads_page.py <project> [...]

Writes `web/notebook/<project>/threads.md`. Commit the output. The page carries
a digest of its three sources so `check-threads-page` can fail the build when the
record moves and the page does not -- the same drift the evidence ledger had
been quietly carrying for weeks before anyone looked.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

AI = Path(__file__).resolve().parents[1]
WEB = AI.parent / "web"

#: Fixed order, so the digest is reproducible.
SOURCES = ("CARD.md", "threads.md")

ESCAPE = str.maketrans({"<": "&lt;", ">": "&gt;", "{": "&#123;", "}": "&#125;"})


def esc(text: str) -> str:
    """MDX parses the output, so anything that can open a tag is escaped."""
    return text.translate(ESCAPE)


def field(block: str, key: str) -> str:
    m = re.search(rf"^\*\*{key}:\*\*(.*)$", block, re.M)
    return m.group(1).strip() if m else ""


def blocks(text: str, head: re.Pattern[str]) -> list[tuple[str, str, str]]:
    """(id, title, body) for each entry."""
    marks = [(m.start(), m.group(1), m.group(2)) for m in head.finditer(text)]
    out = []
    for i, (pos, ident, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((ident, title.strip(), text[pos:end]))
    return out


def first_sentence(text: str, limit: int = 240) -> str:
    """One clause of plain prose, emphasis and links stripped."""
    body = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    body = re.sub(r"[*_`]", "", body)
    body = " ".join(body.split())
    if len(body) <= limit:
        return body
    cut = body[:limit]
    return cut[: cut.rfind(" ")] + "…"


def digest(root: Path) -> str:
    h = hashlib.sha256()
    for name in SOURCES:
        p = root / name
        h.update(p.read_bytes() if p.is_file() else b"")
    return h.hexdigest()[:16]


def build(project: str) -> Path:
    root = AI / project
    out = WEB / "notebook" / project / "threads.md"
    cards = blocks((root / "CARD.md").read_text() if (root / "CARD.md").is_file() else "",
                   re.compile(r"^## (C-\d+) · ([^\n]*)$", re.M))
    threads = blocks((root / "threads.md").read_text() if (root / "threads.md").is_file() else "",
                     re.compile(r"^### (T-\d+[a-z]?) · ([^\n]*)$", re.M))
    tickets = []
    for path in sorted((root / "agents").glob("*/tickets.md")):
        tickets += blocks(path.read_text(),
                          re.compile(r"^### ([A-Z]-\d+[a-z]?) · ([^\n]*)$", re.M))

    closed = [c for c in cards if field(c[2], "Status") == "closed"]
    answered = [t for t in threads if field(t[2], "Status") in ("answered",)]
    live = [t for t in threads if field(t[2], "Status") not in ("answered",)]

    L: list[str] = []
    L.append("---")
    L.append("title: Threads")
    # No sidebar entry at all: this page is reached from the paper's own
    # switch. A project that advertises its backlog in the navigation is
    # showing process where a reader came for a result.
    L.append(f"description: The questions asked on the way to {project}'s paper, in the "
             "order they were asked, and what each one came back as.")
    L.append("toc_max_heading_level: 2")
    L.append(f"source_digest: {digest(root)}")
    L.append("paper:")
    L.append("  kind: Threads")
    L.append(f"  of: {project}")
    L.append("---")
    L.append("")
    L.append(f"<LabLogHead of=\"{project}\" />")
    L.append("")
    L.append("_Generated from this project's `CARD.md` and `threads.md`. Regenerated "
             "rather than edited._")
    L.append("")
    L.append("**The paper does not depend on anything here, and a reader can ignore this "
             "page entirely.** It exists because the paper reports what was found and "
             "not what was asked — which questions were opened, in what order, and which "
             "ones came back the other way. The vocabulary below describes how the work "
             "was organised. A **card** is one question held open at a time, closed only "
             "with a number or a sentence that could have gone the other way. A **thread** "
             "is an open question that may never become work.")
    L.append("")

    L.append("## The questions, in the order they were asked")
    L.append("")
    L.append(f"{len(closed)} of {len(cards)} closed. Each row is one question that was "
             "held open alone until it closed.")
    L.append("")
    L.append("| # | The question | Opened | How it closed |")
    L.append("| --- | --- | --- | --- |")
    for ident, title, body in sorted(cards, key=lambda c: c[0]):
        L.append(f"| `{ident}` | {esc(title)} | {field(body, 'Opened') or '—'} "
                 f"| {esc(first_sentence(field(body, 'Closed'))) or '— still open'} |")
    L.append("")

    L.append("## Questions that were answered along the way")
    L.append("")
    L.append(f"{len(answered)} of {len(threads)}. A thread is not work; it is something "
             "that was not understood, written down so it could not be quietly dropped.")
    L.append("")
    for ident, title, body in sorted(answered, key=lambda t: t[0]):
        L.append(f"**`{ident}` · {esc(title)}**")
        L.append("")
        L.append(f"{esc(first_sentence(field(body, 'Question'), 300))}")
        L.append("")
        L.append(f"> {esc(first_sentence(field(body, 'Answer'), 300))}")
        L.append("")

    if live:
        L.append("## Still open")
        L.append("")
        L.append("Carried rather than closed. Each says what it is waiting for.")
        L.append("")
        L.append("| # | The question | Status |")
        L.append("| --- | --- | --- |")
        for ident, title, body in sorted(live, key=lambda t: t[0]):
            L.append(f"| `{ident}` | {esc(title)} | {field(body, 'Status') or '—'} |")
        L.append("")

    L.append("## What was actually run")
    L.append("")
    done = sum(1 for t in tickets if field(t[2], "Status") in ("closed", "split"))
    L.append(f"{done} of {len(tickets)} tickets closed. A ticket is a unit of work and "
             "carries its artifacts; the runs behind each number in the paper are listed "
             "in its own appendix, which is where a reader checking a figure should go "
             "instead of here.")
    L.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n")
    return out


def main() -> int:
    names = sys.argv[1:]
    if not names:
        print("usage: build_threads_page.py <project> [...]", file=sys.stderr)
        return 2
    for name in names:
        path = build(name)
        print(f"wrote {path.relative_to(AI.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
