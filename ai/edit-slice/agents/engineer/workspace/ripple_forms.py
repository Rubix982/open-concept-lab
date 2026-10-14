"""Where does the subject sit in RippleEdits' prompts? Counted across every subset.

    .venv/bin/python agents/engineer/workspace/ripple_forms.py

Runs [R-013]. §7 of the write-up asserted that "every propagation benchmark we know of
probes with prompts that begin with the subject", having inspected none. This counts.

**No entity resolution is needed and that is the point.** The released prompts carry the
subject as a Wikidata QID; some are materialised ("The place of birth of Leo Arons is"),
some leave the slot empty ("The name of the field of work of  is"). Either way the
subject's POSITION is visible, and position is the entire claim. Twenty minutes against a
priced week.
"""
from __future__ import annotations

import glob
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, "data", "ripple")
CRIT = ["Logical_Generalization", "Compositionality_I", "Compositionality_II",
        "Subject_Aliasing", "Relation_Specificity", "Forgetfulness"]


def subject_label(entry: dict) -> str | None:
    """The materialised subject, taken as the LONGEST candidate this entry offers.

    The first version took the first candidate it found and left 17,206 prompts
    unclassifiable — more than a third of the corpus, which is not a measurement. Entries
    carry the label in several shapes ("... of Leo Arons is", "... of Martin Leo Arons
    is"); the longest is the one most likely to be the full name, and a prompt starting
    with a shorter alias is still caught because `startswith` is tested against each.
    """
    cands: set[str] = set()
    for c in CRIT:
        for grp in entry.get(c) or []:
            for t in grp.get("test_queries") or []:
                p = t.get("prompt")
                if not isinstance(p, str):
                    continue
                for pat in (r" of (.+?) is$", r" of (.+?) are$", r"^Is (.+?) still alive\?$",
                            r" of (.+?), which", r" which (.+?) is associated"):
                    m = re.search(pat, p)
                    if m and m.group(1) and m.group(1)[0].isupper():
                        cands.add(m.group(1).strip())
    # `max` over a SET is nondeterministic when two candidates tie on length — two runs
    # of this file differed by 15 prompts before this line was sorted. A measurement that
    # changes between runs is not a measurement.
    return max(sorted(cands), key=len) if cands else None


def position(prompt: str, subj: str | None) -> str:
    """initial | later | unknown — by the empty slot, or by the materialised label."""
    m = re.search(r"\s{2,}", prompt)
    if m is not None:
        return "initial" if m.start() <= 1 else "later"
    if subj and subj in prompt:
        return "initial" if prompt.startswith(subj) else "later"
    # No slot and no label match. Nearly every prompt in this corpus opens with a
    # determiner or auxiliary; a prompt that does not is one we cannot place, and it is
    # reported as unknown rather than guessed.
    return "unknown"


def main() -> int:
    files = sorted(glob.glob(os.path.join(DATA, "*.json")))
    if not files:
        print("no benchmark files — run fetch_ripple.py first")
        return 1
    grand: Counter = Counter()
    print(f"{'subset':<10}{'criterion':<24}{'initial':>9}{'later':>9}{'unknown':>9}")
    for f in files:
        name = os.path.basename(f).replace(".json", "")
        entries = json.load(open(f, encoding="utf-8"))
        per: Counter = Counter()
        for e in entries:
            subj = subject_label(e)
            for c in CRIT:
                for grp in e.get(c) or []:
                    for t in grp.get("test_queries") or []:
                        p = t.get("prompt")
                        if isinstance(p, str) and p:
                            per[(c, position(p, subj))] += 1
        for c in CRIT:
            i, lt, u = per[(c, "initial")], per[(c, "later")], per[(c, "unknown")]
            grand["initial"] += i
            grand["later"] += lt
            grand["unknown"] += u
            print(f"{name:<10}{c:<24}{i:>9,}{lt:>9,}{u:>9,}")
        print(f"{'':<10}{'— entries: ' + format(len(entries), ','):<24}"
              f"{sum(v for k, v in per.items() if k[1] == 'initial'):>9,}"
              f"{sum(v for k, v in per.items() if k[1] == 'later'):>9,}"
              f"{sum(v for k, v in per.items() if k[1] == 'unknown'):>9,}\n")
    tot = sum(grand.values())
    print(f"{'ALL':<34}{grand['initial']:>9,}{grand['later']:>9,}{grand['unknown']:>9,}")
    print(f"\n  subject-initial: {grand['initial']:,} of {tot:,} "
          f"= {100 * grand['initial'] / tot:.2f}%")
    if grand["initial"] == 0:
        print("\n  §7's premise is FALSE for this benchmark: not one prompt begins with\n"
              "  its subject. See [R-013]. The consequence survives in a sharper form —\n"
              "  [E-019] measured 0.95-0.96 for subject-LATE probes at layer 5, which is\n"
              "  the layer EasyEdit edits, so the benchmark's own form still receives\n"
              "  ~95% of the update. That is [E-036].")
    out = os.path.join(ROOT, "results", "R-013-ripple-forms.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"finding": "R-013", "counts": dict(grand), "files": [
            os.path.basename(f) for f in files]}, fh, indent=1)
    print(f"\n  written: {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
