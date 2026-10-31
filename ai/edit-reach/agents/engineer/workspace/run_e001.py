"""E-001 · Does predicted reach predict measured movement?

Reads the coefficient for every probe on the UNEDITED model, then measures how
far the model's own top answer moves when the edit is applied, and correlates
the two.

**No `v*` is optimised here, and that is not a shortcut.** [E-047] established
that `compute_v` cannot run remotely on nnsight 0.8.1 — NDIF refuses the
gradient of any tensor the model consumed, at every depth, and no arrangement of
our code moves that line. What survives is everything that reads the [E-014]
delta cache, which holds `k*` and `delta_v` for 42 subjects under both a real
and a same-subject control edit. So the subject set is not a choice: it is the
set that can still be edited at all. The probe set is anchored to those exact
case ids for the same reason — a free draw from the same relation under the same
seed overlapped them by 2 of 42.

**Batched, because round trips are the budget.** E-046 traced one prompt at a
time, which here would be 495 items x 3 conditions x ~10s of queue. Right-padded
batches of 200 make that nine traces. The cost is that the final real token sits
at `length - 1` rather than at `-1`, so the gather is explicit.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from editreach.arch import key_site                              # noqa: E402
from editreach.coefficient import Regime, coefficient_for        # noqa: E402
from editreach.logs import setup                                 # noqa: E402
from editreach.remote import connect, encode_prompts, quiet_stdout, retrying  # noqa: E402
from editreach.rome import LAYER, subject_last_index             # noqa: E402

MODEL = "meta-llama/Llama-3.1-8B"
ANCHOR_BAND = (0.999, 1.001)
BOOTSTRAP = 10_000
SEED = 1538

log = setup("E-001")


# --------------------------------------------------------------------------- cache

def load_edit_cache(edit_slice: Path) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor]]:
    """`k*` and `delta_v` per `"<case_id>|real"` / `"<case_id>|ctl"`, from [E-014]."""
    c = edit_slice / "results" / "cache"
    ks = torch.load(c / "E014_kstar_L5_s1538.pt", map_location="cpu", weights_only=False)
    dv = torch.load(c / "E014_deltas_L5_s1538.pt", map_location="cpu", weights_only=False)
    if set(ks) != set(dv):
        raise ValueError("kstar and delta caches disagree on which edits exist")
    return ks, dv


# --------------------------------------------------------------- remote primitives

def read_coefficients(model, items: list[dict], ks: dict, *, layer: int) -> None:
    """Fill `item["coefficient"]` in place. Unedited model; one call per subject."""
    by_subject: dict[str, list[dict]] = {}
    for it in items:
        by_subject.setdefault(it["case_id"], []).append(it)

    tok = model.tokenizer
    for cid, group in by_subject.items():
        k_star = ks[f"{cid}|real"].float()
        denom = float(k_star @ k_star)
        prompts = [g["prompt"] for g in group]
        # The item's own occurrence, never the default: the repetition family
        # exists because the first mention is sometimes the wrong one.
        positions = [subject_last_index(tok, g["prompt"], g["subject"],
                                        occurrence=g.get("occurrence", 0))
                     for g in group]
        got = coefficient_for(model, prompts, positions, u=k_star, denom=denom,
                              layer=layer, remote=True)
        for g, c in zip(group, got):
            g["coefficient"] = c.value
            g["position"] = c.position
        log.info("coefficients read for case %s (%d probes)", cid, len(group))


def top1_batch(model, prompts: list[str], *, layer: int,
               edit: tuple[torch.Tensor, float, torch.Tensor] | None) -> list[tuple[int, float]]:
    """`(top-1 token id, its probability)` at each prompt's final real token.

    `edit` is `(u, denom, delta_v)` applied inline. The intervention is written
    here rather than in a helper: nnsight compiles the source of the frame that
    enters `model.trace`, so a hooked write inside a called function is silently
    dropped (`rome.APPLY_IDIOM`).
    """
    ids, lengths = encode_prompts(model, prompts)
    last = torch.tensor([n - 1 for n in lengths])
    rows = torch.arange(len(prompts))

    def step():
        with quiet_stdout(), model.trace(ids, remote=True):
            if edit is not None:
                u_cpu, den, dv_cpu = edit
                dp = key_site(model, layer)
                kk = dp.input
                uu = u_cpu.to(kk.device, kk.dtype)
                dp.output = dp.output + ((kk @ uu) / den).unsqueeze(-1) \
                                        * dv_cpu.to(kk.device, kk.dtype)
            # Right padding puts the final real token at length-1, not -1.
            probs = model.lm_head.output[rows, last].softmax(-1)
            vals = probs.max(-1).values.save()
            idx = probs.argmax(-1).save()
        return [int(i) for i in idx], [float(v) for v in vals]

    idx, vals = retrying(step, what=f"top1 x{len(prompts)}"
                                    f"{' (edited)' if edit else ''}")
    return list(zip(idx, vals))


def prob_of(model, prompts: list[str], token_ids: list[int], *, layer: int,
            edit: tuple[torch.Tensor, float, torch.Tensor] | None) -> list[float]:
    """Probability of a GIVEN token at each prompt's final real token.

    Movement is measured on the token the model preferred BEFORE the edit, so
    the post-edit pass must be told which token that was rather than reporting
    its own new favourite.
    """
    ids, lengths = encode_prompts(model, prompts)
    last = torch.tensor([n - 1 for n in lengths])
    rows = torch.arange(len(prompts))
    want = torch.tensor(token_ids)

    def step():
        with quiet_stdout(), model.trace(ids, remote=True):
            if edit is not None:
                u_cpu, den, dv_cpu = edit
                dp = key_site(model, layer)
                kk = dp.input
                uu = u_cpu.to(kk.device, kk.dtype)
                dp.output = dp.output + ((kk @ uu) / den).unsqueeze(-1) \
                                        * dv_cpu.to(kk.device, kk.dtype)
            probs = model.lm_head.output[rows, last].softmax(-1)
            got = probs[rows, want].save()
        return [float(x) for x in got]

    return retrying(step, what=f"p(token) x{len(prompts)}"
                               f"{' (edited)' if edit else ''}")


# ------------------------------------------------------------------------ analysis

def spearman(xs: list[float], ys: list[float]) -> float:
    def rank(v: list[float]) -> list[float]:
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):                       # average ties, or ties inflate rho
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else float("nan")


def bootstrap_ci(xs: list[float], ys: list[float], *, n: int = BOOTSTRAP,
                 seed: int = SEED) -> tuple[float, float]:
    import random
    rng = random.Random(seed)
    k = len(xs)
    if k < 3:
        return (float("nan"), float("nan"))
    out = []
    for _ in range(n):
        pick = [rng.randrange(k) for _ in range(k)]
        out.append(spearman([xs[i] for i in pick], [ys[i] for i in pick]))
    out = sorted(v for v in out if v == v)
    if not out:
        return (float("nan"), float("nan"))
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1])


# ---------------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probes", type=Path, default=Path("probes/generated.json"))
    ap.add_argument("--edit-slice", type=Path,
                    default=Path(__file__).resolve().parents[4] / "edit-slice")
    ap.add_argument("--layer", type=int, default=LAYER)
    ap.add_argument("--batch", type=int, default=200)
    ap.add_argument("--out", type=Path, default=Path("results/E-001-predicted-vs-measured.json"))
    ap.add_argument("--checkpoint", type=Path,
                    default=Path("results/cache/E001_partial.json"),
                    help="per-item results, written after every batch. A run that "
                         "dies resumes from here instead of starting over.")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore any checkpoint and start over")
    ap.add_argument("--anchors-only", action="store_true",
                    help="run the gate and stop. Cheap, and it is the one quantity "
                         "known analytically, so a deviation means the pipeline is "
                         "wrong and every later number would look plausible anyway.")
    a = ap.parse_args()

    payload = json.loads(a.probes.read_text())
    items, meta = payload["items"], payload["meta"]
    if not meta.get("anchored_to_case_ids"):
        raise SystemExit("probe set is not anchored to the cached case ids; "
                         "regenerate with --case-ids probes/e014_case_ids.json")

    ks, dv = load_edit_cache(a.edit_slice)
    # Each item carries its own case id. Resolving one from the owner's NAME used
    # to work until two subjects turned out to hold two CounterFact records each,
    # at which point the lookup quietly returned the wrong edit.
    for it in items:
        it["owner"] = it["id"].split("/")[0].replace("_", " ")
        if not it.get("case_id"):
            raise SystemExit(f"{it['id']} carries no case_id; regenerate the probe set")
    missing = {it["case_id"] for it in items} - {k.split("|")[0] for k in ks}
    if missing:
        raise SystemExit(f"no cached edit for case ids {sorted(missing)}")

    model = connect(MODEL)

    # --- gate ---------------------------------------------------------------
    anchors = [it for it in items if it["id"].endswith("/anchor-prefix")]
    read_coefficients(model, anchors, ks, layer=a.layer)
    worst = max(abs(it["coefficient"] - 1.0) for it in anchors)
    inside = all(ANCHOR_BAND[0] <= it["coefficient"] <= ANCHOR_BAND[1] for it in anchors)
    log.info("anchor gate: %d items, worst deviation from 1.000 = %.3e", len(anchors), worst)
    if not inside:
        bad = [(it["id"], it["coefficient"]) for it in anchors
               if not ANCHOR_BAND[0] <= it["coefficient"] <= ANCHOR_BAND[1]]
        log.error("anchor gate FAILED for %d items, e.g. %s", len(bad), bad[:3])
        raise SystemExit("the analytic anchors did not pin. Fix the pipeline — "
                         "padding, position, tokenisation or architecture path — "
                         "before reading anything else.")
    if a.anchors_only:
        log.info("gate passed; stopping as asked")
        return 0

    # --- predicted reach ----------------------------------------------------
    rest = [it for it in items if not it["id"].endswith("/anchor-prefix")]
    read_coefficients(model, rest, ks, layer=a.layer)

    # --- measured movement --------------------------------------------------
    # CLAUDE.md: long runs must be resumable. NDIF's websocket drops under load
    # and a 495-item run is three passes over three conditions; losing it at
    # item 400 is losing the session, not a retry.
    done: dict[str, dict] = {}
    if a.checkpoint.exists() and not a.fresh:
        done = {d["id"]: d for d in json.loads(a.checkpoint.read_text())["items"]}
        log.info("resuming: %d of %d items already scored", len(done), len(items))
    for it in items:
        if it["id"] in done:
            it.update({k: v for k, v in done[it["id"]].items()
                       if k in ("base_token", "p_base", "p_real", "p_ctl")})

    def save_checkpoint() -> None:
        a.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        scored = [i for i in items if "p_ctl" in i]
        a.checkpoint.write_text(json.dumps({"items": scored}, indent=1))

    pending = [i for i in items if "p_ctl" not in i]
    for start in range(0, len(pending), a.batch):
        chunk = pending[start:start + a.batch]
        prompts = [c["prompt"] for c in chunk]
        base = top1_batch(model, prompts, layer=a.layer, edit=None)
        for c, (tid, p) in zip(chunk, base):
            c["base_token"] = tid
            c["p_base"] = p
        log.info("base scored for %d items", len(chunk))

        for kind in ("real", "ctl"):
            # One edit per subject, so the chunk is grouped before tracing.
            for cid in sorted({c["case_id"] for c in chunk}):
                sub = [c for c in chunk if c["case_id"] == cid]
                k_star = ks[f"{cid}|{kind}"].float()
                edit = (k_star, float(k_star @ k_star), dv[f"{cid}|{kind}"].float())
                got = prob_of(model, [s["prompt"] for s in sub],
                              [s["base_token"] for s in sub], layer=a.layer, edit=edit)
                for s, p in zip(sub, got):
                    s[f"p_{kind}"] = p
            log.info("%s scored for %d items", kind, len(chunk))
        save_checkpoint()
        log.info("checkpoint: %d of %d items complete",
                 sum(1 for i in items if "p_ctl" in i), len(items))

    for it in items:
        it["movement"] = it["p_base"] - it["p_real"]
        it["control_movement"] = it["p_base"] - it["p_ctl"]
        it["excess"] = it["movement"] - it["control_movement"]

    # --- correlate ----------------------------------------------------------
    def rho_block(subset: list[dict]) -> dict:
        xs = [s["coefficient"] for s in subset]
        return {
            "n": len(subset),
            "raw": {"rho": spearman(xs, [s["movement"] for s in subset]),
                    "ci95": bootstrap_ci(xs, [s["movement"] for s in subset])},
            # The number C-001 turns on. The raw one is inflated by generic
            # subject-keyed instability, which the same-subject control removes.
            "excess": {"rho": spearman(xs, [s["excess"] for s in subset]),
                       "ci95": bootstrap_ci(xs, [s["excess"] for s in subset])},
        }

    families = sorted({it["family"] for it in items})
    result = {
        "ticket": "E-001", "model": MODEL, "layer": a.layer, "seed": SEED,
        "probe_set": {"path": str(a.probes), **{k: meta[k] for k in
                      ("seed", "relation", "items", "subjects", "anchored_to_case_ids")}},
        "edits": {"source": "edit-slice [E-014] cache", "v_star_optimised_here": False,
                  "why": "compute_v cannot run remotely on nnsight 0.8.1 [E-047]"},
        "anchor_gate": {"n": len(anchors), "worst_deviation": worst, "passed": True},
        "overall": rho_block(items),
        "by_family": {f: rho_block([i for i in items if i["family"] == f]) for f in families},
        "items": items,
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=1))

    log.info("overall raw rho=%.3f %s | excess rho=%.3f %s",
             result["overall"]["raw"]["rho"], result["overall"]["raw"]["ci95"],
             result["overall"]["excess"]["rho"], result["overall"]["excess"]["ci95"])
    for f in families:
        b = result["by_family"][f]
        log.info("  %-16s n=%3d  excess rho=%+.3f %s", f, b["n"],
                 b["excess"]["rho"], b["excess"]["ci95"])
    log.info("written to %s", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
