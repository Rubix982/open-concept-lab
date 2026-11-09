---
title: edit-slice
sidebar_label: Overview
sidebar_position: 1
description: Measuring what a weight-level knowledge edit does to the facts it was not aimed at — and finding the answer is arithmetic.
---

# edit-slice

Editing a fact into a model's weights changes one thing and disturbs an unknown amount of
everything else. This project measures the disturbance — specifically, what happens to the
*premises* of an edited fact, which forward-looking ripple evaluations do not probe.

It is an instrument, not a method. Nothing here proposes a better editor.

<Claim
  label="Where the project ended up"
  superseded="Editing a conclusion leaves its grounds standing and contradictory, and the size of that orphan is the finding."
  record={{
    "What replaced it": "The edit does not retract its grounds, and does not coherently rewrite them either. It displaces probability toward the edited content in anything that mentions the subject — by arithmetic, not by inference.",
    "Why the first version failed": "E-002 (grounds are evidential, so no contradiction exists to count) and E-015 (a work-country edit relocates a birthplace exactly as often as a birth-country edit).",
    Confidence: "High on the mechanism, which is analytic and confirmed at seven layers. Existence-claim only on every rate.",
  }}
>
  ROME divides by <code>u·k*</code>. Any prompt beginning with the edited subject has an
  identical key at that token, so its update coefficient is <strong>exactly 1</strong> —
  for any covariance, at any layer, whatever relation it asks about. A different subject
  gets <strong>0.082</strong>.
</Claim>

<Glance>
  <Stat value="56" label="decisions" note="each with its falsification stated first" />
  <Stat value="33" label="findings" note="from the literature, two of which killed directions" />
  <Stat value="85" label="questions" note="66 answered, 9 parked, 6 open, 3 dropped" />
  <Stat value="12" label="claims made" note="nine withdrawn or narrowed" />
  <Stat value="42" label="chains" note="entailment chains, one model" />
  <Stat value="0.082" label="floor" note="what a different subject receives" />
</Glance>

## How the question moved

The project set out to count something it turned out not to be able to count. Each
denial named the thing that made the next question worth asking, and the arithmetic
account at the end was not what anyone was looking for.

<Figure
  wide
  plain
  caption={<>Four questions, each raised by the answer before it. The project's own question — how large is the contradiction an edit leaves behind — could not be asked, because there is no contradiction to measure.</>}
>
  <svg viewBox="0 0 900 280" role="img" aria-label="Four questions in a chain. How big is the contradiction an edit leaves in its grounds? There is none: the grounds are evidential, so a satisfying world still exists. Which raised: does the model revise the premise to stay consistent? No: an edit to where someone works relocates their birthplace at the same rate. Which raised: then what is moving? Arithmetic, not inference: any prompt opening with the edited subject receives exactly one. Which raised: do published benchmarks test on such prompts? One does.">
    <g fontFamily="Lato, sans-serif" fontSize="10.5" fontWeight="900" letterSpacing="0.9" fill="var(--ocl-ink-faint)">
      <text x="14" y="22">THE PROJECT'S OWN QUESTION</text>
      <text x="14" y="112">WHAT THE DENIALS RAISED</text>
    </g>

    <rect x="14" y="32" width="300" height="54" fill="none" stroke="var(--ocl-oxide)" strokeWidth="1.5" />
    <text x="28" y="54" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">How big is the contradiction</text>
    <text x="28" y="72" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">an edit leaves in its grounds?</text>
    <text x="328" y="58" fontFamily="IBM Plex Mono, monospace" fontSize="12" fontWeight="600" fill="var(--ocl-oxide)">there is none</text>
    <text x="328" y="76" fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-faint)">grounds are evidential</text>

    <path d="M164 86 V122" stroke="var(--ocl-rule-strong)" strokeWidth="1.5" fill="none" />
    <path d="M159 114 l5 8 l5 -8" stroke="var(--ocl-rule-strong)" strokeWidth="1.5" fill="none" />

    <rect x="14" y="124" width="268" height="54" fill="none" stroke="var(--ocl-rule-strong)" strokeWidth="1" />
    <text x="28" y="146" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">Does the model revise the</text>
    <text x="28" y="164" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">premise to stay consistent?</text>
    <text x="28" y="194" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-oxide)">No. Editing where someone works</text>
    <text x="28" y="210" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-oxide)">relocates their birthplace as often.</text>

    <path d="M282 150 H316" stroke="var(--ocl-rule)" strokeWidth="1" strokeDasharray="2 4" fill="none" />

    <rect x="332" y="124" width="250" height="54" fill="none" stroke="var(--ocl-rule-strong)" strokeWidth="1" />
    <text x="346" y="146" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">Then what is moving?</text>
    <text x="346" y="164" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-ink-muted)">Arithmetic, not inference.</text>
    <text x="346" y="194" fontFamily="IBM Plex Mono, monospace" fontSize="11.5" fill="var(--ocl-link)">coefficient = 1.000</text>
    <text x="346" y="210" fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-faint)">on any prompt naming the subject</text>

    <path d="M582 150 H616" stroke="var(--ocl-rule)" strokeWidth="1" strokeDasharray="2 4" fill="none" />

    <rect x="632" y="124" width="254" height="54" fill="none" stroke="var(--ocl-link)" strokeWidth="1.5" />
    <text x="646" y="146" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">Do published benchmarks</text>
    <text x="646" y="164" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">test on such prompts?</text>
    <text x="646" y="194" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-link)">One does, at 0.982 against</text>
    <text x="646" y="210" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-link)">a 0.070 floor. One mostly does not.</text>

    <path d="M14 244 H886" stroke="var(--ocl-rule)" strokeWidth="1" fill="none" />
    <text x="14" y="266" fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-muted)">The thing the project was built to measure does not exist. What it found instead is in the last two boxes, and neither was planned.</text>
  </svg>
</Figure>

## Three ways in

| | for | length |
| --- | --- | --- |
| **[The paper →](./review)** | evaluating the claim. Eight sections, three appendices, two figures and twelve tables, with the attack surface ordered by how much damage each objection does. | ~12,000 words |
| **[The narrative →](/writing/five-days)** | how it actually went — every claim that was withdrawn, in the order it was withdrawn. Revised in place, never forked. | ~13,000 words |
| **[The evidence ledger →](./ledger)** | verifying any single statement. All 56 decisions, 33 findings and 85 threads, generated from the repository. | complete |

If you are deciding whether this is worth your time: read the paper's abstract, then its §7. That is where we say what is wrong with it.

## What is still open

Six questions. They are listed because the useful question from someone who knows the field is not *is this right* but *which of these is worth a month*, and that cannot be ranked from inside.

<Threads>
  <Thread id="T‑086" status="open">What actually sets how far a layer-5 edit travels? Seven candidate predictors were eliminated against a pre-registered floor, and the best pairing of the two survivors is bounded in closed form at 0.534 — about 28% of the variance. Searched, which is the more useful form of unknown.</Thread>
  <Thread id="T‑102" status="open">About half the propagation variance sits <i>within</i> a subject, across probe forms, where no edit-level quantity can reach it. The project already has a pair-level predictor that works and never put it on the candidate list.</Thread>
  <Thread id="T‑103" status="open">Does probe-form variance track the coefficient's spread across forms? The within-subject share is 13% at layer 5 and 52% at layer 20 on the same probe family, and delivery spreads the same way — which would tie the two together or separate them cleanly.</Thread>
  <Thread id="T‑105" status="open">How much of the attribute drift is the essence term already absorbing? <code>compute_v</code> carries a KL anchor whose explicit job is to stop the edit changing what the subject <i>is</i>, and every number this project has was measured with it on.</Thread>
  <Thread id="T‑097" status="open">Is <i>the field's evaluations do not measure what they claim</i> the paper? Three findings look separate and may be one: an efficacy margin that measures suppression, compositional tests that name the subject verbatim, and a floor nobody had measured.</Thread>
  <Thread id="T‑107" status="open">Is the edit-friendly fact the one with few dependents, or the one with a rare subject string? The two predictions come apart, and nothing here separates them yet.</Thread>
</Threads>

## What would change our mind

| | |
| --- | --- |
| the mechanism is already published | the central claim becomes a replication, and the contribution is the measurement tooling |
| ripple benchmarks are unaffected by subject-initial prompts | the consequence we think matters most evaporates |
| a causal measure shows the displacement is not subject-keyed | the whole account is wrong, and [T-067](./ledger) is how to find out |

## Scope, deliberately

- **Existence claims only.** Hand-built and mined sets license *whether*, never *how
  often*. No rate in this project is defensible and the artifacts are written to avoid
  implying one.
- **No method proposals.** Measuring what existing editors do; proposing a better one means
  owning the burden of beating them, which is a different project.
- **Behavioural, not causal.** Everything is input/output under intervention. No activation
  patching. Stated as a limit, not hidden.
