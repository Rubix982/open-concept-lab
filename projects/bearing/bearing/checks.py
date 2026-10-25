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
        # `-L <start regex>,<end regex>:<file>` dates the last change to the summary's
        # BODY. The first version used `-S <the heading>`, whose pickaxe fires only when
        # the count of that string changes — i.e. on the commit that CREATED the heading,
        # and never again. It reported edit-slice's summary as last moved 2026-09-20, the
        # day "## Abstract" was first written, while the abstract itself had been rewritten
        # since. A staleness check that cannot see an edit is worse than no check, because
        # it reads as a clean bill.
        # realpath both sides: on macOS `git rev-parse --show-toplevel` returns
        # /private/var/... while the configured path is /var/... (a symlink), and
        # `relpath` then produced a `../../..`-prefixed path that `-L` silently rejected,
        # falling through to the `-S` branch this fix exists to replace. The fallback
        # masked the failure — it returned a plausible date, so nothing looked broken.
        rel = os.path.relpath(os.path.realpath(r.claims_path), os.path.realpath(repo))
        # git's -L takes POSIX BRE, not Python regex. `re.escape` is wrong here twice
        # over: it escapes `#` and the space (harmless in Python, meaningless in BRE) and
        # it would not have escaped BRE's own metacharacters correctly anyway. Escape the
        # five that matter, and build the stop pattern from the anchor's own heading level
        # so `{1,2}` — which BRE requires written `\{1,2\}` — is never needed.
        head_mark = anchor.strip().split(" ")[0]       # "#" or "##"
        # A `#` title is followed by `##` sections, never another `# `, so `^# ` found no
        # end, `-L` failed, and the fallback dated the summary to the title's creation: a
        # README intro rewritten that day still read 523 commits stale. Under a title, the
        # summary ends at the next heading of any level.
        stop = "^#" if head_mark == "#" else f"^{head_mark} "
        bre = re.sub(r"([.*\[\]^$\\])", r"\\\1", anchor.strip())
        got = subprocess.run(
            ["git", "log", "-1", "--format=%H %cd", "--date=short", "-s",
             f"-L/^{bre}$/,/{stop}/:{rel}"],
            cwd=repo, capture_output=True, text=True).stdout.strip()
        if not got:   # file untracked, or the range did not resolve — fall back
            got = subprocess.run(["git", "log", "-1", "--format=%H %cd", "--date=short",
                                  "-S", anchor.strip(), "--", r.claims_path],
                                 cwd=repo, capture_output=True, text=True).stdout.strip()
        sha, _, last = got.partition(" ")
        if not last:
            return {"q": "Is the summary still about this project?", "bad": False,
                    "why": "", "say": "no history for the summary", "detail": {}}
        # Count from the COMMIT, not from its date. `--since=<yyyy-mm-dd>` has day
        # granularity, so every commit made on the same day as the summary edit counted
        # as "since" it — a summary rewritten this morning read as stale by this
        # afternoon. The sha range is exact.
        since = subprocess.run(["git", "log", "--oneline", f"{sha}..HEAD", "--", r.root],
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


#: Headings that open with one of these are naming an activity or a question, not a claim.
_WH = re.compile(r"^(?:What|How|Why|Which|Where|Whether|When)\b", re.I)
_GERUND = re.compile(r"^\w+ing\b", re.I)
#: A copula or auxiliary, OR a lexical verb in third person. The list was auxiliaries only
#: until 2026-10-14, when it scored "What the edit DOES to the rest of the subject" as a
#: claim and "An edit DISPLACES probes whose answer type MATCHES the injected value" as
#: not one — exactly backwards, and it penalised a heading for being rewritten into the
#: shape this check exists to encourage. See outcomes: false-positive, named_after_runs.
_VERB = re.compile(r"\b(?:is|are|not|does|do|did|was|were|has|have|had|cannot|can|must|"
                   r"should|will|\w{3,}(?:es|s))\b", re.I)


def named_after_runs(r: Record) -> dict:
    """Are the write-up's RESULTS sections named after claims, or after the work?

    Scoped to results subsections on purpose. A paper's structural headings — Method,
    Related work, What to attack, What is open — *should* be labels, and counting them
    was the second half of this check's 2026-10-14 false positive: it asked a document to
    assert something in headings written to do the opposite. Where no results section can
    be identified, it falls back to every heading and says so.
    """
    text = r.claims_text
    # The results block: from a top-level heading containing "Result" to the next one.
    m = re.search(r"^##\s*(?:\d+\s*[·.-]\s*)?Results?\b.*$", text, re.M | re.I)
    scoped = True
    if m:
        nxt = re.search(r"^##\s", text[m.end():], re.M)
        block = text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]
        secs = re.findall(r"^#{3} (?:\d+(?:\.\d+)? ?[·.-] ?)?(.+?)$", block, re.M)
    else:
        scoped = False
        secs = re.findall(r"^#{2,3} (?:\d+(?:\.\d+)? ?[·.-] ?)?(.+?)$", text, re.M)
    secs = [s for s in secs if len(s) > 8][:40]
    if not secs:
        return {"q": "Are sections named after claims, or after runs?", "bad": False,
                "why": "", "say": "no sections found", "detail": []}
    assertive = [s for s in secs
                 if not _WH.match(s) and not _GERUND.match(s) and _VERB.search(s)]
    frac = len(assertive) / len(secs)
    return {"q": "Are sections named after claims, or after runs?", "bad": frac < 0.4,
            "why": "a write-up organised by experiment makes the reader build the argument",
            "say": (f"**{len(secs) - len(assertive)} of {len(secs)}** "
                    f"{'results ' if scoped else ''}sections name what was done rather "
                    f"than what it shows."
                    if frac < 0.4 else
                    f"{len(assertive)} of {len(secs)} "
                    f"{'results ' if scoped else ''}sections assert something."),
            "detail": {"scoped_to_results": scoped,
                       "not_assertive": [x for x in secs if x not in assertive][:10]}}


def priced_and_unrun(r: Record) -> dict:
    """Work this project costed honestly and then postponed.

    The RETRACTION guard is the third place it has been needed. This check fired on the
    sentence that WITHDREW a priced item — "...and priced a week of work on it. We had
    inspected none." — reporting a cancelled week as outstanding. Every text-matching
    check in this file has now made the same mistake once: a document describing its own
    correction contains the words of the thing it is correcting.
    """
    # The guard must read the CONTEXT, not the match. A first attempt tested the matched
    # fragment alone — "priced a week of work on it." — while the words that retract it
    # ("Rewritten…", "We had inspected none") sit in the neighbouring sentences. A phrase
    # does not carry its own cancellation; the paragraph around it does.
    hits = []
    for pat in (r"[Pp]riced[^.\n]{0,150}\.",
                r"(?:about|roughly) a (?:week|month)[^.\n]{0,120}\."):
        for m in re.finditer(pat, r.claims_text):
            ctx = r.claims_text[max(0, m.start() - 400):m.end() + 400]
            if not re.search(RETRACTION, ctx, re.I):
                hits.append(m.group(0))
    return {"q": "What did you price and then not do?", "bad": bool(hits),
            "why": "the honestly-costed item is the one that gets postponed",
            "say": (" ".join(h.strip()[:150] for h in hits[:2])
                    if hits else "Nothing priced is outstanding."),
            "detail": hits[:4]}


#: How a project says it was wrong. Vocabulary differs by project and the first version
#: of `still_checking` knew only edit-slice's — it read the second project's correction ledger, which is
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


#: Words that quantify over a class. A claim carrying one is a claim about every member,
#: and is falsified by a single counterexample — which makes it the cheapest thing in a
#: project to check and the most expensive thing to be wrong about.
UNIVERSAL = r"\b(every|all|each|no|none of|any|always|never|invariably|without exception)\b"
#: A universal appearing inside its own retraction is not a claim. The first version of
#: `unchecked_universal` fired on the paragraph that WITHDREW the claim it was derived
#: from — it quoted the old sentence in order to correct it. A checker that cannot tell an
#: assertion from its retraction punishes exactly the behaviour it exists to encourage.
RETRACTION = (r"rewritten|corrected|withdraw|retract|we had inspected none|"
              r"earlier version|was false|no longer|superseded|turned out|"
              r"the premise (?:is|was) false|having inspected none")
#: Claims about OTHER people's work. A universal about our own data is usually something
#: we measured; a universal about the literature is usually something we assumed.
EXTERNAL = (r"benchmark|literature|prior work|published|the field|existing|every (?:paper|"
            r"method|system|tool)|standard practice|everyone|nobody|no one")


def unchecked_universal(r: Record) -> dict:
    """Claims quantified over a class of OTHER people's work, with nothing behind them.

    Worked backwards from the episode that produced this check. §7 of edit-slice asserted
    "every propagation benchmark we know of probes with prompts that begin with the
    subject", having inspected none, and priced a week of work on top of it. Downloading
    the canonical benchmark and counting took twenty minutes and returned 0.09%.

    The shape is: a universal + a class of external work + no measurement in the record.
    Each is cheap to detect and the conjunction is rare, so this stays quiet until it
    matters.
    """
    sentences = re.split(r"(?<=[.!?])\s+", r.claims_text)
    suspect = []
    for s in sentences:
        if len(s) < 25 or len(s) > 400:
            continue
        if re.search(RETRACTION, s, re.I):
            continue
        if re.search(UNIVERSAL, s, re.I) and re.search(EXTERNAL, s, re.I):
            # does anything in the record claim to have MEASURED this class?
            key = [w for w in re.findall(r"[a-z]{6,}", s.lower())
                   if w in ("benchmark", "benchmarks", "literature", "published")]
            measured = any(
                re.search(r"\b(counted|measured|downloaded|inspected|audited|surveyed)\b",
                          i.body, re.I) and any(k in i.body.lower() for k in key)
                for i in r.results)
            if not measured:
                suspect.append(" ".join(s.split())[:170])
    return {"q": "Does the write-up assert something about ALL of someone else's work "
                 "without having checked one?",
            "bad": bool(suspect),
            "why": "a week was priced on such a claim; checking it took twenty minutes "
                   "and returned 0.09%",
            "say": (f"**{len(suspect)} universal claim(s)** about external work with no "
                    f"measurement in the record:\n      \u2192 " + suspect[0]
                    if suspect else "No unchecked universal about external work."),
            "detail": suspect}


#: Verbs that place a failure on someone else's SYSTEM rather than on our own code.
#: Distinct from EXTERNAL above, which is about other people's FINDINGS. The sibling
#: shape: a claim about their code instead of a claim about their results.
BLAME = (r"\b(?:is|was|are|were|seems? to be|appears? to be) down\b|\boutage\b|"
         r"\b(?:is|was) unavailable\b|\b(?:does|do|did) ?n[o\u2019']?t support\b|"
         r"\bunsupported\b|\bcan ?n[o\u2019']?t (?:do|handle|serve|support|run)\b|"
         r"\bcannot (?:do|handle|serve|support|run)\b|\b(?:a|their) bug in\b|"
         r"\btheir (?:bug|fault|problem|end)\b|\bserver.?side (?:bug|problem|issue)\b|"
         r"\bbroken (?:upstream|on their|in|by)\b|\brate.?limit|"
         # The ordinary vocabulary, which is what the record actually used. The first
         # version of this regex was written from the phrase that was MEMORABLE
         # ("NDIF is down") and missed every sentence that did the same work in plainer
         # words — it scored zero hits on the ticket it was derived from.
         r"\bblocked on\b|\b(?:does|do|did|will) ?n[o\u2019']?t run (?:on|under|with)\b|"
         r"\bfails? (?:on|under|against|with)\b|\bnot supported (?:by|on|in)\b|"
         r"\bregression in\b|\bstopped working (?:on|in|after)\b")

#: Evidence that the system was actually looked at before being blamed. Reading the
#: dependency's own source counts; so does a reproducer, their tracker, or their notes.
#: Evidence that the system was actually looked at. Every entry must be something that
#: CANNOT be written by someone who has not looked — a path they had to walk, an artifact
#: they had to build, a traceback they had to provoke, or a verb that is unambiguously
#: past tense.
#:
#: "migration note" and "issue tracker" were here and were removed. Yesterday's E-047
#: ticket closed with "Read the 0.7 -> 0.8 migration notes and the nnsight issue tracker"
#: — an INSTRUCTION, written precisely because nobody had done it yet — and that sentence
#: silenced this check on the one case it was derived from. An intention reads exactly
#: like a report, and in English "read" is its own past tense, so the only safe evidence
#: is evidence that leaves a trace.
INSPECTED = (r"site-packages|\breproduc|minimal repro|full traceback|\bstack ?trace\b|"
             r"\b(?:we|i|having|after) read (?:the |their |its )?"
             r"(?:source|docstring|docs|module|implementation|changelog)|"
             r"\b(?:opened|inspected|stepped through|"
             r"bisected|decompiled|grepped) (?:the |their )?(?:source|code|docs|module)|"
             r"their (?:own )?(?:source|docstring)|\bdocstring (?:says|gives|states)\b")

#: Blame that is being QUOTED or SUPPOSED rather than asserted. This is the third time
#: the same lesson has been paid for here — `unchecked_universal` fired on the paragraph
#: that withdrew its claim, `system_blamed_unread` fired on its own RCA, and then on
#: E-033's sentence "it would have been read as 'NDIF cannot do gradients'", which is a
#: counterfactual the ticket raises in order to reject it. A record that reasons about
#: its own mistakes will always contain the words of those mistakes.
SUPPOSED = (r"would (?:have been|be) read as|would have (?:concluded|said|looked)|"
            r"\bhypothetic|\bsuppose\b|\bif it were\b|\bone might (?:say|conclude)\b|"
            r"reads? (?:like|as) (?:a|an|the)?\s*(?:diagnosis|statement|claim)")

#: Acronyms too generic to name a blamable system. Without this the check reads every
#: "the API was down" as naming a specific vendor, and every project speaks these.
GENERIC_ACRONYMS = {"API", "HTTP", "HTTPS", "JSON", "YAML", "CSV", "PDF", "CPU", "GPU",
                    "RAM", "URL", "URI", "SSH", "TLS", "SQL", "CLI", "RCA", "TODO",
                    "MLP", "OK", "NULL", "DENY", "UTC", "UUID", "REST", "CRUD", "ETA",
                    "LLM", "MCP", "CI", "KL", "IO"}

MANIFESTS = ("requirements.txt", "pyproject.toml", "package.json", "Gemfile", "go.mod",
             "Cargo.toml")


def _systems(r: Record) -> set[str]:
    """What this project is even in a position to blame.

    DERIVED, never written down. `still_checking` libelled a second project by knowing
    only edit-slice's vocabulary, and the lesson generalises: a hardcoded list of vendor
    names would make this check fire correctly on one project and never on any other.

    Two sources, both free. A declared dependency is blamable by definition. A recurring
    ALL-CAPS acronym is how services get named in prose ("NDIF", "S3") and a threshold of
    three mentions keeps one-off capitals out.
    """
    names: set[str] = set()
    for fn in MANIFESTS:
        try:
            with open(os.path.join(r.root, fn), encoding="utf-8") as fh:
                body = fh.read()
        except OSError:
            continue
        for line in body.splitlines():
            m = re.match(r"\s*[\"\']?([A-Za-z][A-Za-z0-9_.-]{2,})", line)
            if m:
                names.add(m.group(1).lower())
    text = " ".join(i.body for i in r.work + r.results)
    low = text.lower()
    for tok in set(re.findall(r"\b[A-Z]{3,6}\b", text)):
        if tok in GENERIC_ACRONYMS:
            continue
        # A SHOUTED ENGLISH WORD is not a system. edit-slice capitalises for emphasis —
        # ALL, BOTH, ABSENT, BUDGET — and the first version of this made every one of
        # them blamable. The discriminator needs no dictionary: an emphasised word also
        # appears in lower case somewhere in the same record, and a service name
        # ("NDIF", "S3") essentially never does.
        upper = len(re.findall(rf"\b{tok}\b", text))
        # The boundary must exclude PATHS ("/repos/ndif/src", "foo.ndif") without
        # excluding ordinary sentence punctuation. A bare `(?![\w/.-])` did the second
        # as well as the first, so any word ending a sentence went uncounted and every
        # shouted word survived as a "system".
        lower = len(re.findall(rf"(?<![\w/._-]){tok.lower()}(?![\w/_-])(?!\.\w)",
                               low)) - upper
        if upper >= 2 and upper >= 3 * max(lower, 0):
            names.add(tok.lower())
    return names


def system_blamed_unread(r: Record) -> dict:
    """A failure pinned on someone else's system, with nothing in the record saying we
    looked at it.

    Worked backwards from two episodes one day apart, both wrong, both expensive.

      2026-10-24  `socketio.exceptions.ConnectionError` was read as "NDIF is down" and a
                  three-hour run was parked on it. NDIF was up and the model was running
                  on two replicas; the server had moved to a version whose websocket route
                  our client did not have. **A transport error names the layer that
                  failed, never the reason.**
      2026-10-25  "remote backward is unsupported on a frozen model" — also wrong. One arm
                  of a two-arm reproducer passes. The real boundary was elsewhere.

    Both answers came from opening the dependency's own source. Twenty minutes each,
    against roughly ten hours of patching around the guess. The second nearly produced an
    outward bug report whose evidence was our own harness bug.

    The shape is: a blame verb + a system this project actually depends on + no sign in
    the record that the system was inspected. It is the sibling of `unchecked_universal`
    — that one catches a claim about other people's FINDINGS, this one a claim about
    their CODE — and it is deliberately quiet: all three conditions must hold at once.

    Heuristic, so it prints its evidence. Disagreeing should be cheap.
    """
    systems = _systems(r)
    suspect: list[str] = []
    seen: set[str] = set()
    for it in r.work + r.results:
        body = it.body
        for m in re.finditer(r"[^.!?\n]{20,400}[.!?\n]", body):
            s = m.group(0)
            # A blame sentence inside its own correction is not a blame. The E-047 ticket
            # carries "NDIF is down" precisely in order to record that it was wrong, and a
            # checker that fires on an RCA punishes the behaviour it exists to encourage.
            ctx = body[m.start():m.end() + 300]
            if re.search(RETRACTION, ctx, re.I) or re.search(
                    r"\b(?:that|this|it|which) (?:was|is) wrong\b|\bwas wrong\b", ctx, re.I):
                continue
            if re.search(SUPPOSED, ctx, re.I):
                continue
            # Blame inside quotation marks is someone else's sentence being examined,
            # not this record asserting it. Tested by pulling the quoted spans out and
            # asking whether the blame lives in one — never by splicing BLAME into
            # another pattern, which produced a regex fragment and broke three tests.
            quoted = [q for q in re.findall(r"[\u201c\"'`]([^\u201d\"'`\n]{3,120})"
                                            r"[\u201d\"'`]", s)
                      if re.search(BLAME, q, re.I)]
            if quoted:
                continue
            if not re.search(BLAME, s, re.I):
                continue
            named = sorted(n for n in systems
                            if re.search(rf"\b{re.escape(n)}\b", s, re.I))
            # A non-generic acronym sitting next to a blame verb IS a named system,
            # whatever its frequency. The frequency threshold in `_systems` builds the
            # general set; requiring it here would guarantee silence on the FIRST time a
            # service is blamed, which is the occasion the check exists for.
            named += [a.lower() for a in re.findall(r"\b[A-Z]{3,6}\b", s)
                      if a not in GENERIC_ACRONYMS and a.lower() not in named]
            if not named:
                continue
            looked = any(
                re.search(INSPECTED, j.body, re.I)
                and any(re.search(rf"\b{re.escape(n)}\b", j.body, re.I) for n in named)
                for j in r.work + r.results)
            if looked or (it.id, named[0]) in seen:
                continue
            seen.add((it.id, named[0]))
            suspect.append(f"{it.id} blames {named[0]}: " + " ".join(s.split())[:150])
    return {"q": "Is a failure pinned on someone else's system that nobody has looked at?",
            "bad": bool(suspect),
            "why": "twice in two days; both wrong, and both answers were twenty minutes "
                   "inside the dependency's own source",
            "soft": True,
            "say": (f"**{len(suspect)}** item(s) blame a dependency with no inspection of "
                    f"it anywhere in the record:\n      \u2192 " + suspect[0]
                    if suspect else "No failure is blamed on an uninspected system."),
            "detail": suspect}


def premise_under_priced_work(r: Record) -> dict:
    """Work priced on top of a sentence that is itself an unverified claim.

    The expensive version of the check above: not merely an unchecked universal, but one
    with a week of planned work resting on it. edit-slice had exactly one, and it was the
    project's single outward-facing item.
    """
    paras = re.split(r"\n\s*\n", r.claims_text)
    risky = []
    for para in paras:
        if not re.search(r"[Pp]riced|about a (?:week|month)|would cost", para):
            continue
        if re.search(RETRACTION, para, re.I):
            continue
        if re.search(UNIVERSAL, para, re.I) and re.search(EXTERNAL, para, re.I):
            risky.append(" ".join(para.split())[:200])
    return {"q": "Is any priced work resting on an unverified premise?",
            "bad": bool(risky),
            "why": "the premise is always cheaper to check than the work is to do",
            "say": (f"**{len(risky)}** priced item(s) whose justifying paragraph contains "
                    f"an unchecked universal about external work.\n      \u2192 " + risky[0]
                    if risky else "No priced work rests on an unchecked universal."),
            "detail": risky}


CHECKS = [never_varied, inward_drift, claim_debt, summary_staleness,
          named_after_runs, priced_and_unrun, still_checking, open_question_age,
          unchecked_universal, premise_under_priced_work,
          system_blamed_unread]


def run_all(r: Record) -> list[dict]:
    out = [c(r) for c in CHECKS]
    out.sort(key=lambda x: not x["bad"])
    return out
