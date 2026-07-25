# Experiment: Baseline Fact Recall

**Ticket:** E-001
**Goal:** Confirm which facts GPT-J-6B knows before any editing.

## What to implement

`recall.py` — loads fact triples from `data/triples.json`, runs each as a
cloze prompt via NNSight remote trace on GPT-J-6B, records rank of correct
token and top-5 predictions.

## Input format (`data/triples.json`)

```json
[
  {
    "id": "eiffel_location",
    "subject": "The Eiffel Tower",
    "relation": "is located in the city of",
    "object": "Paris",
    "prompt": "The Eiffel Tower is located in the city of",
    "source": "counterfact"
  }
]
```

## Output format (`output/recall_results.json`)

```json
[
  {
    "id": "eiffel_location",
    "object": "Paris",
    "top1_token": " Paris",
    "correct_rank": 1,
    "correct_logit": 14.2,
    "correct_prob": 0.73,
    "known": true
  }
]
```

## Success criterion

≥8/10 triples recalled correctly (correct token rank ≤ 5).
Filter to these triples — they become the edit targets for E-002.

## Key NNSight pattern

```python
with model.trace(prompt, remote=True):
    logits = model.lm_head.output.save()
# logits shape: [1, seq_len, vocab_size]
last = logits[0, -1]   # last token position
```
