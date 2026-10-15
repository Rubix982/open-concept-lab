"""E-042 · Does the negative ‖Δv‖ sign survive relation, model, layer and probe? [T-094]

[E-035] found `‖Δv‖` against propagation at −0.423 — a bigger update travels LESS far,
against the rationale the candidate was listed with. [T-094] says the first move is a check
on whether the sign survives, not a theory about why, because [E-033] found a 6/6 effect
and a 1/6 effect side by side in one run.

The check costs nothing: [E-033] left six result files carrying ‖Δv‖ per subject with pre-
and post-edit log-probabilities for three probes and their controls. Six cells, 2 models x
2 relations x 2 layers, n=29.

NOT INDEPENDENT REPLICATIONS. All 29 subjects in every cell are a subset of [E-035]'s 42,
so this varies model, relation, layer and probe while holding the PEOPLE fixed. A
consistent sign shows the effect is not specific to the configuration; it says nothing
about whether it is specific to these 29 subjects. No p-value is computed over the six,
because that would imply an independence this design does not have.

EFFECT, NOT DELIVERY — unusually for this record. The outcome is a measured drop.
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from run_e035 import spearman  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
HOLDS, FAILS = 5, 2


def cells() -> list[dict]:
    out = []
    for f in sorted(glob.glob(str(ROOT / "results" / "E-033-crossover-*.json"))):
        d = json.loads(Path(f).read_text())
        probe = d.get("type_matched_probe")
        rows = d.get("results") or []
        if not probe or not rows:
            continue
        xs, ys = [], []
        for r in rows:
            b, e = r.get("base", {}), r.get("edit", {})
            sk, ck = f"self|{probe}", f"control|{probe}"
            if sk not in b or sk not in e or ck not in b or ck not in e:
                continue
            # The control-differenced drop, exactly [E-029]'s construction.
            xs.append(r["norm"])
            ys.append((b[sk] - e[sk]) - (b[ck] - e[ck]))
        if len(xs) < 10:
            continue
        out.append({"file": Path(f).name, "model": d.get("model", "?").split("/")[-1],
                    "relation": d.get("relation", "?"), "layer": d.get("layer"),
                    "probe": probe, "n": len(xs),
                    "rho": spearman(xs, ys),
                    "mean_norm": st.mean(xs), "mean_prop": st.mean(ys),
                    "subjects": [r["subject"] for r in rows]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    cs = cells()
    if not cs:
        raise SystemExit("no usable E-033 cells found")

    # Confound 1, asserted rather than asserted-in-prose: every cell must be the same
    # people, or the table means something different from what the ticket says.
    e35 = {r["subject"] for r in json.loads(
        (ROOT / "results" / "E-035-propagation-candidates.json").read_text())["rows"]}
    overlaps = [len(set(c["subjects"]) & e35) for c in cs]

    log = setup("run_e042", config={
        "ticket": "E-042", "thread": "T-094", "cells": len(cs),
        "incumbent": "[E-035] rho(||dv||, propagation) = -0.423 at 8B/birthplace/L5/city",
        "design": "within-subject: model, relation, layer and probe vary; PEOPLE do not",
        "measure": "EFFECT (a control-differenced drop), not delivery"})
    log.info("%d cells; subjects per cell overlapping [E-035]'s 42: %s",
             len(cs), overlaps)
    if any(o < c["n"] for o, c in zip(overlaps, cs)):
        log.warning("a cell contains subjects outside [E-035]'s set — confound 1's "
                    "within-subject framing does not hold for it")

    log.info("")
    log.info("%-10s%-13s%7s%14s%6s%9s", "model", "relation", "layer", "matched probe",
             "n", "rho")
    neg = 0
    for c in sorted(cs, key=lambda x: (x["model"], x["relation"], x["layer"] or 0)):
        log.info("%-10s%-13s%7s%14s%6d%+9.3f", c["model"], c["relation"],
                 c["layer"], c["probe"], c["n"], c["rho"])
        neg += c["rho"] < 0

    log.info("")
    log.info("negative in %d of %d cells; [E-035] measured -0.423 on a seventh "
             "configuration", neg, len(cs))
    med = st.median([c["rho"] for c in cs])
    log.info("median rho across cells %+.3f", med)

    log.info("")
    if neg >= HOLDS:
        log.info("VERDICT: SIGN HOLDS — negative in %d of %d. A bigger update travelling "
                 "less far is not specific to one relation, model, layer or probe, so "
                 "[T-094] becomes a question about mechanism rather than replication. "
                 "WITHIN-SUBJECT: this says nothing about other people.", neg, len(cs))
    elif neg <= FAILS:
        log.warning("VERDICT: SIGN DOES NOT HOLD — negative in only %d of %d. [E-035]'s "
                    "-0.423 is a fact about one configuration and must be written as one. "
                    "This also weakens [R-015]'s reopening of [T-085], which leans on "
                    "||dv|| being something ES fails to see.", neg, len(cs))
    else:
        log.info("VERDICT: MIXED — negative in %d of %d. No general statement; the cells "
                 "that differ are the result.", neg, len(cs))

    out = ROOT / "results" / "E-042-dv-sign.json"
    out.write_text(json.dumps(
        {"ticket": "E-042", "thread": "T-094", "n_cells": len(cs), "n_negative": neg,
         "median_rho": med, "incumbent_rho": -0.423,
         "cells": [{k: v for k, v in c.items() if k != "subjects"} for c in cs]}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
