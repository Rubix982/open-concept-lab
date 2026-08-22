"""
E-012 (T-A) — Make a REAL edit, measure ground-truth propagation.

The pivotal correction: we cannot predict neighbours without editing first. So we
edit one fact, then measure each neighbour PRE vs POST → a per-neighbour label
(propagated / stale / broken). That table is the target every predictor (T-B)
will be measured against.

Edit method: FT-L — fine-tune ONLY one MLP layer's down-projection (the weights
ROME edits) with a few gradient steps to flip the fact. A recognized editing
baseline (FT/FT-L in ROME/MEMIT/MQuAKE); no covariance stats, no EasyEdit.
(EasyEdit/ROME hit a transformers-5.15 incompatibility — deferred, not needed for T-A.)

Editing needs gradients → fp32 on CPU (fp32 stalls loading to MPS on this M2).

Usage:
    source .venv/bin/activate
    python experiments/edit_propagation/edit_ft.py
Env: EDIT_MODEL (default gpt2-medium), N_EDITS (default 5), EDIT_LAYER, FT_STEPS.
"""

import json
import os
import re
from pathlib import Path

os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from ripplekit import config, data

MODEL = os.environ.get("EDIT_MODEL", "gpt2-medium")
N_EDITS = int(os.environ.get("N_EDITS", "5"))
FT_STEPS = int(os.environ.get("FT_STEPS", "25"))
FT_LR = float(os.environ.get("FT_LR", "5e-4"))
DEVICE = "cpu"   # editing needs fp32 grads; MPS fp32 stalls loading on this M2
OUT = config.RESULTS_DIR
OUT.mkdir(parents=True, exist_ok=True)

CRIT = config.CRITERION_TO_TYPE


def norm(k):
    return k.strip().lower().replace(" ", "_")


def parse_edit(entry):
    """Return (cloze, new_target, old_target) or None. cloze = shared prefix of
    the counterfactual and original statements; targets = their differing suffix."""
    ed = entry.get("edit") or {}
    orig = ed.get("original_fact") or {}
    p_new, p_old = ed.get("prompt"), orig.get("prompt")
    if not p_new or not p_old:
        return None
    # longest common prefix
    i = 0
    while i < len(p_new) and i < len(p_old) and p_new[i] == p_old[i]:
        i += 1
    cloze = p_new[:i].rstrip()
    new_t = p_new[i:].strip().rstrip(".").strip()
    old_t = p_old[i:].strip().rstrip(".").strip()
    if not cloze or not new_t or not old_t or cloze == p_new:
        return None
    return cloze, new_t, old_t


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
    return out


# ── model ─────────────────────────────────────────────────────────────────────
print(f"loading {MODEL} (fp32, {DEVICE})...", flush=True)
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float32).to(DEVICE).eval()
n_layer = model.config.n_layer
EDIT_LAYER = int(os.environ.get("EDIT_LAYER", str(n_layer // 3)))   # early-mid, ROME-ish
print(f"  {n_layer} layers; editing MLP c_proj at layer {EDIT_LAYER}\n", flush=True)


@torch.no_grad()
def answer(cloze: str, max_new=6) -> str:
    ids = tok(cloze, return_tensors="pt").to(DEVICE)
    out = model.generate(**ids, max_new_tokens=max_new, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids.input_ids.shape[1]:], skip_special_tokens=True).strip()


def knows(cloze: str, target: str) -> bool:
    return target.lower()[:12] in answer(cloze).lower()


def ft_edit(cloze: str, new_target: str):
    """FT-L: gradient steps on ONLY layer EDIT_LAYER's mlp.c_proj to make the model
    complete `cloze` with `new_target`."""
    w = model.transformer.h[EDIT_LAYER].mlp.c_proj.weight
    for p in model.parameters():
        p.requires_grad_(False)
    w.requires_grad_(True)
    opt = torch.optim.Adam([w], lr=FT_LR)
    full = tok(cloze + " " + new_target, return_tensors="pt").to(DEVICE)
    clen = tok(cloze, return_tensors="pt").input_ids.shape[1]
    labels = full.input_ids.clone()
    labels[0, :clen] = -100   # loss only on the target tokens
    model.train()
    for step in range(FT_STEPS):
        opt.zero_grad()
        loss = model(**full, labels=labels).loss
        loss.backward()
        opt.step()
        if new_target.lower()[:12] in answer(cloze).lower():
            break
    model.eval()
    w.requires_grad_(False)
    return step + 1, float(loss)


# ── run ───────────────────────────────────────────────────────────────────────
entries = data.load_entries()
import random
random.Random(config.SEED).shuffle(entries)

rows = []                    # (type, propagated_bool)
edits_done = 0
print("scanning for facts the model knows pre-edit, then editing...\n", flush=True)
for entry in entries:
    if edits_done >= N_EDITS:
        break
    pe = parse_edit(entry)
    if not pe:
        continue
    cloze, new_t, old_t = pe
    # competence filter optional: small models rarely complete RippleEdits' templated
    # phrasing, so requiring prior knowledge rejects everything. Default OFF — we edit
    # regardless (efficacy gate below ensures the edit actually took) and measure
    # propagation; note the caveat that prior knowledge isn't guaranteed.
    if os.environ.get("REQUIRE_KNOWS", "0") == "1" and not knows(cloze, old_t):
        continue
    nbrs = neighbours_of(entry)
    if not nbrs:
        continue

    # PRE-edit neighbour answers
    pre = {i: answer(p) for i, (_, p, _) in enumerate(nbrs)}
    # snapshot the layer weight to restore after (so edits don't accumulate)
    w = model.transformer.h[EDIT_LAYER].mlp.c_proj.weight
    saved = w.detach().clone()

    steps, loss = ft_edit(cloze, new_t)
    took = knows(cloze, new_t)      # efficacy: did the edit flip the fact?

    edits_done += 1
    print(f"[edit {edits_done}] {cloze[:55]!r} → {new_t!r}", flush=True)
    print(f"    steps={steps} loss={loss:.3f} efficacy={'YES' if took else 'NO'}", flush=True)
    if took:
        for i, (typ, p, expected) in enumerate(nbrs):
            post = answer(p)
            propagated = expected.lower()[:12] in post.lower()
            rows.append((typ, propagated))
        # quick per-edit tally
        pt = {}
        for typ, prop in [(nbrs[i][0], expected.lower()[:12] in answer(nbrs[i][1]).lower())
                          for i, (_, _, expected) in enumerate(nbrs)]:
            pt.setdefault(typ, []).append(prop)

    # restore weights (isolate each edit)
    with torch.no_grad():
        w.copy_(saved)

# ── propagation table ──────────────────────────────────────────────────────────
print("\n── PROPAGATION by neighbour type (real edits) ──────────")
print(f"{'type':12s}  {'n':>4}  {'propagated':>11}")
print("─" * 32)
summary = {}
for t in config.TYPES:
    tr = [prop for (typ, prop) in rows if typ == t]
    if tr:
        rate = sum(tr) / len(tr)
        summary[t] = (len(tr), rate)
        print(f"{t:12s}  {len(tr):>4}  {rate:>10.1%}")

(OUT / "propagation_table.txt").write_text(
    f"model={MODEL} layer={EDIT_LAYER} edits={edits_done} ft_steps<= {FT_STEPS}\n"
    + "\n".join(f"{t}: n={n} propagated={r:.1%}" for t, (n, r) in summary.items())
)
print(f"\nSaved → {OUT/'propagation_table.txt'}")
print("This is the ground-truth target. If propagation drops with hop distance")
print("(paraphrase > 1hop > 2hop), we've reproduced the ripple-failure phenomenon")
print("on our own stack — the foundation T-B predicts against.")
