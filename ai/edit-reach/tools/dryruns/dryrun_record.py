"""Does the record agree with itself?

Three times in one session a thread or ticket was given its answer and its
`**Status:**` line was left saying `open`. Each time it was caught by counting
statuses afterwards and noticing the total had not moved -- which only works if
someone happens to count. The same fault, in older entries, is what [O-003] was
opened for: five tickets that had been finished for over a week and still read
`open`, and a plan that disagreed with them row for row.

So it is checked rather than remembered. Four rules, each of which can fail:

1. A thread whose `**Answer:**` says something must not be `open`.
2. A thread that is `answered` must have an answer.
3. A ticket with a `**Closed:**` date must be `closed` or `split`.
4. A ticket that is `closed` must record a `**Closed:**` date and artifacts.

Exit 1 and name the entry. Run it before committing a session's record.

    python tools/dryruns/dryrun_record.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THREADS = ROOT / "threads.md"
TICKETS = sorted((ROOT / "agents").glob("*/tickets.md"))

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


def main() -> int:
    bad: list[str] = []

    text = THREADS.read_text()
    for name, body in entries(text, re.compile(r"^### (T-\d+)[^\n]*$", re.M)):
        status = (field(body, "Status") or "").strip()
        answer = field(body, "Answer")
        has_answer = answer is not None and not EMPTY.match(answer)
        if has_answer and status == "open":
            bad.append(f"{name}: has an answer but Status says open")
        if status == "answered" and not has_answer:
            bad.append(f"{name}: Status says answered but Answer is empty")

    for path in TICKETS:
        text = path.read_text()
        who = path.parent.name
        for name, body in entries(text, re.compile(r"^### ([A-Z]-\d+)[^\n]*$", re.M)):
            status = (field(body, "Status") or "").strip()
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

    if bad:
        print("\ndryrun_record: the record disagrees with itself\n")
        for b in bad:
            print(f"    {b}")
        print("\n    Discipline rule 1: never mark a ticket closed without recording"
              "\n    its artifacts. An entry that carries its answer and still reads"
              "\n    `open` is the same fault one field earlier.\n")
        return 1

    print("dryrun_record: statuses, answers, closures and artifacts all agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())
