"""Out-of-distribution test set: real CS abstract sentences, hand-labeled.

PubMed-RCT is biomedical; E-001 ingested CS/ML abstracts. R-001 flagged the
cross-domain gap as the thing E-002 must *measure*. This module holds a small set of
hand-labeled sentences drawn from the actual ingested output, keyed by
`(paper_id_suffix, sentence_index)` so the sentence text is joined verbatim from
`data/processed/sentences.jsonl` — no transcription drift.

Labeling rubric (hand-applied by the engineer, 2026-06-14):
  - BACKGROUND: context, motivation, prior work, problem statement, definitions.
  - METHOD: what was built/done — techniques, architecture, training, availability.
  - CLAIM: contributions ("we propose X") and findings/results ("we show", "achieves").
"""

from __future__ import annotations

import json
from pathlib import Path

_SENTENCES_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "sentences.jsonl"
)

# (paper_id_suffix, sentence_index) -> gold label. Suffix = last 6 chars of paper_id.
GOLD: dict[tuple[str, int], str] = {
    # Pro-GNN (W3081203761)
    ("203761", 0): "BACKGROUND",
    ("203761", 1): "BACKGROUND",
    ("203761", 10): "CLAIM",
    ("203761", 11): "CLAIM",
    ("203761", 12): "METHOD",
    # GraphDTA (W3096561213)
    ("561213", 0): "BACKGROUND",
    ("561213", 1): "BACKGROUND",
    ("561213", 6): "CLAIM",
    ("561213", 7): "CLAIM",
    ("561213", 8): "CLAIM",
    ("561213", 9): "METHOD",
    # MIS branching (W4294558607)
    ("558607", 0): "BACKGROUND",
    ("558607", 1): "BACKGROUND",
    ("558607", 8): "CLAIM",
    ("558607", 10): "METHOD",
    ("558607", 11): "CLAIM",
    # SURGE (W3178835722)
    ("835722", 0): "BACKGROUND",
    ("835722", 1): "BACKGROUND",
    ("835722", 4): "CLAIM",
    ("835722", 5): "METHOD",
    ("835722", 7): "METHOD",
    ("835722", 9): "METHOD",
    ("835722", 10): "CLAIM",
    ("835722", 11): "CLAIM",
    # GNN-recsys survey (W4315977496)
    ("977496", 0): "BACKGROUND",
    ("977496", 1): "BACKGROUND",
    # LeNet (W2112796928)
    ("796928", 0): "BACKGROUND",
    # GNN model (W2116341502)
    ("341502", 0): "BACKGROUND",
    # GNN survey (W2907492528)
    ("492528", 0): "BACKGROUND",
    # AlexNet (W...605009)
    ("605009", 0): "METHOD",
    ("605009", 1): "CLAIM",
    ("605009", 2): "METHOD",
    ("605009", 3): "METHOD",
}


def load_ood() -> list[tuple[str, str]]:
    """Return [(sentence_text, gold_label), ...] by joining GOLD with ingested text.

    Requires E-001 output at data/processed/sentences.jsonl.
    """
    if not _SENTENCES_PATH.exists():
        raise FileNotFoundError(
            f"{_SENTENCES_PATH} not found — run `python -m src.ingestion` first."
        )
    index: dict[tuple[str, int], str] = {}
    for line in _SENTENCES_PATH.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["section"] != "abstract":
            continue
        suffix = r["paper_id"][-6:]
        index[(suffix, r["sentence_index"])] = r["text"]

    out: list[tuple[str, str]] = []
    missing: list[tuple[str, int]] = []
    for key, gold in GOLD.items():
        text = index.get(key)
        if text is None:
            missing.append(key)
        else:
            out.append((text, gold))
    if missing:
        raise RuntimeError(
            f"OOD keys not found in ingested data: {missing}. "
            "Re-run ingestion with the same query, or update GOLD keys."
        )
    return out
