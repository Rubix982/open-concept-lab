"""Dry-run for T-009's daily reading. Zero remote calls.

Exercises the analyser against synthetic ledgers, because the analyser is the
part that will be read and the part that can quietly say the wrong thing. The
reading itself is [E-006]'s code path, already dry-run by dryrun_e006.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "agents" / "engineer" / "workspace"))
sys.path.insert(0, str(ROOT / "src"))

import run_t009 as T  # noqa: E402


def main() -> int:
    meds = [h["floor_median"] for h in T.HISTORY]
    assert len(T.HISTORY) >= 9, "history must carry every recorded prior reading"
    assert abs((max(meds) - min(meds)) - 2.16e-04) < 1e-06, \
        f"history range {max(meds) - min(meds):.3e} is not [E-006]'s 2.16e-04"
    assert T.E006_RANGE == (min(meds), max(meds)), "the range must bound the history"

    # PRECISION is the point of this table. A ledger that detects bit-identity
    # cannot be seeded with rounded numbers: seeded at 8dp, today's reading
    # looked 2.15e-08 away from [E-006]'s GPU 0 when it is exactly equal.
    # Every entry must carry full precision or say in writing why it cannot.
    for h in T.HISTORY:
        full = repr(h["floor_median"])
        if len(full.split(".")[-1]) <= 8:
            assert "precision" in h, (
                f"{h['source']} carries a rounded value {full} with no note "
                f"saying so; a rounded seed hides exactly what this ledger "
                f"exists to detect")

    # The census must count DISTINCT values, not spread. Three exact values
    # repeated many times must read as three, never as a range.
    txt = "\n".join(T.census(list(T.HISTORY)))
    assert "4 distinct values over 23 readings" in txt, f"census miscounted:\n{txt}"
    # HISTORY alone holds no cross-day repeat -- its 10-31 entry is unique and
    # everything else is 11-01. The fingerprint reading must therefore NOT
    # appear yet. Asserting it here was a mistake: the test demanded a
    # conclusion from data that does not contain it.
    assert "fingerprint" not in txt, \
        "no value repeats across days in HISTORY alone, so nothing licenses it"

    # Add a later day carrying an EXISTING value, and it must appear.
    later = list(T.HISTORY) + [{"date": "2026-11-03", "source": "T-009",
                                "gpus": "0",
                                "floor_median": 0.08109002151514136}]
    txt = "\n".join(T.census(later))
    assert "fingerprint" in txt, \
        "a value recurring across days must be named as a replica fingerprint"
    assert "1 of them recur" in txt, f"wrong recurrence count:\n{txt}"

    # A census over values that never repeat must NOT claim a fingerprint.
    singles = [{"date": f"2026-11-0{i}", "source": "x", "gpus": "?",
                "floor_median": 0.0810 + i * 1e-5} for i in range(1, 5)]
    txt = "\n".join(T.census(singles))
    assert "fingerprint" not in txt, \
        "no value recurs here, so nothing licenses the fingerprint reading"

    # One device set -> must REFUSE to answer, not answer weakly.
    one = [{"date": "2026-11-03", "gpus": "0", "floor_median": 0.0810 + i * 1e-6,
            "source": "T-009"} for i in range(5)]
    txt = "\n".join(T.analyse(one))
    assert "cannot be asked yet" in txt, "a single device set must refuse the question"

    # Two sets but two days -> must refuse on confounding.
    two_days = one + [{"date": "2026-11-04", "gpus": "2", "floor_median": 0.0811,
                       "source": "T-009"}]
    txt = "\n".join(T.analyse(two_days))
    assert "too few to separate" in txt, "two days must not support a verdict"

    # Three days, two sets, and the drift INSIDE one device set -> the device
    # must be reported as not accounting for it. This is the branch that would
    # keep T-009 open, and it is the one most likely to be written backwards.
    spread_within = [
        {"date": "2026-11-03", "gpus": "0", "floor_median": 0.08087, "source": "T-009"},
        {"date": "2026-11-04", "gpus": "0", "floor_median": 0.08109, "source": "T-009"},
        {"date": "2026-11-05", "gpus": "2", "floor_median": 0.08100, "source": "T-009"},
    ]
    txt = "\n".join(T.analyse(spread_within))
    assert "does NOT account" in txt, \
        "drift inside one device set must not be credited to the device"

    # The mirror: drift that MOSTLY tracks the device set, with a residue
    # inside one device, must report the residue rather than round it away.
    tracks = [
        {"date": "2026-11-03", "gpus": "0", "floor_median": 0.080870, "source": "T-009"},
        {"date": "2026-11-04", "gpus": "0", "floor_median": 0.080871, "source": "T-009"},
        {"date": "2026-11-05", "gpus": "2", "floor_median": 0.081093, "source": "T-009"},
    ]
    txt = "\n".join(T.analyse(tracks))
    assert "Something beyond the device remains" in txt, \
        "a residue inside one device must be reported, not rounded away"

    # The branch the live ledger is actually in: EXACTLY zero inside a device,
    # across days. It must say there is no time component AND must not claim
    # the replica count is known, because the readings that would settle it
    # did not record their device.
    exact = [
        {"date": "2026-11-01", "gpus": "0", "floor_median": 0.08109002, "source": "x"},
        {"date": "2026-11-03", "gpus": "0", "floor_median": 0.08109002, "source": "x"},
        {"date": "2026-11-04", "gpus": "0", "floor_median": 0.08109002, "source": "x"},
        {"date": "2026-11-01", "gpus": "2", "floor_median": 0.08109313, "source": "x"},
    ]
    txt = "\n".join(T.analyse(exact))
    assert "EXACTLY ZERO" in txt, "a zero within-device spread must be stated as zero"
    assert "cannot be made to now" in txt, \
        "the unrecorded-device readings must be named as unrecoverable"

    # No branch may ever claim the question is settled.
    for data in (one, two_days, spread_within, tracks, exact):
        t = "\n".join(T.analyse(data))
        assert "established" not in t.replace("establish it", ""), \
            f"a verdict leaked into the analyser:\n{t}"

    # The rendered table must not round either. The precision guard above
    # covers the seed; this covers the output, which is the half that was
    # still rounding after the seed was fixed.
    src = (ROOT / "agents" / "engineer" / "workspace" / "run_t009.py").read_text()
    table = src[src.index('head = ['):src.index('a.report.write_text')]
    assert "floor_median']!r" in table, \
        "the ledger table must print floor medians at full precision"
    assert ":.8f" not in table, "the ledger table still rounds a floor median"

    print("dryrun_t009 ok -- analyser refuses on 1 set, on 2 days, and on both "
          "three-day branches; history range is [E-006]'s 2.16e-04")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
