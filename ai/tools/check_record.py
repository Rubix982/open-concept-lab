"""Does the record agree with itself?

Three times in one session a thread or ticket was given its answer and its
`**Status:**` line was left saying `open`. Each time it was caught by counting
statuses afterwards and noticing the total had not moved -- which only works if
someone happens to count. The same fault, in older entries, is what [O-003] was
opened for: five tickets that had been finished for over a week and still read
`open`, and a plan that disagreed with them row for row.

So it is checked rather than remembered. Seven rules, each of which can fail:

1. A thread whose `**Answer:**` says something must not be `open`.
2. A thread that is `answered` must have an answer.
3. A ticket with a `**Closed:**` date must be `closed` or `split`.
4. A ticket that is `closed` must record a `**Closed:**` date and artifacts.
5. A ticket's status must be one the lifecycle defines.
6. A ticket that is `blocked` must say what blocks it.
7. An id is never reassigned, so no id appears twice.

    python ai/tools/check_record.py [project-root ...]

**It was written inside edit-reach and that was twice wrong.** Its `ROOT` was
fixed to that one project, so it was blind to the 89 tickets in edit-slice --
where it then found three unfinished tickets, a status outside the lifecycle, a
`blocked` ticket whose blockers field reads `none`, and two research ids whose
results are cited in four files with no ticket behind them. A check aimed only
at the place already cleaned is the fault it exists to catch.

And a checker that serves every project is not one project's instrument. It
lives in `ai/tools/` for the same reason the nine research modules stay in
edit-slice: what encodes a project's own questions stays with it, and what is
general moves out. With no arguments it checks every project beside it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

#: This file sits in `ai/tools/`, so the projects are its parent's siblings.
HERE = Path(__file__).resolve().parent

#: The statuses the ticket lifecycle defines. `split` is in the template;
#: anything else is a status somebody invented mid-run, which reads as
#: meaningful and is not checked by anything.
TICKET_STATUSES = {"open", "in-progress", "blocked", "closed", "re-opened", "split"}

#: An answer field that is only this is not an answer. A trailing parenthetical
#: ("— (resolves through T-010)") is a pointer, not an answer, so the test is
#: whether anything other than a dash and a note survives.
EMPTY = re.compile(r"^\s*—?\s*(\(.*\))?\s*$")


def entries(text: str, head: re.Pattern[str]) -> list[tuple[str, str]]:
    """(heading, body) for each entry, body running to the next heading."""
    marks = [(m.start(), m.group(1)) for m in head.finditer(text)]
    out = []
    for i, (pos, name) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out.append((name, text[pos:end]))
    return out


def field(body: str, key: str) -> str | None:
    m = re.search(rf"^\*\*{key}:\*\*(.*)$", body, re.M)
    return m.group(1) if m else None


def roots(argv: list[str]) -> list[Path]:
    """The projects to check: those named, else this one and its siblings."""
    if argv:
        return [Path(a).resolve() for a in argv]
    return sorted(p for p in HERE.parent.iterdir()
                  if p.is_dir() and ((p / "agents").is_dir() or (p / "threads.md").is_file()))


def check(root: Path) -> list[str]:
    bad: list[str] = []
    threads = root / "threads.md"
    tickets = sorted((root / "agents").glob("*/tickets.md"))
    if not threads.is_file() and not tickets:
        return bad

    text = threads.read_text() if threads.is_file() else ""
    for name, body in entries(text, re.compile(r"^### (T-\d+[a-z]?) ·[^\n]*$", re.M)):
        status = (field(body, "Status") or "").strip()
        answer = field(body, "Answer")
        has_answer = answer is not None and not EMPTY.match(answer)
        if has_answer and status == "open":
            bad.append(f"{name}: has an answer but Status says open")
        if status == "answered" and not has_answer:
            bad.append(f"{name}: Status says answered but Answer is empty")

    seen: dict[str, str] = {}
    for path in tickets:
        text = path.read_text()
        who = path.parent.name
        for name, body in entries(text, re.compile(r"^### ([A-Z]-\d+[a-z]?) ·[^\n]*$", re.M)):
            raw = (field(body, "Status") or "").strip()
            # "closed — superseded by E-005" is a closed ticket with a note on it,
            # not an invented status. Read the word, keep the note for the message.
            status = re.split(r"\s*[—–-]\s|\s*\(", raw, maxsplit=1)[0].strip().lower()
            closed = field(body, "Closed")
            has_closed = closed is not None and not EMPTY.match(closed)
            arts = field(body, "Artifacts")
            has_arts = arts is not None and (
                not EMPTY.match(arts) or "\n- " in body.split("**Artifacts:**")[-1][:400]
            )
            if has_closed and status not in ("closed", "split"):
                bad.append(f"{who}/{name}: has a Closed date but Status says {status!r}")
            if status == "closed" and not has_closed:
                bad.append(f"{who}/{name}: Status says closed but Closed is empty")
            if status == "closed" and not has_arts:
                bad.append(f"{who}/{name}: closed with no artifacts recorded")
            if status and status not in TICKET_STATUSES:
                bad.append(f"{who}/{name}: status {raw!r} is not one the "
                           f"lifecycle defines")
            # Rule 7: an id is never reassigned, so the same one twice is two
            # tickets wearing one number -- and every artifact, changelog line and
            # cross-reference pointing at it now points at both.
            if name in seen:
                bad.append(f"{who}/{name}: id used twice, also in {seen[name]}")
            else:
                seen[name] = who
            if status == "blocked":
                blockers = (field(body, "Blockers") or "").strip()
                if not blockers or blockers.lower().startswith("none"):
                    bad.append(f"{who}/{name}: blocked, but Blockers says "
                               f"{blockers or 'nothing'!r}")
    return bad


def main() -> int:
    found: dict[str, list[str]] = {}
    for root in roots(sys.argv[1:]):
        bad = check(root)
        if bad:
            found[root.name] = bad

    if found:
        print("\ncheck_record: the record disagrees with itself\n")
        for project, bad in found.items():
            print(f"  {project}")
            for b in bad:
                print(f"    {b}")
            print()
        print("    Discipline rule 1: never mark a ticket closed without recording"
              "\n    its artifacts. An entry that carries its answer and still reads"
              "\n    `open` is the same fault one field earlier.\n")
        return 1

    print("check_record: statuses, answers, closures, artifacts and blockers "
          "all agree, across every project checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
