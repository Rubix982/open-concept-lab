"""E-005 · Is `TransformersModel` the same instrument as `LanguageModel`?

nnsight 0.8.1 deprecates `LanguageModel`. Every number in this repo and in
edit-slice came through it, as did every cached tensor on disk. So the question
is not whether the replacement works — it is whether the two are **the same
instrument**. If activations are bit-identical the switch is housekeeping. If
they are not, switching silently re-baselines a cache full of numbers and every
cross-run comparison would straddle two instruments without saying so.

Three comparisons, in order of how cheap they are to run and how expensive they
are to get wrong:

1. **Module paths.** `arch.py` reaches into `model.model.layers[L].mlp.down_proj`.
   If the loaders expose different trees, the switch is a real job, not a line.
2. **Raw activations**, through `keys_at` on the same prompts at the same
   positions. Branch 1 demands `torch.equal`, not `allclose`: activations arrive
   in bf16 and a one-ulp difference is still a difference. `allclose` is exactly
   how a re-baseline gets filed as an upgrade.
3. **The two gates.** The anchors must pin at 1.000 — the one quantity known
   analytically, so it must hold whatever loads the model — and the floor must
   reproduce [E-001]'s 0.0809 over its 42 items.

**Nothing here switches anything.** `connect(loader=...)` was made switchable so
this could be measured; the default stays `LanguageModel` until this card says
otherwise.

**The design changed once, during the run, and the reason is the result.** The
first version compared one reading per loader and asked for `torch.equal`. That
criterion is unsatisfiable on this platform: two readings taken through the SAME
loader, on byte-identical inputs, also differ — by 3.125e-02 on 94% of elements,
which is more than one bf16 ulp for all but 6% of them. The variable is the NDIF
serving session, not the loader. So the comparison is now a **repeat design**:
several readings per loader, and the question is whether readings differ MORE
between loaders than they do within one. That is the same control shape as
[E-004]'s relation split, and for the same reason — a difference is only
attributable once the thing it is being attributed to is varied on its own.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parent))

from editreach.arch import key_site, resolve_arch                 # noqa: E402
from editreach.coefficient import keys_at                         # noqa: E402
from editreach.data import load_counterfact                       # noqa: E402
from editreach.logs import setup                                  # noqa: E402
from editreach.remote import LOADERS, connect, encode_prompts, quiet_stdout, retrying  # noqa: E402
from editreach.rome import subject_last_index                     # noqa: E402
import run_e001 as R                                              # noqa: E402

log = setup("E-005")

#: [E-001]'s own readings, over its 42 anchor-floor items. The empirical
#: companion to the analytic 1.000.
E001_FLOOR_MEDIAN = 0.0809
FLOOR_TOLERANCE = 0.005


def probe_rows(items: list[dict], suffix: str) -> list[dict]:
    return [i for i in items if i["id"].endswith(suffix)]


def read(model, rows: list[dict], tok, layer: int,
         edits: dict[str, str] | None = None) -> tuple[torch.Tensor, torch.Tensor | None]:
    """Keys at each probe's subject token, and optionally `k*` in the same trace.

    `k*` is read live rather than taken from the [E-014] cache. Against the
    cache the 42 analytic anchors read a worst deviation of **4.806e-03** under
    BOTH loaders — identical, so it was never a loader difference, but it is a
    gate reporting a failure for a reason unrelated to what it guards. The cause
    is the one [E-001] already recorded: activations arrive in bf16 and a cached
    `k*` carries the dtype and batch shape of the session that wrote it. Reading
    both in one trace removes it.
    """
    prompts = [r["prompt"] for r in rows]
    positions = [subject_last_index(tok, r["prompt"], r["subject"],
                                    occurrence=r.get("occurrence", 0)) for r in rows]
    if edits is None:
        return keys_at(model, prompts, positions, layer=layer, remote=True), None
    # The edit prompts ride in the same batch, appended so indices stay stable.
    eps = [edits[r["case_id"]] for r in rows]
    subs = [r["subject"] for r in rows]
    prompts = prompts + eps
    positions = positions + [subject_last_index(tok, e, s) for e, s in zip(eps, subs)]
    got = keys_at(model, prompts, positions, layer=layer, remote=True)
    return got[:len(rows)], got[len(rows):]


def logits_at_last(model, prompts: list[str]) -> torch.Tensor:
    """Final-position logits, the quantity `top1_batch` and `prob_of` read.

    The key-site comparison covers one module at one layer. Every behavioural
    number in [E-001] through [E-003] came off `lm_head` instead, so a loader
    that agreed at layer 5 and disagreed at the head would pass a parity check
    and still move every result. Cheap to rule out, so it is ruled out.
    """
    ids, lengths = encode_prompts(model, prompts)
    last = torch.tensor([n - 1 for n in lengths])
    rows = torch.arange(len(prompts))

    def _run():
        with quiet_stdout(), model.trace(ids, remote=True):
            got = model.lm_head.output[rows, last].float().save()
        return got.detach().cpu().float()

    return retrying(_run, what=f"lm_head x{len(prompts)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probes", type=Path, default=Path("probes/generated.json"))
    ap.add_argument("--edit-slice", type=Path, default=HERE.parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=5)
    ap.add_argument("--repeats", type=int, default=3,
                    help="readings per loader. Two or more is what makes the "
                         "within-loader comparison exist, and without it a "
                         "between-loader difference cannot be attributed.")
    ap.add_argument("--out", type=Path, default=Path("results/E-005-loader-parity.json"))
    a = ap.parse_args()

    items = json.loads(a.probes.read_text())["items"]
    anchors = probe_rows(items, "/anchor-prefix")
    floors = probe_rows(items, "/anchor-floor")
    log.info("%d anchor-prefix and %d anchor-floor probes", len(anchors), len(floors))

    ks, _ = R.load_edit_cache(a.edit_slice)
    # CounterFact's own edit prompt per subject, for the live `k*` read.
    cf = {str(r.case_id): r for r in
          load_counterfact(a.edit_slice / "data" / "counterfact.json.gz")}
    edits = {r["case_id"]: cf[r["case_id"]].rewrite.prompt.format(
        cf[r["case_id"]].rewrite.subject) for r in anchors}

    arms, structure = {}, {}
    for loader in [l for l in LOADERS for _ in range(a.repeats)]:
        log.info("")
        log.info("=== loader: %s ===", loader)
        model = connect(R.MODEL, loader=loader)
        tok = model.tokenizer

        # 1. structure, before any remote call
        name, n_layers, d_mlp = resolve_arch(model)
        site = key_site(model, a.layer)
        structure[loader] = {"arch": name, "n_layers": n_layers, "d_mlp": d_mlp,
                             "key_site": type(site).__name__,
                             "path": getattr(site, "path", str(site))}
        log.info("arch %s, %d layers, d_mlp %d, key site %s",
                 name, n_layers, d_mlp, structure[loader]["key_site"])

        # 2. raw activations
        ka, stars = read(model, anchors, tok, a.layer, edits=edits)
        kf, _ = read(model, floors, tok, a.layer)

        # 3. the gates, computed from those very keys — no extra traces.
        # The anchors use the LIVE k* read beside them; the floor keeps the
        # cached one, because 0.0809 is [E-001]'s number and [E-001] read it
        # that way. Changing both at once would compare two things.
        coef_a, coef_f = [], []
        for k, star in zip(ka, stars):
            coef_a.append(float(k @ star) / float(star @ star))
        for r, k in zip(floors, kf):
            star = ks[f"{r['case_id']}|real"].float()
            coef_f.append(float(k @ star) / float(star @ star))
        # 4. the head, which is where every behavioural number is read
        head = logits_at_last(model, [r["prompt"] for r in anchors + floors])
        arms.setdefault(loader, []).append(
            {"anchors": ka, "floors": kf, "head": head,
             "coef_anchors": coef_a, "coef_floors": coef_f})
        log.info("anchors: worst deviation from 1.000 = %.3e | floor median %.4f",
                 max(abs(c - 1.0) for c in coef_a), st.median(coef_f))

    # --- the comparison -----------------------------------------------------
    # Within-loader first. If two readings through the SAME loader already
    # differ, no between-loader difference can be attributed to the loader.
    import itertools

    def spread(pairs) -> dict:
        worst, n_diff, equal = 0.0, 0.0, 0
        total = 0
        for x, y in pairs:
            total += 1
            same = all(torch.equal(x[k], y[k]) for k in SURFACES)
            equal += int(same)
            for k in SURFACES:
                d = (x[k] - y[k]).abs()
                worst = max(worst, float(d.max()))
                n_diff = max(n_diff, float((d > 0).float().mean()))
        return {"pairs": total, "all_equal": equal,
                "worst_abs": worst, "max_fraction_differing": n_diff}

    SURFACES = ("anchors", "floors", "head")
    within = {l: spread(itertools.combinations(arms[l], 2)) for l in LOADERS}
    between = spread([(x, y) for x in arms["language"] for y in arms["transformers"]])
    scale = float(torch.cat([arms["language"][0]["anchors"],
                             arms["language"][0]["floors"]]).abs().median())

    log.info("")
    log.info("module paths identical: %s", same_structure := (
        structure["language"] == structure["transformers"]))
    if not same_structure:
        for loader in LOADERS:
            log.error("  %-12s %s", loader, structure[loader])
    log.info("")
    log.info("%-34s %6s %8s %12s", "comparison", "pairs", "worst|d|", "frac differing")
    for l in LOADERS:
        w = within[l]
        log.info("  WITHIN %-26s %6d %8.3e %11.4f", l, w["pairs"],
                 w["worst_abs"], w["max_fraction_differing"])
    log.info("  BETWEEN %-25s %6d %8.3e %11.4f", "the two loaders", between["pairs"],
             between["worst_abs"], between["max_fraction_differing"])
    log.info("  (median |key| %.3e, so a difference of %.3e is %.1fx it)",
             scale, between["worst_abs"], between["worst_abs"] / scale if scale else 0)

    # The verdict turns on whether BETWEEN exceeds WITHIN, not on bit-identity.
    worst_within = max(within[l]["worst_abs"] for l in LOADERS)
    attributable = between["worst_abs"] > worst_within
    reproducible = worst_within == 0.0

    gates = {}
    for loader in LOADERS:
        wa = max(abs(c - 1.0) for r in arms[loader] for c in r["coef_anchors"])
        fms = [st.median(r["coef_floors"]) for r in arms[loader]]
        gates[loader] = {
            "anchor_worst_deviation": wa,
            "anchors_pinned": all(R.ANCHOR_BAND[0] <= c <= R.ANCHOR_BAND[1]
                                  for r in arms[loader] for c in r["coef_anchors"]),
            "floor_medians": fms,
            "floor_median_spread": max(fms) - min(fms),
            "floor_reproduced": all(abs(f - E001_FLOOR_MEDIAN) <= FLOOR_TOLERANCE
                                    for f in fms),
        }
        log.info("")
        log.info("gate under %-12s anchors pinned %s (worst %.3e)",
                 loader, gates[loader]["anchors_pinned"], wa)
        log.info("   floor medians %s vs [E-001] %.4f, spread %.3e",
                 ["%.6f" % f for f in fms], E001_FLOOR_MEDIAN,
                 gates[loader]["floor_median_spread"])

    if not same_structure:
        verdict = ("branch 3 — the loaders expose different module trees; arch.py "
                   "needs a second mapping and the switch is a scheduled job")
    elif not reproducible and not attributable:
        verdict = ("branch 1, by the repeat design rather than by bit-identity — "
                   "readings differ as much WITHIN one loader as BETWEEN the two, "
                   "so the loader is not the variable and the two are the same "
                   "instrument at this platform's reproducibility. The pre-stated "
                   "bit-identity criterion was unsatisfiable and is recorded as a "
                   "design error, not met and not waived.")
    elif attributable:
        verdict = ("branch 2 — between-loader differences exceed within-loader "
                   "ones, so the switch is a RE-BASELINE, not an upgrade. Do not "
                   "switch; record the loader alongside seed and layer.")
    else:
        verdict = ("branch 1 — readings are bit-reproducible within a loader and "
                   "identical between them; the switch is housekeeping.")
    log.info("")
    log.info("VERDICT: %s", verdict)

    result = {
        "ticket": "E-005", "model": R.MODEL, "layer": a.layer,
        "nnsight": __import__("nnsight").__version__,
        "structure": structure, "same_structure": same_structure,
        "repeats_per_loader": a.repeats,
        "within_loader": within, "between_loaders": between,
        "within_is_reproducible": reproducible,
        "difference_attributable_to_loader": attributable,
        "median_abs_key": scale,
        "verified_surfaces": ["mlp.down_proj.input at the edit layer", "lm_head.output"],
        "gates": gates,
        "e001_floor_median": E001_FLOOR_MEDIAN,
        "n_anchors": len(anchors), "n_floors": len(floors),
        "verdict": verdict,
        "note": "connect(loader=...) is switchable; the DEFAULT is unchanged and "
                "stays LanguageModel unless this says branch 1.",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
