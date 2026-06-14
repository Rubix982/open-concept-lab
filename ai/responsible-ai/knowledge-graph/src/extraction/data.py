"""PubMed-RCT loader (raw source files, no `datasets` dependency — see [E-002]).

Downloads PubMed_20k_RCT/{train,dev,test}.txt from the source repo, caches them, and
parses the `LABEL\\tsentence` format into our 3-class scheme.

Label mapping (from R-001):
    BACKGROUND, OBJECTIVE -> BACKGROUND
    METHODS               -> METHOD
    RESULTS, CONCLUSIONS  -> CLAIM
"""

from __future__ import annotations

import random
from collections import Counter
from pathlib import Path

import requests

from .model import LABEL2ID

_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "pubmed_rct_20k"
_BASE_URL = (
    "https://raw.githubusercontent.com/Franck-Dernoncourt/pubmed-rct/"
    "master/PubMed_20k_RCT"
)

# PubMed-RCT label -> our label
_LABEL_MAP: dict[str, str] = {
    "BACKGROUND": "BACKGROUND",
    "OBJECTIVE": "BACKGROUND",
    "METHODS": "METHOD",
    "RESULTS": "CLAIM",
    "CONCLUSIONS": "CLAIM",
}

_SPLITS = ("train", "dev", "test")


def _download(split: str) -> Path:
    _RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = _RAW_DIR / f"{split}.txt"
    if not path.exists():
        url = f"{_BASE_URL}/{split}.txt"
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        path.write_text(resp.text, encoding="utf-8")
    return path


def _parse(path: Path) -> list[tuple[str, int]]:
    """Parse a PubMed-RCT file into (sentence, our_label_id) pairs."""
    pairs: list[tuple[str, int]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("###"):
            continue
        if "\t" not in line:
            continue
        raw_label, sentence = line.split("\t", 1)
        our_label = _LABEL_MAP.get(raw_label.strip().upper())
        sentence = sentence.strip()
        if our_label and sentence:
            pairs.append((sentence, LABEL2ID[our_label]))
    return pairs


def _balanced_cap(
    pairs: list[tuple[str, int]], cap_per_class: int, seed: int
) -> list[tuple[str, int]]:
    """Downsample to at most `cap_per_class` examples per class (balance + speed)."""
    rng = random.Random(seed)
    by_class: dict[int, list[tuple[str, int]]] = {}
    for p in pairs:
        by_class.setdefault(p[1], []).append(p)
    out: list[tuple[str, int]] = []
    for label_id, items in by_class.items():
        rng.shuffle(items)
        out.extend(items[:cap_per_class])
    rng.shuffle(out)
    return out


def get_splits(
    train_cap_per_class: int = 8000,
    seed: int = 42,
) -> dict[str, list[tuple[str, int]]]:
    """Return {'train','dev','test'} -> list of (sentence, label_id).

    Train is balanced-capped for speed; dev/test are used in full (honest eval on the
    natural distribution).
    """
    splits: dict[str, list[tuple[str, int]]] = {}
    for split in _SPLITS:
        pairs = _parse(_download(split))
        if split == "train":
            pairs = _balanced_cap(pairs, train_cap_per_class, seed)
        splits[split] = pairs
    return splits


def describe(splits: dict[str, list[tuple[str, int]]]) -> str:
    from .model import ID2LABEL

    lines: list[str] = []
    for split, pairs in splits.items():
        counts = Counter(ID2LABEL[lid] for _, lid in pairs)
        lines.append(f"  {split:5s} n={len(pairs):6d}  {dict(counts)}")
    return "\n".join(lines)
