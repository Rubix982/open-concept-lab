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
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final[Path] = Path(__file__).resolve().parent.parent
LOG_DIR: Final[Path] = ROOT / "logs"

FILE_FORMAT: Final[str] = "%(asctime)s %(levelname)-8s %(name)s  %(message)s"
CONSOLE_FORMAT: Final[str] = "%(levelname)-7s %(message)s"


def setup(name: str, *, config: dict[str, Any] | None = None,
          console_level: int = logging.INFO,
          file_level: int = logging.DEBUG) -> logging.Logger:
    """A logger writing DEBUG to a kept file and `console_level` to stderr.

    `config` is written as the first line so a log is self-describing — a run whose
    parameters are not in its log cannot be interpreted later, which is the whole
    reason for keeping it.
    """
    LOG_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    path = LOG_DIR / f"{name}-{stamp}.log"

    # Handlers go on the ROOT logger, not a named one. Module loggers such as
    # `remote` propagate to root, and attaching to a named logger with
    # propagate=False means their warnings — the retries and OOM splits worth
    # knowing about — reach nothing. That silent miss is the failure this module
    # exists to prevent, so it must not be reproduced inside it.
    root = logging.getLogger()
    root.setLevel(min(console_level, file_level))
    root.handlers.clear()         # re-running in one process must not duplicate lines

    fh = logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(file_level)
    fh.setFormatter(logging.Formatter(FILE_FORMAT))
    root.addHandler(fh)

    # stderr, not stdout: a caller piping stdout to a filter cannot accidentally
    # swallow the log as well.
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(console_level)
    sh.setFormatter(logging.Formatter(CONSOLE_FORMAT))
    root.addHandler(sh)

    # Third-party transport chatter is useful at DEBUG in the file and noise on the
    # console; cap it so our own WARNINGs stay findable.
    for noisy in ("httpx", "httpcore", "urllib3", "websocket", "engineio",
                  "socketio", "nnsight", "matplotlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    log = logging.getLogger(name)
    log.info("run %s -> %s", name, path.relative_to(ROOT))
    if config:
        log.info("config %s", json.dumps(config, sort_keys=True, default=str))
    return log


def log_path(logger: logging.Logger | None = None) -> Path | None:
    """The active run's log file. Handlers live on root, so look there."""
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
