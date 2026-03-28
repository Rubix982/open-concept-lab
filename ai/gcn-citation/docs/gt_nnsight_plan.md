# GT + NNsight Intervention Plan

This note captures what would be required to make the `GT + NNsight` path in
this repo feel like a real interpretability workflow instead of "tracing only."

Right now, the repo supports:

- PyTorch Graph Transformer (`GT`)
- optional `NNsight` tracing
- summary statistics for a few internal module outputs

That is already useful for inspection, but it is **not yet** a full
intervention workflow.

## What "real GT + NNsight support" means

To honestly say that we can reason about how interventions compose inside a
Graph Transformer, we need:

1. real intervention hooks
2. clear semantics for residual-path composition
3. reusable helper APIs
4. experiments that demonstrate intervention behavior
5. tests that keep those behaviors stable

## 1. Real intervention points

Tracing is not enough. We need places where we can actually modify the
computation during a traced run.

High-value intervention surfaces:

- `input_projection`
- pre-attention hidden state in each block
- attention output before residual addition
- hidden state after the first residual / norm
- feedforward output before the second residual
- final classifier input
- final logits

These surfaces matter because Graph Transformers are not strictly sequential in
the simple "layer output replaces previous layer output" sense. Residual
connections mean multiple computation paths merge.

## 2. Composition semantics

This is the core research question the user surfaced:

> how do interventions compose when the computation graph is not strictly sequential?

For this repo, we should make those semantics explicit.

Questions to answer:

- If we patch the attention output, does that happen before or after residual
  addition?
- If we patch the hidden state after `norm_1`, how should that interact with
  the feedforward path?
- If we apply two interventions in one block, which one wins?
- If we patch one attention head, how does that propagate through head
  concatenation or averaging?
- If we patch a single node representation, how does that influence downstream
  nodes through graph-aware attention?

## 3. Reusable helper APIs

Instead of putting raw `NNsight` code in experiments, we should add small helper
functions so intervention experiments are easy to repeat.

Candidate helpers:

- `trace_gt_block_outputs(...)`
- `trace_gt_attention_outputs(...)`
- `patch_gt_block_output(...)`
- `ablate_gt_head(...)`
- `replace_gt_node_hidden_state(...)`
- `measure_gt_logit_shift(...)`

These helpers should stay tightly scoped and explicit about:

- target block
- target head
- target node set
- whether the patch is additive, replacement-based, or zero-ablation

## 4. First intervention experiments

The repo should include at least a few focused experiments before claiming that
the `GT + NNsight` path is mature.

Best first experiments:

1. ablate one attention head in one block
2. zero the attention output for a selected block
3. replace one node's hidden state with zeros
4. compare patch-before-residual vs patch-after-residual

For each experiment, record:

- logits before intervention
- logits after intervention
- per-node prediction changes
- top changed nodes

## 5. Output artifacts

Intervention experiments should save structured artifacts, not only console
output.

Recommended artifacts:

- `intervention_report.json`
- `logit_shift.npy`
- `prediction_changes.json`
- optionally a small Markdown summary

## 6. Tests

At minimum, add tests or smoke checks that confirm:

- tracing works on the custom GT model
- a block-output intervention changes the final logits
- repeated runs with the same patch are deterministic
- head ablation only affects the intended head path

## 7. Recommended implementation order

To keep scope disciplined:

1. add one block-output patch helper
2. add one head-ablation helper
3. define residual-composition semantics in code comments and docs
4. add one comparison experiment showing before/after logits
5. only then expand to richer intervention families

## Immediate next milestone

The best next milestone is:

- implement `ablate_gt_head(...)`
- run it on a small Cora example
- save a concise `before vs after` logit-difference artifact

That would make the current `GT + NNsight` path feel genuinely research-ready.

## Current implementation status

The repo now has the first intervention helper:

- `patch_gt_block_output_with_nnsight(...)`

Current supported patch modes:

- `zero`
- `scale`

This gives us the first real `before vs after logits` intervention path for GT.
