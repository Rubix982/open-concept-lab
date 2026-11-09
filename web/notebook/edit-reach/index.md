---
title: edit-reach
sidebar_label: Overview
sidebar_position: 1
description: Testing whether an edit's reach can be predicted before the edit is applied. It cannot — and what the measure does detect is worth saying precisely.
---

# edit-reach

[edit-slice](/notebook/edit-slice/) found that a ROME edit reaches everything sharing its subject by arithmetic rather than by inference. This project asked whether that finding could be turned into a tool: a number, computed in one forward pass through the **unedited** model, that says in advance how far an edit will travel.

The two are kept apart on purpose. edit-slice accumulates findings. This one was to produce a working screen or show that it cannot.

It showed that it cannot. [The paper](./paper) is where the line falls.

<Claim
  label="What the instrument is"
  superseded="The coefficient screens whether a benchmark item can test propagation, so it can be used as a pre-run gate on propagation evaluations."
  record={{
    "What replaced it": "It detects contamination — that a prompt names the edited subject, and which relation it asks about. It does not detect propagation.",
    "Why the first version failed": "C-001 (the coefficient does not predict measured movement) and E-004 (in the far field, a stranger's edit on the same relation reaches a question as much as the real subject's edit does).",
    Confidence: "High on the near field, which is analytic. The far-field result is one model, one layer, two-hop chains.",
  }}
>
  A contamination detector, not a propagation detector.
</Claim>

## What is here

| | |
| --- | --- |
| [A cheap pre-edit estimate detects contamination, not propagation](./paper) | The paper. Ten sections, three appendices: the method, the control, the result, what it says about a published benchmark, the findings ledger with every claim this project withdrew, and the provenance of every number. |
| [`editreach` 0.1.0](https://github.com/Rubix982/open-concept-lab/tree/main/ai/edit-reach) | Ten modules, about 1,900 lines. A reading without a control does not type-check. |
| [NDIF reproducibility reference](https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/docs/ndif-reproducibility.md) | Whether a number read off a remote model is the same number tomorrow, with the conformance suite that found four errors in it. |

## What would change this

A layer sweep that finds far-field dynamic range at some depth other than 5 brings the screen back at that depth, and narrows the scope sentence to layer 5. A graded relation-similarity control that moves the +0.0002 would mean the categorical split is too coarse. Lifting the backward-pass block would let the delivery-to-effect link be tested on a free draw instead of 42 cached survivors.
