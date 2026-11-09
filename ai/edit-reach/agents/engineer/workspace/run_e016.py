"""E-016 · Does a subject's prominence predict how hard an edit hits?

Seven geometric candidates have been eliminated against a pre-registered floor,
and the published page says the absence "is now evidence of having looked."
Every one of them was a property of the activation geometry. This is the first
test of a property of the *subject*. Closes C-008, answers T-002.

Two predictors of per-subject damage:

  prominence       number of Wikipedia language editions (Wikidata sitelinks)
  dependent count  number of Wikidata statements on the subject's item

Damage is the median `excess` -- real movement minus same-subject control
movement -- because [E-002] showed generic subject-keyed instability is 65x the
content effect, so raw movement would measure the control's job.

Everything is offline except one cached Wikidata fetch.

    python agents/engineer/workspace/run_e016.py
"""
from __future__ import annotations

import gzip
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from editreach.logs import setup  # noqa: E402

E001 = ROOT / "results/E-001-predicted-vs-measured.json"
SNAP = ROOT.parent / "edit-slice/data/wikidata/2026-09-20/snapshot.json.gz"
SITE = ROOT / "results/cache/E016_sitelinks.json"
OUT = ROOT / "results/E-016-subject-properties.json"

SEED = 1538
RESAMPLES = 10_000


def rank(x: np.ndarray) -> np.ndarray:
    """Average ranks, so ties do not bias the correlation."""
    order = np.argsort(x, kind="stable")
    r = np.empty(len(x), float)
    r[order] = np.arange(len(x), dtype=float)
    # average over tied groups
    for v in np.unique(x):
        m = x == v
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d else float("nan")


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    return pearson(rank(a), rank(b))


def residual(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """y with the linear part of x removed, on ranks."""
    X = np.column_stack([np.ones(len(x)), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return y - X @ beta


def partial_spearman(a: np.ndarray, b: np.ndarray, *ctrl: np.ndarray) -> float:
    """Spearman between a and b with every control removed from both."""
    ra, rb = rank(a), rank(b)
    C = np.column_stack([rank(c) for c in ctrl])
    for j in range(C.shape[1]):
        pass
    X = np.column_stack([np.ones(len(ra)), C])
    beta_a, *_ = np.linalg.lstsq(X, ra, rcond=None)
    beta_b, *_ = np.linalg.lstsq(X, rb, rcond=None)
    return pearson(ra - X @ beta_a, rb - X @ beta_b)


def boot(fn, *cols, rng) -> tuple[float, float]:
    n = len(cols[0])
    vals = []
    for _ in range(RESAMPLES):
        i = rng.integers(0, n, n)
        try:
            v = fn(*[c[i] for c in cols])
        except np.linalg.LinAlgError:
            continue
        if np.isfinite(v):
            vals.append(v)
    if len(vals) < RESAMPLES // 2:
        return (float("nan"), float("nan"))
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def main() -> None:
    log = setup("run_e016", config={"seed": SEED, "resamples": RESAMPLES})

    items = json.load(open(E001))["items"]
    snap = json.load(gzip.open(SNAP, "rt"))
    cache = json.load(open(SITE))
    by_label = {v: k for k, v in snap["labels"].items()}
    claims = snap["claims"]
    sitelinks = cache["sitelinks"]

    # ---- per-subject table ----
    rows = []
    unresolved = []
    for owner in sorted({it["owner"] for it in items}):
        mine = [it for it in items if it["owner"] == owner]
        qid = by_label.get(owner)
        if not qid or qid not in sitelinks:
            unresolved.append(owner)
            continue
        c = claims.get(qid, {})
        rows.append({
            "subject": owner, "qid": qid, "n_probes": len(mine),
            "median_excess": st.median(it["excess"] for it in mine),
            "median_p_base": st.median(it["p_base"] for it in mine),
            "distinct_properties": len(c),
            "total_statements": sum(len(v) for v in c.values()),
            "sitelinks": sitelinks[qid],
            "families": dict(Counter(it["family"] for it in mine)),
        })
    log.info("%d subjects resolved, %d unresolved: %s",
             len(rows), len(unresolved), unresolved or "none")

    # ---- step 1: the gate ----
    all_excess = [it["excess"] for it in items]
    med_excess = st.median(all_excess)
    med_ctl = st.median(it["control_movement"] for it in items)
    log.info("gate: median excess over all %d probes %.4f "
             "(the paired identity-vs-content split lives in [E-002]; "
             "median control movement here %.4f)", len(items), med_excess, med_ctl)

    rng = np.random.default_rng(SEED)
    dmg = np.array([r["median_excess"] for r in rows])
    prom = np.array([r["sitelinks"] for r in rows], float)
    dep = np.array([r["distinct_properties"] for r in rows], float)
    tot = np.array([r["total_statements"] for r in rows], float)
    head = np.array([r["median_p_base"] for r in rows], float)

    # ---- confound 1: are the predictors independent? ----
    rho_pd = spearman(prom, dep)
    log.info("confound 1 — prominence vs dependent count: rho = %.3f%s",
             rho_pd, "  (>0.8: partials unstable at this n)" if abs(rho_pd) > 0.8 else "")

    res: dict[str, dict] = {}

    def record(name, fn, *cols):
        v = fn(*cols)
        lo, hi = boot(fn, *cols, rng=rng)
        res[name] = {"rho": float(v), "ci95": [lo, hi],
                     "excludes_zero": bool(np.isfinite(lo) and (lo > 0 or hi < 0))}
        log.info("%-46s rho = %+.3f  (95%% CI %+.3f, %+.3f)%s",
                 name, v, lo, hi, "  *" if res[name]["excludes_zero"] else "")

    record("prominence vs damage", spearman, prom, dmg)
    record("dependent count vs damage", spearman, dep, dmg)
    record("total statements vs damage", spearman, tot, dmg)
    record("headroom (p_base) vs damage", spearman, head, dmg)
    record("prominence | dependent count", partial_spearman, prom, dmg, dep)
    record("dependent count | prominence", partial_spearman, dep, dmg, prom)
    record("prominence | dependent count, headroom", partial_spearman, prom, dmg, dep, head)
    record("dependent count | prominence, headroom", partial_spearman, dep, dmg, prom, head)

    # ---- confound 3: families every subject has ----
    common = set.intersection(*(set(r["families"]) for r in rows))
    log.info("confound 3 — families present for every subject: %s", sorted(common) or "none")
    sens = None
    if common:
        dmg2 = np.array([
            st.median(it["excess"] for it in items
                      if it["owner"] == r["subject"] and it["family"] in common)
            for r in rows])
        sens = {
            "families": sorted(common),
            "prominence": float(spearman(prom, dmg2)),
            "dependent_count": float(spearman(dep, dmg2)),
        }
        log.info("confound 3 — on %s only: prominence %+.3f, dependent count %+.3f",
                 sorted(common), sens["prominence"], sens["dependent_count"])

    OUT.write_text(json.dumps({
        "ticket": "E-016", "card": "C-008",
        "n_subjects": len(rows), "unresolved": unresolved,
        "meta": {
            "damage": "median per-subject `excess` = real movement - same-subject control movement",
            "prominence": "Wikidata sitelinks (Wikipedia language editions), fetched 2026-11-09",
            "dependent_count": "distinct Wikidata properties on the subject's item",
            "snapshot": str(SNAP.name), "seed": SEED, "resamples": RESAMPLES,
            "gate_median_excess_all_probes": med_excess,
        },
        "predictor_correlation_prominence_vs_dependent": float(rho_pd),
        "results": res,
        "family_sensitivity": sens,
        "subjects": rows,
    }, indent=1) + "\n")
    log.info("wrote %s", OUT)


if __name__ == "__main__":
    main()
