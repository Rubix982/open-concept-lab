# [E-003] Destination: the new answer goes where the edit said

_2026-11-01 · Llama-3.1-8B · layer 5 · the same 495 probes and the same three arms as [E-002] · seed 1538_

## The question

[E-002] found that **destruction** — what happens to the model's own pre-edit answer — is keyed on *whose* key the edit touched and almost not at all on *what* the edit said. [E-014], on a different probe set under a different metric, found **destination** to be content-specific. Reading those two against each other gives a two-route story, and a story that fits three experiments it was not tested against is the cheapest kind to tell. This measures both halves on one probe set under one metric.

Only the readout changed: from the probability of a named token to a full-vocabulary argmax. The arms, the probes, the edits and the donor pairing are [E-002]'s, read from its output rather than recomputed.

## The answer

```
                       base   real    ctl  other
top-1 lands in the
injected country         1%    29%     1%     1%
```

Paired over the 495 probes, bootstrap 10,000:

```
destination   real - ctl     +0.2828   95% CI (+0.2424, +0.3232)
              ctl  - other   +0.0000   95% CI (-0.0101, +0.0101)

destruction   real - ctl     +0.0009   95% CI (+0.0004, +0.0024)   [E-002]
              ctl  - other   +0.0583   95% CI (+0.0472, +0.0732)   [E-002]
```

**The two halves separate, and they separate in opposite directions on the same probes.** Destruction barely distinguishes the real edit from a different edit on the same person (+0.0009) and strongly distinguishes that person from someone else (+0.0583). Destination does the reverse: the real edit delivers (+0.2828 over the control) and the same-subject control delivers *nothing at all* — its interval straddles zero against the different-subject arm, and its 1% is the base rate.

Discordant pairs: 142 probes where the real edit lands in the injected country and the control does not; **2** the other way.

## By family

```
family            base   real    ctl  other
semantics           0%    48%     0%     0%
repetition          0%    45%     0%     0%
position            0%    29%     1%     0%
alias               1%    20%     1%     0%
exposure            2%    17%     0%     2%
discrimination      3%     5%     0%     3%
```

The real arm's deliveries are ordinary city names — Copenhagen 24, Santiago 14, Stockholm 14, Helsinki 13 — against the control arm's unmoved Paris, London and New York. 30 of the 42 subjects deliver on at least one probe.

`discrimination` is the one family where the real arm barely delivers (5%), and it is also the family whose probes name a *different* person or a place as the subject. That is the expected direction and it is not explained here.

## Three controls, checked before the run rather than after

1. **The hit test is not an equality.** The probes ask for a city and the edit injects a country, so `top1 == target` would have scored the real arm near zero and looked like a finding. A hit is a top-1 token that begins a city in the injected country, over [E-014]'s own 81-city map.
2. **The token → country map adds no slack.** 81 cities give 80 distinct first tokens, each resolving to exactly one country. Zero ambiguous. Asserted at run time, not assumed.
3. **`ctl` is not the weaker edit.** Signed paired median difference in `‖delta_v‖/‖k*‖` is +0.0899 with `ctl` weaker in 20 of 42 — unbiased in direction. The unsigned median is 0.7614 over a range of 2.627, so the two are **not matched subject by subject**; the claim here is aggregate and no per-subject claim is made.

The anchor gate passed at a worst deviation of **0.000e+00** over 42 readings.

## The limit, which belongs with the result

The control edit injects an **occupation** (`By profession, {} is a` → `urban planner`) and these probes ask for a **city**. So there is no arm-symmetric check available on this probe set: we cannot ask whether the control delivers *its own* content somewhere. What is measured is that **content which can answer the question is what arrives** — not that every edit delivers its own content.

A reader may put it the other way round: of course an occupation does not show up as a city. That reading and ours are the same claim. The result is that the control edit, matched in direction of magnitude and applied to the same person's key, destroys the old answer just as thoroughly (+0.0009 apart) while supplying none of the new one.

## What it settles

One rank-one update does two separable things. It breaks the old answer because it touched that subject's key — which a different fact about the same person does equally well, and a different person does not do at all. It supplies the new answer because of what it said — which only the real edit does.

This replicates [E-014]'s 67% / 5% on a second probe set, in a different metric family, at 29% / 1%. The rates differ because [E-014] scored a restricted city pool by teacher forcing and this scores a free argmax over the whole vocabulary; the separation is the quantity that carries across, not the level.
