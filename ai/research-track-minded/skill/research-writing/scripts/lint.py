#!/usr/bin/env python3
"""Tier 1 lint: flag constructions absent from the reference corpus.

This is a FLOOR, not a quality gate. A passage can score 0.0 here and still say
nothing that could be wrong — measured directly in E-001, where the AI-generated
baseline scored 0.0/10k and carried exactly one falsifiable claim in 472 words.
Run the Tier 2 claim audit for anything that matters.

Blockquotes, fenced code and lines marked with a check or cross are skipped:
those are mention, not use.

Usage:  lint.py FILE [FILE ...]
        lint.py --rate FILE      # also print hits per 10k words
        lint.py --all FILE       # do not skip quoted material
"""
from __future__ import annotations

import re
import sys
import pathlib
from typing import Iterator, NamedTuple

class Rule(NamedTuple):
    name: str
    pattern: str
    fix: str

RULES: list[Rule] = [
    Rule("throat-clearing",
         r"\b(it is|it's) (important|worth) (to note|noting|mentioning)\b|\bit should be (noted|emphasi\w+)\b",
         "delete the frame; keep the sentence"),
    # Anchored at sentence start and requiring a subject: "in this post" as a
    # mid-sentence cross-reference is legitimate and must not fire.
    Rule("section pre-announcement",
         r"(?:^|[.!?]\s+)[Ii]n this (?:section|chapter|post),?\s+(?:we|I)\b"
         r"|\b[Ww]e begin by\b|\b[Tt]his section (?:will|describes)\b",
         "name the commitments, then deliver them in order"),
    Rule("additive connective",
         r"(?m)^\s*(Moreover|Furthermore|Additionally)\b",
         "delete, or name the actual relation"),
    Rule("hedge adverb",
         r"\b(arguably|potentially|somewhat|relatively|fairly|presumably|possibly)\b",
         "state it unhedged; put the specific limit in the Limits section"),
    Rule("register verb",
         r"\b(delve[sd]?|delving|leverag(e|es|ed|ing)|utili[sz](e|es|ed|ing))\b",
         "use, apply, examine"),
    Rule("importance adjective",
         r"\b(crucial|pivotal|vital|paramount|essential)\b",
         "give the quantity that makes it important"),
    Rule("abstraction noun",
         r"\b(landscape|realm|tapestry|space) of\b",
         "name the actual set"),
    Rule("assertive evidentiary verb",
         r"\b(underscore[sd]?|showcase[sd]?|demonstrat(es|ing) the importance)\b|\bhighlights the\b",
         "say what the result licenses, and what it does not"),
    Rule("reaction adverb",
         r"\b(Interestingly|Surprisingly|Notably|Remarkably|Importantly)\b",
         "delete, or say to whom it was surprising and why"),
    Rule("deferred number",
         r"\bas (can be seen|shown|we can see)\b|\bsee (Table|Figure) \d+ for\b",
         "put the number in the sentence making the claim"),
    Rule("recap",
         r"\b[Ii]n conclusion\b|\b[Tt]o summari[sz]e\b|\b[Ii]n summary\b|\b[Aa]s (we have|previously) (shown|discussed)\b",
         "end on an artifact, or end"),
    Rule("empty role",
         r"\bplays? an? \w+ role\b",
         "use the verb that says what it does"),
    # "the primary source" / "primary key" are fixed terms, not ranking claims.
    Rule("unquantified superlative",
         r"\bthe (?:clearest|leading|foremost)\b"
         r"|\bthe (?:main|primary) (?!source|sources|key)\w+"
         r"|\bone of the few\b"
         r"|\bthe most (?:promising|significant|important)\b",
         "give the criterion, or drop the ranking"),
]

# Quoted material is mention, not use: you do not lint text you are citing, and
# a style guide necessarily quotes the constructions it bans.
SKIP = re.compile(r"^\s*(>|```|\||\s*[-*]?\s*\[[ x]\])|[\u2717\u2713]")

# Inline mention: backticked, emphasised or quoted spans. Matched over the whole
# text rather than per line, because emphasis wraps across lines in real drafts —
# a span split by a newline otherwise leaves its second half exposed. Blanked to
# spaces, newlines preserved, so line numbers stay correct.
_SPAN = r"(?:[^{c}\n]|\n(?!\n))"
INLINE = re.compile(
    r"`[^`]*`"
    + rf"|\*\*{_SPAN.format(c='*')}+?\*\*"
    + rf"|\*{_SPAN.format(c='*')}+?\*"
    + rf"|\"{_SPAN.format(c='\"')}*?\""
    + rf"|\u201c{_SPAN.format(c='\u201d')}*?\u201d"
)

def _blank(m: re.Match[str]) -> str:
    return re.sub(r"[^\n]", " ", m.group(0))

def strip_mentions(text: str) -> str:
    """Blank out quoted/emphasised spans so mention is not linted as use."""
    return INLINE.sub(_blank, text)


def scan(text: str, skip_quoted: bool = True) -> Iterator[tuple[int, str, str, str]]:
    if skip_quoted:
        text = strip_mentions(text)
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if skip_quoted and (in_fence or SKIP.search(line)):
            continue
        for rule in RULES:
            for m in re.finditer(rule.pattern, line):
                yield lineno, rule.name, m.group(0), rule.fix

def main(argv: list[str]) -> int:
    show_rate = "--rate" in argv
    skip_quoted = "--all" not in argv
    paths = [pathlib.Path(a) for a in argv if not a.startswith("-")]
    if not paths:
        print(__doc__)
        return 2

    total = 0
    for path in paths:
        text = path.read_text()
        hits = list(scan(text, skip_quoted))
        total += len(hits)
        print(f"\n{path}")
        if not hits:
            print("  clean — note that this is the floor, not a pass")
        for lineno, name, match, fix in hits:
            print(f"  {lineno:>4}  {name:<28} {match!r}\n        → {fix}")
        if show_rate:
            words = len(re.findall(r"\b[a-zA-Z']+\b", text))
            rate = len(hits) / words * 10000 if words else 0.0
            print(f"  {len(hits)} hits / {words} words = {rate:.1f} per 10k")

    print(f"\n{total} total. Reference rates for this lint: hand-written research "
          f"prose 1.3/10k, published mech interp papers 11.6/10k, AI-generated "
          f"reports 13.9/10k.\nThe last two are close on purpose — this check "
          f"cannot tell a good paper from a bad report. Run the claim audit.")
    return 1 if total else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
