# E-001 pre-registration

Written **before** the treated version was produced. Nothing below was revised
after seeing the result.

## Design change from the ticket

The ticket specified generating a baseline myself. **That design is broken**: I
would be author, reviser and scorer, and I know the hypothesis. A generated
baseline would be contaminated by my knowing what the treatment is supposed to
improve.

Replaced with a **blind baseline**: a passage of the AI-generated Deep Research
report's *own* prose (not its quotations), produced by a system with no knowledge
of Tier 2 or of this project. The test becomes a **revision** test rather than a
generation test — which is also the more useful one, since the skill will mostly
revise.

Remaining confound, unfixable in this spike: **I am both reviser and scorer.**
Mitigation is to list every counted item so the scoring can be audited rather
than trusted. Named as the primary limitation.

## Baseline

`01-baseline.md` — 419 words, §"Predictors and detectors of broken entailed or
ripple-neighbor facts", pp. 7–8 of *Knowledge Editing Reliability, Repair
Wrappers, and Ripple-Effect Benchmarks*
(`ai/rome-neighbors/experiments/edit_propagation/`).

Chosen because the topic — whether GradSim predicts ripple success — sits inside
`rome-neighbors`, so the content is one Saif can judge on the merits.

## Treatment

The eight Tier 2 questions from `corpus/deletion-list.md`, supplied as the only
instruction. No Tier 1, no voice profile, no exemplar passages. Isolating the
variable is the point.

**Constraint held fixed:** the revision may use only facts present in the baseline
or verifiable in the repo. No invented numbers. If Tier 2 demands a falsifiable
claim and no data exists to make one, the correct output is to say so — and that
outcome is itself a finding.

## Metrics, defined before treatment

- **M1 · Own-claims.** Assertions the document makes on its own authority, which
  could be wrong *even if every cited paper is accurately reported*. This is the
  load-bearing metric: the anti-exemplar's defining property is that it only
  relays others' claims, so nothing in it can be wrong.
- **M2 · Falsifiable-as-written.** Sentences where a reader could name a specific
  observation that would make them false, *using only what the sentence supplies*.
  "Strongly correlates" fails — no threshold to violate. "Correlates at r > 0.5
  across three models" passes.
- **M3 · Headings with a truth value**, over total headings.
- **M4 · Word count.** Null check.
- **M5 · Tier 1 hits per 10k.** Negative control. Tier 2 says nothing about
  vocabulary, so a large move here means the arms were not isolated.
- **M6 · Numbers attached to an instrument.**

## Outcomes, stated in advance

- **CONFIRM** — M1 and M2 rise materially, M3 improves, and M4 does not balloon.
- **DENY** — the treated version is structurally identical, merely reworded.
- **NULL** — it differs, but not on the predicted axis. Most likely form: **longer
  output that is equally unfalsifiable.** Record which axis it moved on instead.

A rise in M4 alone, with M1 flat, is a DENY dressed as a CONFIRM. Watch for it.
