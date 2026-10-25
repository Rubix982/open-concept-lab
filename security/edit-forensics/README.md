# edit-forensics

**Can a defender name a fact someone secretly planted in a model, and does that still
work when the attacker tries to hide it?**

In 2023 "PoisonGPT" used ROME, a one-layer rank-one weight edit, to plant a false fact
in an open model and republish it. This project plays both sides on GPT-2:

- **Attacker** (`src/rome.py`): a compact ROME that plants CounterFact facts. It can
  also spread one edit over several layers (MEMIT-style), stack many edits, add
  weight noise, fine-tune afterwards, or add decoy updates.
- **Defender** (`src/forensics.py`, `src/invert.py`): given the suspect checkpoint,
  1. find the edited layer, from the weight diff against the claimed base;
  2. find the planted **subject**, by scoring 20,391 names on how hard the update fires on them;
  3. read back the planted **object**, by asking both models all 34 relation prompts about that subject;
  4. with **no base model**, flag the subject from outsized MLP writes;
  5. with **no name list**, search token strings for the trigger the update was built for (GCG).

Results: **`report.html`** (open it in a browser; it works from disk) and
`results/summary.json`. What changed mid-run and why: `notes/log.md`. Prior work and
where this sits: `notes/prior-art.md`. The one open question: `CARD.md`.

## Run

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./experiments/queue.sh                 # everything, one job at a time (hours)
.venv/bin/python src/summarize.py      # rebuild report.html from results/
```

Single pieces:

```bash
.venv/bin/python experiments/exp1_with_base.py gpt2-medium 100   # clean attacker
.venv/bin/python experiments/exp2_evasion.py noise 30            # noise | finetune | spread | batch | decoy
.venv/bin/python experiments/exp3_open_vocab.py 30               # no name list
SMOKE=1 .venv/bin/python experiments/exp2_evasion.py batch       # tiny version, to check it runs
```

The first run downloads WikiText-103 and computes key covariance stats. These are
cached in `cache/` (gitignored, about 0.3 GB per layer set).

## Layout

```
src/        common.py (model, hooks) · rome.py (attacker) · forensics.py, invert.py (defender) · summarize.py
experiments exp1 clean · exp2 evasion · exp3 open-vocab · queue.sh · dev scripts (readback_ab, gcg_dev, smoke)
results/    one JSON per experiment + logs
notes/      prior-art.md · log.md
data/       counterfact.json.gz (copied from ai/edit-slice)
```

## Known rough edges

- GPT-2 only. Uses an M-series GPU via MPS, and the machine swaps if two jobs run at once.
- The subject list is CounterFact's own subjects, so closed-list recovery is the easy setting.
- The object is scored on its first token only.
