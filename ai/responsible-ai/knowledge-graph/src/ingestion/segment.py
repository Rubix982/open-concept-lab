"""Lightweight sentence segmentation.

We deliberately avoid a heavy NLP dependency (spaCy / nltk are not in the venv) for
this slice. This is a rule-based splitter tuned for scientific abstracts: it splits on
sentence-final punctuation followed by whitespace + a capital/digit, while guarding a
short list of common abbreviations (e.g., i.e., et al., Fig., vs.).

Tradeoff recorded in agents/shared/decisions.md → [E-001]. If segmentation quality
turns out to gate downstream quality, swap in a real segmenter behind this same
`split_sentences` interface.
"""

from __future__ import annotations

import re

# Abbreviations whose trailing period must NOT end a sentence.
_ABBREVIATIONS: frozenset[str] = frozenset(
    {
        "e.g", "i.e", "et al", "etc", "cf", "vs", "fig", "eq", "no",
        "al", "ref", "sec", "approx", "dr", "prof", "mr", "ms", "mrs",
        "st", "vol", "pp", "ch", "resp",
    }
)

# Candidate sentence boundary: . ! or ? possibly followed by ) " ' then whitespace,
# then an uppercase letter, digit, or opening quote/paren (start of next sentence).
_BOUNDARY = re.compile(r'([.!?])(["\')\]]?)\s+(?=[A-Z0-9"\'(\[])')


def _looks_like_abbreviation(text: str, period_pos: int) -> bool:
    """Return True if the period at `period_pos` likely belongs to an abbreviation."""
    # Grab the token immediately preceding the period.
    start = period_pos
    while start > 0 and (text[start - 1].isalpha() or text[start - 1] == "."):
        start -= 1
    token = text[start:period_pos].lower().rstrip(".")
    if token in _ABBREVIATIONS:
        return True
    # Single capital letter initial, e.g. "J. Smith".
    if len(token) == 1 and token.isalpha():
        return True
    return False


def split_sentences(text: str) -> list[tuple[int, int, str]]:
    """Split `text` into sentences.

    Returns a list of (char_start, char_end, sentence_text) over the *original* string,
    so offsets are valid provenance into `text`.
    """
    text = text.strip()
    if not text:
        return []

    spans: list[tuple[int, int, str]] = []
    start = 0
    for match in _BOUNDARY.finditer(text):
        period_pos = match.start(1)
        if _looks_like_abbreviation(text, period_pos):
            continue
        end = match.end(2)  # include trailing punctuation/quote, exclude the space
        sentence = text[start:end].strip()
        if sentence:
            # Recompute exact offsets of the stripped sentence within `text`.
            lead = len(text[start:end]) - len(text[start:end].lstrip())
            s0 = start + lead
            spans.append((s0, s0 + len(sentence), sentence))
        start = match.end()

    tail = text[start:].strip()
    if tail:
        lead = len(text[start:]) - len(text[start:].lstrip())
        s0 = start + lead
        spans.append((s0, s0 + len(tail), tail))

    return spans
