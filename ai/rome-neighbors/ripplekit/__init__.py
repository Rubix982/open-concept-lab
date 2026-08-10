"""ripplekit — reusable library for the rome-neighbors research project.

Does structured representational geometry predict whether a knowledge edit
propagates to logically entailed neighbours? See design.md and readings/MAP.md.

Modules:
  config      — constants (model, layers, seeds, criterion→type map, paths)
  data        — schema-verified RippleEdits loader + answer-anchor index
  reps        — GPT-J representation extraction via NNsight/NDIF (remote)
  predictors  — raw distance (baseline), alignment (STEAM), structured (stub)
  analysis    — aggregate-by-type, separation metric, plotting
"""

from . import analysis, config, data, predictors, reps  # noqa: F401

__all__ = ["config", "data", "reps", "predictors", "analysis"]
__version__ = "0.1.0"
