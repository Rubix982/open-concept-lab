# TODO — resume next session

## 0 · Batch `possession.run()` across items — do this before re-running the gate

E-009 stalled on throughput, not correctness. `src/possession.py::run()` makes
**two remote calls per item**, so 408 chain facts is 816 round trips — one to two
hours. `possession_lift.py` already solved this: pack several items, both arms,
into a single trace via `remote.score_pairs`, which measured **8.3x faster**.

The shipped filter did not inherit that. It is the same cost-model mistake as
before — round trips are the budget, not FLOPs — and it is now inside the tool
other people are meant to run.

- [ ] Rework `run()` to batch N items per scorer call (N=4 worked at 50 candidates)
- [ ] Keep per-item caching; the cache key is already fingerprinted correctly
- [ ] Re-run `gate_chains.py`; it resumes from cache

---

# Earlier TODO — resume 2026-09-15

_State at handoff: tree clean, everything pushed. One arc delivered (possession
filter + published post), one arc newly un-parked (T-041, contraction existence)._

---

## 1 · Fix the chain family — the blocker, do this first

E-008 produced 62 chains from 120 seeds (52%). The pipeline works; the **family is
wrong**, and `probes/relation_modality.md` predicted it.

**`P131` is labelled mutable** — "boundaries are redrawn" — so editing the outer
fact admits a temporal reconciliation ("it's in Italy *now*"). That is the same
escape that made [E-002]'s cases non-contradictory, and T-058 claimed the opposite
without checking our own table.

**Fix: anchor the outer on a RIGID relation.**

```
inner-1   X was born in Paris      P19  — RIGID, no relocation escape
inner-2   Paris is in France       P131
------------------------------------------------ entails
outer     X was born in France
```

Editing the outer to Germany cannot be rescued by relocation, because birth cannot
be relocated. Residual escape — "Paris was in Germany at birth time" — is filtered
by excluding defunct states and disputed regions.

Concretely:
- [ ] Re-seed from CounterFact **P19** records (779 available) instead of P131/P17
- [ ] Keep `P131` as inner-2 only
- [ ] Update `src/chains.py` templates: outer becomes a birth-place prompt
- [ ] Check the other rigid relations for the same shape: **P20** place of death
      (816), **P740** location of formation (774) — all take containment as
      inner-2

## 2 · Fix the template type bug — 60% of current chains

```
"Gracie Mansion is located in the country of"  ->  New York City
```

The outer template names a type the answer does not have. **This is the same error
class as CounterFact's "died at" -> "the age of 90"** [T-044] which we published
about two days earlier.

- [ ] Either require Z to be a country (`P31` instance-of check against
      `Q6256`), or use a type-neutral outer template
- [ ] Add the check to `is_degenerate`, so it is enforced by the rule rather than
      noticed afterwards

## 3 · Filter defunct entities — 2/62 currently

Saratov Oblast -> Russian SFSR -> **Soviet Union**; Jablanica -> Serbia ->
**Federal Republic of Yugoslavia**. The model's answer depends on which era it
recalls.

- [ ] Reject chains containing dissolved states (`P576` dissolved/abolished date
      present on any entity in the chain)

## 4 · Possession-gate the chains — T-058's open point

A chain whose inner-2 the model does not hold cannot test contraction: there is
nothing to retract.

- [ ] Run all three facts per chain through the possession filter
      (`src/possession.py`, already built and verified)
- [ ] Report the shrinkage — it is a result, not overhead
- [ ] Expect real attrition: GPT-J holds 13% of P19 [E-005], so a P19-anchored
      family will lose a lot. **If it loses too much, that is itself the finding,**
      and the model choice moves to Llama-3.1-8B per [O-004]

## 5 · Then E-009 — the actual experiment

Only after 1–4.

- [ ] Edit the outer fact on Llama-3.1-8B via NDIF ([E-006] confirmed intervention
      and remote gradients both work)
- [ ] Probe inner-1 and inner-2 pre/post
- [ ] Ask: does the editor retract **either** premise, or leave both standing?
- [ ] **Existence claim only** [O-004]. No rate may be estimated from these sets.

---

## Standing, not urgent

- **GPT-2-XL under the constrained measure** — the one gap the published post
  admits. Needs a local run; conflicts with the NDIF-only preference. Small.
- **Show the post to Natalie and Arnab.** Still the highest-value non-technical
  move: the Standard's "invite judgment", and it may dissolve the annotation-study
  blocker on the triage tool.
- **R-005** — read 2605.28839 properly; deferred with the suppression/T-011 arc.

## Do not re-litigate

- The annotation study blocks the **triage tool's `contested` validation** only.
  It does **not** block T-041. That misattribution parked an arc for four days.
- Hand-built sets license **existence**, never **frequency** [O-004].
- Possession is measured, published, and closed. 56 / 74 / 79 / 85%.
