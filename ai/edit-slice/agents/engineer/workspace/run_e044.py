"""E-044 · Does the subject key still reorient when context cannot reach it? [T-095]

[E-041] found the MLP writes more of the divergence than attention at every depth — but the
MLP's input comes through attention, so a context-driven reorientation routed through the
MLP looks identical to a local one. This is the causal test.

[T-095] ruled out two implementations: zeroing `self_attn.output` deletes RoPE with the
context, and truncation ablates nothing. The third works and was probed before the ticket
was written — mask the non-subject prefix via `attention_mask`, and pin `position_ids` so
RoPE cannot shift when the mask does.

**Because positions are pinned, the subject keeps its own index in each form. So whatever
divergence survives the mask is POSITIONAL, not contextual.**

CORRECTNESS GATE: the edit form has no non-subject prefix, so masking it changes nothing
and its keys must reproduce the unmasked run EXACTLY. If they move, the intervention is
doing something other than advertised and the run aborts. `LOOP.md` rule 4 — seven harness
defects in two days each returned a plausible value rather than an error.

DELIVERY, NOT EFFECT. [E-028d], 2.96x.
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
from edit import LAYER, subject_last_index  # noqa: E402
from logs import setup  # noqa: E402
from remote import _quiet_stdout, connect, retrying  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
MODEL = "meta-llama/Llama-3.1-8B"
PROBE = [0, 3, 5, 8, 12, 16, 24, 31]
DEEP = [16, 24, 31]
EDIT_FORM = "{} was born in the city of"
FORMS = {
    "edit form":      EDIT_FORM,
    "late clause":    "The city where {} was born is",
    "possessive":     "The birthplace of {} is the city of",
    "matched filler": "Among other things {} was born in the city of",
}
NAMES = list(FORMS)
NECESSARY, NOT_NECESSARY = 0.95, 0.75
GATE_TOL = 1e-4

E020_COSINE = {0: 0.984, 3: 0.962, 5: 0.951, 8: 0.898, 12: 0.812,
                16: 0.733, 24: 0.598, 31: 0.471}


def cos(a, b) -> float:
    na, nb = float(a.norm()), float(b.norm())
    return float(a @ b) / (na * nb) if na and nb else 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=16)
    a = ap.parse_args()

    chains = {c["seed_case_id"]: c for c in json.loads(
        (ROOT / "probes" /
         "chains_gated_meta-llama_Llama-3.1-8B.json").read_text())["chains"]}
    ks = torch.load(ROOT / "results" / "cache" / f"E014_kstar_L{LAYER}_s1538.pt")
    # The cache supplies only the subject LIST, but a partial one would silently shrink
    # the study — [E-033]'s lesson, and the same guard [E-041] carries.
    real = [k.split("|")[0] for k in ks if k.endswith("|real")]
    want = set(real[: a.n])
    missing = want - set(chains)
    cids = [c for c in real[: a.n] if c in chains]
    if missing:
        print(f"  {len(missing)} of {a.n} cached ids have no chain record")
    if len(cids) < a.n:
        raise SystemExit(f"asked for {a.n} subjects, got {len(cids)}; refusing a smaller "
                         f"study than the ticket scoped")

    log = setup("run_e044", config={
        "ticket": "E-044", "thread": "T-095", "model": MODEL, "n_subjects": len(cids),
        "forms": NAMES, "probe_layers": PROBE,
        "intervention": "attention_mask zeroes [1, subject_start); position_ids pinned",
        "gate": "edit form must reproduce its unmasked keys exactly",
        "reading": "surviving divergence is POSITIONAL — RoPE — not contextual"})
    log.info("%d subjects, %d forms, masked vs unmasked in one batch", len(cids), len(NAMES))

    m = connect(MODEL)
    tok = m.tokenizer
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    # acc[masked][form][layer] -> cosines to the edit form's key in the SAME condition
    acc = {cond: {f: {L: [] for L in PROBE} for f in NAMES} for cond in (0, 1)}
    gate_max = 0.0
    n_masked: dict[str, int] = {}

    for n, cid in enumerate(cids, 1):
        subj = chains[cid]["inner_1"]["subject"]
        prompts = [t.format(subj) for t in FORMS.values()]
        ids = [tok(p).input_ids for p in prompts]
        try:
            idxs = [subject_last_index(tok, p, subj) for p in prompts]
        except ValueError:
            continue
        # where the subject STARTS, so the prefix is [1, start)
        starts = []
        for p, x in zip(prompts, ids):
            cut = p.index(subj)
            starts.append(len(tok(p[:cut]).input_ids) if cut else 1)
        width = max(len(x) for x in ids)

        # rows 0..3 unmasked, rows 4..7 the same prompts masked
        k = len(prompts)
        batch = torch.full((2 * k, width), pad, dtype=torch.long)
        mask = torch.zeros((2 * k, width), dtype=torch.long)
        for j, x in enumerate(ids):
            batch[j, : len(x)] = torch.tensor(x)
            batch[k + j, : len(x)] = torch.tensor(x)
            mask[j, : len(x)] = 1
            mask[k + j, : len(x)] = 1
            lo, hi = 1, max(1, starts[j])
            mask[k + j, lo:hi] = 0
            n_masked[NAMES[j]] = hi - lo
        pos = torch.arange(width).unsqueeze(0).repeat(2 * k, 1)

        def once(b=batch, mk=mask, ps=pos):
            with _quiet_stdout(), m.trace({"input_ids": b, "attention_mask": mk,
                                           "position_ids": ps}, remote=True):
                k0 = m.model.layers[0].mlp.down_proj.input.half().save()
                k3 = m.model.layers[3].mlp.down_proj.input.half().save()
                k5 = m.model.layers[5].mlp.down_proj.input.half().save()
                k8 = m.model.layers[8].mlp.down_proj.input.half().save()
                k12 = m.model.layers[12].mlp.down_proj.input.half().save()
                k16 = m.model.layers[16].mlp.down_proj.input.half().save()
                k24 = m.model.layers[24].mlp.down_proj.input.half().save()
                k31 = m.model.layers[31].mlp.down_proj.input.half().save()
            saved = {"0": k0, "3": k3, "5": k5, "8": k8, "12": k12, "16": k16, "24": k24, "31": k31}
            with _quiet_stdout():
                return {int(key): v.float() for key, v in saved.items()}

        got = retrying(once, what=f"{subj!r}")
        for L in PROBE:
            h = got[L]
            # GATE: the edit form masks nothing, so masked and unmasked must agree.
            drift = float((h[0, idxs[0]] - h[k, idxs[0]]).abs().max())
            gate_max = max(gate_max, drift)
            for cond in (0, 1):
                ref = h[cond * k + 0, idxs[0]]
                for j, name in enumerate(NAMES):
                    acc[cond][name][L].append(cos(h[cond * k + j, idxs[j]], ref))
        if n % 4 == 0 or n == len(cids):
            log.info("  %d/%d subjects", n, len(cids))

    log.info("")
    log.info("prefix tokens masked per form: %s", n_masked)
    log.info("GATE — largest edit-form drift between masked and unmasked: %.2e", gate_max)
    if gate_max > GATE_TOL:
        log.error("GATE FAILED — the edit form moved under a mask that masks nothing. The "
                  "intervention is not doing what it claims (silently shifted RoPE, or "
                  "masked more than the prefix). No number below is trustworthy.")
        raise SystemExit(1)
    log.info("gate passed: the edit form is untouched, so the mask does only what it says")

    report(acc, n_masked, gate_max, log)


def report(acc, n_masked, gate_max, log, out=None) -> None:
    # `out` exists so a dry-run can redirect this file. Without it the dry-run wrote
    # FAKE results to the real path — worse than the deletion bug it replaced.
    log.info("")
    log.info("E-044 — cosine to the edit form's key, with and without the prefix masked")
    log.info("surviving divergence is POSITIONAL: position_ids are pinned")
    verdicts = {}
    for name in NAMES:
        if name == "edit form":
            continue
        log.info("")
        log.info("%s  (%d prefix tokens masked)", name.upper(), n_masked.get(name, 0))
        log.info("%-8s%12s%12s%14s%12s", "layer", "unmasked", "masked", "div removed",
                 "E-020 cos")
        removed = []
        for L in PROBE:
            u = acc[0][name][L]
            k = acc[1][name][L]
            if not u or not k:
                continue
            mu, mk = st.median(u), st.median(k)
            # fraction of the ORIGINAL divergence (1 - cos) that masking removes
            fr = ((1 - mu) - (1 - mk)) / (1 - mu) if (1 - mu) > 1e-6 else float("nan")
            if L in DEEP:
                removed.append(fr)
            log.info("%-8d%12.3f%12.3f%14s%12.3f", L, mu, mk,
                     f"{fr:+.0%}" if fr == fr else "—", E020_COSINE.get(L, float("nan")))
        deep_k = st.median([st.median(acc[1][name][L]) for L in DEEP if acc[1][name][L]])
        verdicts[name] = (deep_k, st.median(removed) if removed else float("nan"))

    log.info("")
    if not verdicts:
        log.error("no form produced a comparison")
        return
    dk = st.median([v[0] for v in verdicts.values()])
    dr = st.median([v[1] for v in verdicts.values()])
    if dk >= NECESSARY:
        log.info("VERDICT: CONTEXT NECESSARY — masked cosine at depth is %.3f. Cutting "
                 "attention to the prefix removes the reorientation, so context mixing is "
                 "what does it and [E-041]'s direct-write reading was the wrong frame.", dk)
    elif dk <= NOT_NECESSARY:
        log.warning("VERDICT: CONTEXT NOT NECESSARY — masked cosine at depth is %.3f, and "
                    "masking removes only %.0f%% of the divergence. The key reorients with "
                    "context unreachable, so it is POSITIONAL, and [E-020]'s attention "
                    "account is wrong a second independent way.", dk, 100 * dr)
    else:
        log.info("VERDICT: PARTIAL — masked cosine at depth %.3f, and the mask removes "
                 "%.0f%% of the divergence. [E-041]'s matched-filler arm predicted ~40%%; "
                 "report the fraction, not a band.", dk, 100 * dr)

    out = out or ROOT / "results" / "E-044-context-ablation.json"
    out.write_text(json.dumps(
        {"ticket": "E-044", "thread": "T-095", "probe": PROBE, "gate_max_drift": gate_max,
          "masked_prefix_tokens": n_masked,
          "deep_masked_cosine": {k: v[0] for k, v in verdicts.items()},
          "deep_fraction_removed": {k: v[1] for k, v in verdicts.items()},
          "per_layer": {c: {f: {str(L): acc[c][f][L] for L in PROBE} for f in NAMES}
                        for c in (0, 1)}}, indent=1))
    log.info("written: %s", out.relative_to(ROOT))


if __name__ == "__main__":
    main()
