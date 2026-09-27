"""E-031 · Is the floor's dip near the edit layer real, or two coincidences? [T-083]

[E-027] noticed, without looking for it, that BOTH models' different-subject floors are
non-monotonic with a minimum near depth fraction 0.15 — Llama 0.082 at L5, GPT-J 0.155 at
L4 — which is approximately where ROME edits in both. The evidence was 4 points on Llama
and 6 on GPT-J at n=12-16: too coarse to tell a dip from sampling noise.

Five points below fraction 0.25 instead of two, n=20, both models.

    DIP                 each model's minimum falls inside fraction 0.05-0.25, sits below
                        BOTH neighbours by more than one SEM, and the two minima are
                        within 0.15 of each other in depth fraction
    NO DIP              flat/monotone across the window on either model, or the minimum
                        is within one SEM of its neighbours -> the [E-027] observation was
                        noise and comes out of §4.3's margin
    DIFFERENT LOCATION  both dip, more than 0.15 apart -> each is a fact about its model

**What a DIP would NOT license.** Nothing about ROME's layer choice. ROME selects its
layer by causal tracing, on a criterion with nothing to do with inter-subject separation.
Two quantities peaking at similar depths is a coincidence of location, not a mechanism —
establishing the connection would need the causal-tracing peak and the floor minimum shown
to MOVE TOGETHER across models, which needs causal tracing run on both. Not done here, not
proposed here, and no sentence in this run's entry may imply otherwise.
"""
from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from edit import subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402
from run_e027 import FORMS  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FRACTIONS = (0.00, 0.06, 0.10, 0.16, 0.23, 0.32, 0.55, 1.00)
LLAMA = ("meta-llama/Llama-3.1-8B", [0, 2, 3, 5, 7, 10, 17, 31])
GPTJ = ("EleutherAI/gpt-j-6b", [0, 2, 3, 4, 6, 9, 15, 27])
WINDOW = (0.05, 0.25)
SAME_LOCATION = 0.15


def keys_llama(m, batch, layers):
    """Saves are UNROLLED: a loop inside a trace body returns zero saves ([O-008])."""
    assert layers == [0, 2, 3, 5, 7, 10, 17, 31], "unrolled saves must match layers"

    def once():
        with _quiet_stdout(), m.trace(batch, remote=True):
            a0 = m.model.layers[0].mlp.down_proj.input.half().save()
            a2 = m.model.layers[2].mlp.down_proj.input.half().save()
            a3 = m.model.layers[3].mlp.down_proj.input.half().save()
            a5 = m.model.layers[5].mlp.down_proj.input.half().save()
            a7 = m.model.layers[7].mlp.down_proj.input.half().save()
            a10 = m.model.layers[10].mlp.down_proj.input.half().save()
            a17 = m.model.layers[17].mlp.down_proj.input.half().save()
            a31 = m.model.layers[31].mlp.down_proj.input.half().save()
        saved = {0: a0, 2: a2, 3: a3, 5: a5, 7: a7, 10: a10, 17: a17, 31: a31}
        with _quiet_stdout():
            return {L: v.float() for L, v in saved.items()}
    return once


def keys_gptj(m, batch, layers):
    assert layers == [0, 2, 3, 4, 6, 9, 15, 27], "unrolled saves must match layers"

    def once():
        with _quiet_stdout(), m.trace(batch, remote=True):
            a0 = m.transformer.h[0].mlp.fc_out.input.half().save()
            a2 = m.transformer.h[2].mlp.fc_out.input.half().save()
            a3 = m.transformer.h[3].mlp.fc_out.input.half().save()
            a4 = m.transformer.h[4].mlp.fc_out.input.half().save()
            a6 = m.transformer.h[6].mlp.fc_out.input.half().save()
            a9 = m.transformer.h[9].mlp.fc_out.input.half().save()
            a15 = m.transformer.h[15].mlp.fc_out.input.half().save()
            a27 = m.transformer.h[27].mlp.fc_out.input.half().save()
        saved = {0: a0, 2: a2, 3: a3, 4: a4, 6: a6, 9: a9, 15: a15, 27: a27}
        with _quiet_stdout():
            return {L: v.float() for L, v in saved.items()}
    return once


def sweep(name, layers, maker, subs, log):
    m = connect(name)
    n_layers = (getattr(m.config, "num_hidden_layers", None)
                or getattr(m.config, "n_layer"))
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    acc = {L: [] for L in layers}
    for n, subj in enumerate(subs, 1):
        # Same pairing rule as [E-018]/[E-027]: chain i against chain i+1. Fixed, not
        # averaged over — a different pairing gives different numbers.
        other = subs[n % len(subs)]
        if other == subj:
            continue
        prompts = [t.format(subj) for t in FORMS.values()] + [
            FORMS["edit form"].format(other)]
        owners = [subj] * len(FORMS) + [other]
        ids = [tok(p).input_ids for p in prompts]
        idxs = [subject_last_index(tok, p, s) for p, s in zip(prompts, owners)]
        width = max(len(x) for x in ids)
        batch = torch.full((len(ids), width), pad, dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)
        got = retrying(maker(m, batch, layers), what=f"{name} {subj!r}")
        for L in layers:
            a = got[L]
            kstar = a[0, idxs[0]]
            acc[L].append(float((a[-1, idxs[-1]] @ kstar) / float(kstar @ kstar)))
        if n % 5 == 0 or n == len(subs):
            log.info("  %s %d/%d", name, n, len(subs))
    return {L: acc[L] for L in layers}, n_layers


def sem(xs):
    return st.stdev(xs) / len(xs) ** 0.5 if len(xs) > 1 else float("inf")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=20)
    args = ap.parse_args()

    chains = json.loads((ROOT / "probes" /
                         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]
    subs = [c["inner_1"]["subject"] for c in chains if c["usable"]][: args.n]

    log = setup("run_e031", config={
        "ticket": "E-031", "thread": "T-083", "n": len(subs),
        "fractions": list(FRACTIONS), "models": [LLAMA[0], GPTJ[0]],
        "layers": {LLAMA[0]: LLAMA[1], GPTJ[0]: GPTJ[1]},
        "window": list(WINDOW), "measure": "different-subject coefficient; no edits",
        "pairing": "chain i vs chain i+1, fixed — same rule as [E-018]/[E-027]",
        "scope": "a dip licenses NOTHING about ROME's layer choice; see the docstring"})

    out = {}
    for (name, layers), maker in ((LLAMA, keys_llama), (GPTJ, keys_gptj)):
        acc, n_layers = sweep(name, layers, maker, subs, log)
        out[name] = {"n_layers": n_layers, "layers": layers,
                     "frac": {str(L): L / (n_layers - 1) for L in layers},
                     "mean": {str(L): st.mean(acc[L]) for L in layers},
                     "sem": {str(L): sem(acc[L]) for L in layers},
                     "per_subject": {str(L): acc[L] for L in layers}}
    report(out, log)


def report(out, log) -> None:
    log.info("")
    log.info("E-031 — different-subject floor against depth fraction")
    verdicts = {}
    for name, d in out.items():
        layers = d["layers"]
        log.info("")
        log.info("%s", name)
        log.info("  %-8s%9s%9s%9s", "layer", "frac", "floor", "±sem")
        for L in layers:
            log.info("  %-8s%9.2f%9.3f%9.3f", f"L{L}", d["frac"][str(L)],
                     d["mean"][str(L)], d["sem"][str(L)])
        inwin = [L for L in layers if WINDOW[0] <= d["frac"][str(L)] <= WINDOW[1]]
        lo = min(layers, key=lambda L: d["mean"][str(L)])
        in_window = d["frac"][str(lo)] >= WINDOW[0] and d["frac"][str(lo)] <= WINDOW[1]
        i = layers.index(lo)
        nbrs = [layers[j] for j in (i - 1, i + 1) if 0 <= j < len(layers)]
        below = all(d["mean"][str(lo)] + d["sem"][str(lo)] < d["mean"][str(nb)]
                    for nb in nbrs) if nbrs else False
        verdicts[name] = {"min_layer": lo, "min_frac": d["frac"][str(lo)],
                          "in_window": in_window, "below_neighbours_by_sem": below,
                          "window_layers": inwin}
        log.info("  minimum at L%d (fraction %.2f) — in window: %s · below both "
                 "neighbours by >1 SEM: %s", lo, d["frac"][str(lo)], in_window, below)

    log.info("")
    names = list(out)
    a, b = verdicts[names[0]], verdicts[names[1]]
    apart = abs(a["min_frac"] - b["min_frac"])
    if not (a["in_window"] and b["in_window"]):
        log.warning("VERDICT: NO DIP — the minimum falls outside fraction %.2f-%.2f on at "
                    "least one model (%s %.2f, %s %.2f). [E-027]'s observation does not "
                    "survive finer spacing and the sentence comes out of §4.3's margin.",
                    *WINDOW, names[0], a["min_frac"], names[1], b["min_frac"])
    elif not (a["below_neighbours_by_sem"] and b["below_neighbours_by_sem"]):
        log.warning("VERDICT: NO DIP — the minimum is inside the window on both models but "
                    "within one SEM of its neighbours on at least one (%s %s, %s %s). "
                    "That is a wobble, not a dip; it comes out of §4.3's margin.",
                    names[0], a["below_neighbours_by_sem"],
                    names[1], b["below_neighbours_by_sem"])
    elif apart > SAME_LOCATION:
        log.info("VERDICT: DIFFERENT LOCATION — both models dip, but %.2f apart in depth "
                 "fraction (>%.2f). Each is a fact about its own model; the shared-"
                 "coincidence claim dies even though both curves are non-monotonic.",
                 apart, SAME_LOCATION)
    else:
        log.info("VERDICT: DIP — both minima fall in fraction %.2f-%.2f, both sit below "
                 "their neighbours by more than one SEM, and they are %.2f apart. "
                 "Different subjects are maximally separated at the subject position at "
                 "roughly this depth, in two architectures.", *WINDOW, apart)
        log.warning("SCOPE: this licenses NOTHING about ROME's layer choice. ROME selects "
                    "its layer by causal tracing, on a criterion unrelated to "
                    "inter-subject separation; a coincidence of location is not a "
                    "mechanism. Claiming the connection needs the tracing peak and this "
                    "minimum shown to MOVE TOGETHER across models — not run, not "
                    "proposed. Do not write that sentence.")

    f = ROOT / "results" / "E-031-floor-curve.json"
    f.write_text(json.dumps({"ticket": "E-031", "thread": "T-083",
                             "window": list(WINDOW), "verdicts": verdicts,
                             "models": out}, indent=1))
    log.info("written: %s", f.relative_to(ROOT))


if __name__ == "__main__":
    main()
