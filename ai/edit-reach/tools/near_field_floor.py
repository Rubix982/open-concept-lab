"""The near field under the same donor floor the far field already uses.

§5's summary table gives the near field as own **0.9334** against a stranger's
**0.0506**. The first is in [E-004]'s result file as
`reproduction_gate.hop1_natural`. **The second is in no committed file** —
[E-002] and [E-003] were checked too — and the figure draws it and its alt text
states it. So the largest excess in the paper has an unsourced half.

It does not need a run. `run_e004.py` caches, per instance, `k*`, the natural
key, the final key, the hop and the relation, and there is one cache per model.
The near-field floor is the construction §5.2 already uses for hop-2, applied to
hop-1 instead: score each natural key against every *other* instance's `k*`, and
split the donors by whether they share the relation.

**Why the split matters more here than it does in the far field.** A hop-1
question names the edited subject, so a high reading is expected and the floor
is what makes it mean anything. A donor that shares the relation is topically as
close as the real subject; one that does not is not. The number the table should
print is the one against the tighter floor.

    python3 ai/edit-reach/tools/near_field_floor.py

Writes results/E-046-near-field-floor.json. No forward pass; nothing is edited.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))

from editreach.tidy import Source, rows as tidy_rows, write as tidy_write  # noqa: E402

RES = HERE.parents[1] / "results"
CACHE = RES / "cache"

#: model -> its cached key file. The 8B's predates the per-model naming.
CACHES: dict[str, str] = {
    "meta-llama/Llama-3.1-8B": "E004_keys.pt",
    "meta-llama/Llama-3.1-70B": "E004_keys_meta-llama_Llama-3.1-70B.pt",
    "EleutherAI/gpt-j-6b": "E004_keys_EleutherAI_gpt-j-6b.pt",
}
SHAPE = {"meta-llama/Llama-3.1-8B": ("llama", 32, 14336),
         "meta-llama/Llama-3.1-70B": ("llama", 80, 28672),
         "EleutherAI/gpt-j-6b": ("gptj", 28, 16384)}
LAYER = 5
PUBLISHED_OWN, PUBLISHED_FLOOR = 0.9334, 0.0506
TOLERANCE = 0.002


def near_field(rows: list[dict]) -> dict:
    """Own and floor on the hop-1 questions, by the hop-2 construction."""
    hop1 = [i for i, r in enumerate(rows) if r["hop"] == 1]
    if not hop1:
        return {}
    stars = torch.stack([r["k_star"].float() for r in rows])
    denom = (stars * stars).sum(1)

    # One row per hop-1 question, one column per possible donor.
    keys, owner = [], []
    for i in hop1:
        for k in rows[i]["k_natural"]:
            keys.append(k.float())
            owner.append(i)
    K = torch.stack(keys)
    grid = (K @ stars.T) / denom                                  # (Q, instances)
    own = torch.tensor([c for i in hop1 for c in rows[i]["own_natural"]]) \
        if "own_natural" in rows[hop1[0]] else grid[torch.arange(len(owner)),
                                                    torch.tensor(owner)]

    rel = [r["relation"] for r in rows]
    same, diff, allf = [], [], []
    for q, o in enumerate(owner):
        s = [grid[q, j].item() for j in range(len(rows)) if j != o and rel[j] == rel[o]]
        d = [grid[q, j].item() for j in range(len(rows)) if j != o and rel[j] != rel[o]]
        a = [grid[q, j].item() for j in range(len(rows)) if j != o]
        same.append(st.median(s) if s else float("nan"))
        diff.append(st.median(d) if d else float("nan"))
        allf.append(st.median(a))
    same_t, diff_t, all_t = (torch.tensor(x) for x in (same, diff, allf))
    return {
        "n_questions": len(owner), "n_instances": len(hop1),
        "own_median": float(own.nanmedian()),
        "floor_median": float(all_t.nanmedian()),
        "excess_median": float((own - all_t).nanmedian()),
        "floor_same_relation": float(same_t.nanmedian()),
        "excess_over_same_relation": float((own - same_t).nanmedian()),
        "floor_diff_relation": float(diff_t.nanmedian()),
        "excess_over_diff_relation": float((own - diff_t).nanmedian()),
        "fraction_above_floor": float(((own - all_t) > 0).float().mean()),
        "per_question": {"own": own.tolist(), "floor": allf,
                         "floor_same_relation": same, "floor_diff_relation": diff},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=RES / "E-046-near-field-floor.json")
    ap.add_argument("--tidy", type=Path, default=RES / "tidy")
    a = ap.parse_args()

    out: dict[str, dict] = {}
    for model, fname in CACHES.items():
        path = CACHE / fname
        if not path.exists():
            print(f"{model:<28} no cache at {path.name}, skipped")
            continue
        rows = list(torch.load(path, map_location="cpu", weights_only=False).values())
        res = near_field(rows)
        out[model] = res
        print(f"{model:<28} n={res['n_questions']:<5} own {res['own_median']:.4f}  "
              f"floor {res['floor_median']:.4f}  excess {res['excess_median']:+.4f}  "
              f"same-rel floor {res['floor_same_relation']:.4f}")

        arch, n_layers, d_mlp = SHAPE[model]
        src = Source("E-046", model, LAYER, arch, n_layers, d_mlp)
        recs = [r for metric, vals in res["per_question"].items()
                for r in tidy_rows(src, "hop1", metric, vals)]
        tidy_write(a.tidy / f"E-046-near-field-{model.replace('/', '_')}.csv", recs)

    ref = out.get("meta-llama/Llama-3.1-8B")
    verdict = "no Llama-3.1-8B cache; the published cell stays unsourced"
    if ref:
        d_own = abs(ref["own_median"] - PUBLISHED_OWN)
        d_floor = abs(ref["floor_median"] - PUBLISHED_FLOOR)
        d_same = abs(ref["floor_same_relation"] - PUBLISHED_FLOOR)
        if d_own <= TOLERANCE and min(d_floor, d_same) <= TOLERANCE:
            which = "all donors" if d_floor <= d_same else "same-relation donors"
            verdict = (f"sourced: own {ref['own_median']:.4f} against a published "
                       f"{PUBLISHED_OWN} and the floor over {which} against "
                       f"{PUBLISHED_FLOOR}.")
        else:
            verdict = (
                f"the published near-field floor {PUBLISHED_FLOOR} is not what this "
                f"cache produces. Over all donors it is {ref['floor_median']:.4f} and "
                f"over same-relation donors {ref['floor_same_relation']:.4f}; own is "
                f"{ref['own_median']:.4f} against a published {PUBLISHED_OWN}, so the "
                f"instances are the right ones. The table and the figure take the "
                f"computed value and the discrepancy is recorded, not replaced "
                f"quietly.")
    print(f"\nVERDICT: {verdict}")

    a.out.write_text(json.dumps({
        "ticket": "E-046", "layer": LAYER,
        "source": "offline over results/cache/E004_keys*.pt",
        "published_own": PUBLISHED_OWN, "published_floor": PUBLISHED_FLOOR,
        "tolerance": TOLERANCE, "verdict": verdict,
        "by_model": out,
        "note": ("DELIVERY, not effect. The same donor construction §5.2 uses for "
                 "hop-2, applied to hop-1. No forward pass; nothing is edited."),
    }, indent=1))
    print(f"written to {a.out.relative_to(HERE.parents[2])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
