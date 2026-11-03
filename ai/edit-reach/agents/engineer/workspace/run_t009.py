"""T-009 · Does the floor median move when the set of serving GPUs moves?

[E-006] left ~2e-04 of observed drift unattributed. Four readings of the same
42 floor probes, over two days:

    0.08087725   [E-001]  10-31
    0.08094215   [E-005]  11-01, first reading
    0.08109000   [E-006]  11-01, GPU 0
    0.08109313   [E-006]  11-01, GPU 2

Range 2.16e-04. The serving device explains 3.11e-06 of it -- 1.4%.

[E-009] then promoted one candidate from guess to observation: the set of GPUs
serving this model CHANGED between 11-01 (GPUs 0 and 2) and 11-03 (GPU 0
alone, 16/16 connections). A deployment change demonstrably happens between
days, and it sits between exactly the sessions whose medians differ.

**That is a coincidence of timing, not a measurement.** Nothing yet shows the
two move together. This script is the falsifier: one reading a day, recording
the device set and the median at full precision, until there are enough days
to say whether the median moves when the device set does.

**What would refute the deployment hypothesis.** The median moving on a day
when the device set did not, or holding across a day when it did. Either is
decisive and either is cheap. The prediction being tested is that they move
together; the honest expectation is that the deployment is only one of several
things that change between days, so partial agreement is the likely outcome
and would settle nothing -- which is why the ledger records the raw values
rather than a verdict.

One fresh connection, one trace, 126 prompts. Appends; never rewrites.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parent))

from editreach.coefficient import keys_at                         # noqa: E402
from editreach.data import load_counterfact                       # noqa: E402
from editreach.logs import setup                                  # noqa: E402
from editreach.remote import connect                              # noqa: E402
from editreach.rome import subject_last_index                     # noqa: E402
import run_e001 as R                                              # noqa: E402

#: Prior readings, from the tickets that produced them. Carried here so the
#: ledger starts with history rather than with today, and so a drift that
#: predates this script is visible on its first run.
HISTORY: tuple[dict, ...] = (
    # FULL precision, read back out of the result JSONs. The first version of
    # this table carried the 8-decimal figures that had been quoted in prose,
    # and that alone hid the finding: today's reading differs from [E-006]'s
    # GPU 0 by 2.15e-08 when rounded and by EXACTLY ZERO when not. A ledger
    # built to detect bit-identity must not be seeded with rounded numbers.
    {"date": "2026-10-31", "source": "E-001", "gpus": "?",
     "floor_median": 0.08087725, "precision": "8dp, quoted in [E-006]; the "
     "full-precision value is not recoverable from E-001's artifacts"},
    {"date": "2026-11-01", "source": "E-005/language#0", "gpus": "?",
     "floor_median": 0.08094214687103357},
    {"date": "2026-11-01", "source": "E-005/language#1", "gpus": "?",
     "floor_median": 0.08109313181234508},
    {"date": "2026-11-01", "source": "E-005/language#2", "gpus": "?",
     "floor_median": 0.08109313181234508},
    {"date": "2026-11-01", "source": "E-005/transformers#0", "gpus": "?",
     "floor_median": 0.08109313181234508},
    {"date": "2026-11-01", "source": "E-005/transformers#1", "gpus": "?",
     "floor_median": 0.08109313181234508},
    {"date": "2026-11-01", "source": "E-005/transformers#2", "gpus": "?",
     "floor_median": 0.08109313181234508},
    {"date": "2026-11-01", "source": "E-006", "gpus": "0", "readings": 8,
     "signature": "edd2b2b152de2098", "floor_median": 0.08109002151514136},
    {"date": "2026-11-01", "source": "E-006", "gpus": "2", "readings": 8,
     "signature": "54a1755349e607dc", "floor_median": 0.08109313181234508},
)

#: The range observed before this ledger existed, DERIVED from the table above
#: rather than typed again. It was typed again once, at 8 decimal places, and
#: stopped matching the table the moment the table gained full precision.
E006_RANGE = (min(h["floor_median"] for h in HISTORY),
              max(h["floor_median"] for h in HISTORY))


def signature(t: torch.Tensor) -> str:
    return hashlib.sha1(t.numpy().tobytes()).hexdigest()[:16]


def gpu_of(meta: dict) -> str:
    by_gpu = meta.get("max_mem_by_gpu") or {}
    return ",".join(sorted(by_gpu)) if by_gpu else "?"


def read_once(probes: Path, edit_slice: Path, layer: int, log) -> dict:
    """One fresh connection, one trace, the same three groups [E-006] read."""
    items = json.loads(probes.read_text())["items"]
    anchors = [i for i in items if i["id"].endswith("/anchor-prefix")]
    floors = [i for i in items if i["id"].endswith("/anchor-floor")]
    ks, _ = R.load_edit_cache(edit_slice)
    cf = {str(r.case_id): r for r in
          load_counterfact(edit_slice / "data" / "counterfact.json.gz")}

    model = connect(R.MODEL)
    tok = model.tokenizer
    prompts = [r["prompt"] for r in anchors]
    positions = [subject_last_index(tok, r["prompt"], r["subject"],
                                    occurrence=r.get("occurrence", 0)) for r in anchors]
    eps = [cf[r["case_id"]].rewrite.prompt.format(cf[r["case_id"]].rewrite.subject)
           for r in anchors]
    epos = [subject_last_index(tok, e, r["subject"]) for e, r in zip(eps, anchors)]
    fprompts = [r["prompt"] for r in floors]
    fpos = [subject_last_index(tok, r["prompt"], r["subject"],
                               occurrence=r.get("occurrence", 0)) for r in floors]

    meta: dict = {}
    keys = keys_at(model, prompts + eps + fprompts, positions + epos + fpos,
                   layer=layer, remote=True, meta_out=meta)
    half = len(anchors)
    coef = [float(k @ s) / float(s @ s)
            for k, s in zip(keys[:half], keys[half:2 * half])]
    fl = [float(k @ ks[f"{r['case_id']}|real"].float())
          / float(ks[f"{r['case_id']}|real"].float()
                  @ ks[f"{r['case_id']}|real"].float())
          for r, k in zip(floors, keys[2 * half:])]

    now = dt.datetime.now().astimezone()
    return {
        "date": now.date().isoformat(),
        "time": now.strftime("%H:%M:%S%z"),
        "source": "T-009",
        "gpus": gpu_of(meta),
        "runtime": meta.get("runtime"),
        "signature": signature(keys),
        # The anchor ratio is read inside the trace and cancels the device, so
        # it is the control: if it ever leaves 0, the reading is faulty and the
        # day's floor value means nothing.
        "anchor_worst_deviation": max(abs(c - 1.0) for c in coef),
        "floor_median": st.median(fl),
        "n_floors": len(fl),
    }


def census(rows: list[dict]) -> list[str]:
    """How many DISTINCT values the quantity takes, and how often each recurs.

    This, not a spread, is the statistic that answers T-009. A spread assumes a
    continuum and reports how wide it is. If the quantity instead takes a few
    exact values and repeats them, the spread is a summary of the wrong shape --
    it says "drift of 2.16e-04" where the truth is "three values, each exact".
    """
    out = ["", "value census -- distinct values and how often each recurs", ""]
    by_val: dict[float, list[dict]] = defaultdict(list)
    for r in rows:
        by_val[r["floor_median"]].append(r)
    for v in sorted(by_val):
        rs = by_val[v]
        n = sum(r.get("readings", 1) for r in rs)
        days = sorted({r["date"] for r in rs})
        gpus = sorted({r.get("gpus", "?") for r in rs} - {"?"}) or ["unrecorded"]
        out.append(f"  {v!r:<22} n={n:<3} GPUs {','.join(gpus):<10} "
                   f"{' '.join(days)}")
    out.append("")
    out.append(f"  {len(by_val)} distinct values over "
               f"{sum(r.get('readings', 1) for r in rows)} readings")
    multi = [v for v, rs in by_val.items() if len({r["date"] for r in rs}) > 1]
    if multi:
        out.append(f"  {len(multi)} of them recur across more than one day, "
                   f"bit-exactly")
        out.append("")
        out.append("  A value that repeats to the last bit on a different day is")
        out.append("  not drift. It is a fingerprint of which replica served you.")
    return out


def analyse(rows: list[dict]) -> list[str]:
    """What the ledger can and cannot say yet. Deliberately refuses to guess."""
    out = []
    dated = [r for r in rows if r.get("gpus") not in (None, "?")]
    by_gpu: dict[str, list[float]] = defaultdict(list)
    for r in dated:
        by_gpu[r["gpus"]].append(r["floor_median"])

    # The sharpest statistic available, and it is not a spread: does a reading
    # taken on one day come back BIT-IDENTICAL on another? A spread can be made
    # small by a tolerance; bit-identity cannot be argued with.
    by_sig: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("signature"):
            by_sig[r["signature"]].append(r)
    recurring = {s: rs for s, rs in by_sig.items()
                 if len({r["date"] for r in rs}) > 1}

    meds = [r["floor_median"] for r in rows]
    out.append(f"readings        {len(rows)}  ({len(dated)} with a known device set)")
    out.append(f"floor median    {min(meds):.8f} .. {max(meds):.8f}"
               f"   range {max(meds) - min(meds):.3e}")

    days = sorted({r["date"] for r in rows})
    sets = sorted({r["gpus"] for r in dated})
    out.append(f"days            {len(days)}  {days[0]} .. {days[-1]}")
    out.append(f"device sets     {sets if sets else 'none recorded'}")

    if recurring:
        out.append("")
        out.append("  BIT-IDENTICAL ACROSS DAYS")
        for sig, rs in sorted(recurring.items()):
            ds = sorted({r["date"] for r in rs})
            gs = sorted({r.get("gpus", "?") for r in rs})
            same = len({r["floor_median"] for r in rs}) == 1
            out.append(f"    {sig}  GPUs {','.join(gs):<8} {' and '.join(ds)}"
                       f"   floor identical: {same}")
        out.append("    A reading reproduces exactly across days when the reported")
        out.append("    device matches. There is no day effect to find for a")
        out.append("    device-matched comparison; the drift lives in WHICH replica")
        out.append("    served you, and readings whose device went unrecorded cannot")
        out.append("    be attributed after the fact.")

    if len(sets) < 2:
        out.append("")
        out.append("  Only one device set has been seen, so the question this ledger")
        out.append("  exists to answer cannot be asked yet. Keep reading daily.")
        return out
    if len(days) < 3:
        out.append("")
        out.append("  Two device sets but fewer than three days: too few to separate")
        out.append("  'the device changed' from 'the day changed'.")
        return out

    within = max((max(v) - min(v)) for v in by_gpu.values() if len(v) > 1) \
        if any(len(v) > 1 for v in by_gpu.values()) else None
    across = max(meds) - min(meds)
    out.append("")
    for g, v in sorted(by_gpu.items()):
        out.append(f"  GPUs {g:<8} n={len(v):<3} median {st.median(v):.8f}"
                   f"  spread {max(v) - min(v):.3e}")
    if within is not None:
        out.append(f"  spread WITHIN a device set   {within:.3e}")
        out.append(f"  spread ACROSS everything     {across:.3e}")
        out.append("")
        if within >= across * 0.5:
            out.append("  The within-device spread is of the same order as the total.")
            out.append("  The device set does NOT account for the drift. T-009 stands.")
        elif within == 0.0:
            out.append("  Within a device the spread is EXACTLY ZERO, across days.")
            out.append("  So there is no time component to find: a reading is a")
            out.append("  function of which replica served it and nothing else that")
            out.append("  has been varied. What remains open is narrower than T-009")
            out.append("  was opened for -- not 'what causes the drift' but 'how many")
            out.append("  replicas are there', and the readings that would answer it")
            out.append("  did not record their device and cannot be made to now.")
        else:
            out.append("  The device set accounts for most of the spread, but not")
            out.append("  all: readings on one device still differ by")
            out.append(f"  {within:.3e}. Something beyond the device remains.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--probes", type=Path, default=Path("probes/generated.json"))
    ap.add_argument("--edit-slice", type=Path, default=HERE.parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=5)
    ap.add_argument("--ledger", type=Path, default=Path("results/T-009-ledger.jsonl"))
    ap.add_argument("--report", type=Path, default=Path("results/T-009-ledger.md"))
    ap.add_argument("--analyse-only", action="store_true",
                    help="re-read the ledger and reprint, with NO remote call")
    a = ap.parse_args()

    log = setup("T-009")

    rows: list[dict] = []
    if a.ledger.exists():
        rows = [json.loads(l) for l in a.ledger.read_text().splitlines() if l.strip()]
    else:
        rows = [dict(h) for h in HISTORY]

    if not a.analyse_only:
        row = read_once(a.probes, a.edit_slice, a.layer, log)
        log.info("gpus %-8s  sig %s  anchors %.3e  floor %.8f",
                 row["gpus"], row["signature"],
                 row["anchor_worst_deviation"], row["floor_median"])
        if row["anchor_worst_deviation"] > 0.0:
            log.warning("anchor control left 0.000e+00 — today's floor value is "
                        "not comparable and is recorded as suspect")
            row["suspect"] = True
        lo, hi = E006_RANGE
        if not lo <= row["floor_median"] <= hi:
            log.warning("floor %.8f is OUTSIDE [E-006]'s observed range "
                        "[%.8f, %.8f] — that is news by itself",
                        row["floor_median"], lo, hi)
        rows.append(row)
        a.ledger.parent.mkdir(parents=True, exist_ok=True)
        with a.ledger.open("a") as fh:
            if a.ledger.stat().st_size == 0:
                for h in HISTORY:
                    fh.write(json.dumps(h) + "\n")
            fh.write(json.dumps(row) + "\n")

    lines = census(rows) + analyse(rows)
    for l in lines:
        log.info(l)

    head = ["# T-009 ledger — does the floor median move when the device set does?",
            "",
            "Appended by `agents/engineer/workspace/run_t009.py`, one reading a day.",
            "42 floor probes, layer 5, Llama-3.1-8B, one fresh connection each.",
            "",
            "Floor medians are printed at **full precision**. The whole point of",
            "this table is that values repeat to the last bit; rendering them at",
            "eight decimals would hide exactly what it exists to show, and did,",
            "in its first draft.",
            "",
            "| date | time | source | GPUs | floor median | anchor control | signature |",
            "|---|---|---|---|---|---|---|"]
    for r in rows:
        head.append(f"| {r['date']} | {r.get('time','—')} | {r['source']} | "
                    f"{r.get('gpus','?')} | `{r['floor_median']!r}` | "
                    f"{r.get('anchor_worst_deviation', float('nan')):.3e} | "
                    f"{r.get('signature','—')} |")
    head += ["", "## What the ledger says today", "", "```"] + lines + ["```"]
    a.report.write_text("\n".join(head) + "\n")
    log.info("written: %s", a.report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
