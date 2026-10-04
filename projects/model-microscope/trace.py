"""Work out the three lenses for every prepared case and write data/*.json.

    .venv/bin/python trace.py            # all cases
    .venv/bin/python trace.py eiffel     # just one

Lens 1, logit lens: each layer's residual stream, read out through the final
layer norm and the unembedding, as if the model stopped there.
Lens 2, attention: the attention pattern of every layer (mean over heads),
and per head for the last token.
Lens 3, causal tracing (Meng et al. 2022, ROME): noise the subject's
embeddings, then restore one clean activation at a time and measure how much
of the answer's probability comes back.
"""
import json, sys, time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from cases import CASES

MODEL = "gpt2-medium"
NOISE_SAMPLES = 10   # noise draws averaged per restoration (ROME uses 10)
WINDOW = 10          # MLP / attention restorations cover this many layers
OUT = Path(__file__).parent / "site" / "data"

torch.manual_seed(0)
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, attn_implementation="eager").eval()
# The weights arrive memory-mapped from the safetensors file, and on this
# machine the accelerated matmul returns NaN on that memory; copy them first.
for p in model.parameters():
    p.data = p.data.clone()
blocks = model.transformer.h
L = len(blocks)
# ROME: noise with 3x the standard deviation of the token embeddings
NOISE_STD = 3 * model.transformer.wte.weight.std().item()


def first(out):
    return out[0] if isinstance(out, tuple) else out


def replace_first(out, new):
    return (new, *out[1:]) if isinstance(out, tuple) else new


def token_strs(ids):
    return [tok.decode([i]) for i in ids]


def span_positions(prompt, ids, sub):
    """Token positions covering the substring `sub` of the prompt."""
    start = prompt.index(sub)
    end = start + len(sub)
    pos, at = [], 0
    for k, i in enumerate(ids):
        s = tok.decode([i])
        if at < end and at + len(s) > start:
            pos.append(k)
        at += len(s)
    return pos


def top(probs, k=5):
    p, i = probs.topk(k)
    return [[tok.decode([j]), round(q, 4)] for j, q in zip(i.tolist(), p.tolist())]


@torch.no_grad()
def run(case):
    prompt, target = case["prompt"], case["target"]
    ids = tok(prompt)["input_ids"]
    T = len(ids)
    tgt = tok(target)["input_ids"][0]
    x = torch.tensor([ids])

    # ---- clean run: record everything
    rec = {"mlp": [None] * L, "attn": [None] * L}
    hooks = []
    for l, b in enumerate(blocks):
        hooks.append(b.mlp.register_forward_hook(lambda m, i, o, l=l: rec["mlp"].__setitem__(l, first(o)[0].clone())))
        hooks.append(b.attn.register_forward_hook(lambda m, i, o, l=l: rec["attn"].__setitem__(l, first(o)[0].clone())))
    out = model(x, output_hidden_states=True, output_attentions=True)
    for h in hooks:
        h.remove()
    hs = out.hidden_states  # L+1 entries; the last already has ln_f applied
    final = out.logits[0, -1].softmax(-1)

    # ---- lens 1: logit lens
    lens, target_track = [], []
    for l in range(L + 1):
        h = hs[l][0] if l == L else model.transformer.ln_f(hs[l][0])
        probs = model.lm_head(h).softmax(-1)
        lens.append([top(probs[t]) for t in range(T)])
        last = probs[-1]
        target_track.append({"p": round(last[tgt].item(), 4), "rank": int((last > last[tgt]).sum().item()) + 1})

    # ---- lens 2: attention
    att = torch.stack([a[0] for a in out.attentions])  # L, heads, T, T
    attn_mean = att.mean(1)
    attention = {
        "mean": [[[round(v, 3) for v in row] for row in layer.tolist()] for layer in attn_mean],
        "lastHeads": [[[round(v, 3) for v in head] for head in layer.tolist()] for layer in att[:, :, -1, :]],
    }

    # ---- lens 3: causal tracing
    corrupt = span_positions(prompt, ids, case["corrupt"])
    noise = torch.randn(NOISE_SAMPLES, len(corrupt), model.config.n_embd) * NOISE_STD

    def traced(configs):
        """configs: list of (kind, pos, layers). Returns p(target) for each,
        averaged over the noise samples, in one batched forward pass."""
        n = len(configs)
        batch = x.repeat(n * NOISE_SAMPLES, 1)
        hs_ = []
        def add_noise(m, i, o):
            o = o.clone()
            o[:, corrupt] += noise.repeat(n, 1, 1)
            return o
        hs_.append(model.transformer.wte.register_forward_hook(add_noise))
        for l, b in enumerate(blocks):
            for kind, mod in (("hidden", b), ("mlp", b.mlp), ("attn", b.attn)):
                rows = [(r, pos) for r, (k, pos, ls) in enumerate(configs) if k == kind and l in ls]
                if not rows:
                    continue
                clean = hs[l + 1][0] if kind == "hidden" else rec[kind][l]
                def patch(m, i, o, rows=rows, clean=clean):
                    h = first(o).clone()
                    for r, pos in rows:
                        h[r * NOISE_SAMPLES:(r + 1) * NOISE_SAMPLES, pos] = clean[pos]
                    return replace_first(o, h)
                hs_.append(mod.register_forward_hook(patch))
        logits = model(batch).logits[:, -1].softmax(-1)[:, tgt]
        for h in hs_:
            h.remove()
        return logits.view(n, NOISE_SAMPLES).mean(1).tolist()

    p_corrupt = traced([("none", -1, [])])[0]
    trace = {}
    for kind in ("hidden", "mlp", "attn"):
        grid = []
        for pos in range(T):
            configs = []
            for l in range(L):
                ls = [l] if kind == "hidden" else list(range(max(0, l - WINDOW // 2), min(L, l + WINDOW // 2)))
                configs.append((kind, pos, ls))
            grid.append([round(p, 4) for p in traced(configs)])
        trace[kind] = grid  # [position][layer] = p(target) with that restored

    return {
        **{k: case[k] for k in ("id", "group", "title", "prompt", "target", "corrupt")},
        "model": MODEL,
        "layers": L,
        "tokens": token_strs(ids),
        "targetToken": tok.decode([tgt]),
        "says": top(final),
        "clean": round(final[tgt].item(), 4),
        "lens": lens,
        "targetTrack": target_track,
        "attention": attention,
        "trace": {"corrupt": corrupt, "pCorrupt": round(p_corrupt, 4), "window": WINDOW, **trace},
    }


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    only = set(sys.argv[1:])
    for case in CASES:
        if only and case["id"] not in only:
            continue
        t0 = time.time()
        d = run(case)
        (OUT / f"{case['id']}.json").write_text(json.dumps(d, separators=(",", ":")))
        print(f"{case['id']:<14} says {d['says'][0][0]!r:<12} p({d['targetToken']!r})={d['clean']:.3f}  corrupted={d['trace']['pCorrupt']:.3f}  {time.time() - t0:.0f}s")
    index = [{k: c[k] for k in ("id", "group", "title")} for c in CASES]
    (OUT / "index.json").write_text(json.dumps(index, indent=1))
