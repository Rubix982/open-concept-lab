"""E-043 · Is `popular`'s retained delivery familiarity, or still composition? [T-092]

[E-038]: alias medians popular 0.587, random 0.301, recent 0.179 — a 0.408 span.
[E-040]: the drop is graded by surface similarity, and within strata `random` and `recent`
agree to 0.017-0.033, so composition explains those two. `popular` has 19 aliases in cells
of 5/5/9 and could not be tested — and it sits at the top of the span.

[T-092] names two accounts predicting opposite things: FAMILIARITY (a well-known entity's
alias is itself well-represented and keys closer to the canonical form, surviving
stratification) against COMPOSITION (its aliases are simply more similar strings).

**No new measurement.** The 370 coefficients exist, their 288 subjects map to QIDs in the
released files, and sitelink count is a standard popularity proxy. The question is whether
popularity predicts delivery once surface similarity is partialled out.

CONFOUND 1 IS A GATE, NOT A NOTE: if sitelink count does not separate RippleEdits' own
`popular` subset from `recent`, the proxy does not measure what the subsets encode and no
outcome here is readable. It is reported first and the run says so.

DELIVERY, NOT EFFECT. [E-028d], 2.96x.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from run_e035 import spearman  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FAMILIAR, INVERTED = 0.20, -0.20
STRATA = ((0.0, 0.5, "very different"), (0.5, 0.8, "moderate"), (0.8, 1.01, "near-variant"))


def partial(x, y, z) -> float:
    rxy, rxz, ryz = spearman(x, y), spearman(x, z), spearman(y, z)
    den = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return (rxy - rxz * ryz) / den if den else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args()
    rows = json.loads((ROOT / "results" / "E-040-alias-gradient.json").read_text())["rows"]
    sl = json.loads((ROOT / "data" / "wikidata" / "sitelinks.json").read_text())
    s2q, counts = sl["subject_to_qid"], sl["sitelinks"]

    data = []
    for r in rows:
        q = s2q.get(r["canon"])
        if q is None or q not in counts:
            continue
        data.append({**r, "qid": q, "sitelinks": counts[q]})
    dropped = len(rows) - len(data)

    log = setup("run_e043", config={
        "ticket": "E-043", "thread": "T-092", "n_aliases": len(data), "dropped": dropped,
        "proxy": "Wikidata sitelink count", "control": "SequenceMatcher ratio",
        "measure": "no model, no network — existing coefficients"})
    log.info("%d aliases with a sitelink count, %d dropped for want of one",
             len(data), dropped)

    # ---- confound 1: does the proxy separate the subsets it is standing in for? ----
    by_sub = {s: [d["sitelinks"] for d in data if d["subset"] == s]
              for s in ("popular", "random", "recent")}
    log.info("")
    log.info("VALIDITY CHECK — sitelinks by RippleEdits subset (confound 1)")
    log.info("%-10s%7s%10s%10s", "subset", "n", "median", "mean")
    for s, v in by_sub.items():
        if v:
            log.info("%-10s%7d%10.1f%10.1f", s, len(v), st.median(v), st.mean(v))
    pop, rec = by_sub.get("popular") or [], by_sub.get("recent") or []
    valid = bool(pop and rec and st.median(pop) > st.median(rec))
    if not valid:
        log.error("PROXY FAILS ITS CHECK — sitelink count does not rank `popular` above "
                  "`recent` (medians %.1f vs %.1f). It is not measuring what the subsets "
                  "encode, and NOTHING BELOW IS READABLE as a popularity result.",
                  st.median(pop) if pop else float('nan'),
                  st.median(rec) if rec else float('nan'))

    # ---- the partial, per alias and per subject (confound 2) ----
    y = [d["coef"] for d in data]
    p = [float(d["sitelinks"]) for d in data]
    r = [d["ratio"] for d in data]
    pr_alias = partial(p, y, r)

    bysubj: dict[str, list] = {}
    for d in data:
        bysubj.setdefault(d["canon"], []).append(d)
    sy = [st.median([x["coef"] for x in v]) for v in bysubj.values()]
    sp = [float(v[0]["sitelinks"]) for v in bysubj.values()]
    sr = [st.median([x["ratio"] for x in v]) for v in bysubj.values()]
    pr_subj = partial(sp, sy, sr)

    log.info("")
    log.info("  rho(sitelinks, coefficient)            %+.3f", spearman(p, y))
    log.info("  rho(similarity, coefficient)           %+.3f   ([E-040] found +0.778)",
             spearman(r, y))
    log.info("  rho(sitelinks, similarity)             %+.3f", spearman(p, r))
    log.info("")
    log.info("  PARTIAL rho(sitelinks, coef | similarity), per alias   %+.3f  (n=%d)",
             pr_alias, len(data))
    log.info("  PARTIAL rho(sitelinks, coef | similarity), per subject %+.3f  (n=%d)",
             pr_subj, len(bysubj))

    # ---- confound 4: do not rest on one estimator ----
    qs = sorted(p)
    t1, t2 = qs[len(qs) // 3], qs[2 * len(qs) // 3]
    log.info("")
    log.info("STRATIFIED — similarity stratum x sitelink tertile (cut at %.0f / %.0f)",
             t1, t2)
    log.info("%-16s%16s%16s%16s", "stratum", "low", "mid", "high")
    for lo, hi, name in STRATA:
        cells = []
        for a, b in ((-1, t1), (t1, t2), (t2, 1e9)):
            v = [d["coef"] for d in data
                 if lo <= d["ratio"] < hi and a <= d["sitelinks"] < b]
            cells.append(f"{st.median(v):.3f} ({len(v)})" if len(v) >= 3 else f"— ({len(v)})")
        log.info("%-16s%16s%16s%16s", name, *cells)

    log.info("")
    use = pr_subj if abs(pr_subj - pr_alias) > 0.1 else pr_alias
    which = "per-subject" if use is pr_subj else "per-alias"
    if not valid:
        log.warning("VERDICT: UNREADABLE — the proxy failed its validity check. The "
                    "partial is %+.3f but it cannot be interpreted as popularity.", use)
    elif use >= FAMILIAR:
        log.info("VERDICT: FAMILIARITY — partial rho %+.3f (%s). A well-known entity "
                 "retains delivery under renaming beyond what string similarity explains, "
                 "and [E-038]'s subset span becomes a popularity effect.", use, which)
    elif use <= INVERTED:
        log.warning("VERDICT: INVERTED — partial rho %+.3f (%s). Well-known entities lose "
                    "MORE delivery under renaming. No account on the table predicts this.",
                    use, which)
    else:
        log.info("VERDICT: NOT FAMILIARITY — partial rho %+.3f (%s), inside [%.2f, %.2f]. "
                 "How well known an entity is does not predict delivery once the string is "
                 "accounted for. [T-092] needs another account and [E-038]'s caution "
                 "stands.", use, which, INVERTED, FAMILIAR)

    out = ROOT / "results" / "E-043-popularity.json"
    out.write_text(json.dumps({"ticket": "E-043", "thread": "T-092", "n": len(data),
                               "proxy_valid": valid,
                               "partial_alias": pr_alias, "partial_subject": pr_subj,
                               "rho_sitelinks": spearman(p, y),
                               "rho_similarity": spearman(r, y),
                               "subset_sitelinks": {k: (st.median(v) if v else None)
                                                    for k, v in by_sub.items()},
                               "rows": data}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
