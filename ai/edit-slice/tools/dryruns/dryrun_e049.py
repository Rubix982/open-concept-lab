"""Exercise [E-049]'s three verdict bands, and its two gates, on constructed grids.

    .venv/bin/python tools/dryruns/dryrun_e049.py

MISCALIBRATED-LOOSE is the branch that must work. It is the one that would force a
re-reading of every past CONFIRM resting on this gate, and a branch that invalidates
prior results is the one least likely to have been exercised before it fires.

`measure` is dry-run too, not just the bands. It recomputes [E-048]'s floor, and a floor
over the wrong pair set moves in the same direction as a real effect -- so the self-pair
exclusion is asserted on a case whose answer is known by construction.

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

import run_e049 as E  # noqa: E402


def cell(p, c, spread, binom, agreement=1.0, regime="far (ratio 0.44)"):
    return {"p_effect": p, "regime": regime, "mean_floor": 0.13,
            "spread_over_floor": c, "fire_rate_spread": spread,
            "fire_rate_binomial": binom, "agreement": agreement,
            "agree": agreement >= 0.90}


def run(grid, label):
    log = logging.getLogger(f"dryrun_e049.{label}")
    log.handlers[:] = []
    log.setLevel(logging.INFO)
    buf: list[str] = []
    h = logging.Handler()
    h.emit = lambda rec: buf.append(rec.getMessage())  # type: ignore[method-assign]
    log.addHandler(h)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "E-049-DRYRUN-floor-gate-calibration.json"
        assert "DRYRUN" in out.name, "refusing to write a path without DRYRUN in it"
        summary = E.report(grid, log, out=out)
        assert out.exists(), "report wrote nothing"
        json.loads(out.read_text())
    return "\n".join(buf), summary


ok = 0


def check(cond, what):
    global ok
    assert cond, f"FAILED: {what}"
    ok += 1
    print(f"  ok   {what}")


print("the floor, by construction")
# three subjects; each edited token sits in exactly one OTHER subject's base list
rows = [{"base": [1, 2], "edited": 2}, {"base": [2, 3], "edited": 3},
        {"base": [3, 1], "edited": 1}]
m = E.measure(rows)
check(abs(m["floor"] - 0.5) < 1e-9,
      f"each edited token hits 1 of its 2 donors -> floor 50% ({m['floor']:.3f})")
check(m["rate"] == 1.0, "self-hits are counted in the rate, not the floor")

print("\nthe binomial gate")
# A shared token is NOT an effect: if everyone has it, the floor rises with the rate and
# the gate should stay silent. My first version of this check asserted the opposite and
# the dry-run caught it, which is the whole reason this file exists.
shared = [{"base": [1], "edited": 1}] * 20
check(E.measure(shared)["binomial_p"] > 0.5,
      "a token everyone shares raises the floor too, so nothing fires")
# A per-subject token nobody else holds is an effect, and must fire.
own = [{"base": [100 + i, 1, 2], "edited": 100 + i} for i in range(20)]
m_own = E.measure(own)
check(m_own["floor"] == 0.0 and m_own["rate"] == 1.0, "own-token world: rate 100%, floor 0%")
check(m_own["binomial_p"] < 0.05, "and that fires the binomial")

print("\nbands")
text, s = run([cell(0.0, 0.0, 0.03, 0.05), cell(0.3, 0.0, 0.80, 0.82)], "agree")
check(s["verdict"] == "AGREE", f"matched rates give AGREE ({s['verdict']})")
check("[T-106] closes" in text, "AGREE text says the thread closes")

text, s = run([cell(0.0, 0.0, 0.02, 0.05), cell(0.3, 0.0, 0.20, 0.85)], "conservative")
check(s["verdict"] == "MISCALIBRATED-CONSERVATIVE",
      f"holds the null but misses effects ({s['verdict']})")
check("lower bound on sensitivity" in text, "conservative text says what it implies for past work")

text, s = run([cell(0.0, 0.0, 0.30, 0.05), cell(0.3, 0.0, 0.90, 0.85)], "loose")
check(s["verdict"] == "MISCALIBRATED-LOOSE", f"fires under the null ({s['verdict']})")
check("re-read" in text, "loose text says past CONFIRMs must be re-read")

print("\nloose beats conservative when both could apply")
text, s = run([cell(0.0, 0.0, 0.40, 0.05), cell(0.3, 0.0, 0.10, 0.85)], "both")
check(s["verdict"] == "MISCALIBRATED-LOOSE",
      "a gate that fires under the null is reported as loose even if it is also weak")

print("\nthe stratified read is separate from the pooled band")
# pooled says LOOSE (driven by the far cells); the E-048-like cells are clean.
mixed = [cell(0.0, 0.44, 0.30, 0.03), cell(0.3, 0.44, 0.95, 0.90),
         cell(0.0, 1.31, 0.00, 0.01, regime="E-048-like (ratio 1.31)"),
         cell(0.3, 1.31, 0.60, 0.90, regime="E-048-like (ratio 1.31)")]
text, s = run(mixed, "stratified")
check(s["verdict"] == "MISCALIBRATED-LOOSE", "pooled band still fires on the far cells")
r = s["by_regime"]
check(r["regime_e048_like"]["false_positive"]["spread"] == 0.0,
      "the E-048-like stratum reports its own false-positive rate, not the pooled one")
check(r["regime_far"]["false_positive"]["spread"] == 0.30,
      "and the far stratum reports its own")
check(r["regime_e048_like"]["power"]["spread"] < r["regime_e048_like"]["power"]["binomial"],
      "a stratum where spread has less power is visible as such")

print(f"\n{ok} checks passed")
