"""Shared helpers: model loading, CounterFact access, activation capture."""
import gzip
import json
import os
from contextlib import contextmanager
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESULTS = ROOT / "results"
CACHE = ROOT / "cache"

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

# ROME's published edit layers for each GPT-2 size.
EDIT_LAYER = {"gpt2": 5, "gpt2-medium": 8, "gpt2-large": 12}


def load_model(name="gpt2-medium"):
    tok = AutoTokenizer.from_pretrained(name)
    tok.pad_token = tok.eos_token
    tok.padding_side = "right"
    model = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float32).to(DEVICE)
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model, tok


def n_layers(model):
    return len(model.transformer.h)


def c_proj(model, layer):
    """The MLP output projection ROME rewrites. HF Conv1D: y = x @ W + b, W is (4d, d)."""
    return model.transformer.h[layer].mlp.c_proj


def snapshot(model):
    """Copy of every c_proj weight, so an edited model can be restored."""
    return {l: c_proj(model, l).weight.detach().clone() for l in range(n_layers(model))}


def restore(model, snap):
    with torch.no_grad():
        for l, w in snap.items():
            c_proj(model, l).weight.copy_(w)


def load_counterfact():
    return json.load(gzip.open(DATA / "counterfact.json.gz"))


class _Stop(Exception):
    pass


@contextmanager
def capture_key(model, layer, store, stop=False):
    """Record the input to c_proj at `layer` (the ROME key, post-GELU, 4d wide).
    With stop=True the forward pass is aborted right after, to skip later layers."""
    def hook(mod, inp):
        store["k"] = inp[0]
        if stop:
            raise _Stop
    h = c_proj(model, layer).register_forward_pre_hook(hook)
    try:
        yield
    finally:
        h.remove()


def last_subject_index(tok, prompt_with_subject, subject):
    """Token index of the last subject token in `prompt_with_subject` (which contains subject once)."""
    pre = prompt_with_subject[: prompt_with_subject.index(subject) + len(subject)]
    return len(tok(pre)["input_ids"]) - 1


@torch.no_grad()
def keys_at(model, tok, layer, texts, idxs, batch=64):
    """Key vectors (c_proj input at `layer`) for each text at token index idxs[i]."""
    out = []
    for i in range(0, len(texts), batch):
        enc = tok(texts[i:i + batch], return_tensors="pt", padding=True).to(DEVICE)
        store = {}
        try:
            with capture_key(model, layer, store, stop=True):
                model.transformer(**enc)
        except _Stop:
            pass
        k = store["k"]
        ix = torch.tensor(idxs[i:i + batch], device=DEVICE)
        out.append(k[torch.arange(len(ix), device=DEVICE), ix].float().cpu())
    return torch.cat(out)


def save_json(obj, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2))


class SwappedBase:
    """The clean base model, without a second copy in memory. Edits that only touch
    c_proj leave everything else shared, so the base is the suspect with its c_proj
    weights temporarily swapped back to the snapshot. Callable like a model."""

    def __init__(self, model, snap):
        self.model, self.snap = model, snap

    @torch.no_grad()
    def __call__(self, **kw):
        keep = {}
        for l, w in self.snap.items():
            W = c_proj(self.model, l).weight
            if not torch.equal(W, w):
                keep[l] = W.clone()
                W.copy_(w)
        try:
            return self.model(**kw)
        finally:
            for l, w in keep.items():
                c_proj(self.model, l).weight.copy_(w)


def free_gpu():
    import gc
    gc.collect()
    if DEVICE == "mps":
        torch.mps.empty_cache()
