---
title: "Rank-one edits are pinned to their subject"
sidebar_label: Paper
sidebar_position: 2
description: A weight edit's update coefficient is exactly 1 on any prompt beginning with the edited subject, for any covariance, at every layer. Measured, with the evidence and the attack surface.
---

# Rank-one edits are pinned to their subject

<p className="ocl-paper-sub">An arithmetic account of what ROME does to facts it was not
aimed at</p>

<p className="ocl-paper-meta">edit-slice · Llama-3.1-8B · assembled 2026-09-20 · revised
in place · <a href="/open-concept-lab/writing/five-days">narrative version</a> ·
<a href="./ledger">evidence ledger</a></p>

<Aside>

Written to be judged. **Section 6** is the attack surface, ordered by how much damage each
objection does; **section 5** lists every claim this project withdrew. If you are deciding
whether to spend time on this, read the abstract, then section 6.

</Aside>

<div className="ocl-abstract">

## Abstract

Weight-editing methods are evaluated by how their changes propagate to related facts. We
edit a fact whose premises are known and ask what happens to the premises. On 42
entailment chains in Llama-3.1-8B, editing *"X was born in the country of Z"* moves the
answer to *"X was born in the city of…"* into a city of the new country **67%** of the
time, against **5%** for baseline and **5%** for a magnitude-matched control edit on the
same subject. This looks like the model revising a premise to stay consistent. It is not.
Editing where the person **works** relocates their **birthplace** at an identical rate
(28/42 both arms, paired difference **+0.0 pp**, exact McNemar p = 1.000), and work
country licenses nothing about birth city. The cause is arithmetic: ROME's update divides
by `u·k*`, and a prompt beginning with the edited subject has a key identical to `k*` at
that token under causal attention, so its update coefficient is **exactly 1** for any `u`
— hence for any covariance, at every layer, whatever relation it asks about. A prompt
about a *different* subject receives **0.082**. The distributions do not overlap. What
reads as propagation is displacement keyed on the subject string. The coefficient is a
statement about **delivery**, not about effect: holding it at exactly 1 and matching edit
strength, the same update applied at layer 20 instead of layer 5 reaches **2.96× less
far**.

</div>

## Figures and tables

| | |
| --- | --- |
| **Figure 1** | The pinned coefficient — why a shared prefix forces the value to 1 |
| **Figure 2** | Coefficient by layer, five probe forms, seven depths |
| **Table 1** | Usable chains by rendering × control — the interaction (§3.1) |
| **Table 2** | The relation control — the +0.0 pp paired difference (§4.2) |
| **Table 3** | Observations against the mechanism (§4.1) |
| **Table 4** | Position ablation — sufficient and necessary (§4.1) |
| **Table 5** | Claim status — eleven claims, eight withdrawn or narrowed |
| **Table 6** | Delivery is not effect — propagation at a fixed coefficient (§4.4) |
| **Table 7** | Floor plus type-matched displacement — what else the edit moves (§4.5) |
| **Table 8** | Open threads, what each would decide, and what it costs (§8) |
| **Table 9** | The pinning across a 68× parameter range (§4.3) |

## 1 · The question

An edit is supposed to change one fact. It changes an unknown amount of everything else,
and the standard way to measure that looks *forward* — at consequences of the edited fact
<Cite id="cohen2024ripple" />. We look at the **premises**: facts that made the edited fact
true and are still sitting in the weights afterwards.

Our chains have the form

```
inner_1   X was born in the city of Y        (P19, rigid)
inner_2   Y is located in the country of Z   (P17)
--------------------------------------------------- entails
outer     X was born in the country of Z
```

Edit `outer` to a different country. Both premises still entail the original. A coherent
model must give something up. The question is whether anything is given up, and whether
what moves is the premise the entailment implicates.

## 2 · Related work, and what we do not claim

**We do not claim the surface-form result.** Section 3.1 depends on the fact that scoring
answers by string probability is distorted by how the answer is spelled. That is surface
form competition <Cite id="holtzman2021surface" narrative />, and the correction we
independently rebuilt — score against a subject-free version of the same prompt — is
essentially their Domain Conditional PMI. We rediscovered a 2021 result and its standard
remedy, and cite it to disclaim novelty.<Margin>Found by a prior-art gate run *after* the
measurement and *before* publication, which is later than it should have been.<Evidence id="f-R-010">R-010</Evidence></Margin>

**We do not claim knowledge-status × editability.** Whether a model already knowing a fact
predicts how well that fact edits has been measured, on Llama-3.1-8B, with MEMIT,
AlphaEdit and fine-tuning <Cite id="knowledgespectrum2025" />. That closed a direction we
had designed and were about to build.<Margin>Two further gates cleared rather than closed: <Evidence id="f-R-002">R-002</Evidence> on intra-memory conflict and uncertainty-based deferral, and <Evidence id="f-R-007">R-007</Evidence> on the nearest remaining competitor.</Margin>

**Template sets exist upstream.** CounterFact records derive from ParaRel entries
containing hand-curated template *sets*, and keep one prompt per record
<Cite id="elazar2021pararel" />; our probes inherit that collapse.

**Backward probing is narrower than we first claimed.** RippleEdits' Logical Generalization covers inverse and symmetric relations, which is the closest existing thing to a grounds probe; reading its test-type definitions directly is what forced the narrowing.<Evidence id="f-R-001">R-001</Evidence>

**What is left.** None of the above examines what an edit does to a fact's *premises*, and
none reports the coefficient structure of the update itself. ROME <Cite id="meng2022rome" />
derives the `C⁻¹` term and its own repository enables it by default; EasyEdit disables it
in all fourteen of its ROME configs, including for the two models the paper used.<Margin>Read from both repositories rather than from either paper.<Evidence id="f-R-009">R-009</Evidence></Margin> Both
values read from the raw config files.

## 3 · Method

_Records: <Evidence id="E-007" /> · <Evidence id="O-006" /> · <Evidence id="E-012" /> · <Evidence id="E-013">E-013 gate</Evidence>_

**Possession gate.** A chain is usable only if the model holds all three facts.<Margin>The gate exists because CounterFact has none: its construction never checks the model knows the fact being edited, verified from source.<Evidence id="f-D-002">D-002</Evidence> · <Evidence id="f-R-006">R-006</Evidence> The measure was built over <Evidence id="f-E-004">E-004</Evidence> → <Evidence id="f-E-005">E-005</Evidence>, and <Evidence id="f-E-006">E-006</Evidence> established ROME on Llama-3.1-8B via NDIF is feasible at all.</Margin> Each is
scored against a type-matched candidate pool under two criteria: the true answer ranks
first with the real subject (*row test*), and outscores it under foil prompts whose true
answer differs (*column test*, an AUROC; chance 0.5). The column test replaces a
placeholder control that is undefined for high-prior answers — see §3.1. 136 chains mined →
78 usable → 42 carried through the edit.<Margin>The relation inventory behind the chains is <Evidence id="f-R-003">R-003</Evidence>; the entailment structure and why grounds are evidential rather than deductive is <Evidence id="f-E-001">E-001</Evidence> · <Evidence id="E-002" />. Set-level coordination lift, which does not survive per-candidate, is <Evidence id="f-T-055">T-055</Evidence>.</Margin><Margin>The 29 missing chains were lost to backend
outages, not excluded by any criterion — see <Evidence id="O-007" />. Every rate here is an
existence claim, never a frequency.</Margin>

**Model choice.** Possession is a *construct requirement*, not ambition: a model that never held the grounds cannot orphan them, which replaced this project's original size ceiling with a size floor.<Evidence id="O-005" /> Possession rises with scale and the field's standard test overstates it at every size<Evidence id="f-E-003">E-003</Evidence>; GPT-J-6B sits at 73%<Evidence id="f-E-003b">E-003b</Evidence>, and the 70B gate clears while showing the three chain legs are not independent<Evidence id="E-009" /> — which is why §3's gate scores all three rather than the edited fact alone.

**Edit.** ROME as configured by EasyEdit, `C = I`, layer 5, `v*` optimised by gradient
descent through the frozen model with EasyEdit's `llama3-8b.yaml` hyperparameters. Applied
as a trace-time intervention computed from each position's own key, so the edited weight
matrix is never formed — exact, not approximate.

**Controls.** Three, all required. A **same-subject** control edits an unrelated property
(occupation) of the same person at matched magnitude, isolating content from subject-key
perturbation. A **relation** control edits the same subject to the same target country
through a relation that licenses nothing (*works in*). A **placebo country** gives the null
rate for "lands in country X".

**Readout.** Full city names ranked over a 75-city pool of chain cities plus every target
country's capital — widened deliberately.<Margin>A pool that cannot express the coherent
answer scores a correct relocation as a failure. That mistake is <Evidence id="E-011" />,
and widening the pool is how it was avoided here.</Margin>

### 3.1 · Repairing the measure, which took two orthogonal fixes

_Records: <Evidence id="E-009b" /> · <Evidence id="E-011" /> · <Evidence id="E-012" />_

Before any edit: the possession measure failed on the most common answers. Rendering
countries as Wikidata labels (`United States`) rather than naturally (`the United States`)
is ungrammatical after *"born in the country of"*, and rank-1 on those answers sat at 21%.
Rendering naturally moved it to **69%** — but then the placeholder control ranked the same
answer first at the identical 69%, because *"[X] was born in the country of the United
States"* is the modal completion whether or not `[X]` means anything.

Neither repair alone recovers anything. Together they recover twenty chains.

<p className="ocl-tablecap"><strong>Table 1.</strong> Usable chains out of 136, by rendering × control. Each fix alone moves the</p>
count by one; together they move it by twenty.

| | placeholder control | paired control |
| --- | ---: | ---: |
| bare rendering | 58 | 59 |
| natural rendering | 59 | **78** |

This is an interaction, not two additive fixes, and it is why each looked like a null when
tested alone. Llama-3.1-70B under the old measure gave 74 usable chains; Llama-3.1-8B under
the repaired one gives 78. Repairing the instrument was worth more than an order of
magnitude of scale.

## 4 · Results

### 4.1 · The update coefficient is pinned at the subject

_Records: <Evidence id="E-016">E-016 gate</Evidence> · <Evidence id="E-016-2">E-016 result</Evidence>_

ROME's update divides by `u·k*`. That one term fixes the coefficient across a whole class
of prompts, and the class is larger than it looks.

<Figure
  caption="Why the coefficient is pinned. The two prompts share every token up to the subject's last. Causal attention makes the key there identical, and ROME's own normalisation divides by u·k*, so the coefficient is exactly 1 for any u."
>

<svg viewBox="0 0 700 380" role="img" aria-label="Diagram: two prompts share the subject token, so its key is identical and the ROME update coefficient there is exactly one." style={{width:"100%",height:"auto"}}>
  <title>The pinned coefficient</title>
  <defs>
    <style>{`
      .pc-subj { fill: #a8503f; opacity: .18; }
      .pc-bar  { fill: #3d72a8; }
      .pc-barq { fill: #3d72a8; opacity: .45; }
      .pc-t    { font: 13px/1.3 var(--ifm-font-family-base); fill: var(--ocl-ink); }
      .pc-s    { font: 600 13px/1.3 var(--ifm-font-family-base); fill: var(--ocl-ink); }
      .pc-m    { font: 11px/1.3 var(--ifm-font-family-base); fill: var(--ocl-ink-muted); }
      .pc-r    { stroke: var(--ocl-rule-strong); stroke-width: 1; fill: none; }
      .pc-a    { stroke: #a8503f; stroke-width: 1.5; fill: none; }
      [data-theme='dark'] .pc-subj { fill: #c87c62; opacity: .26; }
      [data-theme='dark'] .pc-bar  { fill: #5596d4; }
      [data-theme='dark'] .pc-barq { fill: #5596d4; opacity: .45; }
      [data-theme='dark'] .pc-a    { stroke: #c87c62; }
    `}</style>
  </defs>

  <text className="pc-m" x="24" y="24">THE EDIT — k* is read at the subject's last token</text>
  <rect className="pc-subj" x="24" y="34" width="86" height="26" rx="3" />
  <text className="pc-s" x="30" y="52">Vlaminck</text>
  <text className="pc-t" x="118" y="52">was born in the country of  →  Germany</text>

  <text className="pc-m" x="24" y="88">THE PROBE — same subject, a relation that implies nothing about it</text>
  <rect className="pc-subj" x="24" y="98" width="86" height="26" rx="3" />
  <text className="pc-s" x="30" y="116">Vlaminck</text>
  <text className="pc-t" x="118" y="116">works in the country of  →  …</text>

  <path className="pc-a" d="M24 47 L14 47 L14 165 L300 165" />
  <path className="pc-a" d="M24 111 L14 111" />
  <text className="pc-m" x="30" y="159">no token before this one differs</text>

  <text className="pc-s" x="308" y="159">k(probe) = k*  exactly</text>
  <text className="pc-s" x="308" y="181">coefficient = (k*·u)/(u·k*) = 1</text>
  <text className="pc-m" x="308" y="199">for every u — hence for every covariance C</text>

  <line className="pc-r" x1="24" y1="222" x2="660" y2="222" />
  <text className="pc-m" x="24" y="238">MEASURED COEFFICIENT AT EACH POSITION OF THE PROBE</text>

  <text className="pc-m" x="96" y="263" textAnchor="end">'amin'</text>
  <rect className="pc-barq" x="104" y="254" width="37" height="11" rx="3" />
  <text className="pc-m" x="149" y="263">0.092</text>

  <text className="pc-s" x="96" y="287" textAnchor="end">'ck'</text>
  <rect className="pc-bar" x="104" y="276" width="400" height="14" rx="4" />
  <text className="pc-s" x="512" y="287">1.0000</text>
  <text className="pc-m" x="566" y="287">← subject-last</text>

  <text className="pc-m" x="96" y="311" textAnchor="end">' was'</text>
  <rect className="pc-barq" x="104" y="302" width="46" height="11" rx="3" />
  <text className="pc-m" x="158" y="311">0.116</text>

  <text className="pc-m" x="96" y="335" textAnchor="end">' of'</text>
  <rect className="pc-barq" x="104" y="326" width="12" height="11" rx="3" />
  <text className="pc-m" x="124" y="335">0.031</text>

  <text className="pc-m" x="24" y="366">A different SUBJECT in the same template scores 0.082. The distributions do not overlap.</text>
</svg>

</Figure>

`k*` is read at the subject's last token of the edit prompt. A probe beginning with the
same subject has an identical key there, so the coefficient is `(k*·u)/(u·k*) = 1` for any
`u`. The measured value is **1.0000**, not approximately one.

Everything in §4.2 and §4.3 follows from this. The measurements came first
chronologically — the [narrative version](/writing/five-days) keeps that order — but the
dependency runs the other way:

<p className="ocl-tablecap"><strong>Table 3.</strong> Every observation in the arc, against the one mechanism.</p>

| observation | explanation |
| --- | --- |
| birth-city probe displaced, 67% | shares the prefix → pinned at 1.0 |
| *"Paris is located in…"* inert, −0.02 | shares no prefix → nothing pinned |
| whitening changed nothing, 42/42 | cannot alter a coefficient fixed by arithmetic |
| a uniform ×0.27 rescale **does** break it (3 of 4) | it scales the pinned term too |
| the work-country null, +0.0 pp | both prompts begin with the subject |

<p className="ocl-tablecap"><strong>Table 4.</strong> A position ablation inside the
update. Only the mask varies — same edit, same cached <code>v*</code>, same
<code>k*</code>. Arm E restores the magnitude the mask removed, so position is the only
difference from the full edit.</p>

| arm | positions receiving δ | mass | in target |
| --- | --- | ---: | ---: |
| **A** full | all | 100% | 28/42 = **67%** |
| **B** only | the subject's last token alone | 67% | 29/42 = **69%** |
| **C** except | all but it | 33% | 2/42 = 5% |
| **E** except, **mass restored** | all but it, rescaled to 100% | 100% | 5/42 = **12%** |
| **D** none | — | 0% | 2/42 = 5% |

A coefficient of 1 at a position contributing nothing would produce the same numbers as
one that does the work, so the arithmetic on its own does not settle where the effect
lives. Masking the update by position does.

**Sufficient:** arm B reproduces the full edit from one position out of roughly twelve —
69% against 67%, one discordant pair, p = 1.000.

**Necessary:** arm C also strips two thirds of the magnitude, and §4.1's scale test showed
0.27× breaks relocation unaided, so C ≈ D is what magnitude loss alone predicts. Arm E
restores that magnitude to the surviving positions and reaches 12% against a 5% baseline.

The comparison that carries it is **B against E**. Arm B has *less* mass at one position;
arm E has *more*, spread over every other position. **29 against 5, twenty-four discordant
pairs, none reversed, p < 0.0001.**<Margin>Coefficient mass at the subject token ranges 31–80% across chains, mean 66.8%.
Arm E's rescaling is per chain, so each restoration is exact rather than
averaged.<Evidence id="E-021" /></Margin>

Less magnitude in the right place beats more magnitude everywhere else, and no chain goes
the other way.

### 4.2 · What it predicts: displacement without inference

_Records: <Evidence id="E-013" /> · <Evidence id="E-014" /> · <Evidence id="E-015" />_

§4.1 predicts that a probe beginning with the edited subject receives the full update
whatever it asks about — so an edit should move a *premise* as readily as a consequence,
and a semantically unrelated edit should move it just as far. Both hold.

The birth-city probe lands in the edited country 67% of the time (baseline 5%, same-subject
control 5%, placebo 0%). Edinburgh → Hamburg for Germany; Paris → Santiago for Chile.

**That 67% is an undercount, and the cause is ours.** Letting the edited model generate
freely instead of ranking the pool, it names a city in the target country in **30 of 30**
chains. The 75-city pool cannot express most of its answers — Hamburg, Sydney, Zurich,
Milan, Gisborne and Plzeň are all absent — so ranking falls back to the highest-prior item
on the menu.<Margin>Which is also what the `Washington, D.C.` attractor was: 33% of ranked
destinations, read at the time as the model's fallback. It was the ranking's.
<Evidence id="E-023" /></Margin> **Differences survive a bad pool; absolute levels do
not** — §4.2 and §4.3 are paired contrasts using the same pool in every arm, so the
artifact cancels there and only this level is affected.

Then the relation control:

<p className="ocl-tablecap"><strong>Table 2.</strong> The relation control. Subject and target country held fixed; only the</p>
edited relation varies. Exact McNemar p = 1.000, nine discordant pairs each way.

| arm | lands in target country |
| --- | ---: |
| `X was born in the country of` → T — licenses the inference | 28/42 = **67%** |
| `X works in the country of` → T — licenses nothing | 28/42 = **67%** |
| **paired difference** | **+0.0 pp** |

Exact McNemar p = 1.000 (nine discordant each way). Where both arms land in the target
country, they choose the *same city* 84% of the time. Editing where a person works
relocates their birthplace exactly as often as editing where they were born.
### 4.3 · Scope: the claim's boundary, measured

_Records: <Evidence id="E-017" /> · <Evidence id="E-019" /> · <Evidence id="T-075" /> · <Evidence id="E-018" /> · <Evidence id="E-020" /> · <Evidence id="E-027" />_

<Figure
  caption="Coefficient at the subject's last token, by layer, 12 subjects. Prompts beginning with the subject are pinned at exactly 1.000 at every depth. Reordering the subject escapes progressively — but not at layer 5, which is the layer this configuration edits."
>

<svg viewBox="0 0 700 330" role="img" aria-label="Line chart: prefix-sharing probes stay at 1.0 across layers 0 to 31, while reordered probes decay from 0.99 to about 0.58." style={{width:"100%",height:"auto"}}>
  <title>Coefficient by layer</title>
  <defs>
    <style>{`
      .ls-fix  { stroke: #a8503f; stroke-width: 2.5; fill: none; }
      .ls-a    { stroke: #3d72a8; stroke-width: 2; fill: none; }
      .ls-b    { stroke: #3d72a8; stroke-width: 2; fill: none; stroke-dasharray: 6 4; }
      .ls-d    { fill: #3d72a8; }
      .ls-df   { fill: #a8503f; }
      .ls-t    { font: 11px/1.3 var(--ifm-font-family-base); fill: var(--ocl-ink); }
      .ls-m    { font: 11px/1.3 var(--ifm-font-family-base); fill: var(--ocl-ink-muted); }
      .ls-g    { stroke: var(--ocl-rule); stroke-width: 1; }
      [data-theme='dark'] .ls-fix { stroke: #c87c62; }
      [data-theme='dark'] .ls-a, [data-theme='dark'] .ls-b { stroke: #5596d4; }
      [data-theme='dark'] .ls-d   { fill: #5596d4; }
      [data-theme='dark'] .ls-df  { fill: #c87c62; }
    `}</style>
  </defs>

  <line className="ls-g" x1="90" y1="40" x2="90" y2="250" />
  <line className="ls-g" x1="90" y1="250" x2="600" y2="250" />
  <text className="ls-m" x="82" y="44"  textAnchor="end">1.0</text>
  <text className="ls-m" x="82" y="149" textAnchor="end">0.5</text>
  <text className="ls-m" x="82" y="254" textAnchor="end">0.0</text>
  <text className="ls-m" x="90" y="272" textAnchor="middle">L0</text>
  <text className="ls-m" x="163" y="272" textAnchor="middle">L5</text>
  <text className="ls-m" x="236" y="272" textAnchor="middle">L10</text>
  <text className="ls-m" x="309" y="272" textAnchor="middle">L15</text>
  <text className="ls-m" x="382" y="272" textAnchor="middle">L20</text>
  <text className="ls-m" x="455" y="272" textAnchor="middle">L25</text>
  <text className="ls-m" x="528" y="272" textAnchor="middle">L31</text>
  <text className="ls-m" x="90" y="26">coefficient at the subject's last token</text>

  <path className="ls-fix" d="M90 40 L163 40 L236 40 L309 40 L382 40 L455 40 L528 40" />
  <circle className="ls-df" cx="90" cy="40" r="4" /><circle className="ls-df" cx="236" cy="40" r="4" />
  <circle className="ls-df" cx="382" cy="40" r="4" /><circle className="ls-df" cx="528" cy="40" r="4" />
  <text className="ls-t" x="540" y="38">prefix-sharing (3 forms)</text>
  <text className="ls-m" x="540" y="52">1.000 everywhere</text>

  <path className="ls-a" d="M90 42 L163 50 L236 70 L309 84 L382 129 L455 127 L528 124" />
  <circle className="ls-d" cx="163" cy="50" r="3.5" /><circle className="ls-d" cx="382" cy="129" r="3.5" />
  <text className="ls-t" x="540" y="124">late clause</text>

  <path className="ls-b" d="M90 41 L163 48 L236 75 L309 81 L382 121 L455 130 L528 118" />
  <circle className="ls-d" cx="236" cy="75" r="3.5" /><circle className="ls-d" cx="455" cy="130" r="3.5" />
  <text className="ls-t" x="540" y="142">possessive</text>

  <line className="ls-g" x1="163" y1="40" x2="163" y2="250" strokeDasharray="3 4" />
  <text className="ls-m" x="168" y="244">layer 5 — what EasyEdit edits</text>

  <text className="ls-m" x="90" y="300">Reordering the subject costs ~7% at layer 5 and ~42% at layer 20.</text>
  <text className="ls-m" x="90" y="316">The pinning is exact for prefix-sharing probes at all seven depths.</text>
</svg>

</Figure>

A separate control varied the **subject** while holding the form fixed: chain *i*'s `k*`
scored against chain *i+1*'s subject in the same template. Mean **0.082**, max **0.153** —
below the *minimum* same-subject value of 0.483. The distributions do not overlap, and the
pre-stated confirmation threshold was ≤0.3.

**The decay is a change of direction, not of magnitude.** The coefficient is
`(‖k‖/‖k*‖)·cos(k, k*)`, so it can fall two ways, and they are different claims about the
network. Across eight layers, six forms and 16 chains, the cosine falls **0.984 → 0.471**
while the norm ratio never leaves 0.97–1.24 — and drifts slightly *up*, so magnitude works
against the decay. Subject-position keys have essentially the same length regardless of
whose name is in the prompt or how it is worded; everything that distinguishes them is
orientation.<Margin>This does **not** show that attention mixes context into the subject
position. A falling cosine is equally consistent with MLP writes at that position, or
anything else that reorients the residual stream. The attention patterns are unrun.
<Evidence id="E-020" /></Margin> The different-subject floor's rise at layer 31 (0.082 →
0.669) is likewise cosine with a flat ratio: representational convergence near the output,
not a scaling artifact.

**It is a property of ROME, not of this model, and not of this scale.** The derivation
mentions neither architecture nor parameter count, so it should hold anywhere. Measuring
rather than assuming it costs almost nothing, because the coefficient needs **no
gradients** — one forward pass, save the MLP input at the subject's token.

<p className="ocl-tablecap"><strong>Table 9.</strong> Prefix-sharing probes across a 68× parameter range and two</p>
architectures. Every cell is exactly 1.000; the column records the worst deviation found.

| model | params | layers | prefix-sharing probes |
| --- | ---: | ---: | --- |
| GPT-J-6B | 6B | 28 | **1.000** · worst 0.0e+00 |
| Llama-3.1-8B | 8B | 32 | **1.000** |
| Llama-3.1-70B | 70B | 80 | **1.000** · worst 0.0e+00 |
| Llama-3.1-405B-Instruct | 405B | 126 | **1.000** · worst 0.0e+00 |

The **decay** is approximately scale-invariant at matched depth — worst deviations 0.131
and 0.144 against a pre-stated 0.15 band, which is a pass close enough to the threshold to
be worth saying so.<Margin>The 405B arm is instruction-tuned, because it is the only 405B
hosted. It varies scale *and* post-training together, and post-training is exactly the
sort of thing that could move subject representations. It must not be cited for scale
alone.<Evidence id="E-032" /></Margin>

The *decay* transfers too, which was not expected, because it is not derived. Compared at
matched fraction of depth both models fall from 1.0 at the input to ~0.5 by two thirds
depth and flatten — Llama 0.951 / 0.577 / 0.598 against GPT-J 0.861 / 0.597 / 0.482 at
depth fractions 0.15, 0.64 and 1.00.

**The floor does not transfer, and that narrows §4.3.** GPT-J's different-subject floor is
**0.155** at the edit layer against Llama's 0.082, and **0.524** at the final layer — above
that layer's same-subject late-clause value of 0.482, so the coefficient has stopped
telling subjects apart at all. *"Different subjects are near-orthogonal at the subject
position"* is a **Llama-3.1-8B** statement, not a ROME one. The margin at the layer ROME
actually edits stays clean on both (0.87 against 0.71), so the claim above is untouched;
only its generality across depth is model-dependent.

**Floor magnitude is model-specific and is not a scale law.** Mean floor at depth fractions
0.10–0.23: GPT-J **0.144**, Llama-8B **0.061**, Llama-70B **0.110**, Llama-405B-Instruct
**0.012**. The 405B figure is remarkable — 0.009 at fraction 0.10, with a maximum across
all twelve subjects of 0.042, against a same-subject value of 0.992, a **108× contrast**.
But 70B is *worse* than 8B, so the trend is non-monotone on four points and no scale law
follows from it.<Margin>Two structures do hold in all four: the floor is high at layer 0,
before contextualisation, when the key is embedding-driven and names share subword
statistics; and near the output the floor *exceeds* the same-subject value, so the measure
stops discriminating subjects altogether.<Evidence id="E-032" /></Margin>

**What the floor does across depth, in every model measured:** it is lowest in the first
fifth of the network and rises monotonically after — a **14× range** on Llama-3.1-8B,
0.048 to 0.697. An earlier version of this section reported the minimum as falling near
the layer ROME edits, in two models, and drew a line to ROME's layer selection. Measured
at finer spacing that is **false**: the minima sit at fractions 0.06 and 0.11, not the same
place, and Llama's edit layer at fraction 0.16 carries a floor of 0.095 — about twice its
minimum.<Margin>Withdrawn rather than qualified. The claim was attractive, and it did not
survive its own first proper test.<Evidence id="E-031" /></Margin><Margin>Tested rather than assumed. Re-gating the
subjects on GPT-J and splitting them gives a floor of **0.146 for held and 0.146 for
not-held** — a gap of 0.000 against a pre-stated band of 0.05, with every gap running the
*wrong* way for a familiarity account, and GPT-J holding 21 of 36 subjects outright. The
narrowing is confirmed. The residual objection is that a candidate pool undercounts, which
dilutes the contrast toward exactly this zero.<Evidence id="E-030" /> · <Evidence id="E-027" /></Margin>

### 4.4 · Delivery is not effect — the coefficient's boundary, measured

_Records: <Evidence id="E-028a" /> · <Evidence id="E-028c" /> · <Evidence id="E-028d" />_

Everything above measures **delivery**: how much of the update vector arrives at a
position. §6.3 listed the obvious objection — delivery is not behaviour — as one we could
not answer. We can now, and **the objection is correct**. The thread is <Evidence id="T-079" />; the run that asked first and got it wrong is <Evidence id="E-026" />.

Apply the update at layer 20 instead of layer 5. A subject-initial probe receives a
coefficient of **exactly 1.000 at both**, analytically, since both share the edit prompt's
prefix up to the subject's last token. Delivery is therefore held fixed by construction,
and anything that differs is not delivery.

<p className="ocl-tablecap"><strong>Table 6.</strong> Propagation to a prefix-sharing probe at a delivered coefficient of</p>
exactly 1.000 in every cell. Displacement is the drop in log P(true answer) on the edit
prompt itself — the edit's strength, measured where it was optimised.

| cell | displacement | propagation | reach per nat displaced |
| --- | ---: | ---: | ---: |
| layer 5, 25 steps — EasyEdit's shipped config | 7.26 | 9.66 | **1.33** |
| layer 5, 400 steps | 11.74 | 12.96 | **1.10** |
| layer 20, 25 steps | 2.61 | 0.80 | **0.31** |
| layer 20, 400 steps — displacement-matched | 6.97 | 3.59 | **0.52** |

> **1.22 nats of reach per nat displaced at layer 5, against 0.41 at layer 20 — a factor
> of 2.96, holding across a sixteenfold range of optimisation budget.**

Two confounds had to die first, and the order matters because our first attempt got it
wrong. A layer-20 edit under EasyEdit's shipped hyperparameters displaces only 2.61 nats
against layer 5's 7.26, so the first run of this comparison was measuring a **weaker
edit**, and its conclusion — this conclusion — was withdrawn.<Margin>The gate that let it
through measured *lift on the injected target*, which a logit nudge also achieves. Lift
spans 0.17 nats across both layers and a fourfold step budget while displacement spans
5.70: it saturates by 25 steps and carries no information about edit strength thereafter.
<Evidence id="E-028a" /></Margin> Matching took a **16× step budget** at layer 20. That
match then made *layer* collinear with *optimisation budget*, so a fourth cell was bought
to separate them: more optimisation buys **more** reach — +34% at layer 5, +349% at layer
20 — which is the opposite sign to the overfitting account.

**What this costs the sections above.** They describe delivery, and must be read that way.
The claim is unchanged in content and narrower in what it licenses:

> Any probe beginning with the edited subject receives the full, unattenuated edit vector
> at the subject position — at every layer, for any `C`, regardless of relation.

What no longer follows is *how far that probe's answer will move*. §4.1's position ablation
stands as a **layer-5** result.

### 4.5 · What the edit does to the rest of the subject

_Records: <Evidence id="E-024" /> · <Evidence id="E-025" /> · <Evidence id="E-029" />_

If the unit an edit operates on is the **subject**, the relation it targeted is incidental
— so a birthplace edit should disturb attributes of that person having nothing to do with
birth. It does, and not uniformly.

Three probes per subject, teacher-forced log P(true answer), paired against the same probes
on an unedited subject, no candidate pool:

<p className="ocl-tablecap"><strong>Table 7.</strong> Post-edit level of each attribute after a birthplace edit. Levels,</p>
not drops — the probes start far apart, so drops are baseline-dominated and reading them
as targeting is how this run's first conclusion went wrong.

| probe | type-matched to the injected value? | related to birth? | post-edit level |
| --- | --- | --- | ---: |
| occupation | no (a profession) | no | **−6.16** |
| native language | no (a language) | yes | **−6.20** |
| citizenship | **yes** (a country) | yes | **−9.10** |

Occupation and language finish **0.04 nats apart after starting 3.65 apart**. Citizenship
finishes **2.95 below** both. So the structure is two effects, not a relatedness gradient:

> A **floor** — everything about the subject is suppressed to roughly the same level,
> whether or not it relates to the edited relation — plus **type-matched displacement**,
> an additional penalty only where the probe's answer type matches the injected value.

Semantic relatedness predicts language patterns with citizenship. It patterns with
occupation instead. The edit is not reasoning about origin; it is competing for a slot.<Margin>This run's own headline said "semantic relatedness", computed on drops, and was
retracted. The confound was named in the ticket that commissioned it while the code still
computed on drops — naming a confound is not controlling for it.<Evidence id="E-025" /></Margin>

**What predicts how far an edit travels is mostly unmeasured.** Belief displacement on the
edit prompt and ROME's own efficacy margin each correlate with propagation at Spearman
**0.42** — about 18% of variance — and at **0.419 against 0.425** they are not two views of
the answer but one weak view.<Margin>Which also closes a tempting line: since the two agree,
there is no quantity ROME's Efficacy Score fails to see that displacement catches, and an
efficacy-metric critique we had begun to build does not survive at layer 5.
<Evidence id="E-029" /></Margin> The coefficient cannot close the gap either — it is pinned
at exactly 1.000 for precisely the probes in question, so it has **zero variance where the
outcome varies most**. Whatever governs propagation magnitude is none of the three.

## 5 · Every claim this project withdrew

<p className="ocl-tablecap"><strong>Table 5.</strong> Every claim this project made, and what became of it.</p>

| claim | status | what changed it | record |
| --- | --- | --- | --- |
| Backward probing is unexplored | narrowed | RippleEdits covers inverse/symmetric relations | <Evidence id="f-R-005a">R-005a</Evidence> |
| Edits leave grounds *contradictory* | withdrawn | grounds are evidential; improbable, not impossible | <Evidence id="E-002" /> |
| CounterFact verifies possession | withdrawn | reversed from Appendix D; construction is model-independent | <Evidence id="f-D-002">D-002</Evidence> |
| The `outer` deficit is pool concentration | withdrawn | it is two strings, US and UK | <Evidence id="E-009b" /> |
| The surface-form finding is novel | withdrawn | <Cite id="holtzman2021surface" /> | <Evidence id="f-R-010">R-010</Evidence> |
| Possession × editability is unclaimed | withdrawn | <Cite id="knowledgespectrum2025" /> | <Evidence id="f-R-010">R-010</Evidence> |
| The model revises the defeasible premise | withdrawn | the work-country edit does the same thing | <Evidence id="E-015" /> |
| Leakage is structural *in ROME* | narrowed | structural given the layer; reordering helps at depth | <Evidence id="T-075" /> |
| Four nnsight constraints | withdrawn, one reinstated | a flaky backend explained three; the fourth is real and silent | <Evidence id="O-007" /> · <Evidence id="O-008" /> |
| Prefix-sharing probes receive the full delta | **holds** | analytic · all layers · floor measured | <Evidence id="E-016-2">E-016</Evidence> · <Evidence id="E-018" /> |
| The coefficient predicts how far an edit travels | **withdrawn** | never asserted here, then measured false: 2.96× at fixed delivery | <Evidence id="E-028d" /> |

Eleven claims, **eight withdrawn or narrowed**. That ratio is the honest summary.

The last row is one we never claimed and checked anyway. §6.3 carried it as an objection
we could not answer; answering it took four runs and cost us the strongest available
reading of our own mechanism.

### 5.1 · What the withdrawals rule out, and the boundary they leave

Table 5 is a list. This is what it adds up to — and the first thing to separate is
**elimination** from **our own cost**, because only one of them is a contribution and a
record that mixes them earns credit for neither.

**Eliminations. These constrain the space for anyone working in it.**

| ruled out | by | what it closes |
| --- | --- | --- |
| Blast radius can be predicted from how much of the edit arrives | <Evidence id="E-028d" /> | Delivery held at exactly 1.000 still gives **2.96×** variation in reach. The cheap-predictor route fails, and the measurement says why. |
| An edit suppresses everything about the subject uniformly | <Evidence id="E-033" /> | The floor is **1 of 6** arms. Two effects become one effect and one special case. |
| ROME's efficacy score misses what displacement catches | <Evidence id="E-029" /> | At the standard edit layer the two predict propagation equally — **0.425 against 0.419**. There is no metric critique available here. |
| Different subjects are near-orthogonal at the subject position | <Evidence id="E-027" /> · <Evidence id="E-030" /> | A Llama-3.1-8B fact, not a ROME one, and architectural rather than an artifact of unfamiliar names. |
| The floor dips where ROME edits | <Evidence id="E-031" /> | Minima sit at different depths in different models, and in neither at the edited layer. |
| Backward probing is unexplored · the surface-form result is ours · knowledge-status × editability is unclaimed | <Evidence id="f-R-001">R-001</Evidence> · <Evidence id="f-R-010">R-010</Evidence> | Three framings retired against existing literature, two of them after we had designed around them. |

**Our own cost. These constrain nothing and are not offered as findings.**

A gate that measured target lift, which a logit nudge also passes
(<Evidence id="E-026" />). A dip criterion defeated by a flat-bottomed minimum
(<Evidence id="E-031" />). Layer 5 used on two models where it is depth fraction 0.16 and
0.06 (<Evidence id="E-033" />). A delta cache that reported a partial run as a whole one.
They are in the record because they are why the rest can be trusted — not because they
narrowed anything.

**The boundary the eliminations leave.** Stated as sharply as the evidence allows:

> **Achievable.** *Whether* an edit reaches a given prompt — exactly, with no forward pass
> through the edited model, at any scale from 6B to 405B. And *which* probes take the worst
> of it — the injected value's answer type predicts it, 6 of 6 arms.
>
> **Not achievable, on this record.** *How much* any of them moves. Belief displacement and
> the efficacy margin reach ρ ≈ 0.42 — about 18% of variance — and the coefficient cannot
> help by construction, because it is pinned at exactly 1.000 across precisely the probes
> whose outcomes differ most.

**We can say which facts an edit touches. We cannot say how hard.** That sentence is the
whole contribution of the negative results, and the question on the far side of it —
what *does* set the magnitude — is <Evidence id="T-086" />, which has no candidate
explanation anywhere in this record.

## 6 · What to attack

**1 · n = 42, one model, one relation family, one layer.** Every statement here is an
*existence* claim; no rate is defensible and the artifacts are written to avoid implying
one.<Margin>A standing constraint rather than a disclaimer added at write-up: hand-built and mined sets license existence and never frequency.<Evidence id="O-004" /></Margin> If the mechanism needs a frequency result to matter, that objection stands and we
cannot meet it.

**2 · The mechanism is a line of algebra — is it interesting?** A reviewer could
reasonably say practitioners already assume this. We have not found it stated, and "we did
not find it" is the weakest form of novelty claim.

**3 · Coefficient is not behaviour — conceded, and now measured.** This was listed here
as an objection we could not answer. §4.4 answers it against us: holding delivery fixed at
a coefficient of exactly 1.000 and matching the edits on belief displacement, a layer-5
edit still reaches **2.96× further** than a layer-20 one. The coefficient **bounds delivery
and does not predict effect**, so every section above describes delivery only. The original
form of the objection was right on its own terms too — rescaling by 0.27 broke relocation
in 3 of 4 chains while whitening's 3.7× attenuation changed nothing, so the map from
coefficient to destination was never monotone.<Margin>We asserted §4.4's conclusion once on
a design whose arms differed in edit strength, and withdrew it. Earning the same sentence
took three further runs: matched displacement, matched norm, and a budget control. <Evidence id="E-028d" /></Margin>

**4 · `C = I` is what *EasyEdit users* run — and two implementations circulate.** Verified
from both repositories: `kmeng01/rome` sets `mom2_adjustment: true` for gpt2-xl and
gpt-j-6B; EasyEdit sets it `false` for all fourteen configs including those two. So the
whitening term the method is built around is on by default in the authors' code and off in
the toolkit most third-party work reaches for. Our earlier phrasing — "what the field runs"
— was too strong and is corrected here.<Margin>This does not touch the central claim.
<Evidence id="E-016" /> measured the whitened arm too, and <Evidence id="E-021" /> showed
the mechanism lives in the `u·k*` normalisation, which both implementations
share.</Margin> Our whitened arm also estimated the covariance over the CounterFact prompt
distribution rather than Wikipedia, from 2048 keys, with a ridge chosen by an
in-sample/held-out agreement rule. Defensible, but not ROME.

**5 · The causal claim is about the edit, not the model.** §4.1's ablation intervenes on
ROME's own update and shows which positions the relocation depends on. It does **not**
patch the model's activations, so it says which part of *the edit* matters and never which
part of *the network* represents the fact. Interchange interventions remain unrun, and the
distinction between "this position of the update is necessary" and "this component encodes
the fact" is exactly the gap that remains.

**6 · Every absolute rate here is measured by ranking a closed pool, and that undercounts.**
Free generation relocates in 30 of 30 chains where ranking gives 67%. We report paired
contrasts precisely because they survive this — but any single rate in this paper should be
read as a floor, not an estimate.<Evidence id="E-023" />

**7 · The stronger version of our own measurement critique is refuted — by us.** A
plausible reading of §3.1 is that possession is not a fact-level property at all, only a
property of the (fact, template) pair, which would make every per-fact possession number
here and in the literature a category error. We tested it against ParaRel's own P19
templates: the modal-cell share is **0.923** against a chance value of 0.125, and 65% of
facts are identical across all eight templates.<Margin>60 facts × 8 templates. All eight
templates sit between 65% and 72% HELD, so no single bad probe carries the
stability.<Evidence id="E-022" /></Margin> Single-template probing is a noisy estimator of
a real property, not a category error. The critique that survives is narrower: a cell can
flip on phrasing, which biases a single-template estimate — not that there is nothing to
estimate.

**6 · Self-review has a ceiling.** An adversary agent checks claims against this repo's own
record and caught one overclaim before publication. It cannot catch an error the whole
record shares — which is why this page exists.

**8 · This is not a method, and the nearest misreading is a specific one.** The pinned
coefficient explains why an edit reaches every prompt sharing its subject. It is a
consequence of how ROME normalises, not a technique on offer. The nearest misreading is *"edit a deeper layer to
leak less"* — and as of §4.4 that is no longer blocked by a missing measurement, because we
made it. A layer-20 edit does reach less far per nat of belief displaced, by a factor of
2.96.

**We still do not offer it, and the reason is in our own numbers rather than in scope
policy.** Matching layer 5's displacement at layer 20 took a **16× step budget**. And what
we measured falling is reach to *any* prefix-sharing probe — which includes the paraphrases
an editor **wants** to reach. Our probes cannot separate leakage an editor would pay to
remove from generalisation it would pay to keep, so "leaks less" and "generalises less" are
the same measurement here. That is the field's specificity/generalisation tradeoff, and
naming which side of it a deeper layer lands on is work we have not done.<Margin>Reporting
that a knob moves a quantity is measurement. Recommending the knob means showing the trade
is favourable, which would mean owning a baseline.<Evidence id="E-028d" /></Margin>

_This entry exists because an adversarial framing has no natural slot for it. "What to
attack" collects what a reviewer would dispute, and nobody disputes a constraint on use —
so the category has to be added deliberately or it vanishes in the rename._

## 7 · What we would like decided

1. **Is the pinned-coefficient result known?** The question we cannot answer from inside.
2. **Does it matter for ripple benchmarks?** Every propagation benchmark we know of probes
   with prompts that begin with the subject. If the coefficient is pinned on exactly those
   prompts, part of what they measure may be mechanical. **Priced:** re-scoring one published
   ripple benchmark under a subject-final probe form against its own subject-initial one is
   about a week — rewriting the probes is the work, scoring is hours. What it would change:
   either their propagation rates survive the reform, or a share of reported ripple is the
   coefficient rather than the model.
3. **Is n = 42 with an existence claim publishable anywhere**, or does this need the
   frequency work it currently forbids itself?

## 8 · What is open

Nine threads are open or active. They are listed because the useful question to a reader
who knows the field is not *"is this right"* but *"which of these is worth a month"* — and
we cannot rank them from inside.

<p className="ocl-tablecap"><strong>Table 8.</strong> Open threads, what each would decide, and what it costs. Ordered by</p>
what we would spend next, which is a judgement we would like contradicted.

| thread | the question | what a result would settle | cost |
| --- | --- | --- | --- |
| <Evidence id="T-086" /> | What sets how far an edit travels? | The coefficient is pinned where the outcome varies, displacement and efficacy explain 18% between them. Nothing in the record predicts the other 82%. | unknown — needs a candidate |
| <Evidence id="T-082" /> | Is GPT-J's higher floor real, or unfamiliarity? | Whether §4.3's narrowing of the floor to a Llama fact is confirmed or an artifact of running Llama-gated subjects on another model | hours |
| <Evidence id="T-078" /> | What reorients the subject key with depth? | §4.3 rules out magnitude and names attention as the candidate without testing it. "cos fell" is not "context was mixed in". | a day |
| <Evidence id="T-081" /> | Is the floor-plus-displacement structure a *birthplace* fact? | §4.5 is measured on one relation. Editing occupation instead inverts the prediction; a clean crossover would establish the mechanism. | a day |
| <Evidence id="T-083" /> | Why is the different-subject floor lowest near the edit layer? | Both models' floors dip near depth fraction 0.15, which is roughly where ROME edits. Either a connection to ROME's own causal-tracing layer choice, or a coincidence at n≈12. | a day |
| <Evidence id="T-054" /> | CounterFact runs no possession check | Its premise was reversed by <Evidence id="f-D-002">D-002</Evidence>; it needs re-reading rather than running | reading |

Two further threads are answered but worth naming because they cost us claims:
<Evidence id="T-085" /> killed an efficacy-metric critique in an hour by joining two files
already on disk, and <Evidence id="T-084" /> cost six hours of compute to establish that a
weak edit at depth was a hyperparameter artifact rather than a fact about depth.

**The meta-result, and the reason §5 is the shape it is.** Classifying this project's own
17 results by comparison shape found every narrowing came from **varying a dimension
previously held fixed**, and none from adding arms to a dimension already varied. The
three never varied anywhere were model, edit layer, and edited relation. Two of them are
now §4.3 and §4.4. The third is <Evidence id="T-081" />.<Margin>Prescriptively: before
running a comparison, list what it holds fixed — model, layer, relation, template, pool,
measurement method, decoding — and ask which has never been varied anywhere in the record.
<Evidence id="f-T-065">T-065</Evidence></Margin>

## Artifacts

Every record behind this paper is listed in the **[evidence ledger](./ledger)** — all 33
decisions, 18 findings and 67 threads, generated from the repository so it cannot drift
from it. Most of them went nowhere; that is the point of publishing the whole list rather
than the ten claims this paper defends.

| | |
| --- | --- |
| [evidence ledger](./ledger) | the complete record, generated |
| `agents/shared/decisions.md` | 33 entries; falsification stated before each run |
| `agents/shared/findings.md` | 18 literature entries, including the two that killed directions |
| `threads.md` | 67 threads — 47 answered, 8 parked, 7 open, 2 active, 3 dropped |
| `results/*.json` | per-item records, <Evidence id="E-011" /> … <Evidence id="E-018" />, <Evidence id="T-075" /> |
| `logs/` | every run, levelled and committed, including the failures |
| `src/possession.py`, `src/discrimination.py` | the shipped measure and the paired control |

<References project="edit-slice" />
