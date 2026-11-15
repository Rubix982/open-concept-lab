"""E-040 · Re-measure the prefix-sharing premise across four models.

The paper's second contribution says the delivery coefficient is exactly 1 on
any prefix-sharing prompt, *with its premise measured on four models from 6B to
405B*, and §3.2 puts a different-subject floor of **0.082** beside it. Both
numbers come from [E-018], 23 October, whose output directory is gone and whose
runner was never committed. So an analytic claim's empirical half currently has
no retrievable source.

This does not restore that run. It measures the same quantity again, and the
paper must say which of the two it is.

**What is analytic and what is not.** Under causal attention a prompt that opens
with the edited subject has, at that subject's last token, exactly the text the
edit prompt had. Its key is therefore k*, and c = (k·u)/(u·k*) = 1 for any
covariance at any layer — u cancels. Nothing about the model is being tested
there. What is being tested is whether this implementation realises that
premise: tokenisation, padding, position indexing, and the per-architecture
path to the MLP output projection. A deviation is a fault in the code, not a
finding about the model, which is why the band is `(0.999, 1.001)` and why the
same band is applied unchanged to all four.

The floor is the opposite. A prompt naming a *different* person shares no
prefix, so its coefficient is empirical, and it is what makes the 1.000 mean
anything. It may well differ by model and by layer; [E-018] published a single
0.082 and the paper repeats it without a model attached. If the four disagree,
that sentence needs the qualifier it does not currently carry.

**Why this is one pass per model.** Anchors, edit prompts and floor prompts are
read inside a single trace, so k and k* come from the same forward pass and no
cached k* is needed. That matters twice: it removes the cross-session variation
[E-005] found, and it removes the only thing in `run_e006.py` that was tied to
one model's cache. Position indices are recomputed per model because the
tokenisers differ.

Nothing here edits anything. Four forward passes.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parent))

from editreach.arch import resolve_arch                            # noqa: E402
from editreach.coefficient import keys_at                          # noqa: E402
from editreach.data import load_counterfact                        # noqa: E402
from editreach.logs import setup                                   # noqa: E402
from editreach.remote import connect                               # noqa: E402
from editreach.rome import subject_last_index                      # noqa: E402

log = setup("E-040")

#: The four [E-018] covered, smallest first. 6B is the only non-Llama, which is
#: the reason `editreach.arch` exists: every other script hard-coded Llama's
#: path to the MLP output projection and would have read the wrong module here
#: without raising.
MODELS: tuple[str, ...] = (
    "EleutherAI/gpt-j-6b",
    "meta-llama/Llama-3.1-8B",
    "meta-llama/Llama-3.1-70B",
    "meta-llama/Llama-3.1-405B",
)

#: From the probe file's own `band` on every anchor item, restated here so the
#: pass/fail in this script does not depend on reading it back.
ANCHOR_BAND = (0.999, 1.001)

#: What [E-018] published, for comparison only. It is not a gate: a floor far
#: from this refutes the single-number phrasing in §3.2, not the premise.
E018_FLOOR = 0.082


def measure(model_name: str, anchors: list, floors: list, cf: dict,
            layer: int) -> dict:
    """One model, one trace, three groups of prompts."""
    model = connect(model_name)
    arch, n_layers, d_mlp = resolve_arch(model, model_name)
    tok = model.tokenizer

    prompts = [r["prompt"] for r in anchors]
    positions = [subject_last_index(tok, r["prompt"], r["subject"],
                                    occurrence=r.get("occurrence", 0))
                 for r in anchors]
    # The edit prompt supplies k*. Read in the same trace as k, so the ratio is
    # taken within one forward pass and the device variation [E-005] measured
    # cancels in it.
    eps = [cf[r["case_id"]].rewrite.prompt.format(cf[r["case_id"]].rewrite.subject)
           for r in anchors]
    epos = [subject_last_index(tok, e, r["subject"]) for e, r in zip(eps, anchors)]
    fprompts = [r["prompt"] for r in floors]
    fpos = [subject_last_index(tok, r["prompt"], r["subject"],
                               occurrence=r.get("occurrence", 0)) for r in floors]

    meta: dict = {}
    keys = keys_at(model, prompts + eps + fprompts, positions + epos + fpos,
                   layer=layer, remote=True, meta_out=meta)

    half = len(anchors)
    stars = keys[half:2 * half]
    coef = [float(k @ s) / float(s @ s) for k, s in zip(keys[:half], stars)]
    # Each floor prompt is paired to the same case as the anchor at its index,
    # so the stranger's key is read against that case's own k*.
    floor = [float(k @ s) / float(s @ s) for k, s in zip(keys[2 * half:], stars)]

    worst = max(abs(c - 1.0) for c in coef)
    out_of_band = [a["id"] for a, c in zip(anchors, coef)
                   if not ANCHOR_BAND[0] <= c <= ANCHOR_BAND[1]]
    row = {
        "model": model_name, "arch": arch, "n_layers": n_layers, "d_mlp": d_mlp,
        "layer": layer, "n_anchors": len(anchors),
        "anchor_median": st.median(coef),
        "anchor_min": min(coef), "anchor_max": max(coef),
        "anchor_worst_deviation": worst,
        "anchor_out_of_band": out_of_band,
        "premise_holds": not out_of_band,
        "floor_median": st.median(floor),
        "floor_min": min(floor), "floor_max": max(floor),
        "separation": st.median(coef) - st.median(floor),
        "runtime": meta.get("runtime"),
        "gpu": ",".join(sorted(meta.get("max_mem_by_gpu") or {})) or "?",
    }
    log.info("  %-28s %-6s L%-3d anchors %.6f (worst dev %.3e, %d out of band)  "
             "floor %.6f  sep %.3f",
             model_name, arch, layer, row["anchor_median"], worst,
             len(out_of_band), row["floor_median"], row["separation"])
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probes", type=Path, default=Path("probes/generated.json"))
    ap.add_argument("--edit-slice", type=Path, default=HERE.parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=5,
                    help="the premise is layer-independent; the floor is not")
    ap.add_argument("--models", nargs="*", default=list(MODELS),
                    help="subset to run; the 405B is the expensive one")
    ap.add_argument("--out", type=Path,
                    default=Path("results/E-040-premise-four-models.json"))
    a = ap.parse_args()

    items = json.loads(a.probes.read_text())["items"]
    anchors = [i for i in items if i["id"].endswith("/anchor-prefix")]
    floors = [i for i in items if i["id"].endswith("/anchor-floor")]
    if [x["case_id"] for x in anchors] != [x["case_id"] for x in floors]:
        log.error("anchors and floors are not case-aligned; the pairing above "
                  "reads each floor against the wrong k*")
        return 2
    cf = {str(r.case_id): r for r in
          load_counterfact(a.edit_slice / "data" / "counterfact.json.gz")}

    log.info("%d anchors, %d floors, %d models, layer %d",
             len(anchors), len(floors), len(a.models), a.layer)

    rows, failed = [], []
    for name in a.models:
        try:
            rows.append(measure(name, anchors, floors, cf, a.layer))
        except Exception as e:
            # Recorded rather than crashed: a model this run could not read is a
            # gap in the claim's coverage, and it belongs in the output file
            # where the paper can see it.
            #
            # The first draft caught only `UnsupportedArchitecture`, and on
            # 2026-11-15 the 405B came back `CANT_ACCOMMODATE: placed 0 of 1 new
            # replicas` — NDIF had no room. That is not an architecture the code
            # cannot read; it is a model the cluster could not serve, which is
            # an ordinary condition on shared infrastructure and the commoner of
            # the two. The narrow except let it take three completed models down
            # with it, because the result file is written at the end. The models
            # are independent of each other, so one failing must not cost the
            # others.
            log.error("  %-28s SKIPPED: %s: %s", name, type(e).__name__, e)
            failed.append({"model": name, "error": f"{type(e).__name__}: {e}"})

    if not rows:
        log.error("no model was read; nothing to say about the premise")
        return 1

    held = [r for r in rows if r["premise_holds"]]
    floors_med = [r["floor_median"] for r in rows]
    log.info("")
    log.info("premise holds on %d of %d models read, band %s",
             len(held), len(rows), ANCHOR_BAND)
    log.info("anchor median across models   %.6f .. %.6f",
             min(r["anchor_median"] for r in rows),
             max(r["anchor_median"] for r in rows))
    log.info("floor median across models    %.6f .. %.6f   (E-018 published %.3f)",
             min(floors_med), max(floors_med), E018_FLOOR)

    if len(held) < len(rows):
        verdict = (f"the premise failed on {len(rows) - len(held)} of {len(rows)} "
                   f"models read. That is an implementation fault — tokenisation, "
                   f"position, or the architecture's key site — not a finding "
                   f"about the models. The contribution's 'exactly 1' may not be "
                   f"claimed for those until it is found.")
    elif max(floors_med) - min(floors_med) > 0.02:
        verdict = (f"the premise held on all {len(rows)} models, so the analytic "
                   f"claim stands. The floor did not: it spans "
                   f"{min(floors_med):.3f}..{max(floors_med):.3f} across models, "
                   f"so §3.2's single 0.082 needs a model named beside it.")
    else:
        verdict = (f"the premise held on all {len(rows)} models and the floor "
                   f"agreed to within 0.02 across them, median "
                   f"{st.median(floors_med):.3f} against [E-018]'s "
                   f"{E018_FLOOR:.3f}. Both halves of the contribution are "
                   f"reproducible from this file.")
    if failed:
        # The contribution names four models. A verdict over three is a verdict
        # about a narrower claim, and it has to say so itself rather than leave
        # the reader to notice the count.
        verdict += (" Not read: " + ", ".join(f["model"] for f in failed) +
                    ". The contribution names four models, so it may not be "
                    "stated for those until they are.")
    log.info("")
    log.info("VERDICT: %s", verdict)

    result = {
        "ticket": "E-040", "layer": a.layer,
        "nnsight": __import__("nnsight").__version__,
        "anchor_band": list(ANCHOR_BAND),
        "n_anchors": len(anchors),
        "models_read": [r["model"] for r in rows],
        "models_skipped": failed,
        "premise_holds_on_all": len(held) == len(rows),
        "anchor_median_by_model": {r["model"]: r["anchor_median"] for r in rows},
        "floor_median_by_model": {r["model"]: r["floor_median"] for r in rows},
        "floor_spread_across_models": max(floors_med) - min(floors_med),
        "e018_published_anchor": 1.000,
        "e018_published_floor": E018_FLOOR,
        "verdict": verdict,
        "rows": rows,
        "note": ("A fresh measurement of the same quantity, not a re-run of "
                 "[E-018]: that run's outputs are lost and its runner was never "
                 "committed. Nothing is edited here."),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
