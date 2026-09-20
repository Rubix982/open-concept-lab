"""What exactly does NDIF now reject? Single string vs list vs tensor."""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import _quiet_stdout, connect, score_pairs  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
P = "Maurice de Vlaminck was born in the city of"
Q = "Rio Natsuki was born in the city of"

def run(name, fn):
    try:
        print(f"[OK]   {name}: {fn()}")
    except Exception as e:
        print(f"[FAIL] {name}: {str(e)[:70]}")

def s_str():
    with _quiet_stdout(), m.trace(P, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    return tuple(a.shape)

def s_list():
    with _quiet_stdout(), m.trace([P, Q], remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    return tuple(a.shape)

def s_tensor1():
    t = torch.tensor([tok(P).input_ids])
    with _quiet_stdout(), m.trace(t, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    return tuple(a.shape)

def s_tensor2():
    ids = [tok(P).input_ids, tok(Q).input_ids]
    w = max(len(x) for x in ids)
    pad = tok.pad_token_id or tok.eos_token_id
    t = torch.full((2, w), pad, dtype=torch.long)
    for i, x in enumerate(ids):
        t[i, : len(x)] = torch.tensor(x)
    with _quiet_stdout(), m.trace(t, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    return tuple(a.shape)

def s_scorer():
    return [round(x, 3) for x in score_pairs(m, [(P, "Paris"), (P, "Tokyo")])]

run("trace(single string)", s_str)
run("trace(list of strings)", s_list)
run("trace(tensor, batch 1)", s_tensor1)
run("trace(tensor, batch 2)", s_tensor2)
run("score_pairs (the shipped scorer)", s_scorer)
