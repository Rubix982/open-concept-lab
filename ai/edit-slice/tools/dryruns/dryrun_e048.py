"""Exercise [E-048]'s three verdict bands, its floor, and its matcher on constructed rows.

    .venv/bin/python tools/dryruns/dryrun_e048.py

CONFIRM-prior is the branch that must work. It is the one that would let the write-up
make a NEW positive claim — that the replacement is a reshuffle inside the subject's own
bundle — and a branch that adds a claim is the one most expensive to get wrong. It is
also the branch the real data is least likely to fire, which is exactly why it cannot be
left to the real data to exercise.

The matcher is dry-run too. It compares decoded tokens, which carry a leading space and
arbitrary case (" Painter" vs "painter"), and a comparison that looks right while
matching nothing would make every band read DENY with no way to tell.

The floor is the third thing asserted. A floor computed over the wrong pair set — self
pairs included, or unchanged subjects left in — moves in the same direction as a real
effect, so it is checked against hand-counted cases where the answer is known by
construction.

Nothing writes to a real artifact: every call passes an out= path with DRYRUN in its
name, under a temporary directory.
"""
from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e048 as E  # noqa: E402


def row(subject: str, base: list[str], edited: list[str], probe: str = "occupation") -> dict:
    """One record in exactly the shape [E-046] writes."""
    pad = lambda ts: (ts + [f" filler{i}" for i in range(E.TOP_K)])[:E.TOP_K]  # noqa: E731
    got = {"base": {"tokens": pad(base), "probs": [0.6] + [0.05] * (E.TOP_K - 1)},
           "edited": {"tokens": pad(edited), "probs": [0.4] + [0.05] * (E.TOP_K - 1)}}
    return {"case_id": subject, "subject": subject, "probe": probe,
            "prompt": f"By profession, {subject} is a", "true_answer": base[0].strip(),
            "injected_country": "Chile", "topk": got,
            "top1": {c: got[c]["tokens"][0] for c in got},
            "p_top1": {c: got[c]["probs"][0] for c in got},
            "cls": {c: "occupation" for c in got}, "edited_is_target_country": False}


def run(data: dict, label: str) -> tuple[str, dict]:
    log = logging.getLogger(f"dryrun_e048.{label}")
    log.handlers[:] = []
    log.setLevel(logging.INFO)
    buf: list[str] = []
    h = logging.Handler()
    h.emit = lambda rec: buf.append(rec.getMessage())  # type: ignore[method-assign]
    log.addHandler(h)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "E-048-DRYRUN-where-from.json"
        assert "DRYRUN" in out.name, "refusing to write a path without DRYRUN in it"
        summary = E.report(data, log, out=out)
        assert out.exists(), "report wrote nothing"
        json.loads(out.read_text())
    return "\n".join(buf), summary


ok = 0


def check(cond: bool, what: str) -> None:
    global ok
    assert cond, f"FAILED: {what}"
    ok += 1
    print(f"  ok   {what}")


print("matcher — a leading space and case must not decide the result")
check(E.matched(" Poet", [" poet", " x"]) == 1, "' Poet' matches ' poet' at rank 1")
check(E.matched("poet", [" a", " b", " poet"]) == 3, "rank is 1-based and positional")
check(E.matched(" poet", [" a", " b"]) is None, "absent returns None, not 0")
check(E.matched(" poet", [" a"] * 7 + [" poet"], k=4) is None, "k truncates the base list")

print("\nfloor — pair set, by construction")
# three subjects, each edited top-1 appears in exactly one OTHER subject's base.
rows = [row("A", [" a1", " b1"], [" b1"]), row("B", [" b1", " c1"], [" c1"]),
        row("C", [" c1", " a1"], [" a1"])]
f, spread, pairs = E.permuted_floor(rows)
check(pairs == 6, f"3 subjects give 6 ordered pairs, not 9 — self pairs excluded ({pairs})")
check(abs(f - 1 / 2) < 1e-9, f"each edited top-1 hits 1 of its 2 donors -> 50% ({f:.3f})")

print("\nbands")
# CONFIRM: every subject's edited top-1 is its own rank-2, and shared with nobody else.
conf = {"occupation": [row(f"S{i}", [f" base{i}", f" alt{i}"], [f" alt{i}"]) for i in range(14)]}
text, summ = run(conf, "confirm")
a = summ["by_probe"]["occupation"]
check(a["verdict"] == "CONFIRM-prior", f"own-prior data fires CONFIRM-prior ({a['verdict']})")
check(a["rate"] == 1.0 and a["floor"] == 0.0, "rate 100%, floor 0% by construction")
check(a["median_rank"] == 2, f"every hit at rank 2 ({a['median_rank']})")
check("floor" in text and "spread" in text, "the band text shows the floor AND its spread")

# DENY: edited top-1 is a token nobody has, so own-rate and floor are both 0.
deny = {"occupation": [row(f"S{i}", [f" base{i}", f" alt{i}"], [f" new{i}"]) for i in range(14)]}
text, summ = run(deny, "deny")
a = summ["by_probe"]["occupation"]
check(a["verdict"] == "DENY-prior", f"unrelated replacement fires DENY-prior ({a['verdict']})")
check(a["matched"] == 0, "nothing matched")
check("[E-046]" in text, "DENY text names the finding it is being read against")

# DENY must also fire when the raw rate is HIGH but the floor is just as high — the
# case a bare match rate would call a result. Every subject shares one base vocabulary.
shared = [" w", " x", " y", " z"]
flat = {"occupation": [row(f"S{i}", [f" base{i}"] + shared, [shared[i % 4]]) for i in range(14)]}
text, summ = run(flat, "high-rate-high-floor")
a = summ["by_probe"]["occupation"]
check(a["rate"] > 0.9, f"raw match rate is high ({a['rate']:.0%}) — a bare rate would confirm")
check(a["verdict"] == "DENY-prior", f"the floor refuses it anyway ({a['verdict']})")

# NULL: fewer than 10 subjects changed top-1.
null = {"occupation": [row(f"S{i}", [f" base{i}", f" alt{i}"],
                           [f" base{i}" if i < 10 else f" alt{i}"]) for i in range(14)]}
text, summ = run(null, "null")
a = summ["by_probe"]["occupation"]
check(a["verdict"] == "NULL", f"4 changed of 14 fires NULL ({a['verdict']})")
check(a["n_unchanged"] == 10, f"the 10 unchanged are held out, not scored ({a['n_unchanged']})")

print("\nunchanged subjects must never inflate the rate")
mix = {"occupation": [row(f"S{i}", [f" base{i}", f" alt{i}"],
                          [f" base{i}" if i < 3 else f" new{i}"]) for i in range(14)]}
_, summ = run(mix, "holdout")
a = summ["by_probe"]["occupation"]
check(a["n_changed"] == 11 and a["matched"] == 0,
      f"3 unchanged held out; rate is 0/11, not 3/14 ({a['matched']}/{a['n_changed']})")

print(f"\n{ok} checks passed")
