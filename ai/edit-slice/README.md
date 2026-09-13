# edit-slice

A **possession filter** for knowledge-editing experiments: before you edit a fact,
check whether the model held it.

## Why

Propagation results in knowledge editing are conditional on the model having held
the fact being edited. CounterFact does filter for this — records were selected
where `P(true) > P(counterfactual)` — but that filter was applied **once, in 2022,
against its authors' model**, and the same fixed 21,919 records are reused on every
model since. Nothing in the usual pipeline re-establishes the guarantee.

Measured here, possession under a harder test:

| model | possession |
| --- | ---: |
| gpt-j-6b | 56% |
| Llama-3.1-8B | 74% |
| Llama-3.1-70B | 79% |
| Llama-3.1-405B | 85% |

Not saturated at 405B. GPT-J holds **13%** of `P19` place-of-birth — the relation
with the richest surrounding context. An orphan or propagation failure measured on
a fact the model never held is an artifact of ignorance, not a property of the
editor.

## Use

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python src/run_filter.py --config configs/possession_gptj.json     # CounterFact
python src/run_filter.py --config configs/possession_byo.json      # your own edits
```

Bring your own edit set as JSONL:

```json
{"case_id": "a1", "prompt": "The capital city of France is", "subject": "France", "true_answer": "Paris", "relation_id": "capital"}
```

`relation_id` groups items so candidates are type-matched. Point
`_candidate_reference` at a **larger** set than the one you are filtering — see
`agents/shared/decisions.md` [E-007] for why that matters more than it sounds.

NDIF backends need `NNSIGHT_API_KEY` (from login.ndif.us). `backend: "local"` runs
HuggingFace models on the machine instead.

## What the measure is

Possession requires **both**:

1. the true answer ranks **first** among N type-matched candidates, and
2. it ranks higher with the real subject than with the subject replaced by a
   placeholder — so a model riding the template's base rate earns nothing.

## Reading the numbers honestly

- **Absolute levels depend on `n_candidates`.** Ordering across models is robust;
  levels are not. The config is written beside every result for this reason.
- **Scoring is teacher-forced.** That measures whether the knowledge is *present*,
  not whether the model would spontaneously emit it. On identical items: two-way
  75%, constrained teacher-forced 61%, free generation 12% — and the last is
  depressed mostly by prompt ambiguity, not ignorance.
- **Coverage is reported.** Items that cannot be scored are listed with reasons,
  never dropped silently.

## Layout

```
src/        possession.py (the filter) · probing.py (local) · remote.py (NDIF)
            typematch.py · data.py · wikidata.py
configs/    run configs — parameters live in files, not argv defaults
data/       pinned CounterFact + dated Wikidata snapshots, checksummed
probes/     contestable tables: relation modality, ground templates
agents/     tickets, findings, decisions
notes/      definitions.md — binding, and the most important file here
```

Research record: `design.md` (ten lenses), `threads.md`, `agents/shared/findings.md`.
