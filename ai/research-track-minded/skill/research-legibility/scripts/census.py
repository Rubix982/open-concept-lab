#!/usr/bin/env python3
"""The stranger's census: every term a reader might not hold, and where it first appears.

This finds CANDIDATES. It cannot tell whether a term was defined, because a definition
is a sentence a human recognises and not a pattern. So it prints the first use of each
candidate and leaves the second column to you. Every row you cannot fill is a defect.

The count is the finding. Run it before and after a revision; the drop is the only
number this produces.

What it looks for:

  identifiers   C-001, E-004, T-009, F-07, ADR-12 -- a letter or two, a separator,
                digits. These are a project's bookkeeping and mean nothing outside it.
  code terms    `alias`, `compute_v` -- backticked, so the writer already marked them
                as jargon.
  coinages      Bolded or italicised phrases, which is how a writer introduces a
                term they are about to rely on. This class is NOISY -- emphasis and
                terms of art are typographically identical -- so scan it, do not
                trust it. The noise is cheap and a missed term is not.

Usage:  census.py FILE [FILE ...]
        census.py --ids-only FILE     # just the identifiers
        census.py --min-uses 2 FILE   # ignore anything used once (default 1)
"""
from __future__ import annotations

import re
import sys
import pathlib
from collections import defaultdict

# A letter or two, a REQUIRED separator, two to four digits. Matches C-001 and E‑004
# (en dash). The separator is required because without it the pattern eats SVG path
# data -- M300, H820, V252 -- which is how this script first ran, and a census full of
# path commands is a census nobody reads.
IDENTIFIER = re.compile(r"\b([A-Z]{1,4}[-‑–_]\d{2,4})\b")

# Backticked, but not a path, a flag, a number or a whole expression.
CODE_TERM = re.compile(r"`([a-zA-Z][a-zA-Z0-9_]{2,30})`")

# **bold** or *italic* phrases of one to four words, lower case, which is how a term
# of art is usually introduced. Skips sentence-initial capitals and headings.
COINAGE = re.compile(r"(?<![*\w])\*\*?([a-z][a-z \-]{3,40}[a-z])\*\*?(?![*\w])")

SKIP_CODE_FENCE = re.compile(r"^\s*```")
SVG_OPEN = re.compile(r"<svg\b")
SVG_CLOSE = re.compile(r"</svg>")
HEADING = re.compile(r"^\s*#{1,6}\s")
FRONTMATTER = "---"

# Words that are backticked constantly and are not terms of art.
NOISE = {
    "true", "false", "none", "null", "null", "https", "http", "www", "md", "py",
    "json", "yml", "yaml", "tsx", "css", "html", "git", "npm", "and", "the", "not",
}


def candidates(path: pathlib.Path) -> dict[str, dict[str, list]]:
    text = path.read_text(encoding="utf-8").splitlines()
    found: dict[str, dict[str, list]] = {
        "identifier": defaultdict(list),
        "code term": defaultdict(list),
        "coinage": defaultdict(list),
    }

    in_fence = False
    in_svg = False
    in_frontmatter = False
    section = "(before the first heading)"

    for n, line in enumerate(text, 1):
        if n == 1 and line.strip() == FRONTMATTER:
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line.strip() == FRONTMATTER:
                in_frontmatter = False
            continue
        if SKIP_CODE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # A figure's innards are drawing instructions, not prose. Its caption and
        # its alt text are prose and sit outside the element.
        if SVG_OPEN.search(line):
            in_svg = True
        if in_svg:
            if SVG_CLOSE.search(line):
                in_svg = False
            continue
        if HEADING.match(line):
            section = line.strip().lstrip("#").strip()

        where = (n, section)
        for m in IDENTIFIER.finditer(line):
            found["identifier"][m.group(1).replace("‑", "-").replace("–", "-")].append(where)
        for m in CODE_TERM.finditer(line):
            term = m.group(1)
            if term.lower() not in NOISE:
                found["code term"][term].append(where)
        for m in COINAGE.finditer(line):
            found["coinage"][m.group(1).strip()].append(where)

    return found


def report(path: pathlib.Path, ids_only: bool, min_uses: int) -> int:
    found = candidates(path)
    classes = ["identifier"] if ids_only else ["identifier", "code term", "coinage"]

    print(f"\n{path}")
    total = 0

    for cls in classes:
        rows = {t: w for t, w in found[cls].items() if len(w) >= min_uses}
        if not rows:
            continue
        note = "  (noisy: emphasis looks like a coinage — scan, do not trust)" if cls == "coinage" else ""
        print(f"\n  {cls}s — {len(rows)} distinct{note}")
        width = min(34, max(len(t) for t in rows))
        for term in sorted(rows, key=lambda t: rows[t][0][0]):
            uses = rows[term]
            line, section = uses[0]
            print(f"    {term:<{width}}  first used line {line:>4}  in {section[:42]:<42}  ×{len(uses)}")
        total += len(rows)

    print(
        f"\n  {total} candidates. For each, find the line where it is first DEFINED."
        f"\n  Any you cannot find, and any defined after its first use, is a defect."
        f"\n  Fix by class: terms of art take the ladder, identifiers leave the prose,"
        f"\n  process nouns move to the state-of-the-work page. See SKILL.md."
    )
    return total


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    ids_only = "--ids-only" in argv
    min_uses = 1
    if "--min-uses" in argv:
        i = argv.index("--min-uses")
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            min_uses = int(argv[i + 1])
            args = [a for a in args if a != argv[i + 1]]

    if not args:
        print(__doc__)
        return 2

    grand = 0
    for name in args:
        p = pathlib.Path(name)
        if not p.is_file():
            print(f"not a file: {name}", file=sys.stderr)
            continue
        grand += report(p, ids_only, min_uses)

    if len(args) > 1:
        print(f"\n{grand} candidates across {len(args)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
