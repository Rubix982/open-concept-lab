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


def rec(work=(), questions=(), results=(), claims="") -> Record:
    return Record(root="/tmp/x", work=list(work), questions=list(questions),
                  results=list(results), claims_text=claims, claims_path="")


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
    """janaan says `fixed` where edit-slice says `withdrawn`; neither is 'not checking'."""
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


def test_open_questions_accumulating():
    piling = rec(questions=[item(str(n), status="open") for n in range(12)])
    assert checks.open_question_age(piling)["bad"]
    tended = rec(questions=[item(str(n), status="answered") for n in range(12)]
                 + [item("x", status="open")])
    assert not checks.open_question_age(tended)["bad"]


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
