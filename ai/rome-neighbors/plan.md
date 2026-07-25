# Project: ROME Neighbors — Neighborhood Consistency in Model Editing

_Last updated: 2026-07-22 by O-001_

## Objective

When a fact is edited in a language model (e.g. "The Eiffel Tower is in Paris"
→ "The Eiffel Tower is in Rome"), the logically entailed *neighbor* facts should
also update. They usually don't. Understand why, measure the gap precisely, and
explore what would be needed to fix it.

Greenlit by Natalie (Bau Lab) — 2026-07-22.

## The Core Problem

A single factual edit carries **implicit logical consequences** — neighbors:

  F  : "The Eiffel Tower is in Rome"         ← the edit
  N1 : "What city is the Eiffel Tower in?"   → Rome      (direct paraphrase)
  N2 : "What country is the Eiffel Tower in?" → Italy    (one hop: Rome → Italy)
  N3 : "What language is spoken near the Eiffel Tower?" → Italian (two hops)
  N4 : "What is in Rome?" → [includes Eiffel Tower]     (reverse lookup)

ROME edits F correctly. N1 sometimes follows. N2–N4 almost never do.
This is the **ripple effect gap**: edits are local, but facts are relational.

## Research Questions

1. **How far does a ROME edit propagate?** Measure accuracy at N1, N2, N3, N4
   hops from the edited fact on GPT-J-6B via NDIF.
2. **Where does propagation fail?** Is it an attention failure, an MLP storage
   failure, or a retrieval failure?
3. **What does the residual stream look like at neighbor queries?** Do the
   activations at the edited subject position change after the edit?
4. **Can a second targeted edit fix a neighbor?** Manual cascade editing —
   does editing N2 explicitly after editing F restore consistency?

## Current Phase

Phase 1 — Literature & Baseline Setup

## Active Tickets

| ID    | Agent      | Title                                    | Status      |
| ----- | ---------- | ---------------------------------------- | ----------- |
| O-001 | Orchestrat | Initialize project structure             | closed      |
| R-001 | Researcher | Survey model editing literature          | open        |
| R-002 | Researcher | Map neighbor taxonomy from ripple papers | open        |
| E-001 | Engineer   | Baseline fact recall on GPT-J-6B (NDIF) | open        |

## Blocked

_(none)_

## Completed This Session

- O-001 · Initialize project structure

## Experiment Sequence

R-001 + R-002 run in parallel (both are reading/research).
E-001 can start immediately — baseline recall needs no prior reading.
E-002 (single ROME edit) opens after E-001 confirms recall baseline.
E-003 (neighbor probe) opens after E-002.
E-004 (ripple sweep) opens after E-003.

## North Star

> See the gap yourself: edit one fact on GPT-J-6B, watch the neighbors fail,
> understand mechanistically *where* the failure lives.
