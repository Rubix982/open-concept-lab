---
title: "Rank-one edits are pinned to their subject"
sidebar_label: Review packet
sidebar_position: 2
description: A weight edit's update coefficient is exactly 1 on any prompt beginning with the edited subject, for any covariance, at every layer. Measured, with the evidence and the attack surface.
---

# Rank-one edits are pinned to their subject

**An arithmetic account of what ROME does to facts it was not aimed at**

_edit-slice · assembled 2026-09-20 · revised in place · [narrative version](/writing/five-days)_

<Aside>

This page is written to be judged. Section 6 is the attack surface, ordered by how much
damage each objection does, and section 5 lists every claim this project withdrew. If you
are deciding whether to spend time on this, read 1, then 6.

</Aside>

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
reads as propagation is displacement keyed on the subject string.

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

**We do not claim the surface-form result.** Section 4.1 depends on the fact that scoring
answers by string probability is distorted by how the answer is spelled. That is surface
form competition <Cite id="holtzman2021surface" narrative />, and the correction we
independently rebuilt — score against a subject-free version of the same prompt — is
essentially their Domain Conditional PMI. We rediscovered a 2021 result and its standard
remedy, and cite it to disclaim novelty.

**We do not claim knowledge-status × editability.** Whether a model already knowing a fact
predicts how well that fact edits has been measured, on Llama-3.1-8B, with MEMIT,
AlphaEdit and fine-tuning <Cite id="knowledgespectrum2025" />. That closed a direction we
had designed and were about to build.

**Template sets exist upstream.** CounterFact records derive from ParaRel entries
containing hand-curated template *sets*, and keep one prompt per record
<Cite id="elazar2021pararel" />; our probes inherit that collapse.

**What is left.** None of the above examines what an edit does to a fact's *premises*, and
none reports the coefficient structure of the update itself. ROME <Cite id="meng2022rome" />
derives the `C⁻¹` term but the widely-used implementation disables it — all fourteen ROME
configs in EasyEdit set `mom2_adjustment: false`, including for the two models the paper
used.

## 3 · Method

**Possession gate.** A chain is usable only if the model holds all three facts. Each is
scored against a type-matched candidate pool under two criteria: the true answer ranks
first with the real subject (*row test*), and outscores it under foil prompts whose true
answer differs (*column test*, an AUROC; chance 0.5). The column test replaces a
placeholder control that is undefined for high-prior answers — see 4.1. 136 chains mined →
78 usable → 42 carried through the edit after infrastructure loss.

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
country's capital — widened deliberately, because a pool that cannot express the coherent
answer scores a correct relocation as failure.

## 4 · Results

### 4.1 · The measure had no operating point, and fixing it took two orthogonal repairs

Before any edit: the possession measure failed on the most common answers. Rendering
countries as Wikidata labels (`United States`) rather than naturally (`the United States`)
is ungrammatical after *"born in the country of"*, and rank-1 on those answers sat at 21%.
Rendering naturally moved it to **69%** — but then the placeholder control ranked the same
answer first at the identical 69%, because *"[X] was born in the country of the United
States"* is the modal completion whether or not `[X]` means anything.

Neither repair alone recovers anything. Together they recover twenty chains.

| | placeholder control | paired control |
| --- | ---: | ---: |
| bare rendering | 58 | 59 |
| natural rendering | 59 | **78** |

This is an interaction, not two additive fixes, and it is why each looked like a null when
tested alone. Llama-3.1-70B under the old measure gave 74 usable chains; Llama-3.1-8B under
the repaired one gives 78. Repairing the instrument was worth more than an order of
magnitude of scale.

### 4.2 · The edit displaces the premise — and carries no inference

The birth-city probe lands in the edited country 67% of the time (baseline 5%, same-subject
control 5%, placebo 0%). Edinburgh → Hamburg for Germany; Paris → Santiago for Chile.

Then the relation control:

| arm | lands in target country |
| --- | ---: |
| `X was born in the country of` → T — licenses the inference | 28/42 = **67%** |
| `X works in the country of` → T — licenses nothing | 28/42 = **67%** |
| **paired difference** | **+0.0 pp** |

Exact McNemar p = 1.000 (nine discordant each way). Where both arms land in the target
country, they choose the *same city* 84% of the time. Editing where a person works
relocates their birthplace exactly as often as editing where they were born.

### 4.3 · The coefficient is pinned, by arithmetic

A whitened editor — `u = C⁻¹k*`, computed by Woodbury over a low-rank-plus-ridge key
covariance, measured **20× more selective** on held-out keys — produces **42/42 identical
destinations**. That demanded an explanation, and the per-position coefficient profile
supplies one.

<Figure
  caption="Figure 1 — Why the coefficient is pinned. The two prompts share every token up to the subject's last. Causal attention makes the key there identical, and ROME's own normalisation divides by u·k*, so the coefficient is exactly 1 for any u."
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

This accounts for the whole arc:

| observation | explanation |
| --- | --- |
| birth-city probe displaced, 67% | shares the prefix → pinned at 1.0 |
| *"Paris is located in…"* inert, −0.02 | shares no prefix → nothing pinned |
| whitening changed nothing, 42/42 | cannot alter a coefficient fixed by arithmetic |
| a uniform ×0.27 rescale **does** break it (3 of 4) | it scales the pinned term too |
| the work-country null, +0.0 pp | both prompts begin with the subject |

### 4.4 · Scope: pinned at every layer for prefix-sharing probes; escapable otherwise

<Figure
  caption="Figure 2 — Coefficient at the subject's last token, by layer, 12 subjects. Prompts beginning with the subject are pinned at exactly 1.000 at every depth. Reordering the subject escapes progressively — but not at layer 5, which is the layer this configuration edits."
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

## 5 · Every claim this project withdrew

| claim | status | what changed it |
| --- | --- | --- |
| Backward probing is unexplored | narrowed | RippleEdits covers inverse/symmetric relations |
| Edits leave grounds *contradictory* | withdrawn | grounds are evidential; improbable, not impossible |
| CounterFact verifies possession | withdrawn | reversed from Appendix D; construction is model-independent |
| The `outer` deficit is pool concentration | withdrawn | it is two strings, US and UK |
| The surface-form finding is novel | withdrawn | <Cite id="holtzman2021surface" /> |
| Possession × editability is unclaimed | withdrawn | <Cite id="knowledgespectrum2025" /> |
| The model revises the defeasible premise | withdrawn | the work-country edit does the same thing |
| Leakage is structural *in ROME* | narrowed | structural given the layer; reordering helps at depth |
| Four nnsight constraints | withdrawn, one reinstated | a flaky backend explained three; the fourth is real and silent |
| Prefix-sharing probes receive the full delta | **holds** | analytic · all layers · floor measured |

Ten claims, **seven withdrawn or narrowed**. That ratio is the honest summary.

## 6 · What to attack

**1 · n = 42, one model, one relation family, one layer.** Every statement here is an
*existence* claim; no rate is defensible and the artifacts are written to avoid implying
one. If the mechanism needs a frequency result to matter, that objection stands and we
cannot meet it.

**2 · The mechanism is a line of algebra — is it interesting?** A reviewer could
reasonably say practitioners already assume this. We have not found it stated, and "we did
not find it" is the weakest form of novelty claim.

**3 · Coefficient is not behaviour.** Figure 2 shows decay with depth, but rescaling the
coefficient by 0.27 broke relocation in 3 of 4 chains while whitening's 3.7× attenuation
changed nothing — so the map from coefficient to destination is not monotone, and "0.58 at
layer 20" does not license "less displacement at layer 20."

**4 · `C = I` is what the field runs, not what ROME describes.** Our whitened arm estimated
the covariance over the CounterFact prompt distribution rather than Wikipedia, from 2048
keys, with a ridge chosen by an in-sample/held-out agreement rule. Defensible, but not
ROME.

**5 · Everything is behavioural.** No activation patching, no interchange interventions. We
can say the model *behaves as if*; we cannot say a component *causes*. Deliberate scope,
and the largest hole.

**6 · Self-review has a ceiling.** An adversary agent checks claims against this repo's own
record and caught one overclaim before publication. It cannot catch an error the whole
record shares — which is why this page exists.

## 7 · What we would like decided

1. **Is the pinned-coefficient result known?** The question we cannot answer from inside.
2. **Does it matter for ripple benchmarks?** Every propagation benchmark we know of probes
   with prompts that begin with the subject. If the coefficient is pinned on exactly those
   prompts, part of what they measure may be mechanical. Unworked here; the sharpest thing
   the arc raises.
3. **Is n = 42 with an existence claim publishable anywhere**, or does this need the
   frequency work it currently forbids itself?

## Artifacts

| | |
| --- | --- |
| `agents/shared/decisions.md` | 19 entries; falsification stated before each run |
| `agents/shared/findings.md` | 16 literature entries, including the two that killed directions |
| `threads.md` | 57 threads — 40 answered, 8 parked, 4 open, 3 dropped |
| `results/*.json` | per-item records, E-011 … E-018, T-075 |
| `logs/` | every run, levelled and committed, including the failures |
| `src/possession.py`, `src/discrimination.py` | the shipped measure and the paired control |

## References

<References project="edit-slice" />
