"""Check the diagnostic set before it costs a single remote call.

edit-slice's habit, kept: a run that reaches NDIF with a malformed set burns
queue time and comes back with numbers nobody can interpret. Every check here
is structural and offline. It does not say the set is a good one — only that it
is a set whose readings could be interpreted.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from editreach.coefficient import Regime                       # noqa: E402
from editreach.rome import SubjectNotInPrompt, subject_last_index  # noqa: E402
from probes.diagnostic import ITEMS, OTHER, SUBJECT            # noqa: E402


class _Tok:
    """Stands in for a tokenizer. Index arithmetic only; no model is loaded."""

    def __call__(self, text):
        class _R:
            input_ids = list(range(len(text)))
        return _R()


def main() -> int:
    tok, failures, checks = _Tok(), [], 0

    def check(cond: bool, what: str) -> None:
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(what)

    check(len({i.id for i in ITEMS}) == len(ITEMS), "item ids are unique")
    check(all(i.why.strip() for i in ITEMS), "every item says why it predicts what it does")
    check(all(len(i.why) > 60 for i in ITEMS), "no why is a stub")

    # A band that is a point is a fitted number wearing a prediction's clothes.
    for i in ITEMS:
        if i.band is not None:
            lo, hi = i.band
            check(lo < hi, f"{i.id}: band is non-empty")
            check(0.0 <= lo and hi <= 1.01, f"{i.id}: band is inside [0, 1]")

    # The anchors are what make every other reading legible. They must bracket.
    anchor = next(i for i in ITEMS if i.id == "anchor-prefix")
    floor = next(i for i in ITEMS if i.id == "anchor-floor")
    check(anchor.band is not None and floor.band is not None, "both anchors are predicted")
    check(floor.band[1] < anchor.band[0], "the floor's band sits below the anchor's")

    # The far-field item must NOT name its subject, or it is not a far-field item.
    far = [i for i in ITEMS if i.family == "far-field"]
    check(bool(far), "the set contains a far-field item")
    for i in far:
        check(i.subject not in i.prompt, f"{i.id}: reaches its entity by description")
        try:
            subject_last_index(tok, i.prompt, i.subject)
            failures.append(f"{i.id}: absent subject was assigned a position")
        except SubjectNotInPrompt:
            pass
        checks += 1

    # Every other item must contain its subject, or its index is meaningless.
    for i in ITEMS:
        if i.family == "far-field":
            continue
        check(i.subject in i.prompt, f"{i.id}: subject occurs in the prompt")

    # The repetition family exists to catch a silent wrong reading. If the two
    # occurrences gave the same index, the family would be testing nothing.
    for i in ITEMS:
        if i.family == "repetition":
            check(i.subject_occurrences >= 2, f"{i.id}: has more than one mention")
            first = subject_last_index(tok, i.prompt, i.subject)
            last = subject_last_index(tok, i.prompt, i.subject, occurrence=-1)
            check(first != last, f"{i.id}: first and last mention differ, so the choice bites")
            check(subject_last_index(tok, i.prompt, i.subject, occurrence=i.occurrence)
                  in (first, last), f"{i.id}: its stated occurrence resolves")

    # Prefix-sharing is a claim about the prompt, not a label. Check it holds.
    for i in ITEMS:
        if i.family == "far-field":
            continue
        # The regime is a property of the MENTION being read, not of the prompt.
        # The first version of this check tested the prompt and failed the
        # repetition family, correctly.
        if i.regime is Regime.PREFIX_SHARING:
            check(i.reads_at_prefix, f"{i.id}: the mention it reads is at the prefix")
        else:
            check(not i.reads_at_prefix,
                  f"{i.id}: labelled PRECEDED, so the mention it reads has text before it")

    # The floor item must use a different person, or it is not a floor.
    check(floor.subject == OTHER != SUBJECT, "the floor item uses a different subject")

    # An all-OPEN set cannot fail, and a set that cannot fail is not a check.
    check(sum(1 for i in ITEMS if not i.is_open) >= 4,
          "at least four items carry a falsifiable band")

    print(f"{checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL  {f}")
    if not failures:
        banded = sum(1 for i in ITEMS if not i.is_open)
        print(f"\n{len(ITEMS)} items: {banded} with a band to violate, "
              f"{len(ITEMS) - banded} open questions.")
        print("Zero remote calls made.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
