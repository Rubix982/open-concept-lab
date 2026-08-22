"""
Smoke test: one real ROME edit via EasyEdit (isolated .venv-edit).
Confirms ROME (rank-1 + KL, the specificity mechanism our FT lacked) runs and the
edit takes. Run with the EDIT venv:
    source .venv-edit/bin/activate
    PYTHONPATH=~/code/EasyEdit python experiments/edit_propagation/rome_smoke.py
"""

import os
import sys

sys.path.insert(0, os.path.expanduser("~/code/EasyEdit"))
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from easyeditor import ROMEHyperParams, BaseEditor

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = os.environ.get("ROME_CFG", "rome_gpt2.yaml")   # gpt2 reliable; medium NaNs here
hparams = ROMEHyperParams.from_hparams(os.path.join(HERE, CFG))

editor = BaseEditor.from_hparams(hparams)
metrics, edited_model, _ = editor.edit(
    prompts=["The Eiffel Tower is in the city of"],
    target_new=["Rome"],
    subject=["Eiffel Tower"],
    sequential_edit=False,
)
print("\n=ROME METRICS=", metrics)
print("=ROME SMOKE DONE=")
