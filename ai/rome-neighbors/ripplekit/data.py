"""RippleEdits loading — the schema-verified, defensive loader (see readings/MAP.md).

Verified against popular.json/random.json (2026-08-11):
  entry.edit.prompt                          → edited-fact statement (BASE anchor)
  entry.<Criterion>                          → LIST of query-groups
  entry.<Criterion>[g].test_queries[].prompt → neighbour prompts
  test_queries[].answers[0].value            → gold answer
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import config


@dataclass
class Pair:
    """One (base fact, typed neighbour) pair."""
    base: str          # edit.prompt
    neighbour: str     # neighbour query prompt
    answer: str        # neighbour gold answer (value)
    type: str          # our neighbour type (paraphrase/1hop/2hop/locality/control)


def _norm(k: str) -> str:
    return k.strip().lower().replace(" ", "_")


def _answer_of(q: dict[str, Any]) -> str | None:
    anss = q.get("answers") or []
    return anss[0].get("value") if anss and isinstance(anss[0], dict) else None


def load_entries(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or config.RIPPLEEDITS_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"RippleEdits file not found at {path}. Clone edenbiran/RippleEdits and "
            f"set RIPPLEEDITS_FILE, or edit config.RIPPLEEDITS_FILE."
        )
    return json.loads(path.read_text())


def load_pairs(
    path: Path | None = None,
    n_edits: int = config.N_EDITS,
    max_per_criterion: int = config.MAX_PER_CRITERION,
    seed: int = config.SEED,
) -> list[Pair]:
    """Subsample `n_edits` edits and flatten to typed (base, neighbour) pairs."""
    entries = load_entries(path)
    random.Random(seed).shuffle(entries)
    pairs: list[Pair] = []
    for e in entries[:n_edits]:
        base = (e.get("edit") or {}).get("prompt")
        if not base:
            continue
        for key, val in e.items():
            ntype = config.CRITERION_TO_TYPE.get(_norm(key))
            if ntype is None or not isinstance(val, list):
                continue
            collected: list[tuple[str, str]] = []
            for group in val:
                if not isinstance(group, dict):
                    continue
                for q in group.get("test_queries") or []:
                    p, a = (q.get("prompt"), _answer_of(q)) if isinstance(q, dict) else (None, None)
                    if p and a:
                        collected.append((p, a))
            for p, a in collected[:max_per_criterion]:
                pairs.append(Pair(base=base, neighbour=p, answer=a, type=ntype))
    return pairs


def answer_index(path: Path | None = None) -> dict[str, set[str]]:
    """Map each gold-answer value → the set of prompts that elicit it (for anchors)."""
    idx: dict[str, set[str]] = {}
    for e in load_entries(path):
        for _, val in e.items():
            if not isinstance(val, list):
                continue
            for group in val:
                if not isinstance(group, dict):
                    continue
                for q in group.get("test_queries") or []:
                    a, p = (_answer_of(q), q.get("prompt")) if isinstance(q, dict) else (None, None)
                    if a and p:
                        idx.setdefault(a, set()).add(p)
    return idx
