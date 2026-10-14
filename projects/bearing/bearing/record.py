"""What a research record IS, independent of how a project stores it.

Four things, and every check in `checks.py` is written against this interface rather than
against any project's file layout:

    work      things done or being done        (tickets, runs, jobs)
    questions things open and unanswered       (threads, issues)
    results   what was found, with provenance  (decisions, findings)
    claims    what the write-up asserts        (a paper, a report, a README)

One adapter ships. A project storing its record differently implements `Record` and gets
every check for free; that is the whole reason for the indirection.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field


@dataclass
class Item:
    """One unit of the record. `kind` is the adapter's own vocabulary."""

    id: str
    title: str
    body: str
    status: str = ""
    kind: str = ""
    created: str = ""

    #: A status is rarely a bare word. edit-slice writes
    #: `answered — **DENY: the coefficient bounds delivery**`, and an equality test read
    #: 38 of its 67 answered threads as open. Match the leading word, not the whole line.
    DONE_WORDS = ("closed", "split", "answered", "done", "resolved", "fixed", "complete")

    @property
    def done(self) -> bool:
        first = re.split(r"[^a-z]+", self.status.strip().lower(), maxsplit=1)[0]
        return first in self.DONE_WORDS


@dataclass
class Record:
    """A project's record, normalised."""

    root: str
    work: list[Item] = field(default_factory=list)
    questions: list[Item] = field(default_factory=list)
    results: list[Item] = field(default_factory=list)
    claims_text: str = ""
    claims_path: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(os.path.abspath(self.root))

    def ok(self) -> bool:
        return bool(self.work or self.questions or self.results)


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def _sections(src: str, pat: str, kind: str) -> list[Item]:
    out = []
    for m in re.finditer(pat, src, re.M | re.S):
        gid, title, body = m.group(1), m.group(2).strip(), m.group(3)
        status = (re.search(r"\*\*Status:\*\*\s*([^\n*]+)", body) or [0, ""])[1].strip()
        created = (re.search(r"\*\*(?:Created|Opened|Date):\*\*\s*(\S+)", body)
                   or [0, ""])[1].strip()
        out.append(Item(gid, title, body, status, kind, created))
    return out


def agentic(root: str) -> Record:
    """The author's cross-project template: plan.md, threads.md, agents/<role>/.

    Tolerant by design — a project using half the template still yields a usable record,
    because a checker that needs the full layout is one that runs on one project.
    """
    j = lambda *p: os.path.join(root, *p)  # noqa: E731
    work: list[Item] = []
    for rel, kind in (("agents/engineer/tickets.md", "ticket"),
                      ("agents/researcher/tickets.md", "ticket"),
                      ("agents/documentor/tickets.md", "ticket"),
                      ("agents/orchestrator/tickets.md", "ticket")):
        work += _sections(_read(j(rel)), r"^### ([A-Z]-\d+[a-z]?) · (.+?)$(.*?)(?=^### |\Z)",
                          kind)
    questions = _sections(_read(j("threads.md")),
                          r"^### (T-\d+) · (.+?)$(.*?)(?=^### |\Z)", "thread")
    results: list[Item] = []
    for rel, kind in (("agents/shared/decisions.md", "decision"),
                      ("agents/shared/findings.md", "finding")):
        results += _sections(_read(j(rel)),
                             r"^## \[([\w/-]+)\][: ]*(.*?)$(.*?)(?=^## \[|\Z)", kind)

    # the write-up: whatever this project points at, else the longest markdown it owns
    claims, cpath = "", ""
    for cand in ("review.md", "paper.md", "REPORT.md", "README.md"):
        for base in (root, os.path.join(root, "docs")):
            p = os.path.join(base, cand)
            if os.path.exists(p) and len(_read(p)) > len(claims):
                claims, cpath = _read(p), p
    return Record(root, work, questions, results, claims, cpath)


ADAPTERS = {"agentic": agentic}





def pipeline(root: str) -> Record:
    """A production pipeline's record — written against a second, private project, the second project.

    Different furniture, same four things, which is the point of the interface:

        questions  docs/gaps.md          numbered sections: the gap, evidence, fixes
        results    docs/critique-ledger.md   a table of causes, each with a status
        work       out/pipeline/<run>/   one directory per run, state.json inside

    Written to falsify the abstraction. If a second project had needed `checks.py` to
    change, the interface would have been edit-slice's shape wearing a general name.
    """
    j = lambda *p: os.path.join(root, *p)  # noqa: E731
    questions = _sections(_read(j("docs/gaps.md")),
                          r"^## \d+\. (.+?)$()(.*?)(?=^## |\Z)", "gap")
    for q in questions:                       # the heading is the title; synthesise ids
        q.title = q.id
    for n, q in enumerate(questions, 1):
        q.id = f"gap-{n}"
        q.status = "answered" if re.search(r"\*\*Fix(?:es)?\.\*\*|^- \*\*", q.body, re.M) \
            else "open"

    results: list[Item] = []
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|([^|]*)\|\s*([^|]+?)\s*\|",
                         _read(j("docs/critique-ledger.md")), re.M):
        cid, cause, words, status = m.groups()
        results.append(Item(f"cause-{cid}", cause.strip(), words.strip(),
                            status.strip(), "cause"))

    work: list[Item] = []
    pdir = j("out/pipeline")
    if os.path.isdir(pdir):
        for d in sorted(os.listdir(pdir)):
            full = os.path.join(pdir, d)
            if not os.path.isdir(full):
                continue
            st = _read(os.path.join(full, "state.json"))
            work.append(Item(d, d, st[:2000], "closed" if st else "open", "run"))

    claims, cpath = "", ""
    for cand in ("README.md", "docs/pipelines.md", "docs/art-direction.md"):
        p = j(cand)
        if os.path.exists(p) and len(_read(p)) > len(claims):
            claims, cpath = _read(p), p
    return Record(root, work, questions, results, claims, cpath)


ADAPTERS["pipeline"] = pipeline


def load_config(root: str) -> dict:
    """`.bearing.json` beside the project: {"adapter": ..., "claims": "relative/path"}.

    Needed because a project's write-up is not always inside it — `edit-slice`'s paper
    lives in a separate site directory, and guessing picked its README instead.
    """
    import json
    p = os.path.join(root, ".bearing.json")
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def load(root: str, adapter: str | None = None) -> Record:
    root = os.path.abspath(os.path.expanduser(root))
    cfg = load_config(root)
    rec = ADAPTERS[adapter or cfg.get("adapter", "agentic")](root)
    claims = cfg.get("claims")
    if claims:
        path = claims if os.path.isabs(claims) else os.path.join(root, claims)
        text = _read(path)
        if text:
            rec.claims_text, rec.claims_path = text, path
    return rec
