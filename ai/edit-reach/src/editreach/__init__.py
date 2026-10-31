"""Measure how far a rank-one weight edit travels.

The package exists for one question: how much of an edit arrives at a given
token, and can that be known **before** the edit is applied.

Three things it does that its predecessor (`ai/edit-slice/src`) did not:

1. It is a package. The original was a flat module namespace that required
   `src/` on `sys.path` and broke under `src.data`.
2. The coefficient is a first-class object (`coefficient.py`) rather than an
   expression written inline inside each run script. It is the thing being
   claimed, so it has a name.
3. A measurement cannot be constructed without its control (`control.py`).
   edit-slice stated that rule in prose and relied on the author remembering
   it. Here a reading without a baseline does not type-check, because a
   coefficient of 1.000 means nothing without the floor that says the pipeline
   was capable of returning something else.

The measurement code itself is lifted unchanged from edit-slice, deliberately.
A rewrite would have moved the numbers, and the numbers being comparable across
both projects is the only reason to share the code at all.
"""

from __future__ import annotations

__version__ = "0.1.0"

from .arch import UnsupportedArchitecture, key_site, resolve_arch
from .coefficient import Coefficient, Regime, coefficient_for
from .control import Baseline, Reading, Unbaselined
from .rome import (LAYER, EditSpec, RankOneEdit, SubjectNotInPrompt, compute_v,
                   read_key_and_value, subject_last_index)
from .remote import DEFAULT_MODEL, connect, quiet_stdout, retrying, score_pairs
from .whiten import Whitener

__all__ = [
    "Baseline", "Coefficient", "Regime", "UnsupportedArchitecture", "DEFAULT_MODEL", "EditSpec", "LAYER", "RankOneEdit",
    "Reading", "SubjectNotInPrompt", "Unbaselined", "Whitener", "coefficient_for", "compute_v", "connect",
    "key_site", "quiet_stdout", "read_key_and_value", "resolve_arch", "retrying",
    "score_pairs", "subject_last_index",
]
