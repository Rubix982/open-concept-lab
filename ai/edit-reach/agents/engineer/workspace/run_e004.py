"""E-004 · Is the far-field coefficient at floor, measured on its own prompts?

[E-039] established most of this on 2026-10-15: on MQuAKE-CF-3k the coefficient
is 0.933 where a question names the edited subject and 0.055 where it does not.
What it could not do was compare that 0.055 against a floor read **on those same
prompts** — its floors came from a permuted `k*` on RippleEdits (0.069) and a
different token on MQuAKE (0.027). They converge, and convergence across corpora
is not the control T-005 asked for: MQuAKE's questions are longer and multi-hop,
so their own floor is an open quantity.

So this re-reads [E-039]'s exact 513 instances, keeps the **key vectors** rather
than the scalars, and scores every hop-2 question against all 299 other
instances' `k*`. The floor becomes a distribution measured on the prompt itself,
and no single arbitrary donor can carry the answer.

**The selection is imported from [E-039], not reimplemented.** The reproduction
of 0.933 / 0.055 is this run's gate, and a gate against a set I rebuilt from the
same description would be checking my reading of a docstring rather than the
pipeline.

**Delivery, not effect.** [E-028d], 2.96x. Nothing here measures how far an
answer moves, and a floor result does not say an edit fails to reach an answer —
only that this measure, at layer 5, does not see it.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
EDIT_SLICE = HERE.parents[4] / "edit-slice"
sys.path.insert(0, str(HERE.parents[3]))
# [E-039]'s own selection, imported rather than copied: see the module docstring.
sys.path.insert(0, str(EDIT_SLICE / "agents" / "engineer" / "workspace"))

from editreach.coefficient import keys_at                         # noqa: E402
from editreach.logs import setup                                  # noqa: E402
from editreach.remote import connect                              # noqa: E402
from editreach.rome import subject_last_index                     # noqa: E402
from run_e039 import usable                                       # noqa: E402

log = setup("E-004")

MODEL = "meta-llama/Llama-3.1-8B"
LAYER = 5
# [E-039]'s published medians, and the tolerance this run must meet to be read
# at all. Stated here, before the numbers exist, because a tolerance chosen
# afterwards is not a gate.
E039_HOP1_NATURAL = 0.933
E039_HOP2_FINAL = 0.055
TOLERANCE = 0.02
#: A median over a handful of readings cannot be compared against one over 900.
#: Found by running the smoke test: at n=3 the hop-2 arm read 0.0772 and the gate
#: fired, which was the gate being applied to a sample too small to carry it, not
#: a pipeline fault. A gate that can fail for a reason unrelated to what it
#: guards teaches you to ignore it.
MIN_GATE_READINGS = 100


def select(path: Path, chain_len: int, n: int) -> list[dict]:
    """[E-039]'s selection, by its own `usable`, in its own order."""
    picked, skipped = [], 0
    for entry in json.loads(path.read_text()):
        u = usable(entry)
        if u is None:
            skipped += 1
            continue
        if chain_len and u["chain_len"] != chain_len:
            continue
        picked.append(u)
        if len(picked) >= n:
            break
    log.info("%d instances selected, %d skipped (multi-edit or unlocatable hop)",
             len(picked), skipped)
    return picked


def read_instance(model, tok, inst: dict) -> dict | None:
    """`k*` plus one key per question, at the natural position and at the final token."""
    prompts = [inst["edit"]] + inst["questions"]
    try:
        star_pos = subject_last_index(tok, inst["edit"], inst["subject"])
    except ValueError:
        log.debug("case %s: subject not locatable in its own edit prompt", inst["case_id"])
        return None

    natural_pos, named = [], []
    for q in inst["questions"]:
        hit = inst["subject"] in q
        named.append(hit)
        # The final token is `len(ids) - 1` on the UNPADDED prompt. `keys_at`
        # re-encodes and range-checks, so this must agree with its view.
        last = len(tok(q).input_ids) - 1
        natural_pos.append(
            subject_last_index(tok, q, inst["subject"]) if hit else last)

    final_pos = [len(tok(q).input_ids) - 1 for q in inst["questions"]]
    # One trace for the lot: the edit prompt, each question at its natural
    # position, and each question again at its final token.
    all_prompts = prompts + list(inst["questions"])
    all_pos = [star_pos] + natural_pos + final_pos
    keys = keys_at(model, all_prompts, all_pos, layer=LAYER, remote=True)
    nq = len(inst["questions"])
    return {"case_id": inst["case_id"], "hop": inst["hop"],
            "relation": inst["relation"], "names_subject": named,
            "k_star": keys[0], "k_natural": keys[1:1 + nq], "k_final": keys[1 + nq:]}


def coefficients(k: torch.Tensor, k_star: torch.Tensor) -> torch.Tensor:
    """`(k·k*)/(k*·k*)` — each donor normalised by its OWN denominator.

    Using the subject's denominator with a donor's numerator would manufacture a
    floor out of nothing but a norm mismatch.
    """
    return (k @ k_star) / float(k_star @ k_star)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", default="MQuAKE-CF-3k.json")
    ap.add_argument("--n", type=int, default=600)
    ap.add_argument("--chain-len", type=int, default=2)
    ap.add_argument("--cache", type=Path, default=Path("results/cache/E004_keys.pt"))
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--out", type=Path, default=Path("results/E-004-far-field-floor.json"))
    a = ap.parse_args()

    picked = select(EDIT_SLICE / "data" / "mquake" / a.file, a.chain_len, a.n)
    by_hop: dict[int, int] = {}
    for u in picked:
        by_hop[u["hop"]] = by_hop.get(u["hop"], 0) + 1
    log.info("by hop carrying the edit: %s", dict(sorted(by_hop.items())))

    held: dict[str, dict] = {}
    if a.cache.exists() and not a.fresh:
        held = torch.load(a.cache, map_location="cpu", weights_only=False)
        log.info("resuming: %d of %d instances already read", len(held), len(picked))

    model = connect(MODEL)
    tok = model.tokenizer
    for n, inst in enumerate(picked, 1):
        cid = str(inst["case_id"])
        if cid in held and len(held[cid]["names_subject"]) == len(inst["questions"]):
            continue
        got = read_instance(model, tok, inst)
        if got is None:
            continue
        held[cid] = got
        a.cache.parent.mkdir(parents=True, exist_ok=True)
        torch.save(held, a.cache)
        if n % 20 == 0 or n == len(picked):
            log.info("  %d/%d instances", n, len(picked))

    rows = list(held.values())
    log.info("%d instances held", len(rows))

    # --- the gate: reproduce [E-039] ----------------------------------------
    hop1_nat, hop2_fin = [], []
    for r in rows:
        own = coefficients(r["k_natural"], r["k_star"]).tolist()
        fin = coefficients(r["k_final"], r["k_star"]).tolist()
        r["own_natural"], r["own_final"] = own, fin
        (hop1_nat if r["hop"] == 1 else hop2_fin).extend(own if r["hop"] == 1 else fin)

    m1, m2 = st.median(hop1_nat), st.median(hop2_fin)
    log.info("reproduction gate: hop-1 natural %.4f over %d readings (E-039 %.3f) | "
             "hop-2 final %.4f over %d readings (E-039 %.3f)",
             m1, len(hop1_nat), E039_HOP1_NATURAL, m2, len(hop2_fin), E039_HOP2_FINAL)
    if min(len(hop1_nat), len(hop2_fin)) < MIN_GATE_READINGS:
        raise SystemExit(
            f"only {len(hop1_nat)} hop-1 and {len(hop2_fin)} hop-2 readings held; "
            f"the gate needs {MIN_GATE_READINGS} of each to mean anything. This is "
            f"a partial run, not a result — resume it.")
    passed = (abs(m1 - E039_HOP1_NATURAL) <= TOLERANCE
              and abs(m2 - E039_HOP2_FINAL) <= TOLERANCE)
    if not passed:
        raise SystemExit(
            f"reproduction FAILED outside +/-{TOLERANCE}. Something moved between "
            f"2026-10-15 and now — loader, tokenizer or key site — and every number "
            f"in edit-slice was read through this path. Explain it before reading "
            f"anything else in this card.")

    # --- the floor, on these prompts ----------------------------------------
    # Every hop-2 question against every OTHER instance's k*. One matmul: a
    # per-donor loop over 900 x 512 would be the same arithmetic, slower, and
    # easier to get wrong at the exclusion step.
    stars = torch.stack([r["k_star"] for r in rows])                   # (I, d)
    denoms = (stars * stars).sum(-1)                                   # (I,)
    hop2 = [i for i, r in enumerate(rows) if r["hop"] != 1]
    qk = torch.cat([rows[i]["k_final"] for i in hop2])                 # (Q, d)
    owner = torch.tensor([i for i in hop2 for _ in rows[i]["k_final"]])
    grid = (qk @ stars.T) / denoms                                     # (Q, I)
    mask = torch.ones_like(grid, dtype=torch.bool)
    mask[torch.arange(len(owner)), owner] = False                      # never your own
    floors = torch.where(mask, grid, torch.nan)

    floor_med = torch.nanmedian(floors, dim=1).values                  # (Q,)
    own = torch.tensor([c for i in hop2 for c in rows[i]["own_final"]])
    excess = own - floor_med

    # THE CONFOUND, and it turns out to be the whole result. A hop-2 subject is
    # the chain's middle entity, so the question is *about* it indirectly and
    # some overlap is expected from topicality rather than from any edit
    # reaching anywhere. Splitting the donors by relation separates the two:
    # a donor sharing the relation is topically as close as the real subject,
    # a donor with a different relation is not. If the excess survives only
    # against the second, the measure is reading the relation and not the
    # subject.
    rel = [r["relation"] for r in rows]
    same_f, diff_f = [], []
    for q, o in enumerate(owner.tolist()):
        s = [grid[q, j].item() for j in range(len(rows)) if j != o and rel[j] == rel[o]]
        d = [grid[q, j].item() for j in range(len(rows)) if j != o and rel[j] != rel[o]]
        same_f.append(st.median(s) if s else float("nan"))
        diff_f.append(st.median(d))
    same_f_t = torch.tensor(same_f)
    diff_f_t = torch.tensor(diff_f)
    excess_same = own - same_f_t
    excess_diff = own - diff_f_t

    def q(t: torch.Tensor, p: float) -> float:
        return float(t.nanquantile(torch.tensor(p)))

    log.info("")
    log.info("hop-2 far field, n=%d questions over %d instances", len(own), len(hop2))
    log.info("  own k*         median %.4f   IQR %.4f",
             float(own.nanmedian()), q(own, .75) - q(own, .25))
    log.info("  same-prompt floor  median %.4f   IQR %.4f",
             float(floor_med.nanmedian()), q(floor_med, .75) - q(floor_med, .25))
    log.info("  paired excess  median %+.4f   IQR %.4f  | above floor: %.0f%%",
             float(excess.nanmedian()), q(excess, .75) - q(excess, .25),
             100 * float((excess > 0).float().mean()))
    log.info("")
    log.info("  and the same floor, split by whether the donor shares the relation:")
    log.info("    SAME-relation donors      floor %.4f   excess %+.4f",
             float(same_f_t.nanmedian()), float(excess_same.nanmedian()))
    log.info("    DIFFERENT-relation donors floor %.4f   excess %+.4f",
             float(diff_f_t.nanmedian()), float(excess_diff.nanmedian()))

    result = {
        "ticket": "E-004", "model": MODEL, "layer": LAYER, "file": a.file,
        "chain_len_filter": a.chain_len, "instances": len(rows),
        "reproduction_gate": {"hop1_natural": m1, "hop2_final": m2,
                              "e039_hop1_natural": E039_HOP1_NATURAL,
                              "e039_hop2_final": E039_HOP2_FINAL,
                              "tolerance": TOLERANCE, "passed": True},
        "hop2": {
            "n_questions": len(own), "n_instances": len(hop2),
            "own_median": float(own.nanmedian()),
            "floor_median": float(floor_med.nanmedian()),
            "excess_median": float(excess.nanmedian()),
            "excess_iqr": q(excess, .75) - q(excess, .25),
            "fraction_above_floor": float((excess > 0).float().mean()),
            "donors_per_question": len(rows) - 1,
            "floor_same_relation": float(same_f_t.nanmedian()),
            "excess_over_same_relation": float(excess_same.nanmedian()),
            "floor_diff_relation": float(diff_f_t.nanmedian()),
            "excess_over_diff_relation": float(excess_diff.nanmedian()),
        },
        "note": "DELIVERY, not effect. A floor result says this measure does not "
                "see far-field propagation at layer 5; it does not say an edit "
                "fails to reach the answer.",
        "per_question": {"own": own.tolist(), "floor": floor_med.tolist(),
                         "floor_same_relation": same_f, "floor_diff_relation": diff_f},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
