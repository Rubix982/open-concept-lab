"""E-040 · Is the alias drop graded by surface distance? [T-087, follows E-038]

[E-038] found aliases drop in all three subsets and that the magnitude spans 0.408 across
them, so it reported the drop's direction and refused its size. This asks whether that span
is a CONSEQUENCE rather than a confound: if the drop is graded by how different the alias
string is, and the subsets differ in what kind of aliases they hold, one mechanism explains
both.

No model and no network — the 370 coefficients and their SequenceMatcher ratios are already
in [E-038]'s result file, written in one loop iteration and index-aligned by construction.

NOT FULLY PRE-REGISTERED, and the ticket says where: two bucket medians were seen while
verifying that alignment. Nothing here states an outcome about those two buckets. The
functional form, the subset decomposition and the token-length control were all unseen when
the bands were fixed.

DELIVERY, NOT EFFECT. [E-028d], 2.96x.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "results" / "E-037-ripple-floor-recent+random+popular.json"
GRADED_RHO, CONVERGE = 0.5, 0.15
#: Post-hoc, see the comment in main().
POWERED_N = 10
STRATA = ((0.0, 0.5, "very different"), (0.5, 0.8, "moderate"), (0.8, 1.01, "near-variant"))


def spearman(xs: list[float], ys: list[float]) -> float:
    """Rank correlation, ties averaged. Written out because scipy is not a dependency here
    and [E-029]'s rho was computed the same way, so the two numbers stay comparable."""
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(xs), rank(ys)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def partial_spearman(x: list[float], y: list[float], z: list[float]) -> float:
    """rho(x,y) with z partialled out, on ranks. Confound 1: surface ratio and token-count
    difference are entangled, and `subject_last_index` reads a token position."""
    rxy, rxz, ryz = spearman(x, y), spearman(x, z), spearman(y, z)
    den = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return (rxy - rxz * ryz) / den if den else float("nan")


def step_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Best two-level step over x, returning (threshold, residual sum of squares)."""
    best = (float("nan"), float("inf"))
    for t in sorted(set(xs)):
        lo = [y for x, y in zip(xs, ys) if x < t]
        hi = [y for x, y in zip(xs, ys) if x >= t]
        if len(lo) < 10 or len(hi) < 10:
            continue
        ml, mh = st.mean(lo), st.mean(hi)
        rss = sum((y - ml) ** 2 for y in lo) + sum((y - mh) ** 2 for y in hi)
        if rss < best[1]:
            best = (t, rss)
    return best


def line_fit(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """(slope, intercept, residual sum of squares) by least squares."""
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    a = my - b * mx
    return b, a, sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))


def acronymish(canon: str, surf: str) -> bool:
    """Confound 2: an acronym is not 'a bit different', it is a different kind of object."""
    if len(surf) > 8 or " " in surf.strip():
        return False
    letters = re.sub(r"[^A-Za-z]", "", surf)
    return bool(letters) and letters.isupper() and len(letters) <= 6 and len(canon) > len(surf) * 2


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=str(SRC))
    a = ap.parse_args()
    d = json.loads(Path(a.src).read_text())
    coefs = d["alias_different_surface"]
    dists = d["alias_surface_distance"]
    if len(coefs) != len(dists):
        raise SystemExit(f"misaligned: {len(coefs)} coefficients, {len(dists)} distances")

    # Which subset each alias came from. [E-038] built its entry list as
    # `[(s, e) for s in subsets for e in load(s)]`, so `alias_different_surface` is
    # ordered in contiguous SUBSET BLOCKS in the order the subsets were passed —
    # recent, random, popular. That is exact, where matching on coefficient VALUES is
    # not: two aliases sharing a value (0.000 and 1.000 are both common) would be
    # attributed arbitrarily, which is the `max()`-over-a-set bug of [R-013] in a new
    # costume. The block sizes are asserted against the counts [E-038] recorded, so a
    # wrong assumption fails loudly instead of producing a plausible table.
    by_sub = d.get("by_subset", {})
    order = [s.strip() for s in Path(a.src).stem.split("floor-")[-1].split("+")]
    sizes = {k: len(v.get("alias", [])) for k, v in by_sub.items()}
    expected = sum(sizes.values())
    if expected != len(coefs):
        raise SystemExit(f"subset counts {sizes} total {expected}, not {len(coefs)}")
    owner: dict[int, str] = {}
    i = 0
    for sub in order:
        for _ in range(sizes.get(sub, 0)):
            owner[i] = sub
            i += 1
    if i != len(coefs):
        raise SystemExit(f"block assignment covered {i} of {len(coefs)}; subset order "
                         f"{order} does not match {sorted(sizes)}")

    rows = [{"ratio": r, "canon": c, "surf": s, "coef": v,
             "dtok": abs(len(c.split()) - len(s.split())),
             "dchar": abs(len(c) - len(s)),
             "acronym": acronymish(c, s), "subset": owner.get(i, "?")}
            for i, ((r, c, s), v) in enumerate(zip(dists, coefs))]

    log = setup("run_e040", config={
        "ticket": "E-040", "n_aliases": len(rows), "source": Path(a.src).name,
        "measure": "existing coefficients vs SequenceMatcher ratio — no model, no network",
        "disclosure": "two bucket medians were seen before the bands were fixed; no band "
                      "is stated about them"})
    log.info("%d aliases with a different surface form", len(rows))

    xs = [r["ratio"] for r in rows]
    ys = [r["coef"] for r in rows]
    rho = spearman(xs, ys)
    rho_dtok = spearman([r["dtok"] for r in rows], ys)
    rho_part = partial_spearman(xs, ys, [float(r["dtok"]) for r in rows])
    slope, icept, rss_line = line_fit(xs, ys)
    thr, rss_step = step_fit(xs, ys)

    log.info("")
    log.info("E-040 — does surface distance grade the alias drop?")
    log.info("")
    log.info("  Spearman rho(ratio, coefficient)          %+.3f", rho)
    log.info("  Spearman rho(token-count diff, coef)      %+.3f   (confound 1)", rho_dtok)
    log.info("  rho(ratio, coef) partialling token diff   %+.3f", rho_part)
    log.info("")
    log.info("  linear fit   slope %+.3f  intercept %+.3f  RSS %.2f", slope, icept, rss_line)
    log.info("  step fit     threshold %.3f                RSS %.2f", thr, rss_step)

    log.info("")
    log.info("%-16s%8s%10s%10s", "stratum", "n", "median", "IQR")
    strat = {}
    for lo, hi, name in STRATA:
        v = sorted(r["coef"] for r in rows if lo <= r["ratio"] < hi)
        strat[name] = v
        if v:
            q = lambda p, v=v: v[min(len(v) - 1, int(p * len(v)))]  # noqa: E731
            log.info("%-16s%8d%10.3f%10.3f", name, len(v), st.median(v), q(.75) - q(.25))

    log.info("")
    log.info("PER SUBSET WITHIN STRATUM — does composition explain [E-038]'s 0.408 span?")
    log.info("%-16s%12s%12s%12s", "stratum", "popular", "random", "recent")
    conv, conv_pow = [], []
    for _lo, _hi, name in STRATA:
        cells = {}
        for sub in ("popular", "random", "recent"):
            v = [r["coef"] for r in rows
                 if r["subset"] == sub and _lo <= r["ratio"] < _hi]
            cells[sub] = (st.median(v), len(v)) if v else (float("nan"), 0)
        log.info("%-16s%12s%12s%12s", name,
                 *[f"{m:.3f} ({n})" if n else "—" for m, n in
                   (cells["popular"], cells["random"], cells["recent"])])
        have = [m for m, n in cells.values() if n >= 3]
        if len(have) > 1:
            conv.append(max(have) - min(have))
        # Reported alongside, not instead: the n>=3 cut above is what this ticket
        # pre-registered and it stands. It is also too low — a median of five points is
        # not a median — and that was my error in setting it, discovered after seeing the
        # table. The powered cut is therefore POST-HOC and labelled so wherever it is read.
        powered = [m for m, n in cells.values() if n >= POWERED_N]
        if len(powered) > 1:
            conv_pow.append((name, max(powered) - min(powered), len(powered)))

    log.info("")
    acro = [r["coef"] for r in rows if r["acronym"]]
    log.info("acronym-like aliases (confound 2): n=%d  median %s", len(acro),
             f"{st.median(acro):.3f}" if acro else "—")

    log.info("")
    graded = abs(rho) >= GRADED_RHO and rss_line < rss_step
    if abs(rho) < GRADED_RHO:
        log.warning("VERDICT: NEITHER — rho is %+.3f, below %.2f. The bucket contrast is "
                    "not driven by string distance and this ticket's premise is wrong.",
                    rho, GRADED_RHO)
    elif graded:
        log.info("VERDICT: GRADED — rho %+.3f and a line (RSS %.2f) beats the best step "
                 "(RSS %.2f at %.3f). Delivery is a continuous function of how far the "
                 "surface form moved, slope %+.3f.", rho, rss_line, rss_step, thr, slope)
    else:
        log.info("VERDICT: THRESHOLD — rho %+.3f but a step at %.3f (RSS %.2f) beats the "
                 "line (RSS %.2f). There is a similarity boundary, not a slope.",
                 rho, thr, rss_step, rss_line)

    if conv and max(conv) <= CONVERGE:
        log.info("SPLIT EXPLAINED — within strata the subsets agree to %.3f (<= %.2f). "
                 "[E-038]'s 0.408 span is COMPOSITION, not disagreement, and its "
                 "'magnitude not quotable' is lifted: the quotable quantity is the slope.",
                 max(conv), CONVERGE)
    elif conv:
        log.warning("SPLIT NOT EXPLAINED — subsets still differ by %.3f within strata. "
                    "Something beyond alias composition is doing the work and [E-038]'s "
                    "caution stands as written.", max(conv))
    else:
        log.warning("SPLIT UNTESTED — too few aliases per subset-stratum cell to compare.")

    log.info("")
    log.info("POST-HOC — the same comparison restricted to cells with n >= %d", POWERED_N)
    if conv_pow:
        for name, span, k in conv_pow:
            log.info("  %-16s span %.3f across %d subsets", name, span, k)
        worst = max(s for _, s, _ in conv_pow)
        log.info("  max span %.3f. The pre-registered n>=3 verdict above is driven by "
                 "`popular`, whose three cells hold 5, 5 and 9 aliases; it has 19 in "
                 "total and cannot be resolved either way. Where the data can carry the "
                 "question — `random` against `recent` — composition %s.", worst,
                 "explains the difference" if worst <= CONVERGE else "does not")
    else:
        log.info("  no stratum has two subsets with n >= %d. Only `random` is large "
                 "enough to stratify at all, so the subset question is UNANSWERABLE from "
                 "this data rather than answered negatively.", POWERED_N)

    out = ROOT / "results" / "E-040-alias-gradient.json"
    out.write_text(json.dumps({
        "ticket": "E-040", "n": len(rows), "rho": rho, "rho_token_diff": rho_dtok,
        "rho_partial": rho_part, "slope": slope, "intercept": icept,
        "rss_line": rss_line, "step_threshold": thr, "rss_step": rss_step,
        "strata": {k: v for k, v in strat.items()},
        "within_stratum_max_span": max(conv) if conv else None,
        "acronym_n": len(acro), "rows": rows}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
