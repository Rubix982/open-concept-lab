# edit-reach

**How far do an edit's reverberations travel, and how much of that can we see before we run the edit?**

That is the whole project. `ai/edit-slice` is the record of what was found; this is the attempt to turn one of those findings into something usable.

## Why it exists

A benchmark can show that an edit broke something. It can never show that an edit broke nothing — an absent item and an absent failure look the same. Writing a bigger item set does not fix that, because a hand-written set measures the limits of whoever wrote it.

So the move is to replace enumeration with measurement: a quantity defined for any prompt rather than for a listed set, so an item can be scored without having been anticipated. It still has to be evaluated on prompts we have — it removes the need to foresee which ones matter, not the need for any.

[E-036] gives a candidate (`edit-slice/results/E-036-ripple-coefficients.json`, and the decision behind it in `edit-slice/agents/shared/decisions.md`). ROME's update is rank-one, so a coefficient says how much of the edit arrives at a token, and it needs one forward pass through the **unedited** model.

The gap this project exists to close is that the coefficient measures **delivery, not effect**. Until that link is established, a screen built on it is a proposal, not an instrument — and no threshold can be set on it.

## Where to start

Open `CARD.md`. One card is open at a time and it is the only thing being worked on.

| file | what it is |
| --- | --- |
| `CARD.md` | the open card, and closed ones with their results |
| `CLAUDE.md` | scope, what is binding, what is out of bounds |
| `plan.md` | tickets and phase |
| `threads.md` | open questions, parked rather than lost |
| `src/editreach/` | the package — the measurement code has one home |
| `tests/` | 13 tests; the control module's job is to refuse, so most of them check that it does |

## Setup

```bash
source .venv/bin/activate
pip install -r requirements.txt   # pins copied from edit-slice
pip install -e .
```

## What it gives you

```python
from editreach import connect, coefficient_for, Baseline

model = connect("meta-llama/Llama-3.1-8B")
cs = coefficient_for(model, prompts, positions, u=u, denom=denom, layer=5)

floor = Baseline.of("different subject", other_subject_values)
print(cs[0].against(floor))
# preceded @ L5: 0.982 against a different subject floor of 0.067, margin +0.915
```

`against(floor)` is not optional sugar. `Reading` cannot be built without a
baseline, because a coefficient of 1.000 is almost content-free on its own — a
pipeline hard-wired to return 1 produces the same number. What makes it mean
something is that the same code path returns 0.082 for a different subject.

## Relationship to edit-slice

`ai/edit-slice` keeps its findings, its probe sets and its nine research modules.
Its `remote`, `edit`, `whiten`, `probing`, `data` and `logs` are now shims that
forward here, so its 79 existing scripts run unchanged against the same code.
New work in either project imports `editreach`.
