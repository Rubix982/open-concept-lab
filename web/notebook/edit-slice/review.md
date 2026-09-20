---
title: Review packet
sidebar_label: Review packet
sidebar_position: 2
description: Everything edit-slice established in a week, what was withdrawn, and where it is weakest — assembled for someone deciding whether any of it is worth their time.
---

# Review packet

_Assembled 2026-09-20. Revised in place. This page exists to be attacked._

The [running write-up](/writing/five-days) is the narrative. This is the map: what is
claimed, what was withdrawn, what the evidence actually is, and where I think it breaks.
If you read one section, read [What to attack](#what-to-attack).

---

## The claim, in one paragraph

ROME's rank-one update divides by `u·k*`. A probe prompt that **begins with the edited
subject** has, at the subject's last token, a key identical to `k*` — causal attention
guarantees it, since nothing before that token differs. So the update coefficient there is
`(k*·u)/(u·k*) = 1` **exactly**, for any `u`, hence for any choice of covariance `C`, at
every layer, whatever relation the probe asks about. Same-subject probes receive the full,
unattenuated edit vector by arithmetic rather than by tuning. A probe about a *different*
subject receives 0.082 of it. That gap — measured, non-overlapping — is the project's
central result, and it explains why a weight edit's apparent "propagation" to related facts
can be displacement keyed on the subject rather than anything inferential.

---

## The evidence chain

Each step was pre-registered with a falsification condition before it ran.

| # | question | result |
| --- | --- | --- |
| E-014 | does editing a conclusion move its premise? | yes — birth-city probe lands in the edited country **67%** vs **5%** baseline and **5%** same-subject control |
| E-015 | is that an inference? | **no.** Editing where someone *works* relocates their *birthplace* identically. 28/42 both arms, paired gap **+0.0 pp**, McNemar p = 1.000 |
| E-016 | is the null an artifact of a blunt editor? | **no.** A whitened update, measured 20× more selective on held-out keys, gives 42/42 identical destinations |
| E-016 | then why? | the coefficient at the subject's last token is **exactly 1.0000** under both editors |
| E-017 | does any probe form escape? | a *different relation* also scores 1.000; reordering the subject costs ~7% at layer 5 |
| T-075 | at every layer? | prefix-sharing: **1.000 at all seven layers**. Reordered: decays to **0.58** by layer 20 |
| E-018 | what is the floor? | a different subject scores **0.082**; distributions do not overlap |

---

## Claim status

Nothing below is quietly revised. Every withdrawal has an entry saying what killed it.

| claim | status | what changed it |
| --- | --- | --- |
| Backward probing is unexplored | **narrowed** | RippleEdits' Logical Generalization covers inverse/symmetric relations |
| Edits leave grounds *contradictory* | **withdrawn** | E-002 — grounds are evidential; the state is improbable, not impossible |
| CounterFact verifies possession | **withdrawn** | D-002 — reverses R-006 from Appendix D; construction is model-independent |
| The `outer` deficit is pool concentration | **withdrawn** | E-009b — it is two strings, US and UK |
| Surface-form finding is novel | **withdrawn** | R-010 — Holtzman et al., EMNLP 2021; our lift test is essentially their PMI |
| Possession × editability is unclaimed | **withdrawn** | R-010 — arXiv 2509.17482, same model, Sept 2025 |
| The model revises the defeasible premise | **withdrawn** | E-015 — work-country edit does the same thing |
| Leakage is structural *in ROME* | **narrowed** | T-075 — structural given the layer; reordering helps at depth |
| Four nnsight constraints | **withdrawn, then partly reinstated** | O-007 (flaky node), then O-008 (one is real and silent) |
| Prefix-sharing probes receive the full delta | **holds** | E-016 analytic · E-017 · T-075 all layers · E-018 floor |

Ten claims. **Seven withdrawn or narrowed.** That ratio is the honest summary of the week.

---

## What to attack

Ordered by how much damage I think each does.

**1 · n = 42, one model, one relation family, one layer.** The chain set is 136 mined,
78 gated, 42 carried through the edit after a week of infrastructure failures. Everything
is an *existence* claim; no rate in this project is defensible, and I have tried to keep
every artifact from implying one. If you think the mechanism needs a frequency statement to
matter, that is a fair objection and I cannot meet it.

**2 · The mechanism is arithmetic, so is it interesting?** `(k*·u)/(u·k*) = 1` is a line of
algebra. A reasonable reviewer could say this is a known property of rank-one editing that
practitioners already assume. I have not found it stated, but I have not surveyed
exhaustively — and "I could not find it" is the weakest possible form of novelty claim.

**3 · Coefficient is not behaviour.** T-075 shows the coefficient decays with depth, but
E-016's own scale test showed coefficient and destination are *not* linearly related —
rescaling by 0.27 broke relocation in 3 of 4 chains, yet whitening's 3.7× attenuation
changed nothing. So "0.58 at layer 20" does not license "less displacement at layer 20."
That experiment has not been run.

**4 · `C = I` is what we mostly ran.** EasyEdit ships `mom2_adjustment: false` in all
fourteen configs, so this is what the field runs — but it is not what the ROME paper
describes. Our whitened arm used a covariance estimated over the *CounterFact prompt
distribution*, not Wikipedia, from 2048 keys with a ridge chosen by an in-sample/held-out
agreement rule. All three are defensible and none is ROME.

**5 · Everything is behavioural.** We can say the model *behaves as if*; we cannot say a
component *causes*. No activation patching, no interchange interventions. This is the
largest methodological hole and it is deliberate scope, not oversight.

**6 · The adversary agent checks claims against our own record.** It caught a real
overclaim before publication once, which is why it exists. But it cannot catch an error the
whole record shares — which is the same gap as "nothing externally judged", showing up in
the tooling.

---

## Corrections, as a feature

Three of this week's findings are corrections to earlier findings of ours, and two are
corrections to corrections. I list them because a reviewer should weight a record by how it
behaves when it is wrong, not only by what it concludes.

- **R-006 → D-002.** I read ROME §3.3 and concluded CounterFact filters on possession. The
  construction appendix says otherwise. Reversed from the primary source.
- **E-009b.** A "concentration" explanation was disproved by joining the held flag against
  the answer string — data already on disk, never looked at that way.
- **O-007 → O-008.** I attributed four failures to four code changes, then discovered a
  flaky backend and retracted all four. One of the four was real, and its failure mode is
  *silent* — a `for` loop inside a trace executes zero saves and raises nothing. A
  correction that retracts too much is still a correction that has to be corrected.

The rule extracted from the third: **before attributing a failure to a change, re-run the
thing that worked.** O-008 was gathered that way and is the better entry for it.

---

## Where everything is

| artifact | what it is |
| --- | --- |
| `agents/shared/decisions.md` | 19 entries — every result and correction, with falsification stated before the run |
| `agents/shared/findings.md` | 16 entries — literature reads, including the two that killed directions |
| `threads.md` | 57 threads: 40 answered, 8 parked, 4 open, 3 dropped, 2 active |
| `design.md` | three design passes; Part III is live, Parts I–II are superseded and kept |
| `results/*.json` | per-item records for E-011 through E-018 and T-075 |
| `logs/` | every run, levelled, committed — including the ones that failed |
| `src/possession.py` | the shipped measure; `src/discrimination.py` the paired control |

---

## What I would want a reviewer to decide

1. Is the pinned-coefficient result **known**? That is the question I cannot answer from
   inside.
2. Does it **matter for ripple benchmarks**? Every propagation benchmark I know of probes
   with prompts that begin with the subject. If the coefficient is pinned on exactly those
   prompts, their measurements may be partly mechanical. I have not worked this out and it
   is the sharpest thing the arc raises.
3. Is **n = 42 with an existence claim** publishable in any venue, or does this need the
   frequency work it currently forbids itself?
