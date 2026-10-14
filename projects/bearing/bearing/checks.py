"""The questions. Each phrased so that the BAD answer is the computable one.

A check that cannot come back bad is a horoscope. Each returns:

    q        the question, as it would be asked out loud
    bad      whether the answer is uncomfortable
    say      the answer, in a sentence a person can act on
    why      the incident that made this question worth asking
    detail   the evidence, so disagreeing is cheap
    soft     True if the check is a heuristic rather than a measurement

Written against `record.Record` only. Two projects of very different shape — a research
record and a production pipeline — run the same list; if either had needed a special case,
the interface would be one project's habits wearing a general name.
"""
from __future__ import annotations

import os
import re
import subprocess
from collections import Counter

from .record import Record

# Dimensions a project might hold fixed. Matched against the text of finished work; a
# project with its own vocabulary extends this rather than editing the checks.
DIMENSIONS = {
    "model / subject": r"\bmodel\b|\bsubject\b|\bfigure\b",
    "method": r"\bmethod\b|ROME|MEMIT|fine-tun|algorithm|pipeline variant",
    "scale": r"\bscale\b|\bparam|\bsize\b|\bresolution\b",
    "dataset / source": r"dataset|corpus|CounterFact|catalogue|benchmark|photo set",
    "parameter": r"\blayer\b|\bstep\b|\bthreshold\b|\bseed\b",
    "measure": r"\bmetric\b|\bmeasure\b|\bscore\b|\bprobe\b",
}

OUTWARD = (r"other people|the field|published|benchmark|externally|someone outside|"
           r"practitioner|re-?scor|changes what|users?\b|customer|shipped")
INWARD = (r"our (?:measure|claim|record|own)|this project|internal|our instrument|"
          r"\[E-0|\[T-0|our pipeline|the harness")


def _done(items):
    return [i for i in items if i.done]


def never_varied(r: Record) -> dict:
    counts = Counter()
    for it in _done(r.work) + _done(r.results):
        if not re.search(r"vary|varie|across|swept|sweep|compar", it.body, re.I):
            continue
        for d, pat in DIMENSIONS.items():
            if re.search(pat, it.body, re.I):
                counts[d] += 1
    never = [d for d in DIMENSIONS if counts[d] == 0]
    return {"q": "What have you never varied?", "bad": bool(never),
            "why": "every narrowing in edit-slice came from unfixing a held dimension",
            "say": (f"Never varied in finished work: **{', '.join(never)}**."
                    if never else "Every dimension has been varied at least once."),
            "detail": dict(counts)}


def inward_drift(r: Record, window: int = 5) -> dict:
    recent = _done(r.work)[-window:] or _done(r.results)[-window:]
    rows = []
    for it in recent:
        o, i = len(re.findall(OUTWARD, it.body, re.I)), len(re.findall(INWARD, it.body, re.I))
        rows.append((it.id, "outward" if o > i else "inward", o, i))
    inward = [x for x in rows if x[1] == "inward"]
    n = len(rows)
    return {"q": f"Do the last {n} finished items measure your instrument, or the world?",
            "bad": n > 0 and len(inward) >= max(3, int(0.8 * n)),
            "why": "a run of inward work is how a project stops being able to say its point",
            "say": (f"**{len(inward)} of the last {n}** lean inward "
                    f"({', '.join(x[0] for x in inward)})."
                    if inward else f"{n} recent items, none leaning inward."),
            "detail": rows, "soft": True}


def claim_debt(r: Record) -> dict:
    """Claims resting on work that is not finished and not written up anywhere."""
    cited = set(re.findall(r'id="(?:f-)?([A-Z]-\d+[a-z]?)"', r.claims_text))
    cited |= set(re.findall(r"\[([A-Z]-\d+[a-z]?)\]", r.claims_text))
    # A cited open QUESTION is not claim debt — a write-up that lists what it does not
    # know is doing the right thing, and edit-slice's §8 exists for exactly that. The
    # first version flagged nine of its open threads and made the check worthless.
    questions = {i.id for i in r.questions}
    known = {i.id for i in _done(r.work)} | {i.id for i in r.results} | questions
    dangling = sorted(cited - known)
    return {"q": "Does the write-up cite work that is not finished?",
            "bad": bool(dangling),
            "why": "edit-slice's §4.5 asserted a withdrawn claim for nine days",
            "say": (f"Cites **{', '.join(dangling[:6])}** with nothing behind them."
                    if dangling else f"All {len(cited)} cited items are recorded."),
            "detail": dangling}


def summary_staleness(r: Record) -> dict:
    """Results landed since the top of the write-up last moved."""
    if not r.claims_path or not os.path.exists(r.claims_path):
        return {"q": "Is the summary still about this project?", "bad": False,
                "why": "", "say": "no write-up configured", "detail": {}}
    head = "\n".join(r.claims_text.splitlines()[:60])
    anchor = next((ln for ln in head.splitlines()
                   if re.match(r"^#{1,2} ", ln) and "abstract" in ln.lower()), None) \
        or next((ln for ln in head.splitlines() if re.match(r"^#{1,2} ", ln)), "#")
    try:
        repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=r.root,
                              capture_output=True, text=True).stdout.strip()
        last = subprocess.run(["git", "log", "-1", "--format=%cd", "--date=short",
                               "-S", anchor.strip(), "--", r.claims_path],
                              cwd=repo, capture_output=True, text=True).stdout.strip()
        if not last:
            return {"q": "Is the summary still about this project?", "bad": False,
                    "why": "", "say": "no history for the summary", "detail": {}}
        since = subprocess.run(["git", "log", "--oneline", f"--since={last}", "--", r.root],
                               cwd=repo, capture_output=True, text=True).stdout
    except Exception:
        return {"q": "Is the summary still about this project?", "bad": False,
                "why": "", "say": "no git history", "detail": {}}
    n = len([x for x in since.splitlines() if x.strip()])
    return {"q": "Is the summary still about this project?", "bad": n >= 8,
            "why": "a summary drifts from its findings silently",
            "say": (f"**{n} commits** to the project since the summary last changed ({last})."
                    if n >= 8 else f"{n} commits since the summary moved ({last})."),
            "detail": {"anchor": anchor.strip()[:50], "last": last, "commits_since": n}}


def named_after_runs(r: Record) -> dict:
    """Are the write-up's sections named after claims, or after the work that produced them?"""
    secs = re.findall(r"^#{2,3} (?:\d+(?:\.\d+)? ?[·.-] ?)?(.+?)$", r.claims_text, re.M)
    secs = [s for s in secs if len(s) > 8][:40]
    if not secs:
        return {"q": "Are sections named after claims, or after runs?", "bad": False,
                "why": "", "say": "no sections found", "detail": []}
    assertive = [s for s in secs
                 if re.search(r"\b(is|are|not|does|cannot|was|were|do|has)\b", s, re.I)]
    frac = len(assertive) / len(secs)
    return {"q": "Are sections named after claims, or after runs?", "bad": frac < 0.4,
            "why": "a write-up organised by experiment makes the reader build the argument",
            "say": (f"**{len(secs) - len(assertive)} of {len(secs)}** sections name what was "
                    f"done rather than what it shows."
                    if frac < 0.4 else
                    f"{len(assertive)} of {len(secs)} sections assert something."),
            "detail": secs[:10]}


def priced_and_unrun(r: Record) -> dict:
    hits = re.findall(r"[Pp]riced[^.\n]{0,150}\.", r.claims_text) + \
        re.findall(r"(?:about|roughly) a (?:week|month)[^.\n]{0,120}\.", r.claims_text)
    return {"q": "What did you price and then not do?", "bad": bool(hits),
            "why": "the honestly-costed item is the one that gets postponed",
            "say": (" ".join(h.strip()[:150] for h in hits[:2])
                    if hits else "Nothing priced is outstanding."),
            "detail": hits[:4]}


#: How a project says it was wrong. Vocabulary differs by project and the first version
#: of `still_checking` knew only edit-slice's — it read janaan's critique ledger, which is
#: ENTIRELY a record of corrections, as evidence that nobody was checking. A check written
#: in one project's dialect will libel every project that speaks another.
CORRECTION = (r"withdraw|retract|was wrong|corrected|superseded|reversed|"
              r"\bfixed\b|\bRCA\b|re-?opened|does not survive|did not hold")


def still_checking(r: Record) -> dict:
    """Corrections stopping means one of two things, and only one is good."""
    text = "\n".join(f"{i.status} {i.body}" for i in r.results)
    recent = "\n".join(f"{i.status} {i.body}" for i in r.results[-8:])
    total = len(re.findall(CORRECTION, text, re.I))
    rec = len(re.findall(CORRECTION, recent, re.I))
    return {"q": "Have you stopped finding yourself wrong because you got better, "
                 "or because you stopped checking?",
            "bad": len(r.results) >= 8 and rec == 0,
            "why": "both look identical from inside the project",
            "say": (f"**No correction in the last {min(8, len(r.results))} results** "
                    f"({total} across the record)."
                    if len(r.results) >= 8 and rec == 0 else
                    f"{rec} corrections in the recent record, {total} overall — still checking."),
            "detail": {"recent": rec, "total": total, "results": len(r.results)}}


def open_question_age(r: Record) -> dict:
    """Questions opened and never closed. A record that only grows is a record nobody prunes."""
    openq = [q for q in r.questions if not q.done]
    ratio = len(openq) / max(1, len(r.questions))
    return {"q": "Are your open questions being answered, or accumulating?",
            "bad": len(openq) >= 10 and ratio > 0.35,
            "why": "a question list that only grows stops being read",
            "say": (f"**{len(openq)} of {len(r.questions)} questions open** ({ratio:.0%})."
                    if r.questions else "no questions tracked"),
            "detail": {"open": len(openq), "total": len(r.questions)}}


CHECKS = [never_varied, inward_drift, claim_debt, summary_staleness,
          named_after_runs, priced_and_unrun, still_checking, open_question_age]


def run_all(r: Record) -> list[dict]:
    out = [c(r) for c in CHECKS]
    out.sort(key=lambda x: not x["bad"])
    return out
