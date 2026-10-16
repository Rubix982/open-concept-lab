"""E-035 · What sets how far an edit travels? A pre-registered elimination. [T-086]

[T-086] is the one question nothing in this record predicts. [E-029] measured belief
displacement and ROME's efficacy margin against propagation at Spearman 0.419 and 0.425 —
about 18% of variance, and near-identical to each other, so one weak view rather than two.
The coefficient cannot help BY CONSTRUCTION: it is pinned at exactly 1.000 across precisely
the probes whose outcomes differ most, so it has zero variance where the outcome varies.
[R-012] withdrew the only candidate on the table.

**This ticket does not invent a candidate. It eliminates seven**, six of them from data
already on disk, against the same 42 subjects [E-029] used — so the incumbent is measured
on exactly the same people.

    1 ||dv||                     a bigger update should move more
    2 ||k*||                     the key's magnitude scales the delivered vector
    3 ||dv||/||k*||              [E-028c] reported this per arm, never per subject
    4 baseline log P(true)       a confident belief may resist, or have further to fall
    5 target prior log P(target) an edit toward a likely answer may travel cheaply
    6 subject token count        longer names spread the key over more positions
    7 residual norm at subject   the delta competes with what is already there (needs the
                                 network: one batched trace, 42 prompts)

NOTHING BEATS IT is the outcome to expect and the useful one: it would say propagation
magnitude is set by none of update size, key size, their ratio, the belief's strength, the
target's prior, the subject's length, or the local residual norm. That is a sharper [T-086]
than the thread currently has.

CORRELATIONAL. A FOUND result licenses a follow-up design, never a claim.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import LAYER, subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
SEED = 1538
INCUMBENT = 0.425          # [E-029]'s ES margin, the quantity to beat
FOUND_RHO, FOUND_MARGIN, FLOOR_RHO, COLLINEAR = 0.60, 0.15, 0.50, 0.80
ALPHA = 0.05
#: Candidates 1-3 are algebraically related — the ratio is a function of the other two, so
#: it is never counted as a third independent hit. Confound 3.
MAGNITUDE_GROUP = ("norm_delta_v", "norm_k_star", "ratio_dv_over_k")


def spearman(xs: list[float], ys: list[float]) -> float:
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


def p_two_sided(rho: float, n: int) -> float:
    """Fisher z on the Spearman coefficient, with the standard 1.06 variance inflation.

    scipy is not a dependency here and the exact permutation distribution is overkill at
    n=42; the z approximation is the textbook choice for Spearman and is stated rather
    than hidden so a reader can judge it. It is slightly conservative at this n.
    """
    if not -1 < rho < 1 or n < 5:
        return float("nan")
    z = math.atanh(rho) * math.sqrt((n - 3) / 1.06)
    return math.erfc(abs(z) / math.sqrt(2))


def holm(ps: dict[str, float], alpha: float = ALPHA) -> dict[str, float]:
    """Holm-Bonferroni: the threshold each p must clear, in ascending order of p.

    Confound 1. Seven tests on 42 subjects: one test at rho=0.50 is around p=0.001, and
    seven of them are not. Any candidate clearing only the unadjusted bar has not cleared
    it, and the table prints both so that is visible rather than asserted.
    """
    order = sorted(ps, key=lambda k: ps[k])
    m = len(order)
    return {k: alpha / (m - i) for i, k in enumerate(order)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--no-remote", action="store_true",
                    help="skip candidate 7, which is the only one needing the network")
    a = ap.parse_args()

    b = json.loads((ROOT / "results" / "E-026b-edit-prompt.json").read_text())
    d = json.loads((ROOT / "results" / "E-026-depth.json").read_text())
    e29 = json.loads((ROOT / "results" / "E-029-es-vs-propagation.json").read_text())
    deltas = torch.load(ROOT / "results" / "cache" / f"E014_deltas_L{LAYER}_s{SEED}.pt")
    kstars = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s{SEED}.pt")
    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}

    # Rebuilt exactly as run_e029.py built it, so the incumbent and every candidate are
    # measured on the same subjects in the same order. [E-029] stored four 42-length
    # arrays and no ids; the order is recoverable only because this filter is recoverable.
    by_cid = {r["case_id"]: r for r in d["results"]}
    ids = [c for c in b["case_ids"] if c in by_cid]
    idx = {c: i for i, c in enumerate(b["case_ids"])}
    raw = b["raw"]

    # Completeness, stated rather than implied. The per-subject `continue` below is a
    # presence test and the [E-029] cross-check would catch a bad join afterwards — but
    # "it would have been caught downstream" is how [E-033] scored 29 subjects against 9
    # cached deltas. What is missing is named here, before anything is correlated.
    want = {f"{c}|real" for c in ids}
    missing_d, missing_k = want - set(deltas), want - set(kstars)
    no_chain = {c for c in ids if c not in chains}
    if missing_d or missing_k or no_chain:
        log_pre = f"{len(missing_d)} deltas, {len(missing_k)} kstars, {len(no_chain)} chains"
        print(f"  attrition before scoring: {log_pre}")
    rows = []
    for cid in ids:
        key = f"{cid}|real"
        if key not in deltas or key not in kstars or cid not in chains:
            continue
        i = idx[cid]
        s = by_cid[cid]["scores"]
        dv, ks = deltas[key].float(), kstars[key].float()
        rows.append({
            "case_id": cid,
            "subject": chains[cid]["inner_1"]["subject"],
            "propagation": (s["base"]["self|initial"] - s[f"L{LAYER}"]["self|initial"])
                           - (s["base"]["control|initial"] - s[f"L{LAYER}"]["control|initial"]),
            "es_margin": raw[f"L{LAYER}"]["target"][i] - raw[f"L{LAYER}"]["true"][i],
            "displacement": raw["base"]["true"][i] - raw[f"L{LAYER}"]["true"][i],
            "norm_delta_v": float(dv.norm()),
            "norm_k_star": float(ks.norm()),
            "ratio_dv_over_k": float(dv.norm() / ks.norm()),
            "baseline_true": raw["base"]["true"][i],
            "target_prior": raw["base"]["target"][i],
        })

    log = setup("run_e035", config={
        "ticket": "E-035", "thread": "T-086", "layer": LAYER, "model": MODEL,
        "n": len(rows), "incumbent_rho": INCUMBENT, "alpha": ALPHA,
        "outcome": "control-differenced drop on the subject-initial city probe, as [E-029]",
        "nature": "CORRELATIONAL — a FOUND result licenses a design, never a claim"})
    log.info("%d subjects joined across E-026b, E-026-depth and the L%d caches",
             len(rows), LAYER)
    log.info("attrition: %d of %d candidate ids lacked a cached delta, %d lacked a kstar, "
             "%d lacked a chain record", len(missing_d), len(ids), len(missing_k),
             len(no_chain))

    # Cross-check: the rebuilt outcome must reproduce [E-029]'s stored array, or the
    # subject order is wrong and every rho below is meaningless.
    stored = e29["per_subject"]["propagation"]
    mine = [r["propagation"] for r in rows]
    if len(stored) == len(mine):
        drift = max(abs(x - y) for x, y in zip(stored, mine))
        log.info("outcome reproduces [E-029]'s array to %.2e", drift)
        if drift > 1e-6:
            log.error("the rebuilt outcome does not match [E-029]'s. The subject order is "
                      "wrong and no correlation below can be trusted.")
            raise SystemExit(1)
    else:
        log.warning("[E-029] stored %d outcomes, this run joined %d — not comparable",
                    len(stored), len(mine))

    if not a.no_remote:
        rows = add_residual_norm(rows, log)

    report(rows, log)


def add_residual_norm(rows: list[dict], log) -> list[dict]:
    """Candidate 7 — the only one needing the network. One batched trace, 42 prompts."""
    m = connect(MODEL)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    prompts = [f"{r['subject']} was born in the country of" for r in rows]
    ids = [tok(p).input_ids for p in prompts]
    width = max(len(x) for x in ids)
    batch = torch.full((len(ids), width), pad, dtype=torch.long)
    for j, x in enumerate(ids):
        batch[j, : len(x)] = torch.tensor(x)

    def once(bt=batch):
        with _quiet_stdout(), m.trace(bt, remote=True):
            # `.output` is already [batch, seq, hidden] — see `src/edit.py`, which indexes
            # `down_proj.output[0, idx]` as [batch, position]. The first version wrote
            # `.output[0]`, which sliced the BATCH away and left [seq, hidden]. It crashed
            # only because 42 subjects exceeded a 15-token sequence; with a longer prompt
            # than batch it would have returned one subject's activations for all of them,
            # silently. Hence the assertion below rather than trust.
            h = m.model.layers[LAYER].output.half().save()
        with _quiet_stdout():
            return h.float()

    h = retrying(once, what="E-035 residual norms")
    if h.ndim != 3 or h.shape[0] != len(rows):
        raise SystemExit(f"residual read has shape {tuple(h.shape)}; expected "
                         f"({len(rows)}, seq, hidden). Refusing to index it.")
    for j, r in enumerate(rows):
        p = prompts[j]
        try:
            k = subject_last_index(tok, p, r["subject"])
        except ValueError:
            r["residual_norm"] = float("nan")
            continue
        r["residual_norm"] = float(h[j, k].norm())
    ok = sum(1 for r in rows if r.get("residual_norm") == r.get("residual_norm"))
    log.info("candidate 7: residual norm read at the subject position for %d/%d", ok,
             len(rows))
    return rows


def report(rows: list[dict], log, out: object = None) -> None:
    # `out` exists so a dry-run can redirect this file. Without it the dry-run wrote
    # FAKE results to the real path — worse than the deletion bug it replaced.
    n = len(rows)
    y = [r["propagation"] for r in rows]
    cands = [k for k in ("norm_delta_v", "norm_k_star", "ratio_dv_over_k", "baseline_true",
                         "target_prior", "subject_tokens", "residual_norm")
             if any(k in r for r in rows)]
    # candidate 6 is derived here so the tokenizer is not a dependency of the offline path
    if "subject_tokens" not in rows[0]:
        for r in rows:
            r["subject_tokens"] = len(r["subject"].split())
        cands.insert(5, "subject_tokens")

    usable = {}
    for c in cands:
        xs = [r.get(c) for r in rows]
        if any(x is None or x != x for x in xs):
            log.warning("candidate %s has missing values and is not scored", c)
            continue
        usable[c] = spearman(xs, y)

    ps = {c: p_two_sided(r, n) for c, r in usable.items()}
    thr = holm(ps)
    inc = [r["es_margin"] for r in rows]

    # Confound 2 — the outcome has its own spread, so there is a ceiling on any
    # achievable rho and it is not 1.0. Printed before the table, not after.
    log.info("")
    log.info("E-035 — seven candidates against propagation, n=%d, layer %d", n, LAYER)
    log.info("outcome spread: median %.2f, IQR %.2f, sd %.2f — a modest rho must be read "
             "against what is reachable, not against 1.0",
             st.median(y), (sorted(y)[3 * n // 4] - sorted(y)[n // 4]), st.pstdev(y))
    log.info("")
    log.info("%-20s%9s%11s%11s%8s%12s", "candidate", "rho", "p", "Holm thr", "clears",
             "rho w/ ES")
    for c in sorted(usable, key=lambda k: -abs(usable[k])):
        clears = ps[c] <= thr[c]
        log.info("%-20s%+9.3f%11.2e%11.2e%8s%+12.3f", c, usable[c], ps[c], thr[c],
                 "yes" if clears else "no", spearman([r[c] for r in rows], inc))
    log.info("%-20s%+9.3f%11s%11s%8s%12s", "es_margin (incumbent)", INCUMBENT, "—", "—",
             "—", "1.000")

    strong = {c: r for c, r in usable.items()
              if abs(r) > FLOOR_RHO and ps[c] <= thr[c]}
    # Confound 3: the magnitude trio is one quantity, so it counts once.
    distinct = {c for c in strong if c not in MAGNITUDE_GROUP}
    if any(c in MAGNITUDE_GROUP for c in strong):
        distinct.add("magnitude-group")

    best = max(usable, key=lambda k: abs(usable[k])) if usable else None
    log.info("")
    if not strong:
        log.warning("VERDICT: NOTHING BEATS IT — no candidate clears rho %.2f at its Holm "
                    "threshold. Propagation magnitude is set by none of update size, key "
                    "size, their ratio, the belief's strength, the target's prior, the "
                    "subject's length, or the local residual norm. The best was %s at "
                    "%+.3f against the incumbent's %.3f. That is a sharper [T-086] than "
                    "the thread had.", FLOOR_RHO, best, usable[best], INCUMBENT)
    elif len(distinct) > 1 and all(
            abs(spearman([r[x] for r in rows], [r[z] for r in rows])) > COLLINEAR
            for x in strong for z in strong if x != z):
        log.warning("VERDICT: MULTICOLLINEAR — %s all clear, and every pair correlates "
                    "above %.2f. They are one quantity wearing several names; the entry "
                    "must say which rather than report a winner.", sorted(strong), COLLINEAR)
    elif any(abs(r) >= FOUND_RHO and abs(r) - INCUMBENT >= FOUND_MARGIN
             for r in strong.values()):
        win = max(strong, key=lambda k: abs(strong[k]))
        log.info("VERDICT: FOUND — %s reaches rho %+.3f, clearing %.2f and beating the "
                 "incumbent %.3f by %.3f. [T-086] has its first real candidate. This is "
                 "CORRELATIONAL: the follow-up designs the causal test, and no claim is "
                 "licensed until it runs.", win, strong[win], FOUND_RHO, INCUMBENT,
                 abs(strong[win]) - INCUMBENT)
    else:
        log.info("VERDICT: BETWEEN — %s clear the floor but none reaches %.2f with a "
                 "%.2f margin over the incumbent. Report the table; claim no candidate.",
                 sorted(strong), FOUND_RHO, FOUND_MARGIN)

    out = out or ROOT / "results" / "E-035-propagation-candidates.json"
    out.write_text(json.dumps({"ticket": "E-035", "thread": "T-086", "n": n,
                               "layer": LAYER, "incumbent_rho": INCUMBENT,
                               "spearman": usable, "p": ps, "holm_threshold": thr,
                               "outcome_sd": st.pstdev(y), "rows": rows}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
