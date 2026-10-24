"""E-048 · Where does the replacement come from, if not the country?

[E-046] established where it does NOT come from: across the eleven countries that got
more than one subject, no two subjects ever landed on the same new top-1, so the
injected country supplies no content. The write-up has had no positive account since.

The available candidate is the subject's own prior. If the edit reshuffles within what
the model already associated with this person, the edited top-1 should already be sitting
in that person's base top-8.

**Zero remote calls.** [E-046] wrote top-8 tokens for both conditions on both probes;
this is a second reading of that file. [E-047]'s nnsight problem cannot block it.

The floor is the whole measurement. Common profession tokens (" writer", " musician")
sit in many people's top-8, so a bare match rate would be large whatever the edit did.
Every rate here is therefore stated against the **permuted** rate: the same question
asked of a DIFFERENT subject's base top-8, over all ordered pairs. That is the same
discipline as the 0.082/0.065 floors elsewhere in the project, and it is why a number
here is allowed to mean anything at all.

n=37 licenses an existence claim, never a rate [O-004]. The floor contrast is
within-sample; it is not an estimate of how often editing does this in general.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from logs import setup  # noqa: E402

TICKET = "E-048"
TOP_K = 8


def norm(tok: str) -> str:
    """Tokens carry a leading space and arbitrary case; compare on neither."""
    return tok.strip().lower()


def matched(edit_top1: str, base_tokens: list[str], k: int = TOP_K) -> int | None:
    """Rank (1-based) of the edited top-1 inside a base top-k, or None if absent."""
    want = norm(edit_top1)
    for i, t in enumerate(base_tokens[:k], 1):
        if norm(t) == want:
            return i
    return None


def permuted_floor(rows: list[dict], k: int = TOP_K) -> tuple[float, float, int]:
    """Rate, spread, and pair count for edited-top-1 against ANOTHER subject's base.

    All 37x36 ordered pairs, not a sample — the set is small enough that sampling
    would add a seed dependence for nothing. The spread is the standard deviation of
    the per-donor rates, which is what the verdict band compares the margin against:
    a margin inside the floor's own spread is not a result.
    """
    per_donor: list[float] = []
    total = hit = 0
    for i, a in enumerate(rows):
        hits = n = 0
        for j, b in enumerate(rows):
            if i == j:
                continue
            n += 1
            if matched(a["top1"]["edited"], b["topk"]["base"]["tokens"], k) is not None:
                hits += 1
        if n:
            per_donor.append(hits / n)
            total += n
            hit += hits
    spread = statistics.pstdev(per_donor) if len(per_donor) > 1 else 0.0
    return (hit / total if total else 0.0), spread, total


def analyse(rows: list[dict], k: int = TOP_K) -> dict:
    """One probe's numbers. Unchanged-top-1 subjects are held out, never counted in."""
    unchanged = [r for r in rows if norm(r["top1"]["base"]) == norm(r["top1"]["edited"])]
    changed = [r for r in rows if norm(r["top1"]["base"]) != norm(r["top1"]["edited"])]

    ranks = [matched(r["top1"]["edited"], r["topk"]["base"]["tokens"], k) for r in changed]
    hits = [x for x in ranks if x is not None]
    rate = len(hits) / len(changed) if changed else 0.0
    floor, spread, pairs = permuted_floor(changed, k) if changed else (0.0, 0.0, 0)

    return {
        "n": len(rows), "n_unchanged": len(unchanged), "n_changed": len(changed),
        "matched": len(hits), "rate": rate,
        "floor": floor, "floor_spread": spread, "floor_pairs": pairs,
        "margin": rate - floor,
        "rank_histogram": {str(i): ranks.count(i) for i in range(1, k + 1)},
        "median_rank": statistics.median(hits) if hits else None,
        "examples": [{"subject": r["subject"], "base_top1": r["top1"]["base"],
                      "edited_top1": r["top1"]["edited"], "rank_in_base": rk}
                     for r, rk in zip(changed, ranks)],
    }


def verdict(a: dict) -> tuple[str, str]:
    """Pre-stated bands, in the order the ticket states them. Separated so the dry-run
    can fire every branch without any data file existing."""
    if a["n_changed"] < 10:
        return ("NULL", f"only {a['n_changed']} of {a['n']} subjects changed their top-1 "
                        f"answer. Neither rate can be read at that count; nothing is claimed.")
    if a["margin"] > a["floor_spread"]:
        return ("CONFIRM-prior",
                f"the edited answer was already in the subject's OWN base top-{TOP_K} in "
                f"{a['matched']} of {a['n_changed']} ({a['rate']:.1%}), against a permuted "
                f"floor of {a['floor']:.1%} (spread {a['floor_spread']:.1%}) over "
                f"{a['floor_pairs']} pairs. The margin of {a['margin']:+.1%} clears the "
                f"floor's own spread, so the replacement is drawn from what the model "
                f"already associated with this person — a reshuffle inside an existing "
                f"bundle, which is neither damage nor revision about the country.")
    return ("DENY-prior",
            f"the edited answer was in the subject's own base top-{TOP_K} in "
            f"{a['matched']} of {a['n_changed']} ({a['rate']:.1%}), against a permuted "
            f"floor of {a['floor']:.1%} (spread {a['floor_spread']:.1%}) over "
            f"{a['floor_pairs']} pairs — a margin of {a['margin']:+.1%}, inside the "
            f"floor's own spread. The subject's prior predicts the replacement no better "
            f"than a stranger's does. The replacement comes from neither the injected "
            f"country [E-046] nor the subject's prior, and the displacement reading "
            f"survives an explanation that would have defused it.")


def report(data: dict, log, *, out: Path) -> dict:
    """Separated from the read so the dry-run exercises it on constructed rows."""
    summary: dict = {"ticket": TICKET, "top_k": TOP_K, "by_probe": {}}
    for probe, rows in data.items():
        a = analyse(rows)
        band, why = verdict(a)
        a["verdict"], a["verdict_text"] = band, why
        summary["by_probe"][probe] = a

        log.info("")
        log.info("%s  (n=%d)", probe.upper(), a["n"])
        log.info("  top-1 unchanged, held out        %d", a["n_unchanged"])
        log.info("  top-1 changed, scored            %d", a["n_changed"])
        log.info("  edited top-1 in OWN base top-%d   %d/%d = %.1f%%",
                 TOP_K, a["matched"], a["n_changed"], 100 * a["rate"])
        log.info("  same, against ANOTHER subject    %.1f%%  (spread %.1f%%, %d pairs)",
                 100 * a["floor"], 100 * a["floor_spread"], a["floor_pairs"])
        log.info("  margin                           %+.1f%%", 100 * a["margin"])
        log.info("  rank in base top-%d, where hit    %s  (median %s)",
                 TOP_K, a["rank_histogram"], a["median_rank"])
        log.info("  %s: %s", band, why)

    out.write_text(json.dumps(summary, indent=1))
    log.info("")
    log.info("written: %s", out)
    log.info("n=37 licenses an EXISTENCE claim, not a rate [O-004]. The floor contrast "
             "is within-sample and is not an estimate for editing in general.")
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=str(ROOT / "results" / "E-046-what-instead.json"))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        raise SystemExit(f"[E-046] artifact absent: {src} — run run_e046.py first")
    results = json.loads(src.read_text())["results"]

    data: dict[str, list[dict]] = {}
    for r in results:
        data.setdefault(r["probe"], []).append(r)

    # completeness, not existence: a short top-k silently shrinks both rate and floor
    short = [f"{r['subject']}|{r['probe']}|{c}" for r in results for c in ("base", "edited")
             if len(r["topk"][c]["tokens"]) < TOP_K]
    if short:
        raise SystemExit(f"{len(short)} records carry fewer than {TOP_K} tokens: {short[:3]}")

    log = setup("run_e048", config={
        "ticket": TICKET, "source": str(src), "top_k": TOP_K,
        "probes": sorted(data), "n_records": len(results),
        "measure": "is the edited top-1 already in the SAME subject's base top-k, "
                   "against an all-ordered-pairs permuted floor",
        "remote_calls": 0})
    log.info("%d records over %d probes, read from %s", len(results), len(data), src)

    out = Path(args.out) if args.out else ROOT / "results" / "E-048-where-from.json"
    report(data, log, out=out)


if __name__ == "__main__":
    main()
