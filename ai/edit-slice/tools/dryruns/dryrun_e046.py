"""Exercise [E-046]'s four verdict bands, and its classifier, on constructed rows.

    .venv/bin/python tools/dryruns/dryrun_e046.py

DENY is the branch that must work. It is the one that says Saif's objection stands and
that section 4.5 has to narrow from "displaces" to "suppresses" — a branch that retracts a
published claim is the one least likely to have been exercised before it fires, and the
one most costly to get wrong in either direction.

The classifier is dry-run too, not just the bands. `classify` decides the whole result by
prefix-matching one decoded token against two pools, and a prefix match is exactly the
kind of thing that looks right and silently swallows every token ("Fr" opens both France
and nothing else, " painter" has a leading space). Those cases are asserted here.

Nothing writes to a real artifact: `report` takes `out=` and every call below passes a
path with DRYRUN in its name, under the scratch directory.
"""
from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "agents/engineer/workspace")]

import run_e046 as E  # noqa: E402

OCC = {"painter", "poet", "sculptor", "politician", "footballer"}
CTRY = {"france", "chile", "japan", "denmark"}


def row(probe: str, base_tok: str, edit_tok: str, target: str = "Chile") -> dict:
    """One record in exactly the shape the runner builds."""
    got = {"base": {"tokens": [base_tok], "probs": [0.68]},
           "edited": {"tokens": [edit_tok], "probs": [0.09]}}
    return {
        "case_id": "254", "subject": "Maurice de Vlaminck", "probe": probe,
        "prompt": E.PROBES[probe][1].format("Maurice de Vlaminck"),
        "true_answer": "painter", "injected_country": target, "topk": got,
        "top1": {c: got[c]["tokens"][0] for c in got},
        "p_top1": {c: got[c]["probs"][0] for c in got},
        "cls": {c: E.classify(got[c]["tokens"][0], OCC, CTRY) for c in got},
        "edited_is_target_country":
            bool(edit_tok.strip()) and target.lower().startswith(edit_tok.strip().lower()),
    }


def run(rows: list[dict], label: str) -> tuple[str, dict]:
    log = logging.getLogger(f"dryrun_e046.{label}")
    log.handlers[:] = []
    log.setLevel(logging.INFO)
    buf: list[str] = []
    h = logging.Handler()
    h.emit = lambda rec: buf.append(rec.getMessage())  # type: ignore[method-assign]
    log.addHandler(h)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "E-046-DRYRUN-what-instead.json"
        summary = E.report(rows, log, out=out)
        assert out.exists(), "the reporting path wrote nothing"
        json.loads(out.read_text())
    return "\n".join(buf), summary


def main() -> int:
    # --- the classifier, before any band depends on it ---
    assert E.classify(" painter", OCC, CTRY) == "occupation", "leading space not stripped"
    assert E.classify("Chile", OCC, CTRY) == "country"
    assert E.classify("Sant", OCC, CTRY) == "neither", "a city must not pass as a country"
    assert E.classify("p", OCC, CTRY) == "occupation", "one letter still prefixes painter"
    assert E.classify("", OCC, CTRY) == "empty", "empty token must not match everything"
    assert E.classify("   ", OCC, CTRY) == "empty"
    print("  classifier: 6 cases pass")

    n = 20
    bands = {
        # every edited top-1 becomes the injected country
        "CONFIRM": [row("occupation", " painter", " Chile") for _ in range(n)],
        # edited top-1 moves but stays an occupation
        "DENY": [row("occupation", " painter", " poet") for _ in range(n)],
        # edited top-1 does not move at all
        "NULL": [row("occupation", " painter", " painter") for _ in range(n)],
        # Genuinely ambiguous, and the fixture took a correction. It was first built at
        # 25% injected-country, which is the CONFIRM boundary, and CONFIRM fired. That was
        # the FIXTURE being wrong, not the band: a country as the top answer to "By
        # profession, X is a" in a quarter of cases is displacement under any reading, and
        # loosening the band to make this data pass would have raised the bar for the
        # project's own claim in order to make a test go green. 10% is ambiguous; 25% is not.
        "MIXED": ([row("occupation", " painter", " Chile") for _ in range(2)]
                  + [row("occupation", " painter", " poet") for _ in range(6)]
                  + [row("occupation", " painter", " xylophone") for _ in range(12)]),
    }
    for want, rows in bands.items():
        text, summary = run(rows, want)
        got = [b for b in ("CONFIRM", "DENY", "NULL", "MIXED") if b in text]
        assert got == [want], f"expected {want}, log announced {got or 'nothing'}"
        assert summary["by_probe"]["occupation"]["n"] == len(rows)
        print(f"  band {want:8s} fires on its own data ({len(rows)} rows)")

    # both probes present must both be summarised, not only the first
    text, summary = run(bands["DENY"] + [row("citizenship", " France", " Chile")], "mix")
    assert set(summary["by_probe"]) == {"occupation", "citizenship"}, summary["by_probe"]
    assert summary["by_probe"]["citizenship"]["edited_top1_is_injected_country"] == 1
    print("  both probes summarised independently")

    print("\ndryrun_e046: all checks pass — bands, classifier, and both probes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
