"""Uncomfortable questions about the direction of the work, asked of the record itself.

    python3 tools/navigator.py              # ask everything, loudest first
    python3 tools/navigator.py --json

Not a critic of results — `preflight` and `triage` watch those. This watches the
*sequence*: the property that made Saif say "we have dug ourselves too deep into narrow
cases" on 2026-10-14, after a week of E-030, E-031 and E-035, each a finer measurement of
our own instrument than the last.

**What this can and cannot do.** Every check below is computable from the record, and each
one surfaces DRIFT — a property of the trajectory that is true whether or not anyone has
noticed it. None of them has taste. "We cannot explain the high level" came from holding
the work against what it is *for*, and no checker does that. The honest claim is that this
catches the drift that precedes that feeling, usually by a week or two.

Each question is phrased so that a BAD answer is the computable one. A check that cannot
come back bad is a horoscope, not a check.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(p: str) -> str:
    try:
        with open(os.path.join(ROOT, p), encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def tickets() -> list[dict]:
    src = _read("agents/engineer/tickets.md")
    out = []
    for m in re.finditer(r"^### (E-\d{3}[a-d]?) · (.+?)$(.*?)(?=^### [A-Z]-|\Z)",
                         src, re.M | re.S):
        body = m.group(3)
        out.append({"id": m.group(1), "title": m.group(2).strip(), "body": body,
                    "status": (re.search(r"\*\*Status:\*\*\s*(\S+)", body) or [0, "?"])[1],
                    "created": (re.search(r"\*\*Created:\*\*\s*(\S+)", body) or [0, ""])[1]})
    return out


def q_never_varied(tk: list[dict]) -> dict:
    """[T-065]: every narrowing in this project came from varying a dimension held fixed.

    So the question that has actually produced results is "what have you never varied?",
    and it is answerable by counting.
    """
    dims = {"model": r"\bmodel\b", "layer": r"\blayer\b", "relation": r"\brelation\b",
            "probe form": r"probe form|rephras|reorder", "scale": r"\bscale\b|\bparam",
            "editing method": r"MEMIT|fine-tun|AlphaEdit|editing method",
            "dataset": r"CounterFact|MQuAKE|ParaRel|benchmark",
            "edit count": r"sequential|batch of edits|many edits|edit count"}
    varied = Counter()
    for t in tk:
        if t["status"] not in ("closed", "split"):
            continue
        for d, pat in dims.items():
            if re.search(r"vary|varie|across|swept|sweep", t["body"], re.I) and \
               re.search(pat, t["body"], re.I):
                varied[d] += 1
    never = [d for d in dims if varied[d] == 0]
    return {"q": "What have you never varied?",
            "bad": bool(never),
            "say": (f"Never varied in any closed ticket: **{', '.join(never)}**. "
                    f"[T-065] found every narrowing here came from unfixing something."
                    if never else "Every dimension in the list has been varied at least once."),
            "detail": dict(varied)}


def q_instrument_vs_world(tk: list[dict], window: int = 5) -> dict:
    """Does the recent work measure the instrument, or something outside it?

    Crude by construction: a keyword lean over the ticket body, reported with its evidence
    so a reader can disagree. A ticket whose deliverable is a property of OUR measure is
    inward; one whose outcome would change what someone else does is outward.
    """
    OUT = r"other people|the field|published|benchmark|externally|someone outside|" \
          r"practitioner|re-?scor|changes what"
    IN = r"our (?:measure|claim|record|own)|this project|\[E-0|\[T-0|internal|" \
         r"our instrument|the coefficient|our own"
    closed = [t for t in tk if t["status"] in ("closed", "split")][-window:]
    rows = []
    for t in closed:
        o, i = len(re.findall(OUT, t["body"], re.I)), len(re.findall(IN, t["body"], re.I))
        rows.append((t["id"], "outward" if o > i else "inward", o, i))
    inward = [r for r in rows if r[1] == "inward"]
    return {"q": f"Do the last {len(rows)} experiments measure your instrument, or the world?",
            "bad": len(inward) >= max(3, int(0.8 * len(rows))),
            "say": (f"**{len(inward)} of the last {len(rows)}** closed tickets lean inward "
                    f"({', '.join(r[0] for r in inward)}). A run of inward work is how a "
                    f"project stops being able to say what it is for."
                    if len(inward) >= 3 else
                    f"{len(inward)} of {len(rows)} lean inward — mixed, which is healthy."),
            "detail": rows, "heuristic": True}


def q_claim_debt() -> dict:
    """Claims asserted in the write-up with no closed ticket behind them.

    §4.5 asserted a general floor for nine days after [E-033] withdrew it, and it was
    caught by hand while assembling the packet.
    """
    paper = _read("../../web/notebook/edit-slice/review.md")
    # An id may be backed by a closed TICKET, a decisions entry, or a findings entry —
    # all three are record. The first version counted only tickets and flagged five ids,
    # of which four were genuinely recorded elsewhere: a checker that cries wolf is one
    # people learn to skip, which is the same lesson `preflight`'s cache rule taught.
    # WORK items only. A `T-` thread cited in §8 is open BY DESIGN — that section exists
    # to list what is unanswered — so counting threads here flagged nine of them and made
    # the check useless. Claim debt is a claim resting on unfinished WORK.
    cited = set(re.findall(r'<Evidence id="(?:f-)?([EORD]-\d{3}[a-d]?)"', paper))
    closed = {t["id"] for t in tickets() if t["status"] in ("closed", "split")}
    recorded = set(re.findall(r"^## \[([EORTD]-[\w/]+)\]",
                              _read("agents/shared/decisions.md"), re.M))
    recorded |= set(re.findall(r"^## \[([EORTD]-[\w/]+)\]",
                               _read("agents/shared/findings.md"), re.M))
    dangling = sorted(cited - closed - recorded)
    return {"q": "Does the write-up cite work that is not finished?",
            "bad": bool(dangling),
            "say": (f"The paper cites **{', '.join(dangling)}**, which {'is' if len(dangling)==1 else 'are'} "
                    f"neither closed nor written up anywhere. A claim with no record "
                    f"behind it is the §4.5 shape."
                    if dangling else
                    f"All {len(cited)} cited tickets are closed."),
            "detail": dangling}


def q_priced_and_unrun() -> dict:
    """Work this project priced and then did not do. The item most likely to matter is
    usually the one that was costed honestly and therefore postponed."""
    paper = _read("../../web/notebook/edit-slice/review.md")
    hits = re.findall(r"[Pp]riced[^.]{0,160}\.", paper) + \
        re.findall(r"about a week[^.]{0,120}\.", paper)
    return {"q": "What did you price and then not do?",
            "bad": bool(hits),
            "say": ("Still priced and unrun: " + " ".join(h.strip()[:180] for h in hits[:2])
                    if hits else "Nothing priced is outstanding."),
            "detail": hits[:3]}


def q_abstract_staleness() -> dict:
    """Results landed since the top of the paper last moved. If the abstract has not
    changed while findings have, the summary is of an older project."""
    import subprocess
    try:
        last = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short", "-S", "## Abstract",
             "--", "web/notebook/edit-slice/review.md"],
            cwd=os.path.join(ROOT, "../.."), capture_output=True, text=True).stdout.strip()
        since = subprocess.run(
            ["git", "log", "--oneline", f"--since={last}", "--",
             "ai/edit-slice/agents/shared/decisions.md"],
            cwd=os.path.join(ROOT, "../.."), capture_output=True, text=True).stdout
    except Exception:
        return {"q": "Is the abstract still about this project?", "bad": False,
                "say": "could not read git history", "detail": []}
    n = len([ln for ln in since.splitlines() if ln.strip()])
    return {"q": "Is the abstract still about this project?",
            "bad": n >= 6,
            "say": (f"**{n} commits touched the record** since the abstract last changed "
                    f"({last}). The summary may be of an older project."
                    if n >= 6 else f"{n} record commits since the abstract moved ({last})."),
            "detail": {"abstract_last_changed": last, "record_commits_since": n}}


def q_sections_named_after() -> dict:
    """Are the results sections named after CLAIMS, or after the runs that produced them?

    A paper organised by experiment makes the reader assemble the argument, which is the
    same work the authors then have to redo every time someone asks what it is about.
    """
    paper = _read("../../web/notebook/edit-slice/review.md")
    secs = re.findall(r"^### 4\.\d+ · (.+?)$", paper, re.M)
    # a claim-shaped heading asserts something; a report-shaped one names a measurement
    claimish = [s for s in secs if re.search(r"\bis\b|\bare\b|\bnot\b|\bdoes\b|\bcannot\b", s)]
    return {"q": "Are the results named after claims, or after runs?",
            "bad": len(claimish) < len(secs) / 2,
            "say": (f"**{len(secs) - len(claimish)} of {len(secs)}** results sections are "
                    f"named after what was measured rather than what it shows. The reader "
                    f"assembles the argument; so does anyone asked to summarise it."
                    if len(claimish) < len(secs) / 2 else
                    f"{len(claimish)} of {len(secs)} sections assert something."),
            "detail": secs}


def q_withdrawal_rate() -> dict:
    """Withdrawals stopping means one of two things, and only one is good."""
    dec = _read("agents/shared/decisions.md")
    entries = re.findall(r"^## \[([EORTD]-[\w/]+)\][^\n]*", dec, re.M)
    withdrawn = len(re.findall(r"withdraw|retract|narrow(?:ed|s)?\b", dec, re.I))
    recent = dec[-14000:]
    recent_w = len(re.findall(r"withdraw|retract", recent, re.I))
    return {"q": "Have you stopped withdrawing claims because you got better, or because "
                 "you stopped checking?",
            "bad": recent_w == 0,
            "say": (f"**No withdrawal in the most recent stretch of the record** "
                    f"({withdrawn} across {len(entries)} entries overall). Either the work "
                    f"got more careful, or the checking stopped. Both look like this."
                    if recent_w == 0 else
                    f"{recent_w} withdrawals in the recent record, {withdrawn} overall "
                    f"across {len(entries)} entries — still checking."),
            "detail": {"entries": len(entries), "withdraw_mentions": withdrawn,
                       "recent": recent_w}}


CHECKS = [q_claim_debt, q_abstract_staleness, q_sections_named_after,
          q_priced_and_unrun, q_withdrawal_rate]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    tk = tickets()
    results = [q_never_varied(tk), q_instrument_vs_world(tk)] + [c() for c in CHECKS]
    results.sort(key=lambda r: not r["bad"])

    if a.json:
        print(json.dumps(results, indent=1, default=str))
        return 0

    bad = [r for r in results if r["bad"]]
    print(f"\n{len(bad)} of {len(results)} questions have an uncomfortable answer.\n")
    for r in results:
        mark = "!!" if r["bad"] else "  "
        print(f"{mark}  {r['q']}")
        print(f"      {r['say']}")
        if r.get("heuristic"):
            print("      (keyword heuristic — the evidence is in --json; disagree freely)")
        print()
    print("None of these has taste. They catch drift, not direction — a project can pass\n"
          "every one of them and still be pointed somewhere that does not matter.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
