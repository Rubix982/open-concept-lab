"""
E-016: causal (IIA) mediation of propagation — subject-site interchange, local gpt2-small.

For each entailed neighbour of a ROME edit:
  clean answer (BASE)  →  apply edit  →  edited answer (SOURCE) + capture the
  subject-token residual at layer L  →  restore  →  run BASE clean but PATCH that
  residual in at (subject-pos, L).  IIA = does the single-site patch REPRODUCE the
  edited answer, given the neighbour was affected? = propagation mediated by the
  neighbour reading the edited subject site. Control = patch a RANDOM position.

Run from repo root in the EDIT venv:
    source .venv-edit/bin/activate
    N_EDITS=30 python experiments/edit_propagation/iia_scale.py
Out: results/final/{data/iia_scale.json, tables/iia_scale.txt}
"""
import json
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/code/EasyEdit"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer
from easyeditor import ROMEHyperParams, BaseEditor

import easyeditor.editors.editor as _ee
_ee.restore_after_edit = lambda *a, **k: None

HERE = Path(__file__).resolve().parent
CFG = os.environ.get("ROME_CFG", "rome_gpt2_mom2.yaml")
N_EDITS = int(os.environ.get("N_EDITS", "30"))
SEED = int(os.environ.get("SEED", "1538"))
LAYERS = [int(x) for x in os.environ.get("IIA_LAYERS", "5,7,9").split(",")]
RE_FILE = Path(os.environ.get("RE_FILE",
    str(Path.home() / "code" / "RippleEdits" / "data" / "benchmark" / "popular.json")))
FINAL = HERE.parent.parent / "results" / "final"
(FINAL / "data").mkdir(parents=True, exist_ok=True)
(FINAL / "tables").mkdir(parents=True, exist_ok=True)

CRIT = {"logical_generalization": "1hop", "compositionality_i": "2hop",
        "compositionality_ii": "2hop", "subject_aliasing": "paraphrase"}   # entailed only


def norm(k):
    return k.strip().lower().replace(" ", "_")


def parse_edit(entry):
    ed = entry.get("edit") or {}
    p_new = ed.get("prompt")
    p_old = (ed.get("original_fact") or {}).get("prompt")
    if not p_new or not p_old:
        return None
    i = 0
    while i < len(p_new) and i < len(p_old) and p_new[i] == p_old[i]:
        i += 1
    cloze = p_new[:i].rstrip()
    new_t = p_new[i:].strip().rstrip(".").strip()
    if not cloze or not new_t or cloze == p_new:
        return None
    return cloze, new_t


def subject_of(cloze):
    s = cloze
    for tail in (" is", " are", " was", " were"):
        j = s.rfind(tail)
        if j != -1:
            s = s[:j]
    parts = s.split(" of ")
    return (parts[-1] if len(parts) > 1 else s.split()[-1]).strip().strip(".,")


def neighbours_of(entry):
    out = []
    for k, v in entry.items():
        t = CRIT.get(norm(k))
        if t is None or not isinstance(v, list):
            continue
        for g in v:
            if isinstance(g, dict):
                for q in g.get("test_queries") or []:
                    anss = q.get("answers") or []
                    val = anss[0].get("value") if anss and isinstance(anss[0], dict) else None
                    if q.get("prompt") and val:
                        out.append((t, q["prompt"], val))
    return out[:12]   # more neighbours per (expensive) edit — amortize the edit cost


hparams = ROMEHyperParams.from_hparams(str(HERE / CFG))
tok = AutoTokenizer.from_pretrained(hparams.model_name)
editor = BaseEditor.from_hparams(hparams)
model = editor.model
DEV = next(model.parameters()).device
EDIT_LAYER = hparams.layers[0]
wref = model.transformer.h[EDIT_LAYER].mlp.c_proj.weight
rng = random.Random(SEED)


def subj_last_pos(prompt, subject):
    """Token index of the subject's last token in the prompt (offset mapping)."""
    enc = tok(prompt, return_offsets_mapping=True)
    ci = prompt.lower().rfind(subject.lower())
    if ci < 0:
        return None
    cj = ci + len(subject)
    pos = [i for i, (a, b) in enumerate(enc["offset_mapping"]) if a < cj and b > ci]
    return pos[-1] if pos else None


@torch.no_grad()
def argmax_tok(prompt, patch=None):
    """argmax next token; patch=(layer, pos, vec) injects vec at (layer,pos) residual."""
    ids = tok(prompt, return_tensors="pt").to(DEV)
    handle = None
    if patch is not None:
        L, pos, vec = patch

        def hook(mod, inp, out):
            h = _h(out)
            h[:, pos, :] = vec
            return _wrap(out, h)
        handle = model.transformer.h[L].register_forward_hook(hook)
    try:
        logits = model(**ids).logits[0, -1]
    finally:
        if handle:
            handle.remove()
    return tok.decode(int(logits.argmax())).strip()


@torch.no_grad()
def answer_and_capture(prompt, pos, layers):
    """One forward on the (edited) model: capture residual@pos per layer AND the answer."""
    ids = tok(prompt, return_tensors="pt").to(DEV)
    store, handles = {}, []
    for L in layers:
        def mk(L):
            def hook(mod, inp, out):
                store[L] = _h(out)[:, pos, :].detach().clone()
            return hook
        handles.append(model.transformer.h[L].register_forward_hook(mk(L)))
    try:
        logits = model(**ids).logits[0, -1]
    finally:
        for h in handles:
            h.remove()
    return tok.decode(int(logits.argmax())).strip(), store


def _h(out):
    """Block hook output is a tensor (transformers 5.5.4) or a tuple (older)."""
    return out[0] if isinstance(out, tuple) else out


def _wrap(out, h):
    return ((h,) + tuple(out[1:])) if isinstance(out, tuple) else h


def has(a, b):
    return bool(a) and bool(b) and b.strip().lower()[:12] in a.lower()


entries = json.loads(RE_FILE.read_text())
random.Random(SEED).shuffle(entries)

rows = []
done = 0
for entry in entries:
    if done >= N_EDITS:
        break
    pe = parse_edit(entry)
    if not pe:
        continue
    cloze, new_t = pe
    subj = subject_of(cloze)
    if subj not in cloze:
        continue
    nbrs = neighbours_of(entry)
    # keep only neighbours where the subject is locatable
    nbrs = [(t, p, e, subj_last_pos(p, subj)) for (t, p, e) in nbrs]
    nbrs = [n for n in nbrs if n[3] is not None]
    if not nbrs:
        continue

    # 1) clean answers (before edit)
    clean = {p: argmax_tok(p) for (_, p, _, _) in nbrs}

    # 2) edit, confirm efficacy, capture edited answers + residuals
    saved = wref.detach().clone()
    try:
        editor.edit(prompts=[cloze], target_new=[new_t], subject=[subj],
                    sequential_edit=False, verbose=False)
    except Exception as e:
        print(f"  edit err {type(e).__name__}", flush=True)
        with torch.no_grad():
            wref.copy_(saved)
        continue
    if not has(argmax_tok(cloze), new_t):          # efficacy filter
        with torch.no_grad():
            wref.copy_(saved)
        continue
    done += 1
    edited, caps = {}, {}   # one forward per neighbour: answer + residual capture
    for (_, p, _, pos) in nbrs:
        edited[p], caps[p] = answer_and_capture(p, pos, LAYERS)

    # 3) restore clean weights
    with torch.no_grad():
        wref.copy_(saved)

    # 4) clean + patch (subject-pos and random control pos)
    print(f"[{done}] {subj!r} -> {new_t!r}  nbrs={len(nbrs)}", flush=True)
    for (typ, p, expected, pos) in nbrs:
        n_tok = len(tok(p)["input_ids"])
        others = [i for i in range(n_tok) if i != pos]
        ctrl_pos = rng.choice(others) if others else pos
        affected = edited[p] != clean[p]
        rec = {"type": typ, "prompt": p, "subject": subj, "target_new": new_t,
               "expected": expected, "clean": clean[p], "edited": edited[p],
               "affected": affected, "subj_pos": pos}
        for L in LAYERS:
            patched = argmax_tok(p, patch=(L, pos, caps[p][L]))
            ctrl = argmax_tok(p, patch=(L, ctrl_pos, caps[p][L]))
            rec[f"patch_L{L}"] = patched
            rec[f"ctrl_L{L}"] = ctrl
            rec[f"mediated_L{L}"] = bool(affected and patched == edited[p])
            rec[f"ctrl_repro_L{L}"] = bool(affected and ctrl == edited[p])
        rows.append(rec)
    (FINAL / "data" / "iia_scale.json").write_text(json.dumps(rows, indent=1))

# ── summary: IIA (subject-patch reproduces edit) vs control, by hop, ±95% CI ───
import math


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


HOPS = ["paraphrase", "1hop", "2hop"]
lines = [f"Causal IIA (subject-site interchange) · {hparams.model_name} · edits={done} "
         f"· rows={len(rows)} · layers={LAYERS}",
         "IIA = P(subject-patch reproduces edited answer | neighbour affected) ± 95% Wilson CI. "
         "ctrl = same at a random position (should be ~0).", ""]
aff = [r for r in rows if r["affected"]]
lines.append(f"affected neighbours (edit changed the answer): {len(aff)}/{len(rows)}")
for L in LAYERS:
    lines.append(f"\n  layer {L}:")
    for h in ["ALL"] + HOPS:
        sub = aff if h == "ALL" else [r for r in aff if r["type"] == h]
        if not sub:
            continue
        mk = sum(r[f"mediated_L{L}"] for r in sub)
        ck = sum(r[f"ctrl_repro_L{L}"] for r in sub)
        mp, mlo, mhi = wilson(mk, len(sub))
        cp, _, _ = wilson(ck, len(sub))
        lines.append(f"    {h:11s} n={len(sub):>3}  IIA={mp:.0%} [{mlo:.0%},{mhi:.0%}]  "
                     f"ctrl={cp:.0%}")
report = "\n".join(lines)
(FINAL / "tables" / "iia_scale.txt").write_text(report)
print("\n" + report)
print(f"\nSaved → {FINAL/'data'/'iia_scale.json'}, {FINAL/'tables'/'iia_scale.txt'}")
