"""Isolate why apply_delta fails remotely. Four variants, smallest difference first."""
import sys
from pathlib import Path
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from remote import connect  # noqa: E402

m = connect("meta-llama/Llama-3.1-8B")
L, P = 5, "Maurice de Vlaminck was born in the country of"
ks = torch.randn(14336)
dv = torch.randn(4096) * 0.01


def run(name, fn):
    try:
        out = fn()
        print(f"[OK]   {name}: {out}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:110]}")


def v1_read_input_only():
    with m.trace(P, remote=True):
        k = m.model.layers[L].mlp.down_proj.input
        s = k.sum().float().save()
    return f"input sum {float(s):.1f}"


def v2_assign_output_only():
    with m.trace(P, remote=True):
        dp = m.model.layers[L].mlp.down_proj
        dp.output = dp.output + dv.to(dp.output.device, dp.output.dtype)
        t = m.lm_head.output[0, -1].argmax(-1).save()
    return repr(m.tokenizer.decode(t))


def v3_input_then_assign_output():
    with m.trace(P, remote=True):
        dp = m.model.layers[L].mlp.down_proj
        k = dp.input
        coeff = (k @ ks.to(k.device, k.dtype)) / 1000.0
        dp.output = dp.output + coeff.unsqueeze(-1) * dv.to(k.device, k.dtype)
        t = m.lm_head.output[0, -1].argmax(-1).save()
    return repr(m.tokenizer.decode(t))


def v4_input_captured_first():
    with m.trace(P, remote=True):
        dp = m.model.layers[L].mlp.down_proj
        k = dp.input
        o = dp.output
        coeff = (k @ ks.to(o.device, o.dtype)) / 1000.0
        dp.output = o + coeff.unsqueeze(-1) * dv.to(o.device, o.dtype)
        t = m.lm_head.output[0, -1].argmax(-1).save()
    return repr(m.tokenizer.decode(t))


run("v1 read .input only", v1_read_input_only)
run("v2 assign .output only", v2_assign_output_only)
run("v3 .input then assign .output", v3_input_then_assign_output)
run("v4 capture both, then assign", v4_input_captured_first)
