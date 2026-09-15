"""T-061 · Is subject familiarity the variable behind the chain-leg dependence?

[E-009] measured that the three legs of a chain are not independent: the joint
usable rate is 3.27x what multiplying the marginals predicts at GPT-J and 1.25x at
70B, and the pair lift is ordered by whether the two legs share a subject. The
stated explanation was that possession clusters per entity — a chain about a
well-known person holds at every leg, one about an obscure person at none.

That is a story about a variable nobody measured. This measures it, using only the
Wikidata snapshot already on disk: prominence = the number of statements the subject
carries. If familiarity is the binding variable, then stratifying by it should
collapse the within-stratum lift toward 1 while the pooled lift stays high — the
signature of a common cause rather than a direct dependence.

No network, no NDIF.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from logs import setup  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


def prominence(snapshot: dict) -> dict[str, int]:
    """QID -> total statement count. A standard Wikidata prominence proxy.

    Statements, not distinct properties: an entity with 40 values under one property
    is better described than one with 40 properties holding one value each, and the
    quantity we want is how much the world has written down about this entity.
    """
    out: dict[str, int] = {}
    for qid, claims in snapshot["claims"].items():
        if isinstance(claims, dict):
            out[qid] = sum(len(v) if isinstance(v, list) else 1 for v in claims.values())
    return out


def lift(chains: list[dict], a: str, b: str) -> tuple[float, int]:
    """P(a and b) / (P(a) P(b)) — 1.0 is independence."""
    n = len(chains)
    if not n:
        return float("nan"), 0
    pa = sum(c["held"][a] for c in chains) / n
    pb = sum(c["held"][b] for c in chains) / n
    pab = sum(c["held"][a] and c["held"][b] for c in chains) / n
    return (pab / (pa * pb) if pa and pb else float("nan")), n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--snapshot", default="data/wikidata/2026-09-14/snapshot.json.gz")
    args = ap.parse_args()

    snap = json.loads(gzip.open(ROOT / args.snapshot).read())
    prom = prominence(snap)

    log = setup("familiarity", config={"thread": "T-061", "snapshot": args.snapshot,
                                       "entities_in_snapshot": len(prom)})

    for path, tag in (("chains_gated_EleutherAI_gpt-j-6b.json", "GPT-J-6B"),
                      ("chains_gated_meta-llama_Llama-3.1-70B.json", "Llama-3.1-70B")):
        gated = json.loads((ROOT / "probes" / path).read_text())
        chains = gated["chains"]

        scored, missing = [], 0
        for c in chains:
            qid = c["inner_1"].get("qid_subject")
            if qid in prom:
                scored.append({**c, "prom": prom[qid]})
            else:
                missing += 1

        log.info("=" * 62)
        log.info("%s — %d/%d chains have a prominence value (%d missing)",
                 tag, len(scored), len(chains), missing)
        if len(scored) < 30:
            log.error("too few chains with prominence to stratify — aborting for %s", tag)
            continue

        vals = sorted(c["prom"] for c in scored)
        log.info("subject statements: min %d  median %d  max %d",
                 vals[0], statistics.median(vals), vals[-1])

        pooled, n = lift(scored, "inner_1", "outer")
        log.info("POOLED  inner_1 & outer lift = %.2f  (n=%d)", pooled, n)

        # Terciles of prominence. If familiarity is the common cause, within-stratum
        # lift falls toward 1 while the pooled figure stays high.
        cut = [vals[len(vals) // 3], vals[2 * len(vals) // 3]]
        strata = {"low": [], "mid": [], "high": []}
        for c in scored:
            k = "low" if c["prom"] <= cut[0] else "mid" if c["prom"] <= cut[1] else "high"
            strata[k].append(c)

        log.info("%-8s%6s%10s%10s%10s%9s", "stratum", "n", "inner_1", "outer", "both", "lift")
        weighted, total = 0.0, 0
        for k in ("low", "mid", "high"):
            s = strata[k]
            lv, sn = lift(s, "inner_1", "outer")
            if sn:
                log.info("%-8s%6d%9.0f%%%9.0f%%%9.0f%%%9.2f", k, sn,
                         100 * sum(c["held"]["inner_1"] for c in s) / sn,
                         100 * sum(c["held"]["outer"] for c in s) / sn,
                         100 * sum(c["held"]["inner_1"] and c["held"]["outer"]
                                   for c in s) / sn,
                         lv)
                if lv == lv:            # not NaN
                    weighted += lv * sn
                    total += sn
        if total:
            log.info("within-stratum mean lift = %.2f   vs pooled %.2f",
                     weighted / total, pooled)


if __name__ == "__main__":
    main()
