# Ripple Effects of Knowledge Editing in Language Models

**Paper:** Cohen, Biran, Yoran, Globerson, Geva — EMNLP 2023
**arXiv:** https://arxiv.org/abs/2307.12976

## What it claims

Knowledge editing methods (ROME, MEMIT, MEND, etc.) succeed on the *direct*
edit but consistently fail on *ripple* effects — facts logically entailed by
the edit.

## The ripple effect taxonomy (THIS IS THE CORE READING FOR OUR WORK)

Given edit: (subject S, relation R, old object O → new object O*)

| Type | Description | Example |
|------|-------------|---------|
| **Logical** | Direct entailment of the edit | "What is the capital of Italy?" after moving Eiffel Tower to Rome |
| **Compositionality** | Multi-hop: edit + background knowledge | "What currency is used near the Eiffel Tower?" |
| **Symmetry** | Reverse relation | "What is located in Rome?" now includes Eiffel Tower |
| **Paraphrase** | Same fact, different surface form | "Where can you find the Eiffel Tower?" |
| **Subject aliasing** | Different names for same subject | "The Iron Lady of Paris is in ___" |

## The evaluation dataset

RippleEdits: 5,000 edits × ~7 ripple questions each.
CounterFact subset used for comparison with ROME/MEMIT baselines.

## Key finding

All editing methods score well on direct edit (~90%+) and paraphrase (~70%).
They collapse on compositionality and symmetry (often below 20%).

The gap is the research problem.

## Why does it fail?

The paper diagnoses but does not fully explain. Hypotheses:
1. The MLP weight update is "point-like" — changes the subject's stored attribute
   but does not propagate through inference chains
2. Attention routing for neighbor queries does not pass through the edited MLP
3. The model stores multi-hop facts redundantly — there are other "copies" of
   the old fact that the edit didn't reach

## Questions for our work

- Which hypothesis is correct for GPT-J-6B? We can test this with NNSight:
  causal trace a *neighbor* query — does it route through the edited layer?
- If the neighbor query does NOT route through the edited layer, that's the
  mechanistic explanation: not a storage failure, an *access* failure.

---

_Notes written: [date]_
