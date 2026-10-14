"""E-035 · What sets how far an edit travels? A pre-registered candidate sweep. [T-086]

[E-029] measured the two obvious predictors of propagation at Spearman 0.419 and 0.425 —
about 18% of variance, and near-identical to each other, so one weak view rather than two.
The coefficient cannot help BY CONSTRUCTION: pinned at exactly 1.000 across precisely the
probes whose outcomes differ most, it has zero variance where the outcome varies. [R-012]
then withdrew the only candidate explanation available.

**This ticket does not invent a candidate. It eliminates.** Seven quantities against the
same 42 subjects' propagation, six of them from data already on disk.

    FOUND             some candidate reaches rho >= 0.60 AND beats the incumbent by >= 0.15
    NOTHING BEATS IT  none exceeds 0.50 -> magnitude is set by none of these, which is a
                      sharper statement of [T-086] than it has now, and the likely outcome
    MULTICOLLINEAR    two or more clear 0.50 but correlate above 0.80 with each other

Seven tests on 42 subjects: the Holm-adjusted threshold is reported beside every rho and a
candidate clearing only the unadjusted bar has not cleared it.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402
from run_e029 import spearman  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
LAYER = 5
MODEL = "meta-llama/Llama-3.1-8B"
INCUMBENT = 0.425          # [E-029], ES margin, the best of the two already measured
FOUND_RHO, FOUND_MARGIN, FLOOR_RHO, COLLINEAR = 0.60, 0.15, 0.50, 0.80
#: candidates 1-3 are algebraically related; they count as one hit, never three
NORM_GROUP = {"||dv||", "||k*||", "||dv||/||k*||"}


def holm(n_tests: int, alpha: float = 0.05) -> list[float]:
    """Holm thresholds, smallest p first. Reported as rho equivalents by the caller."""
    return [alpha / (n_tests - i) for i in range(n_tests)]


def rho_at_p(p: float, n: int) -> float:
    """The |rho| a two-sided test needs to reach p at this n, via the t approximation."""
    import math
    # t = r*sqrt((n-2)/(1-r^2));  invert for r given a two-sided p
    df = n - 2
    lo, hi = 0.0, 0.999999
    for _ in range(200):
        mid = (lo + hi) / 2
        t = mid * math.sqrt(df / max(1e-12, 1 - mid * mid))
        # two-sided p from the t distribution, by its incomplete beta
        x = df / (df + t * t)
        pv = _betainc(df / 2, 0.5, x)
        if pv > p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta, by continued fraction. Enough for a threshold."""
    import math
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(300):
        m, num = i // 2, 0.0
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1 - c * d) < 1e-10:
            break
    return front * (f - 1)


def candidates(log, want_remote: bool) -> tuple[dict, list[float]]:
    e29 = json.loads((ROOT / "results" / "E-029-es-vs-propagation.json").read_text())
    ps = e29["per_subject"]
    b26 = json.loads((ROOT / "results" / "E-026b-edit-prompt.json").read_text())
    cids = b26["case_ids"]
    prop = ps["propagation"]
    d = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s1538.pt")
    k = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
    # Completeness, not existence. [E-033] loaded 9 of 29 deltas, logged "cached", and
    # walked into scoring short; here a missing subject would silently shorten the
    # correlation instead, which is worse because it still produces a number.
    want = {f"{c}|real" for c in cids}
    missing = sorted((want - set(d)) | (want - set(k)))
    if missing:
        raise SystemExit(f"cache incomplete: {len(missing)} of {len(want)} absent "
                         f"({missing[:3]}...). Correlating on a subset would still "
                         f"produce a rho, which is why this refuses rather than warns.")

    dv = [float(d[f"{c}|real"].norm()) for c in cids]
    ks = [float(k[f"{c}|real"].norm()) for c in cids]
    cand = {
        "||dv||": dv,
        "||k*||": ks,
        "||dv||/||k*||": [a / b for a, b in zip(dv, ks)],
        "baseline log P(true)": ps["baseline_true"],
        "target prior log P(target)": b26["raw"]["base"]["target"],
    }

    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    subs = [chains[c]["outer"]["subject"] for c in cids]
    m = connect(MODEL)
    tok = m.tokenizer
    cand["subject token count"] = [float(len(tok(s).input_ids) - 1) for s in subs]

    if want_remote:
        # the one candidate needing the network: how large is the delta against what is
        # already at that position? one read per subject, no edit applied
        from edit import subject_last_index
        norms = []
        for n, (c, s) in enumerate(zip(cids, subs), 1):
            prompt = chains[c]["outer"]["prompt"]
            idx = subject_last_index(tok, prompt, s)

            def once(p=prompt, i=idx):
                with _quiet_stdout(), m.trace(p, remote=True):
                    h = m.model.layers[LAYER].output[0][0, i].half().save()
                with _quiet_stdout():
                    return h.float()
            norms.append(float(retrying(once, what=f"resid {c}").norm()))
            if n % 10 == 0:
                log.info("  residual norms %d/%d", n, len(cids))
        cand["residual norm at subject, L5"] = norms
    else:
        log.warning("skipping the residual-norm candidate (--no-remote): 6 of 7 measured")
    return cand, prop


def report(cand: dict, prop: list[float], log) -> None:
    n = len(prop)
    rows = []
    for name, xs in cand.items():
        rows.append((name, abs(spearman(xs, prop)), spearman(xs, prop)))
    rows.sort(key=lambda r: -r[1])
    thresholds = [rho_at_p(p, n) for p in holm(len(rows))]

    log.info("")
    log.info("E-035 — candidate predictors of propagation (n=%d, layer %d)", n, LAYER)
    log.info("outcome spread: mean %.2f, sd %.2f, range %.2f  (a ceiling on any rho)",
             st.mean(prop), st.stdev(prop), max(prop) - min(prop))
    log.info("incumbent: ES margin at rho %.3f  [E-029]", INCUMBENT)
    log.info("")
    log.info("%-32s%8s%10s%10s%8s", "candidate", "rho", "signed", "Holm", "clears")
    clears = []
    for (name, arho, srho), thr in zip(rows, thresholds):
        ok = arho >= thr
        if ok:
            clears.append((name, arho))
        log.info("%-32s%8.3f%10.3f%10.3f%8s", name, arho, srho, thr,
                 "yes" if ok else "no")

    log.info("")
    strong = [(nm, r) for nm, r in clears if r >= FLOOR_RHO]
    # candidates 1-3 are one quantity in three forms; never count them as three hits
    distinct = {("norm-group" if nm in NORM_GROUP else nm) for nm, _ in strong}
    best = max(strong, key=lambda x: x[1]) if strong else None

    collinear = []
    if len(strong) > 1:
        for i, (a, _) in enumerate(strong):
            for b, _ in strong[i + 1:]:
                r = abs(spearman(cand[a], cand[b]))
                if r >= COLLINEAR:
                    collinear.append((a, b, r))

    if collinear and len(distinct) > 1:
        log.warning("VERDICT: MULTICOLLINEAR — %s correlate at >= %.2f with each other, so "
                    "they are one quantity wearing several names. Say which, rather than "
                    "reporting a winner.",
                    "; ".join(f"{a} / {b} ({r:.2f})" for a, b, r in collinear), COLLINEAR)
    elif best and best[1] >= FOUND_RHO and best[1] - INCUMBENT >= FOUND_MARGIN:
        log.info("VERDICT: FOUND — %s reaches rho %.3f, beating the incumbent by %.3f. "
                 "[T-086] has its first candidate. This is CORRELATIONAL: it licenses a "
                 "follow-up design, never a claim.", best[0], best[1], best[1] - INCUMBENT)
    elif not strong:
        log.info("VERDICT: NOTHING BEATS IT — no candidate exceeds rho %.2f. Propagation "
                 "magnitude is set by none of: update size, key size, their ratio, the "
                 "belief's strength, the target's prior, the subject's length, or the "
                 "local residual norm. That is a sharper statement of [T-086] than it had.",
                 FLOOR_RHO)
    else:
        log.info("VERDICT: between the bands — best is %s at rho %.3f (needs %.2f and a "
                 "%.2f margin). Report the table, claim nothing.",
                 best[0], best[1], FOUND_RHO, FOUND_MARGIN)

    out = ROOT / "results" / "E-035-candidates.json"
    out.write_text(json.dumps({"ticket": "E-035", "thread": "T-086", "n": n,
                               "incumbent": INCUMBENT,
                               "rho": {nm: r for nm, r, _ in rows},
                               "holm": dict(zip([r[0] for r in rows], thresholds)),
                               "candidates": cand, "propagation": prop}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-remote", action="store_true")
    ap.add_argument("--seed", type=int, default=1538)
    a = ap.parse_args()
    log = setup("run_e035", config={
        "ticket": "E-035", "thread": "T-086", "model": MODEL, "layer": LAYER,
        "incumbent_rho": INCUMBENT, "bands": {"FOUND": FOUND_RHO, "floor": FLOOR_RHO,
                                              "collinear": COLLINEAR},
        "correction": "Holm over 7 tests", "measure": "Spearman against [E-029] propagation"})
    cand, prop = candidates(log, not a.no_remote)
    report(cand, prop, log)


if __name__ == "__main__":
    main()
