"""Run logging: levelled, to a file that is kept, and never filtered away.

This project has twice blinded itself by discarding output. A long NDIF run was
launched as `python gate_chains.py 2>&1 | grep -v ... | tail -30`; `tail` holds the
whole stream until EOF, so for the entire run nothing was visible — no retries, no
OOM auto-splits, no transport warnings — and the only liveness signal was watching
a cache file grow. Reporting "no errors" when the errors are merely invisible is
worse than reporting nothing.

Two rules follow, and both are enforced by using this module instead of `print`:

1. **The file record is never filtered.** The console view may be; the file gets
   everything at DEBUG. Filter what you read, never what you keep.
2. **Logs live in the repository.** Months later the question is not "did it work"
   but "what exactly ran, against which model, with which parameters, and what did
   it complain about". A results file answers the first; only a log answers the
   second.

    from logs import setup
    log = setup("gate_chains", config={"model": ..., "n_candidates": 50})
    log.info("scored %d/%d", i, n)
    log.warning("batch split after OOM: %d -> %d rows", before, after)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Final

#: Where a run's log file goes. `EDITREACH_LOGS` wins; otherwise the project
#: root is found by walking up from the working directory for a marker, and only
#: then does the package's own location get used.
LOG_ENV_VAR: Final[str] = "EDITREACH_LOGS"
#: `agents/` marks a project under the agentic template, which is what a run
#: belongs to. `.git` is NOT a marker: this workspace is one repository
#: holding many projects, so it would send edit-slice's logs to the repo
#: root and quietly move 79 scripts' output.
_MARKERS: Final[tuple[str, ...]] = ("agents", "pyproject.toml")


def _project_root() -> Path:
    """The directory a run belongs to, found rather than assumed.

    This module was lifted from edit-slice unchanged, where it sat at
    `src/logs.py` and `parent.parent` was therefore the project root. Here the
    package lives at `src/editreach/`, so the same expression resolved to
    `src/`, and a session's logs landed in `src/logs/` while every earlier
    session's sat in `logs/`. The record survived, split across two directories,
    which is the quiet half of a logging bug: nothing fails, the history just
    stops being in one place. Same class of fault as `data.py`'s `__file__`
    lookup, and fixed the same way.
    """
    for parent in (Path.cwd().resolve(), *Path.cwd().resolve().parents):
        if any((parent / m).exists() for m in _MARKERS):
            return parent
    return Path(__file__).resolve().parents[2]


def _log_dir() -> Path:
    env = os.environ.get(LOG_ENV_VAR)
    return Path(env).expanduser() if env else _project_root() / "logs"


ROOT: Final[Path] = Path(__file__).resolve().parents[2]

FILE_FORMAT: Final[str] = "%(asctime)s %(levelname)-8s %(name)s  %(message)s"
CONSOLE_FORMAT: Final[str] = "%(levelname)-7s %(message)s"


class _DeferredHeader:
    """Hold the run header until a real record arrives; emit nothing if none does.

    `setup()` used to announce the run immediately. Importing a run module
    therefore created a log file containing one line and nothing else, and the
    dry-runs import every run module — so each pass over the dry-run set left
    eight content-free files in a directory this project commits. Twenty of them
    accumulated in two days before anyone looked.

    The fix is not to suppress the header; a log that does not say what ran is
    the thing `_project_root`'s docstring complains about. It is to emit the
    header **only once something else is emitted**, so that importing a module
    costs nothing and running it still produces a self-describing record.

    Paired with `delay=True` on the file handler, which defers creating the file
    itself until its first write. Both halves are needed: `delay=True` alone
    does nothing when `setup()` immediately logs a line.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending: list[logging.LogRecord] = []
        self._flushed = False

    def add_header(self, record: logging.LogRecord) -> None:
        self._pending.append(record)

    def emit(self, record: logging.LogRecord) -> None:
        if not self._flushed:
            self._flushed = True        # set FIRST: the header emits recurse here
            pending, self._pending = self._pending, []
            for held in pending:
                super().emit(held)
        super().emit(record)


class _DeferredFileHandler(_DeferredHeader, logging.FileHandler):
    pass


class _DeferredStreamHandler(_DeferredHeader, logging.StreamHandler):
    pass


def setup(name: str, *, config: dict[str, Any] | None = None,
          console_level: int = logging.INFO,
          file_level: int = logging.DEBUG) -> logging.Logger:
    """A logger writing DEBUG to a kept file and `console_level` to stderr.

    `config` is written as the first line so a log is self-describing — a run whose
    parameters are not in its log cannot be interpreted later, which is the whole
    reason for keeping it.
    """
    log_dir = _log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = log_dir / f"{name}-{stamp}.log"

    # Handlers go on the ROOT logger, not a named one. Module loggers such as
    # `remote` propagate to root, and attaching to a named logger with
    # propagate=False means their warnings — the retries and OOM splits worth
    # knowing about — reach nothing. That silent miss is the failure this module
    # exists to prevent, so it must not be reproduced inside it.
    root = logging.getLogger()
    root.setLevel(min(console_level, file_level))
    root.handlers.clear()         # re-running in one process must not duplicate lines

    # `delay=True` so the file is not created until something is written to it.
    fh = _DeferredFileHandler(path, encoding="utf-8", delay=True)
    fh.setLevel(file_level)
    fh.setFormatter(logging.Formatter(FILE_FORMAT))
    root.addHandler(fh)

    # stderr, not stdout: a caller piping stdout to a filter cannot accidentally
    # swallow the log as well.
    sh = _DeferredStreamHandler(sys.stderr)
    sh.setLevel(console_level)
    sh.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    root.addHandler(sh)

    # Third-party transport chatter is useful at DEBUG in the file and noise on the
    # console; cap it so our own WARNINGs stay findable.
    for noisy in ("httpx", "httpcore", "urllib3", "websocket", "engineio",
                  "socketio", "nnsight", "matplotlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    log = logging.getLogger(name)

    # Held, not emitted. They go out ahead of the first real record, so a run
    # that logs anything still opens with what it is and what it was given, and
    # a module that is merely imported writes nothing anywhere.
    def _held(msg: str, *args) -> logging.LogRecord:
        return log.makeRecord(name, logging.INFO, __file__, 0, msg, args, None)

    # Relative when it can be, absolute when it cannot. `EDITREACH_LOGS` is a
    # documented way to put logs anywhere, and `relative_to` RAISES rather than
    # falling back -- so setting that variable to a directory outside the
    # project made `setup()` itself crash. Found by the dry-run that was being
    # written to check something else entirely.
    try:
        shown: Path | str = path.relative_to(ROOT)
    except ValueError:
        shown = path
    headers = [_held("run %s -> %s", name, shown)]
    if config:
        headers.append(_held("config %s",
                             json.dumps(config, sort_keys=True, default=str)))
    for h in (fh, sh):
        for rec in headers:
            h.add_header(rec)
    return log


def log_path(logger: logging.Logger | None = None) -> Path | None:
    """The active run's log file. Handlers live on root, so look there.

    The path exists as soon as `setup` runs; the FILE does not, until something
    is logged. Callers that want the file on disk must log something first.
    """
    for h in logging.getLogger().handlers:
        if isinstance(h, logging.FileHandler):
            return Path(h.baseFilename)
    return None


# --- de-noising a log that was captured before the redirect above existed ------

_ANSI = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]")
_SPINNER = re.compile(r"[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏◉✓⬇]")


def strip_progress(raw: str) -> str:
    """Collapse carriage-return animation into the lines a reader needs.

    A `tee` of an NDIF run keeps every frame of every spinner: one measured run was
    553 KB of which 262 of 266 logical lines were animation. The frames are not
    information — each overwrites the last on a terminal — so only the final frame
    of a run of identical-after-normalisation lines is kept. Nothing that is not a
    progress frame is dropped, which is the invariant that makes this safe to apply
    to a record we are keeping.
    """
    out: list[str] = []
    for chunk in raw.replace("\r", "\n").splitlines():
        line = _ANSI.sub("", chunk).rstrip()
        if not line:
            continue
        # A spinner frame differs from its predecessor only in the glyph and the
        # elapsed seconds; normalising both makes consecutive frames compare equal.
        key = _SPINNER.sub("", line)
        key = re.sub(r"\(\d+\.\d+s\)", "(Xs)", key)
        key = re.sub(r"\d+%\|[^|]*\|", "N%|", key)
        if out and key == out[-1][0]:
            out[-1] = (key, line)      # keep the last frame, not the first
        else:
            out.append((key, line))
    return "\n".join(line for _, line in out) + "\n"


if __name__ == "__main__":       # python src/logs.py logs/<file>.log
    for arg in sys.argv[1:]:
        p = Path(arg)
        before = p.read_text(errors="replace")
        after = strip_progress(before)
        p.write_text(after)
        print(f"{p.name}: {len(before):,}B / {before.count(chr(10)):,} lines"
              f"  ->  {len(after):,}B / {after.count(chr(10)):,} lines")
