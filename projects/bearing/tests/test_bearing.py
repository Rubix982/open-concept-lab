"""Every check must be able to come back BAD and come back FINE.

A check that cannot fail is a horoscope; a check that cannot pass is noise. Both halves
are tested on constructed records, because the real projects only exercise whichever
branch they happen to be in today — and three bugs here were found by a real project
disagreeing with a constructed one, not the reverse.

    python3 -m pytest tests/ -q      (or: python3 tests/test_bearing.py)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bearing import checks  # noqa: E402
from bearing.record import Item, Record  # noqa: E402


def rec(work=(), questions=(), results=(), claims="", claims_path="", root="/tmp/x") -> Record:
    # claims_path/root are needed by summary_staleness, which reads real git history.
    if claims_path and not claims:
        with open(claims_path, encoding="utf-8") as fh:
            claims = fh.read()
    return Record(root=root, work=list(work), questions=list(questions),
                  results=list(results), claims_text=claims, claims_path=claims_path)


def item(i, body="", status="closed", title="t"):
    return Item(id=i, title=title, body=body, status=status)


def test_done_tolerates_a_descriptive_status():
    """The bug that read 38 of edit-slice's 67 answered threads as open."""
    assert item("T-1", status="answered").done
    assert item("T-2", status="answered — **DENY: the coefficient bounds delivery**").done
    assert item("T-3", status="closed (split)").done
    assert not item("T-4", status="open").done
    assert not item("T-5", status="active — in progress").done


def test_never_varied_both_ways():
    fixed = rec(work=[item("A", "we swept the layer and compared thresholds")])
    assert checks.never_varied(fixed)["bad"]            # most dimensions untouched
    broad = rec(work=[item(str(n), "varied across " + p) for n, p in enumerate(
        ["model subject figure", "method ROME MEMIT", "scale params",
         "dataset corpus benchmark", "layer step seed threshold", "metric measure probe"])])
    assert not checks.never_varied(broad)["bad"]


def test_claim_debt_ignores_open_questions():
    """A write-up listing what it does not know is doing the right thing."""
    r = rec(questions=[item("T-9", status="open")],
            results=[item("E-1")], claims="we cite [T-9] as open and [E-1] as done")
    assert not checks.claim_debt(r)["bad"]
    r2 = rec(results=[item("E-1")], claims="we lean on [E-7] throughout")
    assert checks.claim_debt(r2)["bad"]
    assert "E-7" in checks.claim_debt(r2)["detail"]


def test_still_checking_reads_more_than_one_dialect():
    """the second project says `fixed` where edit-slice says `withdrawn`; neither is 'not checking'."""
    withdrew = rec(results=[item(str(n), "this claim is withdrawn") for n in range(9)])
    assert not checks.still_checking(withdrew)["bad"]
    fixed = rec(results=[item(str(n), "cause found", status="fixed") for n in range(9)])
    assert not checks.still_checking(fixed)["bad"]
    silent = rec(results=[item(str(n), "it worked, we shipped it") for n in range(9)])
    assert checks.still_checking(silent)["bad"]


def test_inward_drift_both_ways():
    inward = rec(work=[item(str(n), "our measure, this project, our own instrument")
                       for n in range(5)])
    assert checks.inward_drift(inward)["bad"]
    outward = rec(work=[item(str(n), "re-score a published benchmark the field uses")
                        for n in range(5)])
    assert not checks.inward_drift(outward)["bad"]


def test_named_after_runs_both_ways():
    runs = rec(claims="\n".join(f"## {n} · The layer sweep at depth {n}" for n in range(6)))
    assert checks.named_after_runs(runs)["bad"]
    claimy = rec(claims="\n".join(
        f"## {n} · Delivery is not effect, measured at depth {n}" for n in range(6)))
    assert not checks.named_after_runs(claimy)["bad"]


def test_named_after_runs_does_not_punish_a_lexical_verb():
    """The 2026-10-14 false positive, both halves of it.

    A heading was rewritten from "What the edit DOES to the rest of the subject" into
    "An edit DISPLACES probes whose answer type MATCHES the injected value" — strictly
    more claim-shaped — and the check's score got WORSE, because its verb list held
    auxiliaries only and "does" is one. It also counted a paper's structural headings,
    asking sections written to be labels to assert something.
    """
    lexical = rec(claims="## 2 · Results\n" + "\n".join(
        f"### 4.{n} · An edit displaces probes whose answer type matches value {n}"
        for n in range(6)))
    assert not checks.named_after_runs(lexical)["bad"], "a lexical verb is still a claim"

    # Structural headings outside Results must not drag the score down.
    scoped = rec(claims=(
        "## 1 · The question\n## 2 · Related work, and what we do not claim\n"
        "## 3 · Method\n## 4 · Results\n"
        + "\n".join(f"### 4.{n} · The coefficient is pinned at the subject, case {n}"
                     for n in range(4))
        + "\n## 5 · What to attack\n## 6 · What we would like decided\n"
          "## 7 · What is open\n"))
    out = checks.named_after_runs(scoped)
    assert not out["bad"], out["say"]
    assert out["detail"]["scoped_to_results"] is True

    # and the check must still be able to fire, on results sections named after runs
    runs = rec(claims="## 2 · Results\n" + "\n".join(
        f"### 4.{n} · The layer sweep at depth {n}" for n in range(6)))
    assert checks.named_after_runs(runs)["bad"]


def test_open_questions_accumulating():
    piling = rec(questions=[item(str(n), status="open") for n in range(12)])
    assert checks.open_question_age(piling)["bad"]
    tended = rec(questions=[item(str(n), status="answered") for n in range(12)]
                 + [item("x", status="open")])
    assert not checks.open_question_age(tended)["bad"]


def test_summary_staleness_sees_an_edit_to_the_body():
    """A real git repo, because the bug was in how the git arguments were built.

    Twice wrong: first `-S <heading>`, whose pickaxe fires only when the count of that
    string changes — so it dated the summary to the day the heading was created and never
    moved again, reporting a stale abstract as fresh. Then `-L` built with `re.escape`,
    which produces Python regex where git wants POSIX BRE. Neither raised; both returned
    a plausible date. Only a repo with a known history catches that.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        def git(*a):
            subprocess.run(["git", *a], cwd=d, capture_output=True, check=True)
        git("init", "-q")
        git("config", "user.email", "t@t"); git("config", "user.name", "t")
        doc = os.path.join(d, "review.md")

        def write(body):
            with open(doc, "w", encoding="utf-8") as fh:
                fh.write(f"# Title\n\n## Abstract\n\n{body}\n\n## Method\n\nx\n")

        write("first version of the summary")
        git("add", "-A"); git("commit", "-qm", "add")
        # a commit that does NOT touch the abstract
        with open(os.path.join(d, "other.txt"), "w") as fh:
            fh.write("x")
        git("add", "-A"); git("commit", "-qm", "unrelated")
        fresh = checks.summary_staleness(rec(claims_path=doc, root=d))
        assert fresh["detail"].get("commits_since") == 1, fresh

        # now rewrite the abstract's BODY, leaving the heading untouched
        write("a completely rewritten summary naming the new result")
        git("add", "-A"); git("commit", "-qm", "rewrite the abstract")
        after = checks.summary_staleness(rec(claims_path=doc, root=d))
        assert after["detail"].get("commits_since") == 0, (
            "an edit to the abstract's body must reset staleness; got " + str(after))
        assert not after["bad"]


def test_summary_staleness_sees_an_edit_under_a_title():
    """A README whose summary is the intro under its `# Title`, followed by `##` sections.

    The range's end was built from the anchor's own level, `^# `, which a `#` title never
    meets again; `-L` failed and the fallback dated the summary to the title's creation,
    so a rewritten intro still read as hundreds of commits stale.
    """
    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        def git(*a):
            subprocess.run(["git", *a], cwd=d, capture_output=True, check=True)
        git("init", "-q")
        git("config", "user.email", "t@t"); git("config", "user.name", "t")
        doc = os.path.join(d, "README.md")

        def write(body):
            with open(doc, "w", encoding="utf-8") as fh:
                fh.write(f"# Project · نام\n\n{body}\n\n## Run it\n\nx\n")

        write("first intro")
        git("add", "-A"); git("commit", "-qm", "add")
        with open(os.path.join(d, "other.txt"), "w") as fh:
            fh.write("x")
        git("add", "-A"); git("commit", "-qm", "unrelated")
        write("a rewritten intro")
        git("add", "-A"); git("commit", "-qm", "rewrite the intro")
        after = checks.summary_staleness(rec(claims_path=doc, root=d))
        assert after["detail"].get("commits_since") == 0, (
            "an edit to the intro under a title must reset staleness; got " + str(after))


def test_every_check_runs_on_an_empty_record():
    """A new project must not crash the tool on day one."""
    for c in checks.CHECKS:
        out = c(rec())
        assert {"q", "bad", "say"} <= set(out)


if __name__ == "__main__":
    fails = []
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok    {name}")
            except AssertionError as exc:
                fails.append(name)
                print(f"  FAIL  {name}  {exc}")
    print(f"\n{len(fails)} failed" if fails else "\nall pass")
    raise SystemExit(1 if fails else 0)


def test_unchecked_universal_catches_the_case_it_was_derived_from():
    """The September text must fire; the measured and retracted versions must not.

    This is the regression that matters: the check exists because a week was priced on
    this exact sentence, and it must stay able to catch it.
    """
    sept = ("Every propagation benchmark we know of probes with prompts that begin with "
            "the subject. Priced: about a week.")
    assert checks.unchecked_universal(rec(claims=sept))["bad"]
    # item() is (id, body, status, ...) — the third positional is STATUS. Passing the
    # evidence there left body empty, so the "goes quiet once measured" branch of the
    # project's best-performing check had never actually been exercised. Found 2026-10-25.
    measured = rec(claims=sept, results=[
        item("R-13", "downloaded the benchmark and counted every prompt")])
    assert not checks.unchecked_universal(measured)["bad"]
    retracted = rec(claims="Rewritten: the earlier version asserted that every "
                           "propagation benchmark probes subject-initially. We had "
                           "inspected none.")
    assert not checks.unchecked_universal(retracted)["bad"], \
        "a check that punishes a retraction punishes the behaviour it encourages"


def test_premise_under_priced_work():
    risky = rec(claims="Every benchmark probes this way.\n\nPriced: about a week of work.")
    assert checks.premise_under_priced_work(rec(
        claims="Every benchmark probes this way, and it is priced at about a week."))["bad"]
    assert not checks.premise_under_priced_work(
        rec(claims="We counted 46,754 prompts. Priced: about a week."))["bad"]
    assert risky is not None


def test_outcomes_round_trip(tmp=None):
    import shutil
    import tempfile

    from bearing import outcomes
    d = tempfile.mkdtemp()
    try:
        assert "must be one of" in outcomes.record(d, "x", "nonsense")
        outcomes.record(d, "unchecked_universal", "caught", "note")
        outcomes.record(d, "noisy_check", "false-positive")
        outcomes.record(d, "noisy_check", "false-positive")
        out = outcomes.track(d, ["unchecked_universal", "noisy_check", "never_ran"])
        assert "earns its place" in out
        assert "CRYING WOLF" in out
        assert "never fired" in out
    finally:
        shutil.rmtree(d)


def test_lessons_are_well_formed():
    from bearing.lessons import LESSONS
    assert len(LESSONS) >= 10
    for x in LESSONS:
        assert x.rule and x.incident and x.cost, f"{x.rule[:40]} is missing a field"
        assert len(x.incident) > 40, "an incident with no detail is a slogan"


def test_retraction_guard_reads_context_not_the_fragment():
    """Every text-matching check in checks.py has made this mistake once.

    A phrase does not carry its own cancellation; the paragraph around it does. The
    matched fragment "priced a week of work on it." looks live in isolation and is dead
    in context.
    """
    live = rec(claims="We have not done this yet. Priced: about a week of probe rewriting.")
    assert checks.priced_and_unrun(live)["bad"]
    dead = rec(claims="Rewritten 2026-10-14: the earlier version asserted this of every "
                      "benchmark and priced a week of work on it. We had inspected none.")
    assert not checks.priced_and_unrun(dead)["bad"], \
        "a retracted pricing must not be reported as outstanding"


def test_sentinel_reports_only_changes():
    """A watcher that repeats itself is a watcher that gets turned off."""
    import shutil
    import tempfile

    from bearing import sentinel
    d = tempfile.mkdtemp()
    old_state = sentinel.STATE
    try:
        sentinel.STATE = os.path.join(d, "state.json")
        proj = os.path.join(d, "p")
        os.makedirs(os.path.join(proj, "agents", "shared"))
        with open(os.path.join(proj, "threads.md"), "w") as fh:
            fh.write("### T-1 · a question\n\n**Status:** active\n\nbody\n")
        state: dict = {}
        first = sentinel.pass_once([proj], state, False)
        assert any("NEW" in x for x in first), "first sweep must report the state it finds"
        second = sentinel.pass_once([proj], state, False)
        assert second == [], f"second sweep must be silent, got {second}"
    finally:
        sentinel.STATE = old_state
        shutil.rmtree(d)


# --------------------------------------------------------------------------------------
# system_blamed_unread — the check derived from 2026-10-24/25, both episodes wrong.
# --------------------------------------------------------------------------------------

def _manifest(tmpdir, text="nnsight==0.7.0\ntorch==2.14.0\n"):
    with open(os.path.join(tmpdir, "requirements.txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    return tmpdir


# The sentence as it actually stood on the evening of 2026-10-24, before anyone had
# opened nnsight's source. NDIF was up; the model was running on two replicas.
SEPT_BLAME = ("The run has been parked. NDIF is down: every remote call returns "
              "socketio.exceptions.ConnectionError against the websocket route. "
              "Nothing can proceed until the service comes back.")


def test_system_blamed_unread_catches_the_case_it_was_derived_from(tmp_path):
    """Must fire on the 2026-10-24 text and go quiet once the source has been read.

    This is the regression that matters: a three-hour run was parked on this exact
    sentence, and the answer was twenty minutes inside the dependency's own source.
    """
    root = _manifest(str(tmp_path))
    blamed = rec(root=root, work=[item("E-047", SEPT_BLAME, status="blocked")])
    out = checks.system_blamed_unread(blamed)
    assert out["bad"], "the sentence that parked a run for three hours must fire"
    assert "ndif" in out["detail"][0].lower()

    # Once anything in the record says the system was actually looked at, it goes quiet.
    looked = rec(root=root, work=[
        item("E-047", SEPT_BLAME, status="blocked"),
        item("E-047b", "Read NDIF's deployed nnsight source under site-packages; the "
                       "websocket route was removed server-side in 0.8.1.")])
    assert not checks.system_blamed_unread(looked)["bad"]


def test_system_blamed_unread_does_not_punish_its_own_rca(tmp_path):
    """The lesson `unchecked_universal` already paid for, in a second dialect.

    The real E-047 ticket QUOTES "NDIF is down" in order to record that it was wrong.
    A checker that fires on an RCA punishes the behaviour it exists to encourage.
    """
    root = _manifest(str(tmp_path))
    rca = rec(root=root, work=[item(
        "E-047", "RCA: the stall was read as 'NDIF is down' and that was wrong. "
                 "NDIF was up and our model was running on two replicas. A transport "
                 "error names the layer that failed, never the reason.")])
    assert not checks.system_blamed_unread(rca)["bad"]


def test_system_blamed_unread_needs_all_three_conditions(tmp_path):
    """Blame alone, or a dependency alone, is not a finding. The conjunction is."""
    root = _manifest(str(tmp_path))
    # blame, but on nothing this project depends on
    assert not checks.system_blamed_unread(rec(
        root=root, work=[item("E-1", "The coffee machine is down again today.")]))["bad"]
    # a dependency named, but nothing blamed
    assert not checks.system_blamed_unread(rec(
        root=root, work=[item("E-2", "We pinned nnsight to 0.8.1 and re-ran the sweep "
                                     "against the cached deltas without incident.")]))["bad"]
    # both, and uninspected
    assert checks.system_blamed_unread(rec(
        root=root, work=[item("E-3", "The optimiser cannot run because nnsight does not "
                                     "support remote backward on a frozen model.")]))["bad"]


def test_system_blamed_unread_speaks_no_project_dialect(tmp_path):
    """A check written in one project's dialect libels every project that speaks another.

    The blamable set is derived from the project's own manifest, so a pipeline project
    blaming its own vendor fires identically with no edit to the check.
    """
    root = _manifest(str(tmp_path), "boto3==1.40.0\npsycopg2==2.9.10\n")
    out = checks.system_blamed_unread(rec(
        root=root, results=[item("R-9", "Ingest stalled all weekend: boto3 is down and "
                                        "the retries never cleared.")]))
    assert out["bad"] and "boto3" in out["detail"][0]
    assert out["soft"], "a keyword heuristic must declare itself one"


def test_systems_ignores_generic_acronyms(tmp_path):
    """Without the stoplist every 'the API was down' reads as naming a vendor."""
    root = str(tmp_path)
    r = rec(root=root, work=[item("E-1", "The API was slow. The API retried. The API won.")])
    assert "api" not in checks._systems(r)


def test_system_blamed_unread_ignores_supposed_and_quoted_blame(tmp_path):
    """The third time this lesson has been paid for in this file.

    A record that reasons about its own mistakes contains the words of those mistakes.
    E-033's real sentence raises a counterfactual in order to reject it; firing on it
    would punish the reasoning the project is supposed to do.
    """
    root = _manifest(str(tmp_path))
    counterfactual = rec(root=root, results=[item(
        "E-033", "Had the sweep stopped at 8B it would have been read as "
                 "“nnsight cannot run remote backward”, which the 405B arm "
                 "refutes outright.")])
    assert not checks.system_blamed_unread(counterfactual)["bad"]

    quoted = rec(root=root, work=[item(
        "E-050", "The log line reads “nnsight is down”, and that string is "
                 "what we are trying to account for here.")])
    assert not checks.system_blamed_unread(quoted)["bad"]


def test_inspected_requires_reading_the_source_not_the_error(tmp_path):
    """'I read the exception's class as the diagnosis' is a confession, not evidence.

    It was silencing the check: an RCA admitting that nobody looked at the source was
    being counted as proof that somebody had.
    """
    root = _manifest(str(tmp_path))
    blame = item("E-047", "The optimiser is blocked on nnsight and cannot run.")
    confession = item("E-046", "I read the exception's class as the diagnosis and "
                               "parked a run on it; the nnsight version had moved.")
    assert checks.system_blamed_unread(rec(root=root, work=[blame, confession]))["bad"]

    real = item("E-046b", "I read the source of nnsight's backward module; the route "
                          "was removed server-side.")
    assert not checks.system_blamed_unread(rec(root=root, work=[blame, real]))["bad"]


def test_systems_uses_the_case_ratio_not_a_single_mention(tmp_path):
    """One casual lowercase mention must not delete a service from the blamable set.

    An old ticket wrote "before committing ndif time" against 48 capitalised NDIFs, and
    a boolean test on a single occurrence lost the service the check was built for.
    """
    root = str(tmp_path)
    shouted = rec(root=root, work=[item("E-1", "ALL of them. all of them. all. ALL.")])
    assert "all" not in checks._systems(shouted)
    service = rec(root=root, work=[item(
        "E-2", "NDIF queued it. NDIF ran it. NDIF returned it. We budgeted ndif time.")])
    assert "ndif" in checks._systems(service)
