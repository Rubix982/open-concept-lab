"""
nethook + LogitLens Explainer
==============================
Walks through:
  rome/util/nethook.py
  rome/util/logit_lens.py

No real model needed. Uses a tiny hand-built nn.Sequential so every
forward-pass value can be traced by hand.

Run with:
    python scripts/nethook_explainer.py

Dependencies: torch only
"""

from __future__ import annotations

import contextlib
from typing import Any, Callable, Optional

import torch
import torch.nn as nn

SEP: str = "=" * 70


def show(label: str, t: torch.Tensor) -> None:
    print(f"\n  {label}  shape={tuple(t.shape)}")
    print(f"  {t}")


# ═════════════════════════════════════════════════════════════════════════════
# BACKGROUND
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("BACKGROUND — the problem nethook solves")
print(SEP)
print("""
PyTorch's forward pass is a black box. You call model(input) and get an
output. You cannot easily:
  - Read what a middle layer produced
  - Modify a middle layer's output before it flows to the next layer
  - Stop execution partway through

nethook solves all three using PyTorch's hook system:
  module.register_forward_hook(fn)

A forward hook is a function that PyTorch calls automatically after a
module runs, passing it (module, inputs, output). nethook wraps this
with a clean context-manager API so hooks are always cleaned up.

There are three classes:
  Trace      — hook one layer (read, edit, or stop)
  TraceDict  — hook many layers at once
  StopForward — the exception raised to halt execution early

ROME uses nethook to:
  1. READ hidden states during causal tracing (the three-run experiment)
  2. INJECT edited activations during the patch runs
  3. STOP the model early to extract intermediate representations
""")


# ═════════════════════════════════════════════════════════════════════════════
# BUILD A TOY MODEL
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("TOY MODEL — a tiny Sequential we can trace")
print(SEP)

torch.manual_seed(0)

# 4-layer network: each layer is a simple linear + ReLU
layer0: nn.Module = nn.Linear(4, 4, bias=False)
layer1: nn.Module = nn.Linear(4, 4, bias=False)
layer2: nn.Module = nn.Linear(4, 4, bias=False)
layer3: nn.Module = nn.Linear(4, 4, bias=False)

toy_model: nn.Sequential = nn.Sequential(
    layer0, nn.ReLU(),
    layer1, nn.ReLU(),
    layer2, nn.ReLU(),
    layer3,
)

x: torch.Tensor = torch.tensor([[1.0, 0.0, -1.0, 0.5]])
out_baseline: torch.Tensor = toy_model(x)
print("Input x:")
show("x", x)
print("\nBaseline output (no hooks):")
show("toy_model(x)", out_baseline)

print("""
We have 4 Linear layers (indices 0, 2, 4, 6 in the Sequential).
In ROME, these would be the transformer layers.
In the causal trace experiments, ROME traces the MLP layers by name
(e.g. 'model.layers.17.mlp').
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 1 — PyTorch hooks raw, then nethook's Trace
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 1 — How PyTorch hooks work, and what Trace wraps")
print(SEP)
print("""
RAW PYTORCH HOOK
----------------
A forward hook is registered like this:

    handle = module.register_forward_hook(fn)
    # fn signature: fn(module, inputs, output) -> Optional[output]
    # If fn returns something, it REPLACES the module's output.
    # After you're done: handle.remove()

This is powerful but error-prone — if you forget handle.remove(), the hook
stays attached forever, causing subtle bugs and memory leaks.

NETHOOK'S Trace
---------------
Trace is a context manager that:
  1. Registers the hook on __enter__
  2. Removes it on __exit__ (even if an exception is raised)
  3. Stores the captured output as trace.output

So you never forget to clean up.
""")

# ── Mode 1: READ ─────────────────────────────────────────────────────────────
print("--- Mode 1: READ (capture a layer's output) ---")
print("""
    with Trace(model, 'layer_name') as tr:
        _ = model(x)
    print(tr.output)   # the tensor that layer produced
""")

captured_output: Optional[torch.Tensor] = None

def read_hook(m: nn.Module, inputs: tuple[torch.Tensor, ...], output: torch.Tensor) -> None:
    global captured_output
    captured_output = output.detach().clone()

handle = layer1.register_forward_hook(read_hook)
_ = toy_model(x)
handle.remove()

print("Captured output of layer1:")
show("layer1 output", captured_output)

print("""
ROME uses this pattern during the CLEAN RUN of causal tracing:
  - Run the model normally on the factual prompt
  - Capture hidden states at every layer for every token position
  - Store them — these become the "clean states" to restore later
""")

# ── Mode 2: EDIT ─────────────────────────────────────────────────────────────
print("\n--- Mode 2: EDIT (modify a layer's output before it flows forward) ---")
print("""
    def edit_fn(output, layer):
        return output + delta   # modify and return new output

    with Trace(model, 'layer_name', edit_output=edit_fn) as tr:
        result = model(x)
    # result is computed with the modified intermediate value
""")

delta: torch.Tensor = torch.tensor([[10.0, 0.0, 0.0, 0.0]])  # add 10 to first dim

edited_out: Optional[torch.Tensor] = None

def edit_hook(
    m: nn.Module,
    inputs: tuple[torch.Tensor, ...],
    output: torch.Tensor,
) -> torch.Tensor:
    global edited_out
    modified: torch.Tensor = output + delta
    edited_out = modified.detach().clone()
    return modified   # returning replaces the output

handle = layer1.register_forward_hook(edit_hook)
out_edited: torch.Tensor = toy_model(x)
handle.remove()

print("Original layer1 output:")
show("(captured above)", captured_output)
print("\nEdited layer1 output (+ delta):")
show("layer1 output after edit", edited_out)
print("\nFinal model output:")
show("out_baseline (no edit)", out_baseline)
show("out_edited   (with edit)", out_edited)

print("""
This is EXACTLY how ROME injects its edits during the PATCH RUN:
  - The clean hidden states captured earlier are passed through edit_output
  - Specifically, for the "restore" experiment, one layer's hidden state
    is replaced with the clean version to measure its causal contribution
  - This is how they compute the Indirect Effect per layer

In rome_main.py (the actual ROME edit), a different edit_output is used:
  - The weight matrix W is modified by a rank-one update W + v @ k^T
  - This makes the change permanent in the weights, not just per-forward-pass
""")

# ── Mode 3: STOP ─────────────────────────────────────────────────────────────
print("\n--- Mode 3: STOP (halt execution after a target layer) ---")
print("""
    with Trace(model, 'layer_name', stop=True) as tr:
        try:
            model(x)
        except StopForward:
            pass
    print(tr.output)   # only the layers up to 'layer_name' ran
""")

class StopForward(Exception):
    pass

stop_output: Optional[torch.Tensor] = None

def stop_hook(
    m: nn.Module,
    inputs: tuple[torch.Tensor, ...],
    output: torch.Tensor,
) -> None:
    global stop_output
    stop_output = output.detach().clone()
    raise StopForward()

handle = layer1.register_forward_hook(stop_hook)
try:
    _ = toy_model(x)
except StopForward:
    pass
handle.remove()

print("Output captured at layer1 (layers 2, 3 never ran):")
show("stop_output", stop_output)

print("""
ROME uses stop=True to extract subject representations efficiently:
  repr_tools.py runs the model only up to the target layer,
  then reads the hidden state at the subject token position.
  No need to run all 80 layers when you only need layer 17's output.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 2 — TraceDict: hooking multiple layers at once
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 2 — TraceDict: hook many layers in one context manager")
print(SEP)
print("""
TraceDict is just an OrderedDict where each key is a layer name and
each value is a Trace. All hooks are registered on __enter__ and
all are removed on __exit__.

    with TraceDict(model, ['layer1', 'layer3']) as td:
        _ = model(x)
    h1 = td['layer1'].output
    h3 = td['layer3'].output

ROME uses TraceDict during causal tracing to capture ALL layers in one
forward pass — much more efficient than running the model once per layer.
""")

layer_outputs: dict[str, Optional[torch.Tensor]] = {
    "layer0": None,
    "layer1": None,
    "layer2": None,
    "layer3": None,
}

def make_capture_hook(name: str) -> Callable[..., None]:
    def hook(m: nn.Module, inputs: tuple[torch.Tensor, ...], output: torch.Tensor) -> None:
        layer_outputs[name] = output.detach().clone()
    return hook

handles: list[Any] = [
    layer0.register_forward_hook(make_capture_hook("layer0")),
    layer1.register_forward_hook(make_capture_hook("layer1")),
    layer2.register_forward_hook(make_capture_hook("layer2")),
    layer3.register_forward_hook(make_capture_hook("layer3")),
]
_ = toy_model(x)
for h in handles:
    h.remove()

print("Captured outputs for all 4 layers in one forward pass:")
for name, out in layer_outputs.items():
    show(name, out)

print("""
In the causal trace experiment (experiments/causal_trace.py), this dict
is keyed by strings like 'model.layers.{i}.mlp' for each transformer layer.
After the forward pass, the dict holds the full hidden-state trajectory
through the model — one tensor per layer per token.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 3 — get_module and replace_module: navigating the model tree
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 3 — get_module and replace_module")
print(SEP)
print("""
Transformers have deeply nested modules. You access them with dotted names:
  'model.layers.17.mlp.down_proj'

nethook.get_module(model, 'model.layers.17.mlp') walks model.named_modules()
and returns the exact sub-module matching that string.

nethook.replace_module(model, name, new_module) does the reverse:
  - Splits on the last dot to find the parent
  - Uses setattr(parent, attr_name, new_module)

ROME uses replace_module when it needs to permanently swap out a layer's
weight matrix after computing the rank-one update.

In our toy model, modules are named '0', '1', '2', etc.:
""")

print("All named modules in toy_model:")
for name, module in toy_model.named_modules():
    if name:  # skip the root ''
        print(f"  '{name}':  {type(module).__name__}")

# get_module equivalent: walk named_modules
def get_module(model: nn.Module, name: str) -> nn.Module:
    for n, m in model.named_modules():
        if n == name:
            return m
    raise LookupError(name)

retrieved: nn.Module = get_module(toy_model, "2")  # layer1 (index 2 in Sequential)
print(f"\nget_module(toy_model, '2') returned: {retrieved}")
print(f"  Same object as layer1? {retrieved is layer1}")

print("""
In the real ROME codebase, the module name for the MLP of layer 17 would be:
  'transformer.h.17.mlp'   (GPT-2 style naming)

nethook.get_module handles arbitrarily deep nesting by walking the full
named_modules() iterator, which PyTorch generates recursively.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 4 — LogitLens: "what would the model predict if it stopped here?"
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 4 — LogitLens: reading predictions from intermediate layers")
print(SEP)
print("""
LogitLens is a diagnostic tool built on TraceDict.

The idea (from lesswrong.com/posts/AcKRB8wDpdaN6v6ru):
  At each layer, the residual stream is "almost" a prediction.
  If you apply the final LayerNorm + LM head directly to a middle layer's
  output, you get a probability distribution over vocabulary — what the
  model "currently thinks" the next token is at that depth.

This reveals:
  - At which layer a factual prediction becomes confident
  - How the model's "opinion" evolves through the layers
  - Whether an edit (e.g. ROME) changes the prediction at the right layer

LOGIT LENS ALGORITHM
--------------------
  1. Hook every layer's output (TraceDict)
  2. Run one forward pass
  3. For each layer's output tensor:
       a. Apply the final LayerNorm
       b. Apply the LM head (unembedding matrix)
       c. Softmax → probability distribution
       d. Record top-k tokens
""")

# Synthetic demonstration with our toy model
# Simulate "LM head" as a final linear that maps to vocab_size=8
VOCAB_SIZE: int = 8
torch.manual_seed(1)
lm_head: nn.Linear = nn.Linear(4, VOCAB_SIZE, bias=False)

print("Synthetic LogitLens: top predicted 'token' at each layer")
print("(toy vocab of 8 tokens, LM head is random — shows the pattern, not real predictions)\n")

with torch.no_grad():
    # Capture all layer outputs
    all_layer_outs: dict[str, torch.Tensor] = {}
    capture_handles: list[Any] = []
    for idx, layer in enumerate([layer0, layer1, layer2, layer3]):
        def make_hook(i: int) -> Callable[..., None]:
            def hook(m: nn.Module, inputs: tuple[torch.Tensor, ...], output: torch.Tensor) -> None:
                all_layer_outs[f"layer{i}"] = output.detach().clone()
            return hook
        capture_handles.append(layer.register_forward_hook(make_hook(idx)))

    _ = toy_model(x)
    for h in capture_handles:
        h.remove()

    # Apply lm_head to each captured output (simulating layernorm + lm_head)
    print(f"  {'Layer':<10} {'Top token':>10} {'Prob':>8}")
    print("  " + "-" * 32)
    for name, out in all_layer_outs.items():
        logits: torch.Tensor = lm_head(out[0, :])   # (seq=1, vocab)
        probs: torch.Tensor  = torch.softmax(logits, dim=-1)
        top_token: int       = int(probs.argmax().item())
        top_prob: float      = float(probs.max().item())
        print(f"  {name:<10} {'tok_' + str(top_token):>10} {top_prob:>8.3f}")

print("""
In the real LogitLens on a language model:
  - Early layers predict common/generic tokens (articles, punctuation)
  - Middle layers start forming the semantic content
  - Late layers converge on the final prediction

For causal tracing, LogitLens reveals: at which layer does the model
"know" the answer? If restoring a hidden state at layer L flips the
top token from wrong → right, layer L is causally responsible.
""")


# ═════════════════════════════════════════════════════════════════════════════
# PART 5 — Connection to nnsight (used in attn_knockout notebook)
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("PART 5 — nethook vs nnsight: same idea, different API")
print(SEP)
print("""
The attn_knockout notebook uses nnsight. nethook is ROME's custom version.
They solve the same problem differently:

  nethook (ROME, 2022)
  ────────────────────
  • Pure PyTorch hooks (register_forward_hook)
  • Context-manager API: with Trace(model, layer) as tr:
  • Edit via edit_output=fn callback
  • Works on any nn.Module, locally

  nnsight (Lookback paper, 2024+)
  ────────────────────────────────
  • Higher-level abstraction over hooks + proxy tensors
  • API: model.model.layers[l].self_attn.q_proj.output  (direct attribute access)
  • Edit by assignment: module.input = new_tensor
  • Designed for remote inference (NDIF cluster) as well as local
  • Handles deferred execution — the trace block builds a graph, then runs it

CONCEPTUAL EQUIVALENCE
-----------------------
nethook:
    with Trace(model, 'transformer.h.17.mlp', edit_output=fn) as tr:
        model(input)

nnsight:
    with model.trace(input) as tracer:
        hidden = model.transformer.h[17].mlp.output
        model.transformer.h[17].mlp.output = fn(hidden)

Both intercept the same point in the forward pass.
Both can read and write intermediate activations.
nethook is lower-level; nnsight adds remote execution and a cleaner DSL.
""")


# ═════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═════════════════════════════════════════════════════════════════════════════
print(SEP)
print("SUMMARY — nethook's four pieces and what each enables")
print(SEP)
print("""
  Trace(model, layer)
  ────────────────────
  • Hooks one layer, reads/edits/stops
  • edit_output=fn → this is the injection mechanism for ROME patches
  • stop=True      → early exit, used by repr_tools to extract subject reps

  TraceDict(model, [layer1, layer2, ...])
  ────────────────────────────────────────
  • Hooks many layers in one pass
  • Used in causal_trace.py to capture ALL hidden states in one forward pass
  • Used by LogitLens to probe every layer simultaneously

  StopForward
  ────────────
  • Exception that halts the forward pass after a hooked layer
  • Caught by Trace's __exit__; user never sees it

  get_module / replace_module
  ───────────────────────────
  • Navigate the model tree by dotted name string
  • replace_module is used by ROME to install the edited weight matrix

  LogitLens
  ──────────
  • Wraps TraceDict to hook every layer
  • Applies LM head to each captured output → token probabilities per layer
  • Diagnostic: shows when the model "knows" the answer during a forward pass
  • Useful after a ROME edit to verify the edit takes effect at the right depth

  THE CHAIN IN ROME'S CAUSAL TRACE EXPERIMENT
  ─────────────────────────────────────────────
  Run 1 (clean):    TraceDict captures all hidden states → stored as "clean_states"
  Run 2 (corrupt):  model runs with noisy subject embeddings → wrong answer
  Run 3 (restore):  for each layer L: Trace with edit_output that replaces
                    that layer's output with clean_states[L][subject_token]
                    → if correct answer returns, L is causally responsible
""")
