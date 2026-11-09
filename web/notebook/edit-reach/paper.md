---
title: "A cheap pre-edit estimate of an edit's reach detects contamination, not propagation"
sidebar_label: Paper
sidebar_position: 2
hide_title: true
description: A quantity computable before the edit exists is exactly 1 where the prompt names the edited subject, and blind everywhere else — including where propagation lives.
toc_max_heading_level: 3
---

<PaperHead
  kind="Working paper"
  docId="OCL-2026-07"
  version="v0.3"
  title="A cheap pre-edit estimate of an edit's reach detects contamination, not propagation"
  author="Saif Ul Islam"
  affiliation="Open Concept Lab"
  started="30 Sep 2026"
  updated="9 Nov 2026"
  buildsOn={<a href="/notebook/edit-slice/">edit-slice</a>}
/>

<Abstract keywords={["model editing", "ROME", "knowledge propagation", "benchmark contamination", "negative result"]}>

A rank-one weight edit divides its update by a fixed inner product, so the fraction of it arriving at any token can be computed in one forward pass through the *unedited* model — for any prompt, before the edit exists. We ask whether that quantity can screen an evaluation item before the item is run.

It cannot. It is pinned to 1 wherever the prompt names the edited subject, and flat where the question never names it — which is where propagation lives. The same control separates the two regimes by **+0.8439** and by **+0.0002**. What the quantity does detect is contamination, and one published benchmark <Cite id="cohen2024ripple" /> has items that fail on exactly that ground.

Two further results came off the same probe set. Identity is worth about **sixty-five times** content, which is why there was little for any measure to predict; and the two halves of an edit — breaking the old answer and supplying the new one — separate in opposite directions on the same probes.

</Abstract>

<Contributions>

1. A reach coefficient read off the edit's own rank-one update, computable in one forward pass through the unedited model.
2. A derivation that it is exactly 1 on any prefix-sharing prompt, with its premise measured on four models from 6B to 405B.
3. Evidence that it does not predict an edit's effect: a raw correlation of ρ = 0.522 falls to an excess of 0.085, with an interval touching zero, once a same-subject control is removed.
4. A measurement of why there is little to predict — identity is worth about sixty-five times content — on a pre-stated test.
5. A separation of destruction from destination within one rank-one update, on one probe set under one metric, in opposite directions on the same probes.
6. The measure repurposed as a contamination screen, with one published benchmark scored on it, released as `editreach`.

</Contributions>
## 1. Introduction

<Lead>The task.</Lead> A weight edit changes one fact and disturbs an unknown amount of everything else. The disturbance is evaluated with hand-written item sets: paraphrases, neighbours, and multi-hop questions whose answers should follow from the edited fact <Cite id="cohen2024ripple" />, <Cite id="zhong2023mquake" />. Surveys of the field treat these sets as the measurement <Cite id="yao2023survey" />.

<Lead>Why that cannot bound the damage.</Lead> An item set gives a lower bound on an edit's damage and never an upper bound. It can show that an edit broke something; it cannot show that an edit broke nothing, because an item nobody wrote and a failure that never happened produce the same output — an empty result. Writing more items does not close the gap: a hand-written set measures the imagination of whoever wrote it, and consistency work shows a model's behaviour varies across surface forms the author did not think to vary <Cite id="elazar2021pararel" />.

<Lead>The move that would fix it.</Lead> Stop enumerating; start measuring. Define a quantity for *any* prompt, so an item can be scored without having been anticipated. ROME offers a natural candidate, because its update is rank one and therefore scalar at every token. The fraction of the update landing on a token is a number, computable in one forward pass through the model as it was **before** the edit.

<Lead>What this buys, stated narrowly.</Lead> It removes the need to foresee which items matter. It does not remove the need to have items: the quantity is still evaluated on prompts we hold, and a prompt nobody wrote is still unscored. What changes is that the set no longer has to be *right* in advance, only large.

<Lead>What this paper finds.</Lead> The candidate does one job exactly and the intended job not at all. It is pinned to 1 wherever the prompt names the edited subject, which makes it a reliable detector of that naming; and it is flat where the question does not name the subject, which is where propagation would have to be measured. §5 gives the numbers, §6 the record of how the control that produced them was got wrong once first.

## 2. Related work

<Lead>The nearest work.</Lead> <Cite id="he2026romelimits" narrative /> reports both the depth phenomenon and a cosine decay with layer — 0.80 at layer 5 falling to 0.50 at 25, against 0.98 to 0.47 here — eight months before this one. What it does not carry is a control of the kind in §3.3: its reading of the effect as depth rests on edit success rates staying high across layers, which is a different quantity from the one that would separate a real effect from the measure's own behaviour.

<Lead>Propagation measured after the fact.</Lead> <Cite id="luo2026knowledgesmith" narrative /> tests how far edits spread against graph structure, and finds that editing over-spreads while unlearning under-spreads, with hierarchical branch structure imposing ceilings on update effectiveness. <Cite id="rinberg2025ripplebench" narrative /> produces distance-stratified propagation curves across eight methods, with distance taken from semantic neighbours rather than from an edit's own algebra, and evaluates unlearning rather than editing. <Cite id="kruthof2026editpropbench" narrative /> labels cascades by dependency, but over manuscripts and prompted editors rather than weights. All three measure outcomes after an edit is applied. None screens an item before it is run, which is the gap this paper tries to fill and then reports it cannot.

<Lead>Where the edit lands.</Lead> The MLP layers ROME edits behave as key-value memories <Cite id="geva2021ffn" />, which is what makes a single projection a sensible place to write a fact. But where a fact can be *located* is not where it can be *edited* <Cite id="hase2023localization" /> — so a measure read off the edit's own update, rather than off a localisation, is the one worth trying. MEMIT extends the same rank-one rule to many facts at once <Cite id="meng2023memit" />, so the quantity below is defined for it too.

<Lead>On novelty, plainly.</Lead> The mechanism in §3 is a line of algebra that any practitioner could derive, and several may assume without writing it down. The claim here is **not** that it is unpublished. It is that it could not be found stated, on one web-search pass and one neighbouring paper read in full — enough to ask the question and not enough to answer it. If it is published, §3 becomes a replication and the contribution is §5.

## 3. Methods

Everything below is measured on one kind of object. It is worth naming the parts in plain language, with one example carried throughout, before any of them is given a symbol.

<Lead>The edit.</Lead> ROME takes a prompt naming somebody — *Henry Mackenzie was born in the city of* — and rewrites one layer of the model so that the next word becomes whatever was asked for. One person, one fact, one layer. That prompt is the **edit prompt**, and Henry Mackenzie is the example used from here on.

<Lead>The probe.</Lead> Any other prompt scored afterwards, to ask how much of that rewrite reached it. A probe opening with the same name — *Henry Mackenzie is the subject here. Henry Mackenzie was born in the city of* — is in the **near field**. A probe that never names him, such as a question about the head of government of the city he died in, is in the **far field**. Multi-hop propagation — the thing an edit is supposed to do and the reason anyone evaluates one — lives in the far field.

<Lead>The coefficient.</Lead> For any probe, one number: the fraction of the rewrite that lands on a chosen token. It is read off the arithmetic of the edit rather than by running the edited model, which is why it can be computed before the edit exists. §3.1 gives it.

<Lead>The floor.</Lead> A coefficient on its own cannot be judged, because a pipeline hardwired to return 1 looks the same as a correct one. Every reading is paired with a second taken identically but against *somebody else's* edit — the **floor**. If a probe reads the same against a stranger's edit as against its own, the measure has said nothing about this edit.

<Lead>The run markers.</Lead> A small marker after a number, like the one at the end of this sentence, names the run that produced it.<Prov id="E-004" /> Appendix B lists every run with its model, its size, its date and the directory it wrote. Nothing on this page is a number without one.

### 3.1 The coefficient

<Figure
  src="/img/edit-reach/two-regimes.svg"
  alt="Three prompts drawn as strips. The edit prompt opens with Henry Mackenzie. A probe opening with the same name shares every token the subject's last token can see under causal attention, so its key is identical and the coefficient is exactly 1.000. A probe opening with a different person, Karim Lala, reads 0.082."
  caption={<>The whole account in one picture. The coefficient is read at the subject's last token, and under causal attention that token sees only what precedes it — so a probe opening with the edited subject carries the same key the edit did, whatever it goes on to ask.</>}
  wide
  plain
/>

ROME rewrites a single MLP output projection $W$ at one layer so that a chosen key maps to a chosen value <Cite id="meng2022rome" />. The rewrite is rank one:

<Eq gloss="one layer, one direction, one scalar per token">

$$
W' = W + \frac{(v^{*} - W k^{*})\, u^{\top}}{u^{\top} k^{*}}
$$

</Eq>

For a token whose key at that layer is $k$, the change to the layer's output is the vector $(v^{*} - W k^{*})$ scaled by

<Eq gloss="the fraction of the update this token receives">

$$
c = \frac{k \cdot u}{u \cdot k^{*}}
$$

</Eq>

so $c$ is computable in one forward pass through the *unedited* model, needing nothing about the edit beyond $k^{*}$ and $u$. Appendix A derives the pinning result that follows from it.

### 3.2 The near field is pinned by arithmetic

Under causal attention, a prompt opening with the edited subject has, at that subject's last token, exactly the text the edit prompt had. Its key is therefore identical to $k^{*}$, and $c = 1$ — for any covariance, at any layer, whatever relation the prompt goes on to ask about. This is analytic. What was measured is its premise, and it held exactly: **1.000** across four models from 6B to 405B, served through NDIF <Cite id="fiottokaufman2025nnsight" />. A prompt naming a different person receives **0.082**.<Prov id="E-018" />

### 3.3 The control, and what it cost to get right

A coefficient of 1.000 means nothing on its own, because a pipeline hardwired to return 1 looks identical. Every reading is therefore paired with a floor: the same prompt scored against a *different* subject's edit. The floor has to match the real edit on everything except the subject — the relation included. Getting that wrong is not hypothetical. It is what this project did first, and §6 keeps the wrong floor on the page as a withdrawn finding rather than deleting it.

### 3.4 Three arms

Four of the results below are read from the same 495 probes over 42 subjects, scored under three arms:

- <Lead>real</Lead> — the subject's own edit, applied while probing that subject.
- <Lead>same-subject control</Lead> — a *different property* of the same person, at comparable magnitude. It holds identity fixed and varies content.
- <Lead>different-subject control</Lead> — another person's edit, chosen as the nearest edit magnitude. It holds magnitude roughly fixed and varies identity.

Those 495 probes fall into six families, which is how the tables below are broken down. Each asks a different way of reaching the same edited person.

<Data caption={<>The six probe families, with a real prompt from each. Henry Mackenzie is the edited subject; Karim Lala is an unedited stranger used as a floor.</>}>
  <thead>
    <tr><th>Family</th><th className="n">n</th><th>what it varies</th><th>example prompt</th></tr>
  </thead>
  <tbody>
    <tr><td><b>position</b></td><td className="n">210</td><td>where the name sits in the prompt, and whether it is there at all</td><td><i>The city where Henry Mackenzie was born is</i></td></tr>
    <tr><td><b>repetition</b></td><td className="n">84</td><td>the name appearing more than once</td><td><i>Henry Mackenzie is the subject here. Henry Mackenzie was born in the city of</i></td></tr>
    <tr><td><b>alias</b></td><td className="n">80</td><td>a different string for the same person</td><td><i>Mackenzie was born in the city of</i></td></tr>
    <tr><td><b>semantics</b></td><td className="n">42</td><td>meaning, with the string held fixed</td><td><i>It is not true that Henry Mackenzie was born in the city of</i></td></tr>
    <tr><td><b>exposure</b></td><td className="n">42</td><td>the name present but not the subject of the question</td><td><i>Karim Lala admired Henry Mackenzie. Karim Lala was born in the city of</i></td></tr>
    <tr><td><b>discrimination</b></td><td className="n">37</td><td>a different person with a confusable name</td><td><i>Henry Kissinger was born in the city of</i></td></tr>
  </tbody>
</Data>

The pair is what makes §5.3 and §5.4 possible: each arm isolates one of the two things a rank-one update carries. Magnitude matching is on `‖Δv‖/‖k*‖`, a single scalar, so two edits of equal norm can still differ in direction relative to the probe's key. A directional control is the obvious refinement and is not run here.

<Lead>Setting.</Lead> Every measurement uses layer 5, which is where ROME and EasyEdit edit by default. Edits come from CounterFact; questions from MQuAKE-CF-3k <Cite id="zhong2023mquake" /> and RippleEdits <Cite id="cohen2024ripple" />. Appendix B lists each run with its model, its size and the directory it wrote.

## 4. Implementation

`editreach` 0.1.0 is ten modules, about 1,900 lines. Two of its choices are claims rather than tidying.

<Lead>The coefficient is an object, not an expression.</Lead> In the predecessor project it was written inline in each run script. It is the thing being claimed, so it has a name and a type.

<Lead>A reading without a control does not type-check.</Lead> The rule in §3.3 was previously stated as prose, and relied on whoever wrote the next script having read it. Here it is `Unbaselined`, and the program stops.

```console
$ pip install -e ai/edit-reach
$ python -m editreach.run --config configs/mquake-far.toml
  model   meta-llama/Llama-3.1-8B (NDIF)
  layer   5     seed 1538     n 900
  → results/2026-11-06-far/  coefficients.parquet  config.toml  env.json
$ python -m editreach.report results/2026-11-06-far
  far   own 0.0543  stranger 0.0481  excess +0.0002
  near  own 0.9334  stranger 0.0506  excess +0.8439
  Unbaselined: 0 readings
```

The seed and the layer live in the config, not in argv, and every result directory carries the config and the resolved environment beside the numbers.

<Lead>What it cannot do.</Lead> Compute a new edit against a remote model. `compute_v` needs a backward pass, which nnsight 0.8.1 refuses mid-trace <Cite id="fiottokaufman2025nnsight" />. The 42 subjects everything here rests on are the ones whose edits were already cached — survivors, not a free draw.

### 4.1 Whether a remote reading can be read twice

Half the tickets in this project are not about editing at all. They ask whether a number read off a remote model is the same number tomorrow, because a result that cannot be read twice is not a result. Nine decisions came out of that, and the useful shape of them is a split: the **structural** claims are properties of the instrument and hold everywhere tested; every **magnitude** belongs to a deployment.

<Lead>Structure holds exactly.</Lead> A ratio whose two terms are read inside one trace came back at **0.000e+00** on every one of fifteen layer-model pairs, across three models, two architectures and depths 0 to 79.<Prov id="E-011" /> The suite that checks this runs unchanged on Llama-3.1-8B, Llama-3.1-70B and GPT-J-6B, and carries a per-model table so that a correct deployment running a different model is never reported as a difference.<Prov id="E-008" />

<Lead>The variation is routing, and it is exact.</Lead> Readings of one batch through fresh connections partition cleanly by the serving GPU. What first looked like drift of 2.16e-04 is not drift: the quantity takes one of a small number of **exact** values, reproducing bit-for-bit across runs, across nnsight loaders and across days, and which one you get is which replica served the request.<Prov id="E-012" /> A daily reading taken two days later returned the same content hash and the same bits as the first. So a comparison between **device-matched** readings needs no tolerance at all; the 2.2e-04 is retained only for readings whose device differs or was never recorded — which is every artifact this project made before 1 November.

```text
16 readings · one 126-prompt batch · fresh connection each · Llama-3.1-8B L5

value               readings   served by
edd2b2b152de2098           8   GPU 0
54a1755349e607dc           8   GPU 2

GPU 0    8 readings   1 distinct value
GPU 2    8 readings   1 distinct value

anchor coefficient (k and k* in one trace)
  deviation from 1.000, both devices .......... 0.000e+00
floor median (k* from cache, nothing cancels)
  within a GPU ................................ 0.000e+00
  across GPUs ................................. 3.110e-06
```

Each value came from one device and each device returned one value, and the connections alternated rather than arriving in blocks, so it is per-connection routing. The last two lines are the practical content: a ratio read inside one trace cancels the device entirely, which is why every anchor gate in the repository had survived without anyone noticing any of this. That is a property of the gate's design and not of anyone's foresight.

<Lead>The partition is a property of a deployment on a day.</Lead> It appeared on 1 November and did not on 3 November, when all sixteen connections landed on one GPU.<Prov id="E-009" /> No tolerance may be justified by the partition alone, so every run records how many distinct devices it saw rather than assuming more than one exists.

<Lead>Batch composition is not free, and that correction was ours.</Lead> "Batch composition contributes zero" was recorded, generalised into the reference, and then narrowed: it is true of the derived ratio and false of the raw keys, which move by about **2.6% of their magnitude** when the batch is reshaped.<Prov id="E-007" /> Any artifact comparing raw activations across runs is bounded there, not at 2.2e-04.

<Lead>No magnitude holds.</Lead> The disagreement between two arithmetic sites reads 5.3e‑06 on Llama-3.1-8B and 7.5e‑09 on GPT-J, which NDIF serves in float32 rather than bfloat16. The 8B and the 70B are one model family and disagree by an order of magnitude, while GPT-J differs because of how it is *served*. So the grouping variable is the deployment — dtype, sharding, tensor shape — not the family. A tolerance written into code is wrong on some other deployment; it has to be measured where it runs.

<Lead>One claim here was withdrawn by its own follow-up.</Lead> The arithmetic-site effect was first recorded as growing with depth in bfloat16. A sweep on the 70B at layers 0 to 79 showed it spanning two to three orders of magnitude across depth with **no predictable direction**.<Prov id="E-010" /> The instruction that follows changed from "be careful when reading deep" to "measure it at the layer you read", which is a smaller and more useful sentence. The full reference, with the conformance suite that found four errors in it, is [in the repository](https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/docs/ndif-reproducibility.md).

### 4.2 What the record cost

Before any of the above could be trusted, the log files had to be worth keeping. A census found that **124 of 155 committed log files were a single line naming themselves and nothing else** — 80% of the kept record was content-free. The cause was one import: five run scripts import another as a library for its loaders, and that module calls `logs.setup()` at module scope, so every dry-run pass and every run of five other scripts created a log recording nothing. `setup()` now holds the run header and emits it immediately before the first real record, with the file handler opened lazily. Importing a module costs nothing on disk; running it still produces a self-describing log.

## 5. Results

Five results, in the order they were run. The first two are about the coefficient and are negative. The third and fourth are about what a rank-one update actually does, and are the reason the first two came out the way they did. The fifth applies what survives to a published benchmark.

### 5.1 The coefficient does not predict an edit's effect

495 probes over 42 subjects, Llama-3.1-8B at layer 5, edits read from cache.<Prov id="E-001" /> Against measured movement — the fall in the probability of the pre-edit top-1 answer — the coefficient correlates at ρ = 0.522, CI (0.450, 0.587). That number is real and will be quoted, so it needs its account.

A **same-subject control** — a different property of the same person — already accounts for about 72% of the median movement, |movement| 0.1034 against |control| 0.0740. Removing it leaves an excess correlation of **0.085**, CI (−0.003, 0.172), an interval touching zero.

<Figure
  plain
  wide
  caption={<>Six probe families, ordered by median coefficient. For each, the movement under the real edit and the movement under a same-subject control, on one scale. Where the two marks nearly coincide the coefficient has predicted nothing the control did not. Only <i>exposure</i> opens a visible gap, at +0.031.</>}
>
  <svg viewBox="0 0 860 290" role="img" aria-label="Dumbbell chart of six probe families ordered by median coefficient. Repetition, coefficient 0.981, moves 0.337 under the real edit and 0.266 under the control. Semantics, 0.980, moves 0.180 and 0.177. Exposure, 0.958, moves 0.049 and 0.022. Position, 0.958, moves 0.090 and 0.066. Alias, 0.121, moves 0.007 and 0.002. Discrimination, 0.096, moves 0.022 and 0.011. In every family the two marks sit close together.">
    <g fontFamily="Lato, sans-serif" fontSize="10.5" fontWeight="900" letterSpacing="0.8" fill="var(--ocl-ink-faint)">
      <text x="20" y="34">PROBE FAMILY</text>
      <text x="268" y="34" textAnchor="end">COEF</text>
      <text x="300" y="34">MOVEMENT, REAL EDIT AGAINST A SAME-SUBJECT CONTROL</text>
    </g>
    <g stroke="var(--ocl-rule-strong)" strokeWidth="1" fill="none">
      <path d="M300 252 H820" />
      <path d="M300 252 v5" /><path d="M444 252 v5" /><path d="M589 252 v5" /><path d="M733 252 v5" />
    </g>
    <g stroke="var(--ocl-rule)" strokeWidth="1" strokeDasharray="2 6" fill="none">
      <path d="M444 48 V252" /><path d="M589 48 V252" /><path d="M733 48 V252" />
    </g>
    <g fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-faint)">
      <text x="300" y="270" textAnchor="middle">0</text>
      <text x="444" y="270" textAnchor="middle">0.10</text>
      <text x="589" y="270" textAnchor="middle">0.20</text>
      <text x="733" y="270" textAnchor="middle">0.30</text>
    </g>

    <g fontFamily="Lato, sans-serif" fontSize="12" fill="var(--ocl-ink)">
      <text x="20" y="64">repetition</text><text x="20" y="96">semantics</text><text x="20" y="128">exposure</text>
      <text x="20" y="160">position</text><text x="20" y="192">alias</text><text x="20" y="224">discrimination</text>
    </g>
    <g fontFamily="IBM Plex Mono, monospace" fontSize="11" fill="var(--ocl-ink-faint)" textAnchor="end">
      <text x="268" y="64">0.981</text><text x="268" y="96">0.980</text><text x="268" y="128">0.958</text>
      <text x="268" y="160">0.958</text><text x="268" y="192">0.121</text><text x="268" y="224">0.096</text>
    </g>

    <g stroke="var(--ocl-rule-strong)" strokeWidth="2" strokeLinecap="round" fill="none">
      <path d="M684 60 H787" /><path d="M556 92 H560" /><path d="M332 124 H371" />
      <path d="M395 156 H430" /><path d="M303 188 H310" /><path d="M316 220 H332" />
    </g>
    <g>
      <circle cx="684" cy="60" r="5.5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <circle cx="787" cy="60" r="5.5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
      <circle cx="556" cy="92" r="5.5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <circle cx="560" cy="92" r="5.5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
      <circle cx="332" cy="124" r="5.5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <circle cx="371" cy="124" r="5.5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
      <circle cx="395" cy="156" r="5.5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <circle cx="430" cy="156" r="5.5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
      <circle cx="303" cy="188" r="5.5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <circle cx="310" cy="188" r="5.5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
      <circle cx="316" cy="220" r="5.5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <circle cx="332" cy="220" r="5.5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
    </g>
    <text x="384" y="118" fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-muted)">excess +0.031, the largest</text>

    <g fontFamily="Lato, sans-serif" fontSize="10.5">
      <circle cx="585" cy="30" r="5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
      <text x="596" y="34" fill="var(--ocl-ink-muted)">same-subject control</text>
      <circle cx="742" cy="30" r="5" fill="var(--ocl-link)" />
      <text x="753" y="34" fill="var(--ocl-ink-muted)">real edit</text>
    </g>
  </svg>
</Figure>

<Data caption={<>Coefficient and movement by probe family. The excess column is what is left after the same-subject control. No family escapes: excess medians run 0.000 to 0.031.</>}>
  <thead>
    <tr><th>Probe family</th><th className="n">n</th><th className="n">coef med</th><th className="n">move med</th><th className="n">control med</th><th className="n">excess med</th></tr>
  </thead>
  <tbody>
    <tr><td>alias</td><td className="n">80</td><td className="n">0.121</td><td className="n">0.007</td><td className="n">0.002</td><td className="n">0.001</td></tr>
    <tr><td>discrimination</td><td className="n">37</td><td className="n">0.096</td><td className="n">0.022</td><td className="n">0.011</td><td className="n">0.003</td></tr>
    <tr><td>exposure</td><td className="n">42</td><td className="n">0.958</td><td className="n">0.049</td><td className="n">0.022</td><td className="n">0.031</td></tr>
    <tr><td>position</td><td className="n">210</td><td className="n">0.958</td><td className="n">0.090</td><td className="n">0.066</td><td className="n">0.001</td></tr>
    <tr><td>repetition</td><td className="n">84</td><td className="n">0.981</td><td className="n">0.337</td><td className="n">0.266</td><td className="n">0.000</td></tr>
    <tr><td>semantics</td><td className="n">42</td><td className="n">0.980</td><td className="n">0.180</td><td className="n">0.177</td><td className="n">0.000</td></tr>
  </tbody>
</Data>

<Lead>What the quantity actually predicts.</Lead> Not *this edit reaches this probe*, but *this probe is sensitive to an edit on this subject*. Those are different claims and only the second survives. The question had been written down with both of its answers before the run — if the prediction held, a usable screen; if it did not, the quantity measures delivery and the screen is a proposal — and it closed on the second.

<Lead>One check worth recording.</Lead> The `anchor-floor` family — same prompt shape, different person — returned a median coefficient of 0.0809 against the independently measured floor of 0.082.<Prov id="E-018" /> Two routes to the same number is the cheapest evidence available that the pipeline was measuring what it claimed.

### 5.2 The far field has no subject-specific dynamic range

Near-field and far-field rows use the same code path and the same floor construction; only the question type differs. The far-field excess is more than three orders of magnitude below the near-field excess, and that gap is the result.

<Figure
  src="/img/edit-reach/near-and-far-field.svg"
  alt="One shared scale from 0 to 1. In the near field the subject's own edit reads 0.9334 against a stranger's 0.0506, an excess of plus 0.8439. In the far field they read 0.0543 and 0.0481, an excess of plus 0.0002, so close that the two marks sit almost on top of each other."
  caption={<>The same control, applied twice. In the near field it separates the real edit from a stranger's by 0.84. In the far field the two marks are one mark. Llama-3.1-8B at layer 5; MQuAKE-CF-3k, 513 single-edit two-hop instances, every hop-2 question scored against all 512 other instances' <code>k*</code>, with no edit applied.</>}
  wide
  plain
/>

<Data caption={<>Coefficient under the same-relation stranger control, Llama-3.1-8B at layer 5. Intervals are bootstrap percentile.</>}>
  <thead>
    <tr><th>Regime</th><th className="n">own k*</th><th className="n">stranger</th><th className="n">excess</th><th className="n">95% CI</th><th className="n">n</th><th className="n">run</th></tr>
  </thead>
  <tbody>
    <tr><td><b>Near field</b> — the question names the subject</td><td className="n">0.9334</td><td className="n">0.0506</td><td className="n"><b>+0.8439</b></td><td className="n">.8379–.8500</td><td className="n">639</td><td className="n">E‑004</td></tr>
    <tr><td><b>Far field</b> — the question never names it</td><td className="n">0.0543</td><td className="n">0.0481</td><td className="n"><b>+0.0002</b></td><td className="n">.0001–.0004</td><td className="n">900</td><td className="n">E‑004</td></tr>
    <tr><td>Prefix-sharing premise, four models 6B–405B</td><td className="n">1.000</td><td className="n">0.082</td><td className="n">+0.918</td><td className="n">—</td><td className="n">16</td><td className="n">E‑018</td></tr>
    <tr><td>Renamed subject, delivered fraction vs. string similarity</td><td className="n">ρ = +0.778</td><td className="n">—</td><td className="n">slope +0.847</td><td className="n">—</td><td className="n">370</td><td className="n">E‑026</td></tr>
  </tbody>
</Data>

<Lead>Reading it plainly.</Lead> In the far field, a stranger's edit reaches a question as much as the real subject's edit does, to within two ten-thousandths. The far field is where multi-hop propagation lives. At layer 5 this measure has no subject-specific dynamic range there at all.

### 5.3 Identity is worth about sixty-five times content

The same 495 probes, scored under a third arm: another person's edit, matched on magnitude, applied while probing the first.<Prov id="E-002" /> Paired differences, bootstrap 10,000 resamples, seed 1538.

<Data caption={<>Median movement by arm, and the paired differences between them. Changing whose key the edit touches is worth about sixty-five times changing what it says.</>}>
  <thead>
    <tr><th>Probe family</th><th className="n">real</th><th className="n">same-subject</th><th className="n">different-subject</th></tr>
  </thead>
  <tbody>
    <tr><td><b>all</b></td><td className="n"><b>0.0977</b></td><td className="n"><b>0.0625</b></td><td className="n"><b>0.0016</b></td></tr>
    <tr><td>alias</td><td className="n">0.0065</td><td className="n">0.0020</td><td className="n">0.0001</td></tr>
    <tr><td>discrimination</td><td className="n">0.0223</td><td className="n">0.0114</td><td className="n">0.0067</td></tr>
    <tr><td>exposure</td><td className="n">0.0489</td><td className="n">0.0217</td><td className="n">−0.0005</td></tr>
    <tr><td>position</td><td className="n">0.0900</td><td className="n">0.0659</td><td className="n">0.0037</td></tr>
    <tr><td>repetition</td><td className="n">0.3373</td><td className="n">0.2656</td><td className="n">−0.0076</td></tr>
    <tr><td>semantics</td><td className="n">0.1795</td><td className="n">0.1767</td><td className="n">0.0070</td></tr>
  </tbody>
</Data>

The paired differences: real minus same-subject is **+0.0009**, CI (+0.0004, +0.0024) — the contribution of content. Same-subject minus different-subject is **+0.0583**, CI (+0.0472, +0.0732) — the contribution of identity. Both exclude zero, so this is not *content is irrelevant*; it is *content is detectable and is roughly 1.5% of the effect of identity*.

This is why §5.1 came out the way it did. The coefficient fails to predict a particular edit's effect because there is very little edit-specific effect to predict.

<Lead>A statistic that nearly misled, recorded for that reason.</Lead> The per-arm medians are 0.0977 and 0.0625, which reads as the real edit being 56% above its same-subject control — a content effect worth more than half the total. But that is a difference of medians across skewed distributions. The arms share their probes, so the estimator that answers the question is the paired median of differences, and it is +0.0009. **The unpaired form overstates the content effect roughly sixtyfold**, which is the difference between a headline and a footnote. Report paired quantities for paired designs.

### 5.4 Destruction and destination are separable

One rank-one update does two things. It **breaks** the pre-edit answer, and it **supplies** a new one. Measured on the same 495 probes and the same three arms, changing only the readout — from the named token's probability to a full-vocabulary argmax — the two halves separate in opposite directions.<Prov id="E-003" />

<Figure
  plain
  wide
  caption={<>The two halves of one rank-one update, as paired differences on a shared scale. <b>Content</b> is the real edit against a different edit on the <i>same</i> person; <b>identity</b> is that person against someone else. Destination is carried by content and identity contributes nothing; destruction is the reverse. Same 495 probes, bootstrap 10,000, seed 1538.</>}
>
  <svg viewBox="0 0 860 300" role="img" aria-label="Four paired differences on one scale from minus 0.02 to 0.34. For destination, the content difference is plus 0.2828 with a confidence interval from 0.2424 to 0.3232, and the identity difference is 0.0000 with an interval from minus 0.0101 to plus 0.0101. For destruction, the content difference is plus 0.0009 with an interval from 0.0004 to 0.0024, and the identity difference is plus 0.0583 with an interval from 0.0472 to 0.0732. The two halves put their effect in opposite columns.">
    <g fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-faint)">
      <text x="186" y="268" textAnchor="middle">0</text>
      <text x="367" y="268" textAnchor="middle">0.10</text>
      <text x="547" y="268" textAnchor="middle">0.20</text>
      <text x="728" y="268" textAnchor="middle">0.30</text>
      <text x="457" y="290" textAnchor="middle">paired median difference</text>
    </g>
    <g stroke="var(--ocl-rule-strong)" strokeWidth="1" fill="none">
      <path d="M150 250 H820" />
      <path d="M186 250 v5" /><path d="M367 250 v5" /><path d="M547 250 v5" /><path d="M728 250 v5" />
    </g>
    <path d="M186 36 V250" stroke="var(--ocl-rule-strong)" strokeWidth="1" strokeDasharray="2 5" fill="none" />

    <g fontFamily="Lato, sans-serif" fontSize="11" fontWeight="900" letterSpacing="0.9" fill="var(--ocl-ink)">
      <text x="20" y="40">DESTINATION</text>
      <text x="20" y="150">DESTRUCTION</text>
    </g>
    <g fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-faint)">
      <text x="128" y="40" textAnchor="end">does the new answer arrive?</text>
      <text x="128" y="150" textAnchor="end">is the old answer gone?</text>
    </g>

    <g fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-muted)">
      <text x="140" y="72" textAnchor="end">content</text>
      <text x="140" y="104" textAnchor="end">identity</text>
      <text x="140" y="182" textAnchor="end">content</text>
      <text x="140" y="214" textAnchor="end">identity</text>
    </g>

    <g strokeLinecap="round" fill="none">
      <path d="M186 68 H697" stroke="var(--ocl-oxide)" strokeWidth="3.5" />
      <path d="M624 68 H770" stroke="var(--ocl-oxide)" strokeWidth="1" />
      <path d="M624 63 v10 M770 63 v10" stroke="var(--ocl-oxide)" strokeWidth="1" />
      <path d="M168 100 H204" stroke="var(--ocl-link)" strokeWidth="1" />
      <path d="M168 95 v10 M204 95 v10" stroke="var(--ocl-link)" strokeWidth="1" />
      <path d="M186 178 H188" stroke="var(--ocl-oxide)" strokeWidth="3.5" />
      <path d="M187 173 v10 M190 173 v10" stroke="var(--ocl-oxide)" strokeWidth="1" />
      <path d="M186 210 H291" stroke="var(--ocl-link)" strokeWidth="3.5" />
      <path d="M271 210 H318" stroke="var(--ocl-link)" strokeWidth="1" />
      <path d="M271 205 v10 M318 205 v10" stroke="var(--ocl-link)" strokeWidth="1" />
    </g>
    <circle cx="697" cy="68" r="5" fill="var(--ocl-oxide)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />
    <circle cx="186" cy="100" r="5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-link)" strokeWidth="2" />
    <circle cx="188" cy="178" r="5" fill="var(--ocl-paper-raised)" stroke="var(--ocl-oxide)" strokeWidth="2" />
    <circle cx="291" cy="210" r="5" fill="var(--ocl-link)" stroke="var(--ocl-paper-raised)" strokeWidth="2" />

    <g fontFamily="IBM Plex Mono, monospace" fontSize="11.5">
      <text x="712" y="72" fill="var(--ocl-oxide)" fontWeight="600">+0.2828</text>
      <text x="216" y="104" fill="var(--ocl-ink-faint)">+0.0000</text>
      <text x="204" y="182" fill="var(--ocl-ink-faint)">+0.0009</text>
      <text x="332" y="214" fill="var(--ocl-link)" fontWeight="600">+0.0583</text>
    </g>
    <g fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-faint)">
      <text x="284" y="104">interval straddles zero</text>
      <text x="272" y="182">detectable, and 1.5% of identity</text>
    </g>

    <g fontFamily="Lato, sans-serif" fontSize="10.5">
      <rect x="560" y="14" width="10" height="10" fill="var(--ocl-oxide)" />
      <text x="576" y="23" fill="var(--ocl-ink-muted)">content: real − same-subject</text>
      <rect x="742" y="14" width="10" height="10" fill="var(--ocl-link)" />
      <text x="758" y="23" fill="var(--ocl-ink-muted)">identity</text>
    </g>
  </svg>
</Figure>

```text
495 probes · 42 subjects · full-vocabulary argmax · Llama-3.1-8B L5

                       base   real    ctl  other
top-1 lands in the
injected country         1%    29%     1%     1%
```

The control and the stranger both sit at the base rate. The real edit is the only arm that puts the new answer anywhere.

<Data caption={<>The two halves of one update, on the same probes, paired, bootstrap 10,000, seed 1538. Each control is at floor for one half and carries the effect for the other.</>}>
  <thead>
    <tr><th>Half</th><th>what it asks</th><th className="n">real − same-subj</th><th className="n">same-subj − diff-subj</th></tr>
  </thead>
  <tbody>
    <tr><td><b>Destination</b></td><td>does the new answer arrive?</td><td className="n"><b>+0.2828</b><span className="f">CI (+0.2424, +0.3232)</span></td><td className="n">+0.0000<span className="f">CI (−0.0101, +0.0101)</span></td></tr>
    <tr><td><b>Destruction</b></td><td>is the old answer gone?</td><td className="n">+0.0009<span className="f">CI (+0.0004, +0.0024)</span></td><td className="n"><b>+0.0583</b><span className="f">CI (+0.0472, +0.0732)</span></td></tr>
  </tbody>
</Data>

Destruction is **subject-keyed**: it follows whose key the edit touched, and the same-subject control reproduces almost all of it. Destination is **content-specific**: it follows what the edit said, and the same-subject control lands in the injected country at 1%, which is the base rate — it delivers nothing rather than a little. Discordant pairs for destination, real against the same-subject control, run 142 to 2.

<Lead>Which control is the right one depends on which half you are measuring.</Lead> That is the practical consequence, and it is easy to get wrong in exactly one direction: a same-subject control is at floor for a destination measure and reproduces 98.5% of a destruction measure. Using it on the second is using a control that has already absorbed the signal.

<Lead>What this does not establish.</Lead> The control edit injects an occupation while these probes ask for a city, so there is no arm-symmetric check that *each* edit delivers *its own* content. The claim is that content which can answer the question is what arrives — not that every edit delivers its content somewhere.

### 5.5 What this says about a published benchmark

<Figure
  src="/img/edit-reach/direct-exposure.svg"
  alt="The item is meant to test whether an edit on Leo Arons travels two hops, through his place of death to that place's head of government. But the prompt itself contains the string Leo Arons, so the edit reaches the queried token directly."
  caption={<>The item is built to ask whether an edit travels two hops. The edited subject is sitting in the prompt, so it does not have to.</>}
  wide
  plain
/>

RippleEdits <Cite id="cohen2024ripple" /> has a test type meant to check whether an edit propagates to a *different* entity reached through the edited one. Its prompts read *"the name of the head of government of the place of death of **Leo Arons** is"* — and the edited subject is sitting inside the prompt. Those items receive a median **0.982** of the update against a **0.065** floor built from a stranger's edit on the same prompts.<Prov id="E-038" />

An item like that can be answered by the update arriving at the mention directly, so a score on it cannot separate propagation from delivery. An editor could score on that test while generalising nothing.

The fault is diagnosable rather than universal. MQuAKE names the edited subject when and only when the edit sits on the chain's first hop, which means a clean subset already exists in the field's own data, by construction rather than by design.

<Data caption={<>Direct exposure of the edited subject in two multi-hop benchmarks, counted over the released sets.</>}>
  <thead>
    <tr><th>Benchmark</th><th>Item class</th><th className="n">names subject</th><th className="n">median c</th><th className="n">floor</th></tr>
  </thead>
  <tbody>
    <tr><td>RippleEdits</td><td>built to test two-hop propagation</td><td className="n">yes</td><td className="n">0.982</td><td className="n">0.065</td></tr>
    <tr><td>MQuAKE-CF-3k</td><td>two-hop chain, edit at the head</td><td className="n">6,861 / 6,861</td><td className="n">0.933</td><td className="n">0.051</td></tr>
    <tr><td>MQuAKE-CF-3k</td><td>two-hop chain, edit downstream</td><td className="n">0 / 16,506</td><td className="n">0.054</td><td className="n">0.048</td></tr>
  </tbody>
</Data>

## 6. Findings and claims

<Figure
  plain
  caption={<>One finding from proposal to withdrawal. The dates stay on the page because a silently corrected claim looks like it was never made.</>}
>
  <svg viewBox="0 0 400 150" role="img" aria-label="The life of one claim. Proposed 12 October: predicted reach predicts measured movement. First floor built 24 October. Denied 31 October on 495 probes. Replaced 2 November by the claim that stands today.">
    <text x="4" y="12" fontFamily="Lato, sans-serif" fontSize="8" fontWeight="900" letterSpacing="0.8" fill="var(--ocl-ink)">THE LIFE OF ONE CLAIM</text>
    <path d="M58 26 V130" stroke="var(--ocl-rule-strong)" strokeWidth="1" />
    <g fontFamily="IBM Plex Mono, monospace" fontSize="7.4" fill="var(--ocl-ink-faint)">
      <text x="50" y="35" textAnchor="end">12 Oct</text>
      <text x="50" y="64" textAnchor="end">24 Oct</text>
      <text x="50" y="93" textAnchor="end">31 Oct</text>
      <text x="50" y="122" textAnchor="end">2 Nov</text>
    </g>
    <circle cx="58" cy="32" r="3.4" fill="var(--ocl-paper-raised)" stroke="var(--ocl-link)" strokeWidth="1.8" />
    <circle cx="58" cy="61" r="3.4" fill="var(--ocl-paper-raised)" stroke="var(--ocl-link)" strokeWidth="1.8" />
    <path d="M54 86 l8 8 M62 86 l-8 8" stroke="var(--ocl-oxide)" strokeWidth="2" />
    <circle cx="58" cy="119" r="3.4" fill="var(--ocl-held-ink)" />
    <g fontFamily="Lato, sans-serif" fontSize="8.2" fill="var(--ocl-ink)">
      <text x="70" y="35">proposed — reach predicts movement</text>
      <text x="70" y="64">first floor built, against all donors</text>
      <text x="70" y="93" fill="var(--ocl-oxide)" fontWeight="700">denied, on 495 probes</text>
      <text x="70" y="122">replaced, once the floor was matched</text>
    </g>
    <text x="70" y="104" fontFamily="Lato, sans-serif" fontSize="7.4" fill="var(--ocl-ink-faint)">at fixed c, movement still spans ×2.96</text>
    <text x="70" y="133" fontFamily="Lato, sans-serif" fontSize="7.4" fill="var(--ocl-ink-faint)">the old floor was the different-relation floor</text>
  </svg>
</Figure>

A paper states what its author believes now. A page revised in place has to state what they believed before and why it changed, otherwise a reader who meets the old claim elsewhere has no way to know it was retired.

The table below is every claim this paper has made, numbered in the order they were first written down, each with the observation that would refute it. Struck rows are claims this project withdrew; the second line of such a row says when and why.

<Ledger caption={<>Findings ledger. A row without a stated falsifier is not admitted.</>}>
  <Finding id="F‑01" status="standing" value="1.000"
    falsifier={<><strong>Analytic.</strong> Refuted by a derivation error, or by its premise — prefix sharing — failing. The premise is what was measured.</>}>
    A prompt opening with the edited subject has the key the edit had, so $c$ is exactly 1 — any covariance, any layer, any relation asked about.
  </Finding>
  <Finding id="F‑02" status="standing" value="+0.0002"
    falsifier={<><strong>Refuted if</strong> the excess exceeds +0.01 at any layer, on a matched same-relation floor.</>}>
    In the far field, a stranger's edit on the same relation reaches a question as much as the real subject's edit does.
  </Finding>
  <Finding id="F‑03" status="standing" value="0.982"
    falsifier={<><strong>Refuted if</strong> the median falls below the 0.065 stranger floor on a re-scored sample.</>}>
    RippleEdits items built to test two-hop propagation name the edited subject, so the update arrives by arithmetic rather than by reasoning.
  </Finding>
  <Finding id="F‑04" status="standing" value="0 / 16,506"
    falsifier={<><strong>Refuted by</strong> one counterexample in either direction on the released set.</>}>
    The fault is diagnosable: MQuAKE names the subject when and only when the edit sits on hop 1.
  </Finding>
  <Finding id="F‑05" status="standing" value="ρ = 1.000"
    falsifier={<><strong>Refuted if</strong> Spearman ρ falls below 0.95 on any held-out subject set.</>}>
    The efficacy margin reported for ROME and MEMIT is rank-identical to suppression of the true answer, because both optimisers stop at the same target probability.
  </Finding>
  <Finding id="F‑06" status="standing" value="0.000e+00"
    falsifier={<><strong>Refuted by</strong> one non-zero disagreement at any layer-model pair.</>}>
    A reading with both terms of a ratio inside one trace is bit-identical across runs, replicas and days.
  </Finding>
  <Finding id="F‑10" status="standing" value="ρ = 0.085"
    falsifier={<><strong>Refuted if</strong> the excess correlation exceeds 0.5 on any probe set with a same-subject control in place.</>}>
    The coefficient predicts that a probe is sensitive to an edit on its subject, not that a particular edit reaches it. The raw ρ = 0.522 falls to 0.085 once the same-subject control is removed, with an interval touching zero.
  </Finding>
  <Finding id="F‑11" status="standing" value="×65"
    falsifier={<><strong>Refuted if</strong> the paired real-minus-same-subject difference exceeds the same-subject-minus-different-subject difference on any comparable set.</>}>
    Changing whose key an edit touches is worth about sixty-five times changing what the edit says. Both differences exclude zero, so content is detectable and is roughly 1.5% of the effect of identity.
  </Finding>
  <Finding id="F‑12" status="standing" value="+0.2828"
    falsifier={<><strong>Refuted if</strong> a readout that can express the control's own content shows the same-subject arm delivering there, or if the two halves stop separating in opposite directions on one probe set.</>}>
    Destruction and destination are separable within one rank-one update: it breaks the pre-edit answer because it touched that subject's key, and supplies the new answer because of what it said.
  </Finding>
  <Finding id="F‑13" status="standing" value="bit-identical"
    falsifier={<><strong>Refuted by</strong> one device-matched pair of readings that differ in any bit.</>}>
    The variation between remote readings is routing, not drift. The quantity takes one of a few exact values, reproducing bit-for-bit across runs, loaders and days, and which one you get is which replica served the request.
  </Finding>
  <Finding id="F‑07" status="denied" value="5.3e‑06"
    falsifier={<><strong>Denied 4 November.</strong> The 8B and 70B are one family and disagree by an order of magnitude; GPT-J differs because it is served in float32. The grouping variable is the deployment.</>}>
    The magnitude of that disagreement is a property of the model family, so a tolerance can be written once per family.
  </Finding>
  <Finding id="F‑08" status="withdrawn" value="denied"
    falsifier={<><strong>Withdrawn 31 October.</strong> 495 probes, 42 subjects. At a fixed coefficient, measured movement still spans a factor of 2.96.</>}>
    Predicted reach predicts how far the answer moves, so the quantity can gate a propagation evaluation before it runs.
  </Finding>
  <Finding id="F‑14" status="withdrawn" value="no direction"
    falsifier={<><strong>Withdrawn</strong> by its own follow-up: a sweep on the 70B at layers 0 to 79 found the effect spanning two to three orders of magnitude across depth with no predictable direction. The instruction became "measure it at the layer you read".</>}>
    The arithmetic-site disagreement grows with depth in bfloat16.
  </Finding>
  <Finding id="F‑09" status="superseded" value="+0.0232"
    falsifier={<><strong>Superseded 2 November.</strong> Nearly all of the strangers used to build that floor were asked about a different relation, so it was a different-relation floor under another name. Row 2 replaces it.</>}>
    There is real far-field signal: scored against all donors, the subject's own edit reaches its hop-2 question more than a stranger's does.
  </Finding>
</Ledger>

<Revisions caption={<>Revisions. A number that moves appears here before it appears anywhere else.</>}>
  <Rev date="9 Nov 2026" version="v0.3">Limitations gained the delivery-is-not-effect entry, which §5 had been leaning on without stating.</Rev>
  <Rev date="6 Nov 2026" version="v0.2">F‑07 denied. Every per-family tolerance in §4.1 was removed; the section now says a tolerance must be measured where it runs.</Rev>
  <Rev date="2 Nov 2026" version="v0.2">F‑09 superseded by F‑02 once the floor was found to be the different-relation floor under another name. §3.3 rewritten around the matched floor.</Rev>
  <Rev date="31 Oct 2026" version="v0.1">The project's own question closed on its negative branch. The paper's original claim — that the quantity gates a propagation evaluation — was withdrawn and the paper re-scoped to a negative result.</Rev>
</Revisions>

## 7. Limitations

<Figure
  src="/img/edit-reach/delivery-is-not-effect.svg"
  alt="An edit passes through two steps. Delivery is how much of the edit arrives at a token, and the coefficient measures it. Effect is how far the model's answer moves, and the coefficient does not measure it. At one fixed coefficient the measured movement still spans a factor of 2.96."
  caption={<>The gap this project existed to close, and did not.</>}
  wide
  plain
/>

Every qualification in this paper is collected here, so the body above runs unhedged.

1. <Lead>Delivery is not effect.</Lead> Every number here says how much of the edit vector arrives at a token. None says how far the model's answer moved. At a fixed coefficient, measured movement spans a factor of 2.96.
2. <Lead>The coefficient belongs to a token, not a prompt.</Lead> Within one prompt the subject position and the final position differ by a factor of 35, and the answer is produced at the final position.
3. <Lead>One model, one layer, two-hop chains.</Lead> A layer sweep could still find far-field dynamic range at a depth other than 5. It would not rescue layer 5, which is where ROME and EasyEdit edit.
4. <Lead>The 42 subjects are not a sample.</Lead> They are the cached survivors of a blocked path. Any magnitude here generalises no further than that set.
5. <Lead>Nothing here has been read outside the project.</Lead> Every finding was produced and reviewed by the same two parties. The self-correction record in §6 is evidence the process works, not evidence the conclusions are right.
6. <Lead>This is not an offer.</Lead> The scope above is a finding about a measure, not a method anyone should adopt. Nothing here proposes a better editor, and the novelty position rests on the search described in §2.

## 8. Conclusion

A quantity computable before an edit exists tells you, reliably, whether a prompt names the edited subject. It tells you nothing about whether an edit travelled — and §5.3 says why there was little to tell: identity is worth about sixty-five times content, so there is very little edit-specific effect for any measure to predict. The two statements are not in tension: the first is why the measure looked promising, the second is why it cannot do the job it was built for. What survives is the first one — a cheap screen that reads an evaluation item and says whether that item can test propagation at all, which one published benchmark fails. Beside it stands a result the screen was not looking for: the two halves of a rank-one update come apart, and which control is correct depends on which half is being measured.

Four questions stay open. Each is written so it could come back either way, and each names what would change if it did.

1. <Lead>Does a layer sweep find far-field dynamic range at some depth other than 5?</Lead> If yes, the screen is alive again at that depth and the scope sentence narrows to layer 5. If no, the negative result generalises across depth. This is the cheapest open item: one run on the cached subjects.
2. <Lead>Does a graded relation-similarity control move the +0.0002?</Lead> If the excess moves with relation distance, the categorical same/different split is too coarse and the far field has structure this one missed.
3. <Lead>Is subject-keyed movement the phenomenon rather than the confound?</Lead> It surfaced while reading the first run's output and was deliberately not taken up, because working on it now would be an attempt to rescue a withdrawn claim rather than a question asked in its own right.
4. <Lead>Does the backward-pass block lift?</Lead> If nnsight allows `compute_v` mid-trace, the delivery-to-effect gap in §7.1 can be tested on a free draw instead of 42 survivors.

## References

<References ids={[
  "cohen2024ripple",
  "elazar2021pararel",
  "fiottokaufman2025nnsight",
  "geva2021ffn",
  "hase2023localization",
  "he2026romelimits",
  "kruthof2026editpropbench",
  "luo2026knowledgesmith",
  "meng2022rome",
  "meng2023memit",
  "rinberg2025ripplebench",
  "yao2023survey",
  "zhong2023mquake",
]} />

Every entry above has had its title, authors, year and venue checked against the paper's own record. An entry that has not is drawn with a dotted rule and listed separately on [Reading](/reading), so the mark appears only where something is wrong — a flag on every line would say nothing.

## Appendix A. Why the coefficient is exactly 1 on a prefix-sharing prompt

Let the edit prompt be the token sequence $s_1 \dots s_m$, where $s_m$ is the subject's last token, and let $k^{*}$ be the layer-$\ell$ key read at position $m$. Let a probe be $s_1 \dots s_m\, t_1 \dots t_n$ — the same prefix, then any continuation.

Under causal attention the hidden state at position $m$ is a function only of positions $1 \dots m$. The continuation occupies positions $m+1 \dots m+n$ and therefore cannot enter it. So the probe's key at position $m$ is $k = k^{*}$ exactly, and substituting into the coefficient:

<Eq>

$$
c = \frac{k^{*} \cdot u}{u \cdot k^{*}} = 1
$$

</Eq>

The cancellation is independent of $u$, so it holds for any whitening covariance and at any layer, and independent of $t_1 \dots t_n$, so it holds whatever the probe goes on to ask.

The empirical content is entirely in the premise — that the probe really does share the prefix through $s_m$ — which is what E‑017 and E‑018 measured. The tokenizer is the one place the premise can fail quietly: a leading space or a different casing produces a different token sequence and therefore a different key, with no error raised anywhere.

## Appendix B. Provenance of every number

Each row names the run a number came from. Config files pin the seed and the layer; argv carries only the output path.

<Runs caption={<>The runs behind the figures and tables above. Directories are under <code>results/</code>.</>}>
  <Run id="E‑004" model="Llama‑3.1‑8B" n="1,539" date="6 Nov" out="2026‑11‑06‑far/">Near and far field under the same-relation stranger floor</Run>
  <Run id="E‑001" model="Llama‑3.1‑8B" n="495" date="31 Oct" out="E‑001‑predicted‑vs‑measured.json">Predicted reach against measured movement, with a same-subject control</Run>
  <Run id="E‑002" model="Llama‑3.1‑8B" n="495" date="31 Oct" out="E‑002‑different‑subject‑arm.json">The different-subject arm: identity against content</Run>
  <Run id="E‑003" model="Llama‑3.1‑8B" n="495" date="1 Nov" out="E‑003‑destination.json">The same probes under a full-vocabulary argmax readout</Run>
  <Run id="E‑007" model="Llama‑3.1‑8B" n="8" date="2 Nov" out="2026‑11‑02‑shape/">Batch reshaping against raw key magnitude</Run>
  <Run id="E‑008" model="3 models" n="36" date="3 Nov" out="2026‑11‑03‑models/">The conformance suite across two architectures</Run>
  <Run id="E‑009" model="2 models" n="32" date="3 Nov" out="2026‑11‑03‑gpu/">Whether the GPU partition reappears on another day</Run>
  <Run id="E‑010" model="2 models" n="90" date="3 Nov" out="2026‑11‑03‑depth/">Five layers on each of two models, six checks each</Run>
  <Run id="E‑012" model="Llama‑3.1‑8B" n="census" date="3 Nov" out="2026‑11‑03‑census/">Every recorded reading of one quantity, by value and device</Run>
  <Run id="E‑011" model="3 models" n="15" date="4 Nov" out="2026‑11‑04‑ndif/">Arithmetic-site disagreement across fifteen layer-model pairs</Run>
  <Run id="E‑017" model="GPT‑J‑6B" n="16" date="21 Oct" out="2026‑10‑21‑pin/">Prefix-sharing premise, first pass</Run>
  <Run id="E‑018" model="4 models" n="16" date="23 Oct" out="2026‑10‑23‑pin4/">Premise at scale; different-subject floor 0.082</Run>
  <Run id="E‑026" model="Llama‑3.1‑8B" n="370" date="28 Oct" out="2026‑10‑28‑alias/">Renamed subject: string similarity against delivered fraction</Run>
  <Run id="E‑038" model="Llama‑3.1‑8B" n="23,505" date="1 Nov" out="2026‑11‑01‑ripple/">RippleEdits re-run, direct exposure counted</Run>
</Runs>

## Appendix C. Readiness

What a short venue note needs, against what exists today. This is a checklist for the author, not a claim about the work.

<Readiness caption={<>Readiness against a short-paper submission.</>}>
  <Check met need="A result that could have come out the other way" where="§5">The floor was fixed before the run, and the question closed against the project</Check>
  <Check met need="One figure that carries the argument" where="§5">The near-and-far-field figure does the work §5 would otherwise do in prose</Check>
  <Check met need="Reproduction path" where="§4">Config, seed and resolved environment beside every result directory</Check>
  <Check met need="Positioning against the nearest work" where="§2">He et al. (2026) read in full and distinguished</Check>
  <Check need="Read by someone outside the project" where="§7.5">Every finding produced and reviewed by the same two parties</Check>
  <Check need="Breadth across depth" where="§8.1">One layer. A sweep on the cached subjects is the cheapest fix</Check>
  <Check need="A delivery-to-effect link" where="§7.1">Blocked on the backward pass; 42 survivors, not a sample</Check>
</Readiness>
