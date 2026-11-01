"""E-006 · Do the two values partition by the GPU that served the request?

[E-005] found that readings of the same batch, on byte-identical inputs, differ
between NDIF connections on 93.94% of elements, deterministic within a
connection, and that across six readings only **two** distinct values appeared.
That is the shape of routing — several replicas, each internally consistent —
but it was never tested, and an untested explanation that fits is the cheapest
kind of story.

nnsight surfaces what the server reports on `tracer.backend.meta`, and it
carries `max_mem_by_gpu`, keyed by **GPU index**. So the hypothesis is testable
with the client we already have: read the same batch through N fresh
connections, record a content hash and the device, and ask whether the hashes
partition by it.

**What turns on the answer.** If they partition, the fix is bookkeeping — record
the device beside seed and layer, and readings stay comparable within one. If
one device returns two hashes, no equality across readings means anything and
every gate needs a tolerance taken from the measured spread.

Nothing here edits anything. N forward passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torch

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3]))
sys.path.insert(0, str(HERE.parent))

from editreach.coefficient import keys_at                         # noqa: E402
from editreach.data import load_counterfact                       # noqa: E402
from editreach.logs import setup                                  # noqa: E402
from editreach.remote import connect                              # noqa: E402
from editreach.rome import subject_last_index                     # noqa: E402
import run_e001 as R                                              # noqa: E402

log = setup("E-006")


def signature(t: torch.Tensor) -> str:
    """A content hash of the whole tensor.

    Of the raw keys, not of any derived scalar: the quantities this project
    reports are ratios taken inside one trace, and a ratio cancels most of what
    is being measured here. Hashing the ratio would hide the effect.
    """
    return hashlib.sha1(t.numpy().tobytes()).hexdigest()[:16]


def gpu_of(meta: dict) -> str:
    """The GPU index the server reports, or `?` when it reports none."""
    by_gpu = meta.get("max_mem_by_gpu") or {}
    return ",".join(sorted(by_gpu)) if by_gpu else "?"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probes", type=Path, default=Path("probes/generated.json"))
    ap.add_argument("--edit-slice", type=Path, default=HERE.parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=5)
    ap.add_argument("--readings", type=int, default=16)
    ap.add_argument("--out", type=Path, default=Path("results/E-006-session-variation.json"))
    a = ap.parse_args()

    items = json.loads(a.probes.read_text())["items"]
    anchors = [i for i in items if i["id"].endswith("/anchor-prefix")]
    floors = [i for i in items if i["id"].endswith("/anchor-floor")]
    # Two derived quantities, and they differ in the one way that matters here.
    # The anchor coefficient reads k and k* in the SAME trace, so whatever the
    # device does cancels in the ratio — which is why every anchor gate in this
    # repo survived without anyone noticing this. The floor is read against the
    # CACHED k*, so it does not cancel, and it is [E-001]'s published 0.0809.
    # The tolerance this card owes comes from the floor, not the anchors.
    ks, _ = R.load_edit_cache(a.edit_slice)
    cf = {str(r.case_id): r for r in
          load_counterfact(a.edit_slice / "data" / "counterfact.json.gz")}
    log.info("%d probes, %d readings through fresh connections", len(anchors), a.readings)

    rows = []
    for n in range(a.readings):
        # A fresh connection each time: the connection is the variable, so it
        # must be re-made rather than reused.
        model = connect(R.MODEL)
        tok = model.tokenizer
        prompts = [r["prompt"] for r in anchors]
        positions = [subject_last_index(tok, r["prompt"], r["subject"],
                                        occurrence=r.get("occurrence", 0)) for r in anchors]
        eps = [cf[r["case_id"]].rewrite.prompt.format(cf[r["case_id"]].rewrite.subject)
               for r in anchors]
        epos = [subject_last_index(tok, e, r["subject"]) for e, r in zip(eps, anchors)]
        fprompts = [r["prompt"] for r in floors]
        fpos = [subject_last_index(tok, r["prompt"], r["subject"],
                                   occurrence=r.get("occurrence", 0)) for r in floors]
        meta: dict = {}
        # One trace for all three groups: the extra quantity costs no extra pass.
        keys = keys_at(model, prompts + eps + fprompts, positions + epos + fpos,
                       layer=a.layer, remote=True, meta_out=meta)
        # The derived quantity, recorded beside the raw one so the practical
        # impact is visible rather than inferred. k and k* share this trace, so
        # the ratio cancels most of the variation — which is the point.
        half = len(anchors)
        coef = [float(k @ s) / float(s @ s)
                for k, s in zip(keys[:half], keys[half:2 * half])]
        fl = []
        for r, k in zip(floors, keys[2 * half:]):
            star = ks[f"{r['case_id']}|real"].float()
            fl.append(float(k @ star) / float(star @ star))
        rows.append({
            "reading": n, "signature": signature(keys), "gpu": gpu_of(meta),
            "runtime": meta.get("runtime"),
            "max_mem": meta.get("max_memory_usage"),
            "anchor_worst_deviation": max(abs(c - 1.0) for c in coef),
            "floor_median": st.median(fl),
        })
        log.info("  %2d  sig %s  gpu %-4s  runtime %5.2fs  anchors worst %.3e  floor %.6f",
                 n, rows[-1]["signature"], rows[-1]["gpu"],
                 rows[-1]["runtime"] or float("nan"),
                 rows[-1]["anchor_worst_deviation"], rows[-1]["floor_median"])

    # --- does it partition? --------------------------------------------------
    by_gpu: dict[str, set[str]] = defaultdict(set)
    by_sig: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        by_gpu[r["gpu"]].add(r["signature"])
        by_sig[r["signature"]].add(r["gpu"])

    sigs = Counter(r["signature"] for r in rows)
    gpus = Counter(r["gpu"] for r in rows)
    log.info("")
    log.info("%d distinct values over %d readings; %d distinct GPUs",
             len(sigs), len(rows), len(gpus))
    for sig, n in sigs.most_common():
        log.info("  %s  x%-3d served by GPU %s", sig, n, sorted(by_sig[sig]))
    log.info("")
    for gpu, n in gpus.most_common():
        log.info("  GPU %-4s x%-3d returned %d distinct value(s) %s",
                 gpu, n, len(by_gpu[gpu]), sorted(by_gpu[gpu]))

    one_value_per_gpu = all(len(v) == 1 for v in by_gpu.values())
    one_gpu_per_value = all(len(v) == 1 for v in by_sig.values())
    partitions = one_value_per_gpu and one_gpu_per_value

    if len(sigs) == 1:
        verdict = (f"branch 3 — all {len(rows)} readings agree. The effect is not "
                   f"observed at this sample size; that is a frequency bound, not "
                   f"stability, and T-008 stays open with a standing check.")
    elif partitions:
        verdict = ("branch 1 — the values partition cleanly by GPU. It is routing. "
                   "Record the device alongside seed and layer; readings are "
                   "comparable within a device and need a tolerance across them.")
    elif not one_value_per_gpu:
        verdict = ("branch 2 — at least one GPU returned more than one value, so "
                   "the device does not explain it. No equality across readings is "
                   "meaningful; every gate needs a tolerance from the measured spread.")
    else:
        verdict = ("branch 1, partially — each value came from one GPU, but a GPU "
                   "served more than one value is not ruled out at this sample size. "
                   "Treat as routing and keep the tolerance.")

    # --- the tolerance this card owes ---------------------------------------
    floor_by_gpu = defaultdict(list)
    for r in rows:
        floor_by_gpu[r["gpu"]].append(r["floor_median"])
    all_floors = [r["floor_median"] for r in rows]
    within_gpu = max((max(v) - min(v)) for v in floor_by_gpu.values())
    across = max(all_floors) - min(all_floors)
    log.info("")
    log.info("floor median — the quantity that does NOT cancel")
    for gpu, v in sorted(floor_by_gpu.items()):
        log.info("  GPU %-4s %s  spread %.3e", gpu,
                 "%.6f" % st.median(v), max(v) - min(v))
    log.info("  within a GPU  %.3e", within_gpu)
    log.info("  across GPUs   %.3e   <- the tolerance any cross-session gate needs",
             across)

    log.info("")
    log.info("VERDICT: %s", verdict)

    result = {
        "ticket": "E-006", "model": R.MODEL, "layer": a.layer,
        "nnsight": __import__("nnsight").__version__,
        "readings": len(rows), "n_prompts": 2 * len(anchors),
        "distinct_values": len(sigs), "distinct_gpus": len(gpus),
        "values_by_gpu": {g: sorted(v) for g, v in by_gpu.items()},
        "gpus_by_value": {s: sorted(v) for s, v in by_sig.items()},
        "partitions_by_gpu": partitions,
        "anchor_worst_deviation_overall": max(r["anchor_worst_deviation"] for r in rows),
        "runtime_median": st.median([r["runtime"] for r in rows if r["runtime"]]),
        "floor_median_by_gpu": {g: st.median(v) for g, v in floor_by_gpu.items()},
        "floor_spread_within_gpu": within_gpu,
        "floor_spread_across_gpus": across,
        "e001_published_floor": 0.0809,
        "verdict": verdict,
        "rows": rows,
        "note": "Delivery of a measurement, not of an edit. Nothing is edited here.",
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
