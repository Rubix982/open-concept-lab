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
