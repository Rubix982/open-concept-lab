"""E-009: possession-gate the entailment chains.

A chain tests contraction only if the model holds all three of its facts:

    inner-1  X born-in Y      unheld -> nothing to retract
    inner-2  Y in country Z   unheld -> the entailment is not the model's
    outer    X born-in Z      unheld -> the edit is meaningless

Chains failing any leg are unusable. They are reported, never dropped silently —
that is the denominator bug E-007 shipped and had to fix.

Reuses `src/possession.py` untouched. Each fact becomes an `Edit` whose
`relation_id` is its POSITION in the chain, so the candidate pool for each position
is drawn from the right type automatically: birth cities for inner-1, countries for
inner-2 and the outer.

Candidate-set sizes differ by position (78 cities, 28 countries) and are reported,
because absolute levels move with that number — only ordering is robust [E-005].
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from possession import Edit, FilterConfig, ItemResult, run  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
CHAINS = ROOT / "probes" / "containment_chains.json"
OUT = ROOT / "probes" / "chains_gated.json"
POSITIONS = ("inner_1", "inner_2", "outer")


def chain_edits(chains: list[dict]) -> list[Edit]:
    """One Edit per fact; relation_id is the chain position, which types the pool."""
    out: list[Edit] = []
    for c in chains:
        for pos in POSITIONS:
            f = c[pos]
            out.append(Edit(
                case_id=f"{c['seed_case_id']}|{pos}",
                prompt=f["prompt"], subject=f["subject"],
                true_answer=f["answer"], relation_id=pos,
            ))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="EleutherAI/gpt-j-6b")
    ap.add_argument("--n-candidates", type=int, default=50)
    args = ap.parse_args()

    data = json.loads(CHAINS.read_text())
    chains = data["chains"]
    edits = chain_edits(chains)
    cfg = FilterConfig(model=args.model, backend="ndif",
                       n_candidates=args.n_candidates)

    print(f"{len(chains)} chains -> {len(edits)} facts to score "
          f"({args.model})\n", flush=True)

    from remote import connect, score_pairs  # noqa: E402
    model = connect(cfg.model)
    scorer = lambda pairs: score_pairs(model, pairs)  # noqa: E731

    cache = ROOT / "results" / "cache" / f"chains_{cfg.fingerprint.replace('|','_')}.json"
    report = run(edits, cfg, scorer, cache_path=cache, reference=edits,
                 progress=lambda i, n: print(f"  {i}/{n}", flush=True) if i % 25 == 0 else None)

    by_id: dict[str, ItemResult] = {r.case_id: r for r in report.results}
    pos_stats: dict[str, list[bool]] = defaultdict(list)
    cand_n: dict[str, int] = {}
    gated: list[dict[str, Any]] = []

    for c in chains:
        held = {}
        for pos in POSITIONS:
            r = by_id.get(f"{c['seed_case_id']}|{pos}")
            held[pos] = bool(r and r.held(require_lift=True))
            if r:
                pos_stats[pos].append(held[pos])
                cand_n[pos] = r.n_candidates
        c = {**c, "held": held, "usable": all(held.values())}
        gated.append(c)

    usable = [c for c in gated if c["usable"]]
    print(f"\n{'position':<10}{'n':>5}{'candidates':>12}{'held':>8}")
    for pos in POSITIONS:
        v = pos_stats[pos]
        if v:
            print(f"{pos:<10}{len(v):>5}{cand_n.get(pos,0):>12}{sum(v)/len(v):>7.0%}")

    print(f"\nUSABLE CHAINS (all three legs held): {len(usable)}/{len(chains)} "
          f"= {100*len(usable)/len(chains):.0f}%")

    fail = defaultdict(int)
    for c in gated:
        if not c["usable"]:
            missing = tuple(p for p in POSITIONS if not c["held"][p])
            fail[" + ".join(missing)] += 1
    print("\nwhich leg failed (for the unusable):")
    for k, n in sorted(fail.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {k}")

    if usable:
        print("\nusable examples:")
        for c in usable[:6]:
            print(f"  {c['entailment']}")

    OUT.write_text(json.dumps(
        {"model": cfg.model, "n_candidates_requested": cfg.n_candidates,
         "candidates_per_position": cand_n,
         "n_chains": len(chains), "n_usable": len(usable),
         "held_by_position": {p: (sum(v)/len(v) if v else None)
                              for p, v in pos_stats.items()},
         "chains": gated}, indent=1))
    print(f"\nwritten: probes/{OUT.name}")


if __name__ == "__main__":
    main()
