# Experiment: Single ROME Edit

**Ticket:** E-002
**Goal:** Apply one ROME edit to GPT-J-6B, verify it worked.

## What to implement

`edit.py` — applies a rank-1 MLP weight update to GPT-J-6B for one triple,
then verifies the edit succeeded and specificity is maintained.

## The ROME edit operation (manual implementation)

ROME computes a rank-1 update to the MLP projection matrix W at the critical
layer (typically layer 17 for GPT-J-6B, found via causal tracing):

```
v* = target vector (what the MLP should output for the new object)
h  = hidden state at last subject token, target layer (from clean forward pass)
ΔW = (v* - W·h) · h^T / (C·h)    where C is a precomputed covariance matrix
W_new = W + ΔW
```

The covariance matrix C is computed from a set of "random" inputs (WikiText)
to preserve the model's existing knowledge.

## Alternative: use the `easyeditor` library

`pip install easyeditor` wraps ROME/MEMIT for GPT-J-6B with one function call.
Evaluate this as the simpler path before implementing manually.

## Verification queries

After the edit:
1. **Efficacy**: "The Eiffel Tower is located in" → should return "Rome"
2. **Specificity**: "The Colosseum is located in" → should still return "Rome"
   (unrelated fact unchanged)
3. **Anti-specificity**: "Big Ben is located in" → should still return "London"

## Output format (`output/edit_verification.json`)

```json
{
  "edit": {"subject": "...", "relation": "...", "old_object": "...", "new_object": "..."},
  "efficacy": {"top1": "Rome", "correct_rank": 1, "success": true},
  "specificity": [
    {"prompt": "...", "expected": "...", "top1": "...", "unchanged": true}
  ]
}
```
