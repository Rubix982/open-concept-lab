---
title: edit-slice
sidebar_label: edit-slice
sidebar_position: 1
description: Whether a weight-level knowledge edit leaves its own grounds intact and contradictory.
---

# edit-slice

Editing a fact into a model's weights changes one thing and disturbs an unknown
amount of everything else. The standard way to evaluate that disturbance looks
*forward*, at what follows from the edit. This project looks the other way, at
the facts that were premises for the edited fact and are still sitting there
after it changes.

<Claim
  label="What the project claims"
  superseded="Everyone probes forward from an edit; nobody probes backward."
  record={{
    Confidence: "Medium — one benchmark read closely, not a survey",
    Falsified_by: "A published grounds probe distinct from argument inversion",
    Revised: "10 September 2026",
  }}
>
  Inverting the arguments of an edited fact is covered, by RippleEdits, since
  2024. Probing the <em>distinct</em> facts that were premises for the edited
  fact is not covered by anything I can find.
</Claim>

## The distinction the project rests on

Two things look backward and are not the same thing. Keeping them apart is most
of the contribution.

| | What it probes | Covered? |
| --- | --- | --- |
| Argument order | The edited triple with its arguments swapped — `(Rome, contains, Eiffel)` | Yes, RippleEdits Logical Generalization <Cite id="cohen2024ripple" /> |
| Justification order | Distinct facts whose truth was a premise — *built for the 1889 Paris Exposition* | Not that I can find |

An edited model can hold a belief together with a complete, untouched set of
grounds for its negation. That state is what the project calls an **orphan**.

<Aside>
  The transitive case is the sharper one. Getting from "Eiffel is in Rome" to
  "Eiffel is in Italy" requires <em>using</em> the fact that Rome is in Italy,
  but the benchmark only ever checks the conclusion. Whether the premise
  survived is never asked.
</Aside>

## Status

<Status kind="provisional">Phase 0 — definitions and scope, near complete</Status>

Settled so far:

- The scope boundary against [rome-neighbors](/notebook/rome-neighbors/) is
  reuse of code, not of scope.
- RippleEdits' Logical Generalization is not a grounds probe. The claim above
  narrowed as a result, which is the useful thing that came out of Phase 0.

Open:

- Can the benchmark generator's distance function take a code dependency graph
  as input, so grounds are *discovered* rather than enumerated by hand?
- What decides that a fact was a premise, in a way a reviewer can check?

## Deliverable

Two panels and one number: forward propagation against justification-order
survival, on the same edits, with the gap between them stated as a rate.

<References ids={["cohen2024ripple", "meng2022rome", "meng2023memit"]} />
