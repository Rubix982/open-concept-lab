# The Card

One card open at a time. Six fields. Nothing starts until all six are filled, nothing else starts until this one is closed.

A card closes with a number, or with a sentence that could have come out the other way. Never with "explored" or "built". Field 6 is the one that kills cards; fill it honestly.

Promotion to the ten-lens Design Protocol happens only when field 4 names a load-bearing published claim, or field 5's two branches cost more than a week apart.

---

## C-001 · Does predicted reach predict measured movement?

**Status:** closed
**Opened:** 2026-10-31
**Closed:** 2026-10-31

**1. WHERE WE ARE.**
The coefficient is exactly 1.000 for probes that begin with the edited subject (216 cells, four models 6B–405B, worst deviation 0.00e+00), falls from about 0.93 at layer 5 to about 0.52 at layer 24 when a preamble precedes the subject, and sits at a 0.082 different-subject baseline — all of it read from the **unedited** model, with no edit ever run at any layer but 5.

**2. WHAT WE ARE DOING.**
For each of the 42 subjects used in [E-014]/[E-016] and a fixed probe set, compute the layer-5 coefficient on the unedited model, then apply the ROME edit and measure the movement of the same (subject, probe) pair, and report the Spearman correlation between the two with the per-probe baseline removed.

**3. WHY.**
We do not currently know whether the coefficient carries any behavioural content. After this we have a correlation with an interval, over 42 × k pairs, and we know whether a threshold can be set on it at all.

**4. WHAT IS AFFECTED.**
- The email sent to Natalie and Arnab on 2026-10-31 (`ai/edit-slice/notes/email-3-direct-exposure.md`), which proposes a pre-edit screen.
- `ai/edit-slice/CLAUDE.md`, "Probe generation": *"If predicted and measured rankings correlate, cheap predictor plus mechanistic story. If they diverge, that divergence is the finding."*
- The standing sentence "a screen built on it is a proposal, not an instrument" either resolves or hardens into a permanent limit.

**5. CONCLUSION IF WE DO IT.**
- **If the correlation holds** (ρ ≥ 0.5 after removing the per-probe baseline): the coefficient is a usable pre-edit triage signal, a cut can be chosen, and the next card reports false-positive and false-negative rates at that cut. Only then is the word "screen" earned.
- **If it does not** (ρ near zero, or the interval spans zero): the coefficient is a delivery statistic with no behavioural meaning. The screen proposal is withdrawn with Natalie and Arnab in writing. Note what survives either way: the direct-exposure critique of RippleEdits falls back to **counting** whether the edited subject appears in the prompt, which needs no coefficient and is unaffected by this result.

**6. CONSEQUENCE OF NOT DOING IT.**
We would keep recommending a gate with no threshold and no error rates — an instruction with a verb and an object that nobody, including us, can carry out. Email 3's ask to Natalie cannot be answered by anyone until this number exists.

**Closed:** 2026-10-31 — **deny branch**, on the number written in field 5 before the run.

    overall, raw         rho = 0.522   95% CI (0.450, 0.587)
    overall, excess      rho = 0.085   95% CI (-0.003, 0.172)

The test was always the second line: movement in excess of what a **different edit on the same person** produces. It does not reach 0.5, and its interval touches zero. By the branch written in advance, the coefficient is not established as a predictor of a particular edit's effect, and a screen built on it stays a proposal.

What the raw number means, since 0.522 is real and will be quoted. A high-coefficient probe does move more. But the same-subject control already accounts for about **72%** of the median movement (|movement| 0.1034, |control| 0.0740), so what the coefficient tracks is *this probe is sensitive to an edit on this subject*, not *this edit reaches this probe*.

Per family, the excess medians are 0.000–0.031. `exposure` is the largest at 0.031 — the item where the edited subject sits in the prompt while the question is about someone else.

**What survives, as field 5 said it would.** The direct-exposure critique of RippleEdits rests on **counting** whether the edited subject appears in a prompt. That needs no coefficient and is untouched by this result.

**An unresolved tension, recorded rather than resolved.** The same-subject control was introduced in [E-013] to separate contraction from subject-keyed leakage. Here subject-keyed leakage may *be* the phenomenon: if an item moves because an edit happened to this subject rather than because of what the edit said, that is the direct-exposure claim, and controlling it away removes the signal. That reading is **post-hoc** and licenses nothing. It needs its own card with its branches written first.

---

## Closed cards

### C-001 · Does predicted reach predict measured movement? — DENIED

Closed 2026-10-31. `results/E-001-predicted-vs-measured.json`. 495 probes, 42 subjects, Llama-3.1-8B at layer 5, edits from the [E-014] cache. Anchor gate passed at 0.000e+00 after two faults were fixed ([E-001] in decisions.md).

Independent replication worth noting: the `anchor-floor` family — same prompt shape, different person — came back at a median coefficient of **0.0809**, against [E-018]'s floor of 0.082.
