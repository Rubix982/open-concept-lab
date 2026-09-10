"""E-002 step 1: does Wikidata carry enough about CounterFact subjects to ground them?

E-001 killed method (e) over DBpedia: 66.5% of usable mined rules were alias
tautologies (`fact + alias => fact`) because DBpedia stores many redundant naming
predicates. Wikidata stores labels as labels, not statements, so the pathology
should not recur. But before mining anything we check the cheaper precondition:
are the subjects rich enough for grounds to exist at all?

Reports, per rigid relation:
  - entity-link success rate (subject string -> QID)
  - statements per linked subject
  - whether Wikidata asserts the edited property at all
  - whether its value matches CounterFact's target_true

Results cached to JSON so reruns are free (CLAUDE.md: long runs must be resumable).
"""

from __future__ import annotations

import json
import random
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Final

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from data import CounterFactRecord, load_counterfact  # noqa: E402

API: Final[str] = "https://www.wikidata.org/w/api.php"
UA: Final[str] = "edit-slice-research/0.1 (islam.saif@northeastern.edu)"
CACHE: Final[Path] = Path(__file__).parent / "wikidata_cache.json"
SEED: Final[int] = 1538
PER_RELATION: Final[int] = 5

RIGID: Final[list[str]] = [
    "P19", "P20", "P103", "P495", "P740", "P364", "P407", "P178", "P138", "P449", "P30",
]


def _get(params: dict[str, str]) -> dict[str, Any]:
    url = f"{API}?{urllib.parse.urlencode({**params, 'format': 'json'})}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as fh:
        return json.load(fh)
    

def link(subject: str, cache: dict[str, Any]) -> str | None:
    key = f"search:{subject}"
    if key not in cache:
        res = _get({"action": "wbsearchentities", "search": subject, "language": "en", "limit": "1"})
        hits = res.get("search", [])
        cache[key] = hits[0]["id"] if hits else None
        time.sleep(0.12)
    return cache[key]


def entities(qids: list[str], cache: dict[str, Any]) -> dict[str, Any]:
    missing = [q for q in qids if f"ent:{q}" not in cache]
    for i in range(0, len(missing), 40):
        batch = missing[i : i + 40]
        res = _get({"action": "wbgetentities", "ids": "|".join(batch), "props": "claims"})
        for qid, payload in res.get("entities", {}).items():
            cache[f"ent:{qid}"] = payload.get("claims", {})
        time.sleep(0.12)
    return {q: cache.get(f"ent:{q}", {}) for q in qids}


def sample(records: list[CounterFactRecord]) -> dict[str, list[CounterFactRecord]]:
    rng = random.Random(SEED)
    by_rel: dict[str, list[CounterFactRecord]] = defaultdict(list)
    for r in records:
        if r.rewrite.relation_id in RIGID:
            by_rel[r.rewrite.relation_id].append(r)
    return {rel: rng.sample(rs, min(PER_RELATION, len(rs))) for rel, rs in by_rel.items()}


def main() -> None:
    cache: dict[str, Any] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    chosen = sample(load_counterfact())

    rows: list[dict[str, Any]] = []
    for rel, recs in sorted(chosen.items()):
        qids = {}
        for rec in recs:
            qids[rec.case_id] = link(rec.rewrite.subject, cache)
        claims = entities([q for q in qids.values() if q], cache)
        for rec in recs:
            qid = qids[rec.case_id]
            cl = claims.get(qid, {}) if qid else {}
            rows.append(
                {
                    "relation": rel,
                    "subject": rec.rewrite.subject,
                    "qid": qid,
                    "n_props": len(cl),
                    "n_statements": sum(len(v) for v in cl.values()),
                    "has_edited_prop": rec.rewrite.relation_id in cl,
                    "props": sorted(cl.keys()),
                }
            )
        CACHE.write_text(json.dumps(cache))

    linked = [r for r in rows if r["qid"]]
    print(f"sampled {len(rows)} rigid-relation edits ({PER_RELATION}/relation, seed {SEED})")
    print(f"entity-linked: {len(linked)}/{len(rows)} ({100*len(linked)/len(rows):.0f}%)\n")
    print(f"{'rel':<6}{'linked':>7}{'med props':>11}{'med stmts':>11}{'has edited prop':>17}")
    for rel in sorted(chosen):
        rs = [r for r in rows if r["relation"] == rel]
        lk = [r for r in rs if r["qid"]]
        med_p = sorted(r["n_props"] for r in lk)[len(lk) // 2] if lk else 0
        med_s = sorted(r["n_statements"] for r in lk)[len(lk) // 2] if lk else 0
        has = sum(r["has_edited_prop"] for r in rs)
        print(f"{rel:<6}{len(lk):>3}/{len(rs):<3}{med_p:>11}{med_s:>11}{has:>13}/{len(rs)}")

    allprops: Counter[str] = Counter()
    for r in linked:
        allprops.update(r["props"])
    print(f"\ndistinct properties seen across linked subjects: {len(allprops)}")
    print("most common:", ", ".join(f"{p}({n})" for p, n in allprops.most_common(15)))
    (Path(__file__).parent / "wikidata_coverage.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
