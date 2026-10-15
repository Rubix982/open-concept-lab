"""E-045 · Does the model hold typeshed signature facts as densely as CounterFact ones? [T-098]

The gate on claim 3. [T-099] settled what a decidable oracle buys — [T-058] built genuinely
deductive grounds and [E-015] found the editor indifferent, so a formal domain does not make
editing cleaner, it makes the AUDIT decidable. Worth having, and it is claim 2.

The precondition has never been checked. Declaration 1 binds a fact to its probe set, and
[E-005] measured possession at 56/74/79/85% at 6B/8B/70B/405B for CounterFact claims. An
INVENTED notation would have possession near zero — a synthetic formal corpus would install
strings rather than edit beliefs. Typeshed escapes that: the model has seen `os.path.join`
ten thousand times and the stub is machine-checkable ground truth.

Facts are machine-derived from `python/typeshed@main` by `ast`, not hand-picked — the §5
circularity objection applies to hand-built sets and this one is built by rule.

N = 50, exactly [E-005]'s, because `possession.py`'s own docstring warns absolute levels
depend on N and a comparison at a different N would be worthless.

POSSESSION IS NOT EDITABILITY. This gates a direction and licenses nothing about whether
code facts edit cleanly.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from possession import Edit, FilterConfig, run  # noqa: E402
from remote import connect, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
E005_COUNTERFACT_8B = 0.74
HELD, THIN = 0.60, 0.30


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-facts", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1538)
    a = ap.parse_args()

    src = ROOT / "probes" / "typeshed_return_types.jsonl"
    allf = [json.loads(x) for x in src.read_text().splitlines() if x.strip()]
    rng = random.Random(a.seed)
    picked = sorted(rng.sample(allf, min(a.n_facts, len(allf))),
                    key=lambda r: r["case_id"])
    edits = [Edit(case_id=r["case_id"], prompt=r["prompt"], subject=r["subject"],
                  true_answer=r["true_answer"], relation_id=r["relation_id"])
             for r in picked]
    # The candidate vocabulary comes from the FULL set, not the sample — `run` draws
    # candidates from `reference`, and sampling the vocabulary too would quietly shrink N.
    reference = [Edit(case_id=r["case_id"], prompt=r["prompt"], subject=r["subject"],
                      true_answer=r["true_answer"], relation_id=r["relation_id"])
                 for r in allf]

    log = setup("run_e045", config={
        "ticket": "E-045", "thread": "T-098", "model": MODEL, "n_facts": len(edits),
        "n_candidates": 50, "seed": a.seed, "source": src.name,
        "comparator": f"[E-005] CounterFact at 8B, N=50: {E005_COUNTERFACT_8B}",
        "limit": "POSSESSION, not editability"})
    log.info("%d typeshed facts sampled from %d, candidate vocabulary from all %d",
             len(edits), len(allf), len(reference))

    m = connect(MODEL)
    cfg = FilterConfig(model=MODEL, n_candidates=50, seed=a.seed)
    cache = ROOT / "results" / "cache" / \
        f"E045_{cfg.fingerprint.replace('|', '_')}_n{len(edits)}.json"
    rep = run(edits, cfg, lambda p: score_pairs(m, p), cache_path=cache,
              reference=reference,
              progress=lambda i, n: log.info("  %d/%d", i, n) if i % 25 == 0 else None)

    report(rep, picked, log, a)


def report(rep, picked, log, a) -> None:
    # Field names read from the dataclass, not assumed. A first draft of this function
    # used `rep.items`, `.held` as an attribute and `.rank` — none of which exist — and
    # would have produced a plausible rate from `getattr(..., default)` rather than an
    # error. `LOOP.md` rule 4's family, in the reporting path rather than the trace.
    items = rep.results
    if not items:
        log.error("the filter returned no item results — nothing to report")
        return
    truth = {r["case_id"]: r["true_answer"] for r in picked}

    p_held = rep.held_rate                       # rank_subject == 1 AND lift > 0
    p_rank1 = sum(i.held(require_lift=False) for i in items) / len(items)
    p_prior = rep.prior_rate                     # what the template alone gets

    log.info("")
    log.info("E-045 — possession on typeshed return-type facts, N=50, %s", MODEL)
    log.info("coverage %.1f%%, %d item(s) unscoreable and kept in view",
             100 * rep.coverage, len(rep.skipped))
    log.info("")
    log.info("  possession (rank-1 AND lift > 0)   %.1f%%   (%d/%d)",
             100 * p_held, round(p_held * len(items)), len(items))
    log.info("  rank-1 only, no lift requirement   %.1f%%                <- confound 1",
             100 * p_rank1)
    log.info("  the template ALONE, no subject     %.1f%%                <- the baseline",
             100 * p_prior)
    log.info("  [E-005] CounterFact at 8B, N=50    %.1f%%", 100 * E005_COUNTERFACT_8B)
    log.info("")
    log.info("the gap between rows 1 and 2 is what the subject-free arm removes: items "
             "ranked first on type frequency rather than on knowing the function. Row 3 "
             "is what a model scores knowing nothing about which function was named.")

    # Confound 2 — by answer type, so a null can be told from a phrasing failure.
    by: dict[str, list] = defaultdict(list)
    for i in items:
        by[truth.get(i.case_id, "?")].append(i.held(require_lift=True))
    log.info("")
    log.info("%-22s%8s%10s", "answer type", "n", "held")
    for t, v in sorted(by.items(), key=lambda kv: -len(kv[1]))[:12]:
        if len(v) >= 4:
            log.info("%-22s%8d%9.0f%%", t, len(v), 100 * sum(v) / len(v))
    spread = [sum(v) / len(v) for v in by.values() if len(v) >= 8]

    log.info("")
    if p_held >= HELD:
        log.info("VERDICT: HELD — %.1f%% against [E-005]'s %.0f%% for CounterFact at the "
                 "same model and the same N. The model holds stub-level signature facts "
                 "about as densely as encyclopaedic ones, and claim 3 is executable with "
                 "the instrument already built.", 100 * p_held, 100 * E005_COUNTERFACT_8B)
    elif p_held <= THIN:
        log.warning("VERDICT: THIN — %.1f%% against [E-005]'s %.0f%%. The model does not "
                    "hold these densely enough to edit them, so a formal-domain audit "
                    "would measure facts it never had. Claim 3 needs a different fact "
                    "type. NOTE confound 2: if no answer type holds, the prompt phrasing "
                    "is a live alternative to ignorance and this verdict cannot separate "
                    "them.", 100 * p_held, 100 * E005_COUNTERFACT_8B)
    else:
        log.info("VERDICT: BETWEEN — %.1f%%, between the pre-stated %.0f%% and %.0f%%. The "
                 "question becomes WHICH code facts hold: per-type spread is %.0f points "
                 "across types with n>=8.", 100 * p_held, 100 * THIN, 100 * HELD,
                 100 * (max(spread) - min(spread)) if len(spread) > 1 else 0.0)

    out = ROOT / "results" / "E-045-typeshed-possession.json"
    out.write_text(json.dumps({
        "ticket": "E-045", "thread": "T-098", "model": MODEL, "n": len(items),
        "n_candidates": 50, "seed": a.seed,
        "possession": p_held, "rank1_only": p_rank1, "prior_rate": p_prior,
        "coverage": rep.coverage, "skipped": len(rep.skipped),
        "e005_counterfact_8b": E005_COUNTERFACT_8B,
        "by_answer_type": {t: {"n": len(v), "held": sum(v)} for t, v in by.items()}},
        indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
