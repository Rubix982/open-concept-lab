from __future__ import annotations

"""Optional NNsight helpers for the PyTorch Graph Transformer path."""

from typing import Any

import numpy as np

try:
    from nnsight import NNsight
except ImportError:  # pragma: no cover
    NNsight = None


def nnsight_available() -> bool:
    return NNsight is not None


def ensure_nnsight_available() -> None:
    if not nnsight_available():
        raise ImportError("NNsight is not installed. Install `nnsight` before requesting GT tracing with NNsight.")


def _tensor_summary(name: str, value: Any) -> dict[str, object]:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    array = np.asarray(value)
    return {
        "name": name,
        "shape": list(array.shape),
        "mean": float(array.mean()),
        "std": float(array.std()),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def _to_numpy(value: Any) -> np.ndarray:
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def _logit_shift_summary(
    baseline_logits: np.ndarray,
    patched_logits: np.ndarray,
    *,
    top_k_nodes: int = 5,
) -> dict[str, object]:
    difference = patched_logits - baseline_logits
    per_node_l2 = np.linalg.norm(difference, axis=1)
    top_indices = np.argsort(per_node_l2)[::-1][:top_k_nodes]
    baseline_predictions = baseline_logits.argmax(axis=1)
    patched_predictions = patched_logits.argmax(axis=1)

    return {
        "mean_abs_logit_shift": float(np.mean(np.abs(difference))),
        "max_abs_logit_shift": float(np.max(np.abs(difference))),
        "mean_l2_logit_shift": float(np.mean(per_node_l2)),
        "num_prediction_changes": int(np.sum(baseline_predictions != patched_predictions)),
        "top_changed_nodes": [
            {
                "node_index": int(node_index),
                "l2_logit_shift": float(per_node_l2[node_index]),
                "baseline_prediction": int(baseline_predictions[node_index]),
                "patched_prediction": int(patched_predictions[node_index]),
            }
            for node_index in top_indices
        ],
    }


def trace_gt_modules_with_nnsight(
    model,
    *,
    features,
    degree_features,
    attn_mask,
) -> dict[str, object]:
    """Trace a GT forward pass with NNsight and summarize key module outputs."""

    ensure_nnsight_available()
    wrapped = NNsight(model)
    input_projection_output = None
    block_outputs: list[Any] = []
    classifier_output = None
    model_logits = None

    with wrapped.trace(features, degree_features, attn_mask=attn_mask, collect_attention=True):
        input_projection_output = wrapped.input_projection.output.save()
        for index in range(len(model.blocks)):
            block_outputs.append(wrapped.blocks[index].output[0].save())
        classifier_output = wrapped.classifier.output.save()
        model_logits = wrapped.output[0].save()

    return {
        "backend": "nnsight",
        "input_projection": _tensor_summary("input_projection", input_projection_output),
        "blocks": [
            _tensor_summary(f"block_{index}", block_output)
            for index, block_output in enumerate(block_outputs)
        ],
        "classifier": _tensor_summary("classifier", classifier_output),
        "model_logits": _tensor_summary("model_logits", model_logits),
    }


def patch_gt_block_output_with_nnsight(
    model,
    *,
    features,
    degree_features,
    attn_mask,
    block_index: int,
    mode: str = "zero",
    scale: float = 0.0,
) -> dict[str, object]:
    """Patch one GT block output during a traced run and measure the effect.

    This is the first real intervention helper for the repo's Graph Transformer
    path. It keeps the intervention semantics intentionally simple:

    - `mode="zero"`: replace the selected block hidden state with zeros
    - `mode="scale"`: multiply the selected block hidden state by `scale`

    The helper runs one baseline trace and one patched trace, then returns a
    compact before/after summary plus a logit-shift report.
    """

    ensure_nnsight_available()
    if block_index < 0 or block_index >= len(model.blocks):
        raise ValueError(f"Invalid GT block index {block_index}. Model has {len(model.blocks)} blocks.")
    if mode not in {"zero", "scale"}:
        raise ValueError(f"Unsupported GT patch mode: {mode}")

    wrapped = NNsight(model)
    baseline_logits = None
    baseline_block_output = None
    with wrapped.trace(features, degree_features, attn_mask=attn_mask, collect_attention=False):
        baseline_block_output = wrapped.blocks[block_index].output[0].save()
        baseline_logits = wrapped.output[0].save()

    wrapped = NNsight(model)
    patched_logits = None
    original_block_output = None
    with wrapped.trace(features, degree_features, attn_mask=attn_mask, collect_attention=False):
        original_block_output = wrapped.blocks[block_index].output[0].clone().save()
        original_output = wrapped.blocks[block_index].output
        if mode == "zero":
            patched_hidden = original_output[0] * 0.0
        else:
            patched_hidden = original_output[0] * scale
        wrapped.blocks[block_index].output = (patched_hidden, original_output[1])
        patched_logits = wrapped.output[0].save()

    baseline_logits_np = _to_numpy(baseline_logits)
    patched_logits_np = _to_numpy(patched_logits)

    return {
        "backend": "nnsight",
        "intervention": {
            "kind": "block_output_patch",
            "block_index": block_index,
            "mode": mode,
            "scale": scale,
        },
        "baseline_block_output": _tensor_summary(f"block_{block_index}_baseline_output", baseline_block_output),
        "patched_block_input_reference": _tensor_summary(f"block_{block_index}_pre_patch_output", original_block_output),
        "baseline_logits": _tensor_summary("baseline_logits", baseline_logits_np),
        "patched_logits": _tensor_summary("patched_logits", patched_logits_np),
        "logit_shift": _logit_shift_summary(baseline_logits_np, patched_logits_np),
    }


def ablate_gt_head_with_nnsight(
    model,
    *,
    features,
    degree_features,
    attn_mask,
    block_index: int,
    head_index: int,
) -> dict[str, object]:
    """Ablate one GT attention head and measure the downstream effect."""

    ensure_nnsight_available()
    if block_index < 0 or block_index >= len(model.blocks):
        raise ValueError(f"Invalid GT block index {block_index}. Model has {len(model.blocks)} blocks.")
    if head_index < 0 or head_index >= model.blocks[block_index].attention.heads:
        raise ValueError(
            f"Invalid GT head index {head_index} for block {block_index}. "
            f"Block has {model.blocks[block_index].attention.heads} heads."
        )

    wrapped = NNsight(model)
    baseline_logits = None
    baseline_head_outputs = None
    with wrapped.trace(features, degree_features, attn_mask=attn_mask, collect_attention=False):
        baseline_head_outputs = wrapped.blocks[block_index].attention.output[2].save()
        baseline_logits = wrapped.output[0].save()

    wrapped = NNsight(model)
    original_head_outputs = None
    patched_logits = None
    with wrapped.trace(features, degree_features, attn_mask=attn_mask, collect_attention=False):
        original_attention_output = wrapped.blocks[block_index].attention.output
        original_head_outputs = original_attention_output[2].clone().save()
        patched_head_outputs = original_attention_output[2].clone()
        patched_head_outputs[head_index, :, :] = 0.0
        patched_merged_heads = patched_head_outputs.permute(1, 0, 2).reshape(
            patched_head_outputs.shape[1],
            -1,
        )
        patched_merged_output = wrapped.blocks[block_index].attention.out_proj(patched_merged_heads).unsqueeze(0)
        wrapped.blocks[block_index].attention.output = (
            patched_merged_output,
            original_attention_output[1],
            patched_head_outputs,
            patched_merged_heads,
        )
        patched_logits = wrapped.output[0].save()

    baseline_logits_np = _to_numpy(baseline_logits)
    patched_logits_np = _to_numpy(patched_logits)

    return {
        "backend": "nnsight",
        "intervention": {
            "kind": "head_ablation",
            "block_index": block_index,
            "head_index": head_index,
        },
        "baseline_head_outputs": _tensor_summary(
            f"block_{block_index}_head_outputs_baseline",
            baseline_head_outputs,
        ),
        "patched_head_reference": _tensor_summary(
            f"block_{block_index}_head_outputs_pre_ablation",
            original_head_outputs,
        ),
        "baseline_logits": _tensor_summary("baseline_logits", baseline_logits_np),
        "patched_logits": _tensor_summary("patched_logits", patched_logits_np),
        "logit_shift": _logit_shift_summary(baseline_logits_np, patched_logits_np),
    }
