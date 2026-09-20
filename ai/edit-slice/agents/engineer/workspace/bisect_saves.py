"""What exactly does NDIF reject? Bisect the layer_sweep trace, smallest change first."""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import _quiet_stdout, connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
tok = m.tokenizer
P = ["Maurice de Vlaminck was born in the city of"]
ids = tok(P[0]).input_ids
one = torch.tensor([ids])
pad = tok.pad_token_id or tok.eos_token_id
two = torch.full((2, len(ids)), pad, dtype=torch.long)
two[0] = torch.tensor(ids); two[1] = torch.tensor(ids)

def run(name, fn):
    try:
        print(f"[OK]   {name}: {fn()}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:80]}")

def v1():
    with _quiet_stdout(), m.trace(one, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    return tuple(a.shape)

def v2():
    with _quiet_stdout(), m.trace(one, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
        b = m.model.layers[10].mlp.down_proj.input.half().save()
    return (tuple(a.shape), tuple(b.shape))

def v3():
    with _quiet_stdout(), m.trace(two, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
    return tuple(a.shape)

def v4():
    with _quiet_stdout(), m.trace(two, remote=True):
        a = m.model.layers[5].mlp.down_proj.input.half().save()
        b = m.model.layers[10].mlp.down_proj.input.half().save()
    return (tuple(a.shape), tuple(b.shape))

def v5():
    with _quiet_stdout(), m.trace(one, remote=True):
        a = m.model.layers[0].mlp.down_proj.input.half().save()
    return tuple(a.shape)

run("1 save,  batch 1", v1)
run("2 saves, batch 1", v2)
run("1 save,  batch 2", v3)
run("2 saves, batch 2", v4)
run("layer 0 save",     v5)
