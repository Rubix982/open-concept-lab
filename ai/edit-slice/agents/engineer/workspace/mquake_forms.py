"""Do MQuAKE's multi-hop questions name the edited subject? Counted, per hop position.

    .venv/bin/python agents/engineer/workspace/mquake_forms.py

Runs [R-014], which follows [E-037]'s §4.6 row: RippleEdits' different-entity tests sit at
a coefficient of 0.982 because their prompts name the edited subject verbatim. Whether that
is a fact about one benchmark or about how the field builds propagation tests is the whole
difference between a finding and a curiosity.

**No model, no edits, no entity resolution** — the same shape as [R-013], and for the same
reason: the released files carry the edited subject as a string in `requested_rewrite`, and
the question is whether that string appears in the test question. Presence is decidable;
everything else here would be inference.

**What this does NOT measure.** A subject present in a prompt is not a subject at the
position the coefficient is read. This counts construction, never delivery. Delivery needs
[E-036]'s measurement run per benchmark.
"""
from __future__ import annotations

import glob
import json
import os
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
DATA = os.path.join(ROOT, "data", "mquake")


def hop_of(entry: dict, subject: str) -> int | None:
    """Which hop of the chain the edited subject sits at, 1-indexed, or None.

    MQuAKE chains run 2-4 hops and only the FIRST entity is named in the question — an
    edit on hop 2 or 3 is about an intermediate entity the question never mentions. That
    is the structural reason an edit might not be named, and it is the thing worth
    counting, so it is read off `orig.triples_labeled` rather than guessed from position.
    """
    for i, t in enumerate(entry.get("orig", {}).get("triples_labeled") or [], start=1):
        if t and t[0] == subject:
            return i
    return None


def main() -> int:
    files = sorted(glob.glob(os.path.join(DATA, "*.json")))
    if not files:
        print("no MQuAKE files — run fetch_mquake.py first")
        return 1

    print(f"{'file':<24}{'questions':>11}{'names subj':>12}{'%':>8}{'hops':>7}")
    grand = Counter()
    by_hop: Counter = Counter()
    for f in files:
        name = os.path.basename(f).replace(".json", "")
        entries = json.load(open(f, encoding="utf-8"))
        per = Counter()
        hops = Counter()
        for e in entries:
            rw = e.get("requested_rewrite") or []
            subs = [r.get("subject") for r in rw if r.get("subject")]
            hops[len(e.get("orig", {}).get("triples_labeled") or [])] += 1
            for q in e.get("questions") or []:
                if not isinstance(q, str):
                    continue
                per["total"] += 1
                hit = [s for s in subs if s in q]
                if hit:
                    per["named"] += 1
                # Per-hop: only single-edit instances, where "which hop was edited" is
                # unambiguous. Multi-edit instances are counted in the totals and
                # excluded here rather than attributed to one hop.
                if len(subs) == 1:
                    h = hop_of(e, subs[0])
                    if h is not None:
                        by_hop[(h, bool(hit))] += 1
        grand["total"] += per["total"]
        grand["named"] += per["named"]
        span = f"{min(hops)}-{max(hops)}" if hops else "—"
        pct = 100 * per["named"] / per["total"] if per["total"] else 0.0
        print(f"{name:<24}{per['total']:>11,}{per['named']:>12,}{pct:>7.1f}%{span:>7}")

    pct = 100 * grand["named"] / grand["total"] if grand["total"] else 0.0
    print(f"\n{'ALL':<24}{grand['total']:>11,}{grand['named']:>12,}{pct:>7.1f}%")

    print("\nBy which hop of the chain carries the edit (single-edit instances only):")
    print(f"  {'hop':<6}{'questions':>11}{'names subj':>12}{'%':>8}")
    for h in sorted({k[0] for k in by_hop}):
        yes, no = by_hop[(h, True)], by_hop[(h, False)]
        tot = yes + no
        print(f"  {h:<6}{tot:>11,}{yes:>12,}{100 * yes / tot:>7.1f}%")

    out = os.path.join(ROOT, "results", "R-014-mquake-forms.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump({"finding": "R-014", "benchmark": "MQuAKE",
                   "files": [os.path.basename(f) for f in files],
                   "questions": grand["total"], "names_subject": grand["named"],
                   "by_hop": {f"{h}|{b}": v for (h, b), v in by_hop.items()}}, fh, indent=1)
    print(f"\n  written: {os.path.relpath(out, ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
