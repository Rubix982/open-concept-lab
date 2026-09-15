"""Verify the E-012 measure on cases whose answer is known by construction.

Written before the measure touched real data. The E-011 analysis shipped three bugs,
one of which (`FilterReport.kept()` returns only HELD items) would have printed 100%
in every cell rather than crashing — a wrong answer that agrees with you is the
expensive kind.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from discrimination import discriminate, held, summarise  # noqa: E402
from possession import ItemResult  # noqa: E402

POOL = ["US", "France", "Japan", "Chile"]


def item(cid: str, answer: str, scores: dict[str, float]) -> ItemResult:
    cands = list(POOL)
    vec = [scores[c] for c in cands]
    rank = sorted(cands, key=lambda c: -scores[c]).index(answer) + 1
    return ItemResult(case_id=cid, relation_id="outer", subject=f"s{cid}",
                      true_answer=answer, rank_subject=rank, rank_prior=99,
                      n_candidates=len(cands), candidates=cands, scores_subject=vec)


def check(label: str, got, want) -> None:
    ok = "PASS" if got == want else "FAIL"
    print(f"  [{ok}] {label}: got {got!r}, want {want!r}")
    assert got == want, label


print("1 · perfect discriminator — each answer peaks under its own subject")
# 12 items, 3 per answer; the true answer scores 1.0 at home and 0.0 elsewhere.
items = []
for i, a in enumerate(POOL * 3):
    items.append(item(f"c{i}", a, {c: (1.0 if c == a else 0.0) for c in POOL}))
d = {x.case_id: x for x in discriminate(items, min_foils=3)}
check("every AUC is 1.0", {round(x.auc, 3) for x in d.values()}, {1.0})
check("held", all(held(it, d[it.case_id], min_auc=0.8) for it in items), True)

print("\n2 · modal answer, no discrimination — identical score everywhere")
# 'US' scores 5.0 under EVERY prompt: it ranks first every time (row test passes)
# but carries no information about which subject. This is exactly the E-011 case.
items = []
for i, a in enumerate(["US"] * 6 + ["France", "Japan", "Chile"] * 2):
    sc = {c: 0.0 for c in POOL}
    sc["US"] = 5.0
    sc[a] = 5.0 if a == "US" else 1.0
    items.append(item(f"m{i}", a, sc))
d = {x.case_id: x for x in discriminate(items, min_foils=3)}
us = [x for x in d.values() if x.true_answer == "US"]
check("US items rank first under the ROW test",
      all(it.rank_subject == 1 for it in items if it.true_answer == "US"), True)
check("US AUC is chance (all ties)", {round(x.auc, 3) for x in us}, {0.5})
check("US is not held at min_auc=0.8",
      any(held(it, d[it.case_id], min_auc=0.8) for it in items
          if it.true_answer == "US"), False)

print("\n3 · anti-discriminator — the answer peaks under the WRONG subjects")
items = [item("a0", "France", {"US": 0.0, "France": 0.0, "Japan": 9.0, "Chile": 9.0})]
items += [item(f"a{i}", "Japan", {"US": 0.0, "France": 9.0, "Japan": 9.0, "Chile": 0.0})
          for i in range(1, 6)]
d = {x.case_id: x for x in discriminate(items, min_foils=3)}
check("AUC below chance for the anti-case", d["a0"].auc < 0.5, True)

print("\n4 · thin foil coverage is UNMEASURED, never unpossessed")
items = [item(f"t{i}", "US", {c: 1.0 for c in POOL}) for i in range(3)]
items += [item("t9", "France", {c: 1.0 for c in POOL})]
d = {x.case_id: x for x in discriminate(items, min_foils=10)}
check("auc is None", d["t9"].auc, None)
check("held returns None, not False", held(items[-1], d["t9"], min_auc=0.8), None)
s = summarise(items, d.values())
check("summary counts it as unmeasured", s["n_measured"], 0)
check("coverage reported", s["coverage"], 0.0)

print("\n5 · an answer missing from a foil's pool is skipped, not scored as a loss")
a = item("x0", "US", {"US": 1.0, "France": 0.0, "Japan": 0.0, "Chile": 0.0})
b = ItemResult(case_id="x1", relation_id="outer", subject="s", true_answer="France",
               rank_subject=1, rank_prior=99, n_candidates=2,
               candidates=["France", "Japan"], scores_subject=[1.0, 0.0])
d = {x.case_id: x for x in discriminate([a, b], min_foils=1)}
check("US foil count excludes the pool that lacks US", d["x0"].n_foils, 0)
check("possible-foil count still records it", d["x0"].n_foils_possible, 1)
check("so US is unmeasured here", d["x0"].auc, None)

print("\nall checks passed")
