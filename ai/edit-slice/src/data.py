"""Dataset loading for edit-slice.

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

DEFAULT_COUNTERFACT: Final[Path] = (
    Path(__file__).resolve().parent.parent / "data" / "counterfact.json.gz"
)


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


def read_counterfact_bytes(path: Path = DEFAULT_COUNTERFACT) -> bytes:
    """Return the decompressed bytes, transparently handling .gz or plain .json."""
    if path.suffix == ".gz":
        with gzip.open(path, "rb") as fh:
            return fh.read()
    return path.read_bytes()


def load_counterfact(
    path: Path = DEFAULT_COUNTERFACT, *, verify: bool = True
) -> list[CounterFactRecord]:
    """Load pinned CounterFact, verifying integrity by default."""
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
