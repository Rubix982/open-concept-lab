# Project: Lookback Experiments — OID Co-location & Binding Validation

_Last updated: 2026-07-04 by O-002_

## Objective

Empirically validate the lookback mechanism's OID co-location claim from
"Language Models Use Lookbacks to Track Beliefs" (ICLR 2026) by running
probing experiments and causal interventions on GPT-2 locally. Produce data
that confirms or qualifies the paper's findings on a small model.

## Current Phase

Phase 1 — OID Co-location Probe

## Active Tickets

| ID    | Agent    | Title                              | Status      |
| ----- | -------- | ---------------------------------- | ----------- |
| E-002 | Engineer | Binding lookback attention maps    | open        |
| E-003 | Engineer | IIA curve (causal intervention)    | open        |

## Blocked

_(none — E-002 unblocked after E-001 closed)_

## Completed This Session

- O-001 · Initialize project structure
- E-001 · OID co-location linear probe — closed 2026-07-04

## Key Finding (E-001)

Object identity linearly decodable at state token position, layers 6–11 (80% CV accuracy,
chance=25%). Character identity NOT at state token — needs probing at character name
token positions. E-002 updated to include this character-position probe.

## Experiment Sequence

E-002 next: (a) probe character identity at name token, (b) attention maps at answer token.
E-003 after: causal IIA curve — patch residual stream, measure output flip.

## North Star

> See the OID co-location in the activations yourself.
> Replicate the behaviour. Get your own data.
