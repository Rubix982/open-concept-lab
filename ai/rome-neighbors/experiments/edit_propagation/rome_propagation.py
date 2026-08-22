"""
ROME propagation (3-way) — the real, specificity-preserving edit.

For each fact: ROME-edit it (EasyEdit, rank-1 + KL), then measure each neighbour
PRE vs POST → 3-way outcome (updated / stale / broken). Key question vs. our
wrecking-ball FT (88% broken, 94% locality destroyed): does ROME PRESERVE locality?

Self-contained (no ripplekit import — .venv-edit has no nnsight). Run in edit venv:
    source .venv-edit/bin/activate
    python experiments/edit_propagation/rome_propagation.py
Env: ROME_CFG (default rome_gpt2.yaml), N_EDITS (default 8), RE_FILE.
"""

import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/code/EasyEdit"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoTokenizer
from easyeditor import ROMEHyperParams, BaseEditor

HERE = Path(__file__).resolve().parent
CFG = os.environ.get("ROME_CFG", "rome_gpt2.yaml")
N_EDITS = int(os.environ.get("N_EDITS", "8"))
SEED = 1538
RE_FILE = Path(os.environ.get("RE_FILE",
    str(Path.home() / "code" / "RippleEdits" / "data" / "benchmark" / "popular.json")))
OUT = HERE.parent.parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

TYPES = ["paraphrase", "1hop", "2hop", "locality", "control"]
CRIT = {"logical_generalization": "1hop", "compositionality_i": "2hop",
        "compositionality_ii": "2hop", "subject_aliasing": "paraphrase",
        "relation_specificity": "locality", "relation_specifity": "locality",
        "forgetfulness": "control"}


def norm(k):
    return k.strip().lower().replace(" ", "_")


def parse_edit(entry):
    ed = entry.get("edit") or {}
    orig = ed.get("original_fact") or {}
    p_new, p_old = ed.get("prompt"), orig.get("prompt")
    if not p_new or not p_old:
        return None
    i = 0
    while i < len(p_new) and i < len(p_old) and p_new[i] == p_old[i]:
        i += 1
    cloze = p_new[:i].rstrip()
    new_t = p_new[i:].strip().rstrip(".").strip()
    if not cloze or not new_t or cloze == p_new:
        return None
    subj = ed.get("subject_id")
    return cloze, new_t, subj


def neighbours_of(entry):
    out = []
    for k, v in entry.items():
        t = CRIT.get(norm(k))
        if t is None or not isinstance(v, list):
            continue
        for g in v:
            if not isinstance(g, dict):
                continue
            for q in g.get("test_queries") or []:
                anss = q.get("answers") or []
                val = anss[0].get("value") if anss and isinstance(anss[0], dict) else None
                if q.get("prompt") and val:
                    out.append((t, q["prompt"], val))
    return out[:6]   # cap per edit


hparams = ROMEHyperParams.from_hparams(str(HERE / CFG))
tok = AutoTokenizer.from_pretrained(hparams.model_name)
editor = BaseEditor.from_hparams(hparams)
model = editor.model
DEV = next(model.parameters()).device
LAYER = hparams.layers[0]
wref = model.transformer.h[LAYER].mlp.c_proj.weight


@torch.no_grad()
def answer(prompt, max_new=6):
    ids = tok(prompt, return_tensors="pt").to(DEV)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids.input_ids.shape[1]:], skip_special_tokens=True).strip()


def _m(a, b):
    return b.lower()[:12] in a.lower()


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
    cloze, new_t, subj = pe
    nbrs = neighbours_of(entry)
    if not nbrs:
        continue

    pre = [answer(p) for _, p, _ in nbrs]           # PRE-edit answers
    saved = wref.detach().clone()                   # isolate this edit
    try:
        editor.edit(prompts=[cloze], target_new=[new_t],
                    subject=[cloze.split()[-1] if not subj else subj],
                    sequential_edit=False, verbose=False)
    except Exception as e:
        print(f"  edit failed: {type(e).__name__}", flush=True)
        with torch.no_grad():
            wref.copy_(saved)
        continue

    took = _m(answer(cloze), new_t)
    done += 1
    print(f"[edit {done}] {cloze[:50]!r} -> {new_t!r}  efficacy={'YES' if took else 'NO'}", flush=True)
    if took:
        for i, (typ, p, expected) in enumerate(nbrs):
            post = answer(p)
            if _m(post, expected):
                outcome = "updated"
            elif post.strip().lower() == pre[i].strip().lower():
                outcome = "stale"
            else:
                outcome = "broken"
            rows.append((typ, outcome))
    with torch.no_grad():
        wref.copy_(saved)               # restore clean weights

# ── table ───────────────────────────────────────────────────────────────────────
print("\n── ROME 3-way outcome by neighbour type ──")
print(f"{'type':12s}  {'n':>3}  {'updated':>8}  {'stale':>6}  {'broken':>7}")
lines = []
for t in ["ALL"] + TYPES:
    sub = rows if t == "ALL" else [o for (ty, o) in rows if ty == t]
    if t != "ALL":
        sub = [o for (ty, o) in rows if ty == t]
    else:
        sub = [o for (_, o) in rows]
    if not sub:
        continue
    c = Counter(sub)
    n = len(sub)
    line = (f"{t:12s}  {n:>3}  {c['updated']/n:>7.0%}  {c['stale']/n:>5.0%}  {c['broken']/n:>6.0%}")
    print(line)
    lines.append(line)

(OUT / "rome_propagation.txt").write_text(
    f"model={hparams.model_name} layer={LAYER} edits={done}\n" + "\n".join(lines))
print(f"\nSaved -> {OUT/'rome_propagation.txt'}")
print("KEY vs FT: if locality here is mostly STALE (unchanged) not BROKEN, ROME's")
print("rank-1+KL specificity works where our full-matrix FT destroyed locality (94% broken).")
