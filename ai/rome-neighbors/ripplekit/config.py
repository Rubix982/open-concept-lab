"""Central config — the single source of truth for constants that were
duplicated across the demo scripts."""

import os
from pathlib import Path

# ── Model / NDIF ────────────────────────────────────────────────────────────
MODEL_ID: str = "EleutherAI/gpt-j-6b"
N_LAYERS: int = 28
D_MODEL: int = 4096

# ── Experiment defaults ──────────────────────────────────────────────────────
DEFAULT_LAYER: int = 15
SWEEP_LAYERS: list[int] = [int(x) for x in os.environ.get("SWEEP_LAYERS", "6,9,12,15,18").split(",")]
SEED: int = 1538
N_EDITS: int = int(os.environ.get("N_EDITS", "40"))          # override for fast passes
MAX_PER_CRITERION: int = int(os.environ.get("MAX_PER_CRITERION", "3"))
K_ANCHOR: int = 3

# ── Neighbour typing (RippleEdits criteria → our types) ──────────────────────
# NB: the repo's field is correctly spelled "Relation_Specificity" in the data,
# but we tolerate the README's "Specifity" too. Keys normalised (lower, "_").
CRITERION_TO_TYPE: dict[str, str] = {
    "logical_generalization": "1hop",
    "compositionality_i": "2hop",
    "compositionality_ii": "2hop",
    "subject_aliasing": "paraphrase",
    "relation_specificity": "locality",
    "relation_specifity": "locality",   # README misspelling, just in case
    "forgetfulness": "control",
}
TYPES: list[str] = ["paraphrase", "1hop", "2hop", "locality", "control"]
# types expected to propagate after an edit (vs. locality/control)
PROPAGATE_TYPES: list[str] = ["paraphrase", "1hop", "2hop"]

# ── Paths ─────────────────────────────────────────────────────────────────────
RIPPLEEDITS_FILE: Path = Path(os.environ.get(
    "RIPPLEEDITS_FILE",
    str(Path.home() / "code" / "RippleEdits" / "data" / "benchmark" / "popular.json"),
))
RESULTS_DIR: Path = Path(__file__).resolve().parent.parent / "results"


def api_key() -> str:
    """Read the NDIF API key from the environment (never hardcode)."""
    key = os.environ.get("NNSIGHT_API_KEY", "")
    if not key:
        raise EnvironmentError("NNSIGHT_API_KEY not set. Run: source ~/.zshrc")
    return key
