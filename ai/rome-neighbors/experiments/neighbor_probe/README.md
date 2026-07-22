# Experiment: Neighbor Probe After ROME Edit

**Ticket:** E-003
**Goal:** After one ROME edit, measure how many neighbor facts update correctly.

## What to implement

`probe.py` — takes the edited triple from E-002, runs all neighbor query types
(N0–N4), records accuracy per type. This is the core experiment.

## Neighbor query format (`data/neighbor_queries.json`)

```json
{
  "edit": {
    "subject": "The Eiffel Tower",
    "old_object": "Paris",
    "new_object": "Rome"
  },
  "neighbors": [
    {
      "type": "N0_paraphrase",
      "prompt": "Where is the Eiffel Tower located?",
      "expected_new": "Rome",
      "expected_old": "Paris"
    },
    {
      "type": "N1_logical",
      "prompt": "The Eiffel Tower is in the country of",
      "expected_new": "Italy",
      "expected_old": "France",
      "reasoning": "Rome → Italy"
    },
    {
      "type": "N2_compositional",
      "prompt": "The official language spoken where the Eiffel Tower stands is",
      "expected_new": "Italian",
      "expected_old": "French",
      "reasoning": "Rome → Italy → Italian"
    },
    {
      "type": "N_reverse",
      "prompt": "A famous landmark located in Rome is",
      "expected_new": "Eiffel Tower",
      "expected_old": null,
      "reasoning": "reverse lookup of new location"
    },
    {
      "type": "N_distractor",
      "prompt": "The Colosseum is located in",
      "expected": "Rome",
      "should_change": false,
      "reasoning": "unrelated fact — should NOT change"
    }
  ]
}
```

## Measurement

For each neighbor, after the edit:
- Does the model's top-1 prediction match `expected_new`? → success
- Does it still predict `expected_old`? → stale (edit didn't propagate)
- Does it predict something else? → incoherent

## The mechanistic follow-up (NNSight)

For any neighbor query that FAILS: run a causal trace to find where the
forward pass diverges from the expected path. Does the trace route through
the edited MLP layer? If not — that's the access failure hypothesis confirmed.

## Output format (`output/neighbor_accuracy.json`)

```json
{
  "edit_success": true,
  "neighbors": [
    {"type": "N0_paraphrase", "result": "success", "top1": "Rome"},
    {"type": "N1_logical",    "result": "stale",   "top1": "France"},
    {"type": "N2_compositional", "result": "stale", "top1": "French"},
    {"type": "N_reverse",    "result": "stale",   "top1": "Colosseum"},
    {"type": "N_distractor", "result": "correct",  "top1": "Rome"}
  ],
  "summary": {"N0": 1.0, "N1": 0.0, "N2": 0.0, "reverse": 0.0, "specificity": 1.0}
}
```
