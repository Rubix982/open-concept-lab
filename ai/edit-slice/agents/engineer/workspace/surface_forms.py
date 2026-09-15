"""E-011 · Does the `outer` possession deficit come from answer surface form?

[E-009b] found the deficit is two strings — United States 6/40 held, United Kingdom
2/14, against France 13/13 and India 5/5. The hypothesis is that we score a Wikidata
*label* rather than a natural continuation: `"X was born in the country of"` followed
by `" United States"` is ungrammatical where `" France"` is fine.

This re-runs the same 136 `outer` items, same model, same seed, same 28-country pool,
changing exactly one thing: how every candidate in the pool is rendered. Rendering is
applied to the WHOLE pool and never to the true answer alone — scoring
`" the United States"` against bare-form distractors would advantage it for a reason
unrelated to the hypothesis.

    python agents/engineer/workspace/surface_forms.py --model meta-llama/Llama-3.1-70B
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402
from possession import Edit, FilterConfig, ItemResult, run  # noqa: E402
from remote import DEFAULT_MODEL, connect, score_pairs  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CHAINS = ROOT / "probes" / "containment_chains.json"

#: Wikidata label -> the form a sentence actually uses. Only entries that DIFFER are
#: listed; every other country is byte-identical across conditions, which is what
#: isolates the contrast to these five.
NATURAL: dict[str, str] = {
    "United States": "the United States",
    "United Kingdom": "the United Kingdom",
    "Netherlands": "the Netherlands",
    "Philippines": "the Philippines",
    "Czech Republic": "the Czech Republic",
    "People's Republic of China": "China",
}

#: The classes the result is read by. Membership is a property of the label, decided
#: before any scores were seen, so it cannot be tuned to the outcome.
ARTICLE_TAKING = frozenset(NATURAL)


def outer_edits(chains: list[dict], render: dict[str, str]) -> list[Edit]:
    """One Edit per chain's outer fact, answers rendered under `render`.

    `candidate_pool` derives the pool from the edits' `true_answer`, so renaming
    every answer renames the whole pool with no change to possession.py.
    """
    return [Edit(case_id=f"{c['seed_case_id']}|outer",
                 prompt=c["outer"]["prompt"],
                 subject=c["outer"]["subject"],
                 true_answer=render.get(c["outer"]["answer"], c["outer"]["answer"]),
                 relation_id="outer")
            for c in chains]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--n-candidates", type=int, default=50)
    ap.add_argument("--seed", type=int, default=1538)
    args = ap.parse_args()

    chains = json.loads(CHAINS.read_text())["chains"]
    cfg = FilterConfig(model=args.model, n_candidates=args.n_candidates, seed=args.seed)

    log = setup("surface_forms", config={
        "ticket": "E-011", "model": args.model, "n_candidates": args.n_candidates,
        "seed": args.seed, "n_items": len(chains),
        "conditions": ["bare", "natural"], "renamed": NATURAL})
    log.info("E-011: %d outer items, two renderings of the same 28-country pool",
             len(chains))

    model = connect(args.model)
    scorer = lambda pairs: score_pairs(model, pairs)  # noqa: E731

    reports: dict[str, list[ItemResult]] = {}
    for cond, render in (("bare", {}), ("natural", NATURAL)):
        edits = outer_edits(chains, render)
        # A SEPARATE cache file per condition. The fingerprint is model|n|seed|
        # placeholder — identical across conditions — so a shared file would serve
        # `bare` results to the `natural` run and silently fake a null result.
        cache = ROOT / "results" / "cache" / f"E011_{cond}_{cfg.fingerprint.replace('|','_')}.json"
        log.info("condition %s: scoring %d items", cond, len(edits))
        rep = run(edits, cfg, scorer, cache_path=cache, reference=edits,
                  progress=lambda i, n: log.info("  %s %d/%d", cond, i, n)
                  if i % 25 == 0 else None)
        reports[cond] = rep.kept
        log.info("condition %s: held %.0f%% over %d scored",
                 cond, 100 * rep.held_rate, len(rep.kept))

    # --- the deliverable: held rate by condition x answer-string class -----------
    truth = {f"{c['seed_case_id']}|outer": c["outer"]["answer"] for c in chains}
    table: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for cond, kept in reports.items():
        for r in kept:
            cls = "article-taking" if truth[r.case_id] in ARTICLE_TAKING else "bare-name"
            table[(cond, cls)][0] += r.held()
            table[(cond, cls)][1] += 1

    log.info("%-10s%-16s%8s%8s", "condition", "answer class", "n", "held")
    for cond in ("bare", "natural"):
        for cls in ("article-taking", "bare-name"):
            h, n = table[(cond, cls)]
            if n:
                log.info("%-10s%-16s%8d%7.0f%%", cond, cls, n, 100 * h / n)

    # usable chains, recomputed with the better outer condition
    gated = json.loads((ROOT / "probes" /
                        f"chains_gated_{args.model.replace('/','_')}.json").read_text())
    inner = {c["seed_case_id"]: (c["held"]["inner_1"] and c["held"]["inner_2"])
             for c in gated["chains"]}
    for cond, kept in reports.items():
        usable = sum(1 for r in kept
                     if r.held() and inner.get(r.case_id.split("|")[0], False))
        log.info("usable chains under %-8s %3d/%d = %.0f%%",
                 cond, usable, len(chains), 100 * usable / len(chains))

    out = ROOT / "results" / f"E-011-surface-forms-{args.model.replace('/','_')}.json"
    out.write_text(json.dumps({
        "ticket": "E-011", "config": cfg.as_dict(), "renamed": NATURAL,
        "by_class": {f"{c}|{k}": {"held": v[0], "n": v[1]}
                     for (c, k), v in table.items()},
        "per_item": {cond: [{"case_id": r.case_id, "answer": truth[r.case_id],
                             "rank_subject": r.rank_subject,
                             "rank_prior": r.rank_prior, "held": r.held()}
                            for r in kept]
                     for cond, kept in reports.items()},
    }, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
