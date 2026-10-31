"""Dataset loading for edit-slice.

Import convention: this is a real package. `from editreach.data import
load_counterfact` works from anywhere the package is installed. The edit-slice
original required `src/` on `sys.path` and broke under `src.data`; that is the
wart this package was made to remove.

Loading is a module with a typed interface, separate from probing, metrics and
reporting (CLAUDE.md, "Stack and conventions").

CounterFact is **pinned** in `data/counterfact.json.gz` rather than fetched at
runtime. The upstream host can change or disappear; a result that cannot be
reproduced against the exact bytes it was computed from is not reproducible.
Integrity is checked against the SHA-256 of the *decompressed* content, because
gzip headers carry mtime and are not byte-stable across runs.
"""

from __future__ import annotations

import gzip
import os
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

#: SHA-256 of the decompressed counterfact.json as published by the ROME authors.
COUNTERFACT_SHA256: Final[str] = (
    "d017056125178a13728594e66a801357a8db9ed7973a7425554bb4271de9fc6f"
)
COUNTERFACT_RECORDS: Final[int] = 21919
COUNTERFACT_URL: Final[str] = "https://rome.baulab.info/data/dsets/counterfact.json"

#: Where the pinned corpus lives. Deliberately NOT derived from this file's
#: location: that worked while the module sat inside the project that owned the
#: data, and broke silently the moment it became an installed package, resolving
#: to `site-packages/data/`. A library has no business assuming it sits next to
#: a dataset. Set `EDITREACH_DATA` to the directory holding it, or pass `path=`.
DATA_ENV_VAR: Final[str] = "EDITREACH_DATA"
COUNTERFACT_FILENAME: Final[str] = "counterfact.json.gz"


def _search_upwards(start: Path) -> Path | None:
    """Look for `data/<file>` from `start` up to the filesystem root."""
    for parent in (start, *start.parents):
        candidate = parent / "data" / COUNTERFACT_FILENAME
        if candidate.is_file():
            return candidate
    return None


def default_counterfact() -> Path:
    """The pinned corpus, found explicitly rather than assumed.

    `EDITREACH_DATA` wins. Otherwise the working directory and its parents are
    searched, which finds it from anywhere inside a project that owns a copy.
    Raises rather than returning a path that does not exist, because the
    downstream failure is a `FileNotFoundError` naming a directory nobody
    recognises.
    """
    env = os.environ.get(DATA_ENV_VAR)
    if env:
        p = Path(env).expanduser()
        p = p / COUNTERFACT_FILENAME if p.is_dir() else p
        if not p.is_file():
            raise FileNotFoundError(f"{DATA_ENV_VAR}={env!r} but {p} is not a file")
        return p
    found = _search_upwards(Path.cwd().resolve())
    if found is None:
        raise FileNotFoundError(
            f"no data/{COUNTERFACT_FILENAME} found from {Path.cwd()} upwards. "
            f"Set {DATA_ENV_VAR} to the directory holding it, or pass path=."
        )
    return found


class IntegrityError(RuntimeError):
    """Raised when pinned data does not match its recorded checksum."""


@dataclass(frozen=True)
class Rewrite:
    """One CounterFact edit request."""

    prompt: str
    relation_id: str
    subject: str
    target_true: str
    target_new: str


@dataclass(frozen=True)
class CounterFactRecord:
    case_id: int
    rewrite: Rewrite
    paraphrase_prompts: list[str]
    neighborhood_prompts: list[str]

    @classmethod
    def from_raw(cls, raw: dict) -> CounterFactRecord:
        rw = raw["requested_rewrite"]
        return cls(
            case_id=raw["case_id"],
            rewrite=Rewrite(
                prompt=rw["prompt"],
                relation_id=rw["relation_id"],
                subject=rw["subject"],
                target_true=rw["target_true"]["str"],
                target_new=rw["target_new"]["str"],
            ),
            paraphrase_prompts=raw.get("paraphrase_prompts", []),
            neighborhood_prompts=raw.get("neighborhood_prompts", []),
        )


def read_counterfact_bytes(path: Path | None = None) -> bytes:
    """Return the decompressed bytes, transparently handling .gz or plain .json."""
    if path.suffix == ".gz":
        path = Path(path) if path is not None else default_counterfact()
    with gzip.open(path, "rb") as fh:
            return fh.read()
    return path.read_bytes()


def load_counterfact(
    path: Path | None = None, *, verify: bool = True
) -> list[CounterFactRecord]:
    """Load pinned CounterFact, verifying integrity by default.

    `path` defaults to `default_counterfact()`, which reads `EDITREACH_DATA` or
    searches upwards from the working directory.
    """
    path = Path(path) if path is not None else default_counterfact()
    payload = read_counterfact_bytes(path)

    if verify:
        digest = hashlib.sha256(payload).hexdigest()
        if digest != COUNTERFACT_SHA256:
            raise IntegrityError(
                f"{path} decompresses to sha256 {digest}, expected "
                f"{COUNTERFACT_SHA256}. The pin is broken — do not report results "
                f"from this file."
            )

    records = [CounterFactRecord.from_raw(r) for r in json.loads(payload)]
    if verify and len(records) != COUNTERFACT_RECORDS:
        raise IntegrityError(
            f"expected {COUNTERFACT_RECORDS} records, got {len(records)}"
        )
    return records
