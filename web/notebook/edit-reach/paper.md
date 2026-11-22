---
title: "A cheap pre-edit estimate of an edit's reach detects contamination, not propagation"
sidebar_label: Paper
sidebar_position: 2
hide_title: true
description: A quantity computable before the edit exists is exactly 1 where the prompt names the edited subject, and blind everywhere else — including where propagation lives.
toc_max_heading_level: 3

paper:
  kind: Working paper
  id: OCL-2026-07
  version: v0.6
  author: Saif Ul Islam
  affiliation: Open Concept Lab
  started: 30 Sep 2026
  updated: 15 Nov 2026
  pdf: true
  log: true
  builds_on: { label: edit-slice, href: /notebook/edit-slice/ }
  reading: 55-minute read
  hero:
    src: /img/edit-reach/where-the-edit-lands.svg
    alt: >-
      Where a rank-one edit arrives. On the left, a lit field: the edited name at
      the centre, ringed by six questions that all name it and each ask something
      different. Every one is filled in, and 0.9334 of the update arrives, against
      0.0842 for a stranger's edit on the same relation. On the right, past a
      boundary marked "it never does", eight hollow circles sit on bare paper.
      Each keeps a dependency line back to the edited name, because each
      genuinely rests on the fact that was changed — and none is filled in. There
      the reading is 0.0543 from the question's own edit and 0.0480 from a
      stranger's.
  parts:
    - n: "1"
      title: What the number is
      href: "#3-methods"
      what: A quantity read off the edit's own update, in one forward pass through the model as it stood before the edit — and the one case where it is exactly 1.
      figs: ["/img/edit-reach/two-regimes.svg", "/img/edit-reach/premise-and-floor-by-depth.svg"]
    - n: "2"
      title: Whether it predicts anything
      href: "#51-a-number-computable-before-the-edit-tracks-how-far-the-model-moved-until-a-control-removes-almost-all-of-it"
      what: 495 probes, and what is left of a visible correlation once a control on the same subject is taken out of it.
      figs: ["/img/edit-reach/coefficient-vs-movement.svg", "/img/edit-reach/near-and-far-field.svg"]
    - n: "3"
      title: What the edit carries instead
      href: "#53-whose-fact-an-edit-changes-matters-about-sixty-three-times-more-than-what-it-is-changed-to"
      what: Whose fact you edit against what you change it to, the two halves of a single update, and one published benchmark scored on the difference.
      figs: ["/img/edit-reach/identity-against-content.svg", "/img/edit-reach/what-carries-each-half.svg", "/img/edit-reach/direct-exposure.svg"]
    - n: "4"
      title: What is left standing
      href: "#6-findings-and-claims"
      what: A ceiling that forbids nothing, a magnitude nothing predicts, every claim with what would show it false, and the gap this project did not close.
      figs: ["/img/edit-reach/bound-forbids-nothing.svg", "/img/edit-reach/nothing-predicts-magnitude.svg", "/img/edit-reach/delivery-is-not-effect.svg"]
  keywords:
    - model editing
    - ROME
    - knowledge propagation
    - benchmark contamination
    - negative result
  contributions:
    - A reach coefficient read off the edit's own rank-one update, computable in one forward pass through the unedited model.
    - A derivation that it is exactly 1 on any prefix-sharing prompt, with its premise measured on three models at four depths each, and the different-subject control it is read against spanning a factor of twelve over the same readings.
    - "Evidence that it does not predict an edit's effect: a raw correlation of rho = 0.522 falls to an excess of 0.085, with an interval touching zero, once a same-subject control is removed."
    - A measurement of why there is little to predict - whose fact you edit is worth about sixty-three times what you change it to - on a pre-stated test.
    - A separation of destruction from destination within one rank-one update, on one probe set under one metric, in opposite directions on the same probes.
    - The measure repurposed as a contamination screen, with one published benchmark scored on it, released as editreach.
    - A universal upper bound on an edit's reach, derived in one line and shown to be vacuous where propagation lives - its median far-field value permits a question that never names the edited subject to receive more than one that does.
    - "A second class of candidate eliminated for what sets the magnitude: no property of the edited subject predicts it either, to within the effect 41 subjects can resolve."
---

import ThreadsBody from "./_threads.mdx";
import PlainBody from "./_plain.mdx";
import ValueTables from "./_values.mdx";

<Paper>

A rank-one weight edit divides its update by a fixed inner product. Because it does, you can work out for any prompt what fraction of the edit arrives at any token — in one forward pass, through the model as it stood *before* the edit was made.

We asked whether that number could screen an evaluation item before the item is run: score a question, and decide from the score whether it is worth testing.

It cannot. The number sits at 1 wherever the prompt names the edited subject, and it is flat wherever the question never names it. Against a control that holds the edit's size fixed, those two regimes separate by **+0.8439** and by **+0.0002**. The second figure is the one that matters, because a question that never names the subject is what propagation means.

That raised a second question: how much was there for any measure to predict? We compared two things on the same 495 probes. Changing what the edit says, holding the person fixed, moves them by **0.0009**. Changing whose fact is edited, holding everything else fixed, moves them by **0.0583** — about sixty-three times as much. Most of what an edit does follows from whose name it touched rather than from what was said, so there was little edit-specific effect for any measure to find.

If the measure cannot predict an edit's reach, can anything bound it? The same algebra gives one universal ceiling. For a question that never names the edited subject, its median value sits *above* what a question that does name it actually receives, so the ceiling cannot tell those two questions apart and forbids nothing.

The magnitude is not a property of the edited person either. Neither how widely known they are, nor how many facts depend on them, predicts how hard an edit lands — to within the smallest effect 41 subjects can resolve.

What survives is the one thing the number does well. It is high exactly when the edited name is in the prompt, so it can read an evaluation item and say whether that item is able to test propagation at all. One published benchmark <Cite id="cohen2024ripple" /> has a test type built to check two-hop propagation whose prompts contain the edited name; those items take a median **0.982** of the update against a **0.065** floor.

One more result came off the same probe set, and it was not the one we were looking for. A single edit does two things: it breaks the old answer, and it supplies the new one. Those two halves come apart. Each is carried by a different control on the same probes, which means the correct control depends on which half is being measured.

</Paper>

## 1. Introduction

<Gist>Why a number you could compute before making an edit would be worth having, and what we expected it to do.</Gist>

<Lead>The task.</Lead> A weight edit changes one fact and disturbs an unknown amount of everything else. The disturbance is evaluated with hand-written item sets: paraphrases, neighbours, and multi-hop questions whose answers should follow from the edited fact <Cite id="cohen2024ripple" />, <Cite id="zhong2023mquake" />. Surveys of the field treat these sets as the measurement <Cite id="yao2023survey" />.

<Lead>Why that cannot bound the damage.</Lead> An item set gives a lower bound on an edit's damage and never an upper bound.

It can show that an edit broke something. It cannot show that an edit broke nothing, because an item nobody wrote and a failure that never happened produce the same output — an empty result.

Writing more items does not close that gap. A hand-written set measures the imagination of whoever wrote it, and consistency work shows a model's behaviour varies across surface forms the author did not think to vary <Cite id="elazar2021pararel" />.

<Lead>The move that would fix it.</Lead> Stop enumerating; start measuring. Define a quantity for *any* prompt, so an item can be scored without having been anticipated. ROME offers a natural candidate, because its update is rank one and therefore scalar at every token. The fraction of the update landing on a token is a number, computable in one forward pass through the model as it was **before** the edit.

<Lead>What this buys, stated narrowly.</Lead> It removes the need to foresee which items matter. It does not remove the need to have items: the quantity is still evaluated on prompts we hold, and a prompt nobody wrote is still unscored. What changes is that the set no longer has to be *right* in advance, only large.

<Lead>What this paper finds.</Lead> The candidate does one job exactly, and the intended job not at all.

It is pinned to 1 wherever the prompt names the edited subject, which makes it a reliable detector of that naming. And it is flat where the question does not name the subject — which is the only place propagation could be measured.

The same algebra that makes it cheap also yields the upper bound an item set cannot give. That bound turns out to permit a question which never names the subject to receive more than one which does, so it forbids nothing (§5.6).

Nor does any property of the edited subject predict how hard an edit lands (§5.7).

§5 gives the numbers. §6 is the record of how the control that produced them was got wrong once first.

## 2. Related work

<Gist>Who else has measured where an edit travels, and what none of them computes in advance of the edit.</Gist>

<Lead>The nearest work.</Lead> <Cite id="he2026romelimits" narrative /> reports both the depth phenomenon and a cosine decay with layer, eight months before this paper: 0.80 at layer 5 falling to 0.50 at 25, against 0.98 to 0.47 here.

What it does not carry is a control of the kind in §3.3. Its reading of the effect as depth rests on edit success rates staying high across layers, and that is a different quantity from the one that would separate a real effect from the measure's own behaviour.

<Lead>Propagation measured after the fact.</Lead> Three papers measure how far an edit spreads, and all three measure it once the edit has been applied.

<Cite id="luo2026knowledgesmith" narrative /> tests spread against graph structure. It finds that *editing tends to over-spread, unintentionally altering related nodes* while unlearning *often under-spreads*, and that *different hierarchical branches exhibit distinct ceilings for achievable accuracy*.

The variable it moves is a node's **level** in a hierarchy — root, intermediate, leaf. That is not the number of facts depending on a node, and the paper uses no measure of how often a subject appears in text. Both of those are relevant to §5.7, and neither is settled by it.

<Cite id="rinberg2025ripplebench" narrative /> produces distance-stratified propagation curves across eight methods. Its distance comes from semantic neighbours rather than from an edit's own algebra, and it evaluates unlearning rather than editing.

<Cite id="kruthof2026editpropbench" narrative /> labels cascades by dependency, but over manuscripts and prompted editors rather than weights.

None of the three screens an item *before* it is run. That is the gap this paper tries to fill, and then reports it cannot.

<Lead>Where the edit lands.</Lead> The MLP layers ROME edits behave as key-value memories <Cite id="geva2021ffn" />, which is what makes a single projection a sensible place to write a fact.

But where a fact can be *located* is not where it can be *edited* <Cite id="hase2023localization" />. So a measure read off the edit's own update, rather than off a localisation, is the one worth trying.

MEMIT extends the same rank-one rule to many facts at once <Cite id="meng2023memit" />, so the quantity below is defined for it too.

<Lead>The same structure, read the other way.</Lead> <Cite id="youssef2025tracing" narrative /> works from a model's **edited** weights backwards: inferring which object an edit injected without seeing the editing prompt, at up to 99%, and reversing up to 94% of edits. The quantity in §3 runs the other way — forwards, through the model as it stood *before* the edit, to score a prompt that has not been asked yet. Same rank-one structure, opposite direction, and nothing in that paper computes a per-prompt delivery.

<Lead>Bounding a perturbation is a field, and it bounds a ball.</Lead> §5.6 computes an upper bound on how much of a weight edit reaches a token, which is the shape of a certified-robustness guarantee.

That literature certifies against an adversary free to choose any direction inside a norm ball. <Cite id="weng2020certificated" narrative /> certifies a region in weight space, handling single-layer perturbation analytically; <Cite id="tsai2021weightperturb" narrative /> works from the classification margin.

A rank-one edit is a strictly smaller problem: **one** direction, fixed, and known before the edit is applied. Neither paper considers a low-rank perturbation, and neither evaluates a transformer.

So weight-space certification is not an open lane, and nothing here claims it is. What could not be found is certification that exploits a known rank-one direction for editing locality.

<Figure
  src="/img/edit-reach/ball-and-ray.svg"
  alt="Two pictures of the same weight matrix being perturbed. Left: a box of possible perturbations with arrows leaving the centre in every direction, which the certification literature must hold against. Right: one arrow along a fixed direction with only its length varying per input."
  caption={<>Why the rank-one case is the easy one. The literature certifies against a perturbation free to point anywhere in a ball; an edit points one way, and the way is known before it is applied.</>}
  wide
  plain
/>

<Lead>Why §5.6's bound stops at the layer it is read in.</Lead> A bound on the perturbation at one layer says nothing about the model's output on its own. It also needs a number saying how much the rest of the network can amplify a change fed into it — a Lipschitz constant.

<Cite id="kim2021lipschitz" /> is where that number stops being available. It proves dot-product self-attention has no such constant for any $p$-norm on an **unbounded** input domain, because one term in its derivative equals the sample variance of the input, which has no ceiling.

The same paper states that on a *compact* domain it is Lipschitz. It declines that route only because the constant depends on the input range, and a tight one would be non-trivial work.

So the honest position is that **no usable constant exists**, not that no constant exists. This paper got that distinction wrong once, before its theory sections were read.

<Lead>Evaluation in this field is inflated in more than one way, and only one of them is ours.</Lead> <Cite id="yang2025mirage" narrative /> finds the inflation in the **protocol**: teacher forcing at test time leaks both the content and the length of the ground truth, and editing success falls from **96.8%** to **38.5%** once it is removed. §5.5 finds it in the **items**, where a question built to test propagation names the subject it was supposed to reach around.

The two are independent. One is about how any item is scored, the other about which items were written, and a benchmark can suffer both at once. Neither this paper's numbers nor that one's are affected by the other, because the quantity here is a fraction of an update arriving at a token rather than a generated answer scored against a reference.

<Lead>On novelty, plainly.</Lead> The mechanism in §3 is a line of algebra that any practitioner could derive, and several may assume it without writing it down.

The claim here is **not** that it is unpublished. It is that it could not be found stated, on one web-search pass and one neighbouring paper read in full. That is enough to ask the question and not enough to answer it.

If it is published, §3 becomes a replication and the contribution is §5.

## 3. Methods

<Gist>The quantity itself: where it comes from, what it is read on, and the two controls it is read against.</Gist>

Everything below is measured on one kind of object. It is worth naming the parts in plain language, with one example carried throughout, before any of them is given a symbol.

<Lead>The edit.</Lead> ROME takes a prompt naming somebody — *Henry Mackenzie was born in the city of* — and rewrites one layer of the model so that the next word becomes whatever was asked for. One person, one fact, one layer. That prompt is the **edit prompt**, and Henry Mackenzie is the example used from here on.

<Lead>The probe.</Lead> Any other prompt scored afterwards, to ask how much of that rewrite reached it.

A probe opening with the same name — *Henry Mackenzie is the subject here. Henry Mackenzie was born in the city of* — is in the **near field**.

A probe that never names him is in the **far field**. *The author of The Man of Feeling was born in the country of* is one: it reaches him through the book he wrote, and it rests on the city the edit changed.

Multi-hop propagation — the thing an edit is supposed to do, and the reason anyone evaluates one — lives in the far field.

<Lead>The coefficient.</Lead> For any probe, one number: the fraction of the rewrite that lands on a chosen token. It is read off the arithmetic of the edit rather than by running the edited model, which is why it can be computed before the edit exists. §3.1 gives it.

<Lead>The floor.</Lead> A coefficient on its own cannot be judged, because a pipeline hardwired to return 1 looks the same as a correct one.

So every reading is paired with a second one, taken identically but against *somebody else's* edit. That second reading is the **floor**.

If a probe reads the same against a stranger's edit as against its own, the measure has said nothing about this edit.

<Lead>The run markers.</Lead> A small marker after a number, like the one at the end of this sentence, names the run that produced it.<Prov id="E-004" /> Appendix B lists every run with its model, its size, its date and the directory it wrote. Nothing on this page is a number without one.

### 3.1 The edit changes one layer along one direction, so every token receives a fixed fraction of it

<Gist>That fraction is the coefficient. It falls out of the edit's own arithmetic, so it can be read before the edit is applied.</Gist>

<Figure
  src="/img/edit-reach/two-regimes.svg"
  alt="Three prompts drawn as strips. The edit prompt opens with Henry Mackenzie. A probe opening with the same name shares every token the subject's last token can see under causal attention, so its key is identical and the coefficient is exactly 1.000. A probe opening with a different person, Karim Lala, reads 0.081 on Llama-3.1-8B at layer 5 and anywhere from 0.031 to 0.388 elsewhere."
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

### 3.2 A probe that opens with the edited name receives the whole of the update, and that is arithmetic rather than a finding

<Gist>The coefficient is exactly 1 there, at any layer, on any model. What was measured is the premise that makes it so.</Gist>

Under causal attention, a prompt opening with the edited subject has, at that subject's last token, exactly the text the edit prompt had. Its key is therefore identical to $k^{*}$, and $c = 1$ — for any covariance, at any layer, whatever relation the prompt goes on to ask about. This is analytic. What was measured is its premise.

It held exactly. On GPT-J-6B, Llama-3.1-8B and Llama-3.1-70B, each read at four fractions of its own depth, the median coefficient over 42 prefix-sharing probes was **1.000** at every one of the twelve readings, with a worst deviation of **0.000e+00** — not a rounded zero, the same float. Served through NDIF <Cite id="fiottokaufman2025nnsight" />.<Prov id="E-040" />

<Lead>The floor does not travel the way the pinned value does.</Lead> It is a prompt naming a different person, and it moves everywhere the pinned value stays put. Over those same twelve readings it runs from **0.031 to 0.388**, a factor of twelve, and it is not ordered by model size or by depth: at 16% of depth the largest model returns the highest floor of the three, and at 30% the middle one does. Llama-3.1-70B alone reads 0.031, 0.140, 0.046 and 0.161 as the layer descends.<Prov id="E-040" />

<Lead>The structure the premise rests on is not a transformer artifact.</Lead> <Cite id="sharma2024locating" narrative /> runs causal tracing in Mamba, a state space model rather than a transformer, and finds the strong causal effect at the last token of the subject in middle layers, with rank-one edits inserting facts there — the same place and the same shape. That is the best outside support the prefix-sharing premise has, and it is support for the premise rather than for anything measured here.

So the floor is a property of a model at a layer and of nothing more general. Every excess reported in §5 is measured against one, which is what limitation 6 is about.

<Figure
  src="/img/edit-reach/premise-and-floor-by-depth.svg"
  alt="Two quantities read at twelve points: three models, each at four fractions of its own depth. The anchor coefficient is 1.000 at every one of the twelve, drawn as a straight rule across the top, worst deviation from 1 being zero. The different-subject floor beneath it is not fixed: it runs from 0.031 to 0.388 and is ordered by neither model size nor depth. At 16 percent of depth the largest model, Llama-3.1-70B, returns the highest floor of the three at 0.140, and at 30 percent the middle model, Llama-3.1-8B, does at 0.256. Llama-3.1-70B alone reads 0.031, 0.140, 0.046 and 0.161 as the layer descends."
  caption={<>The analytic value and the measured one, on the same axes. Twelve readings, three models, four fractions of each model's depth.<Prov id="E-040" /></>}
  wide
  plain
/>

### 3.3 A reading means nothing without a floor, and the first floor this project built was the wrong one

<Gist>The floor has to match the real edit on everything except whose edit it is — the relation included. Getting that wrong is not hypothetical.</Gist>

A coefficient of 1.000 means nothing on its own, because a pipeline hardwired to return 1 looks identical. Every reading is therefore paired with a floor: the same prompt scored against a *different* subject's edit. The floor has to match the real edit on everything except the subject — the relation included. Getting that wrong is not hypothetical. It is what this project did first, and §6 keeps the wrong floor on the page as a withdrawn finding rather than deleting it.

### 3.4 Four of the results below come from the same 495 probes, scored under three different edits

<Gist>One edit is the real one, one changes what the edit says, one changes whose edit it is. Subtracting a pair of them is what separates the two things an edit carries.</Gist>

Four of the results below are read from the same 495 probes over 42 subjects. Each probe is scored three times, under a different edit each time.

- <Lead>real</Lead> — the subject's own edit, applied while probing that subject.
- <Lead>same-subject control</Lead> — a *different property* of the same person, at comparable magnitude. It keeps the person and changes the fact.
- <Lead>different-subject control</Lead> — another person's edit, chosen as the nearest edit magnitude. It keeps the shape of the edit and changes the person.

An edit therefore carries two things that can be separated by subtraction, and both get a name here because §5.3 and §5.4 are about the difference between them.

<Lead>Content</Lead> is what changes when the person is held and the fact is changed: the real edit minus the same-subject control.

<Lead>Identity</Lead> is what changes when the fact's shape is held and the person is changed: the same-subject control minus the different-subject control.

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

<Lead>Each of the two differences isolates one of those things and not the other.</Lead> Magnitude matching is on `‖Δv‖/‖k*‖`, a single scalar, so two edits of equal norm can still differ in direction relative to the probe's key. A directional control is the obvious refinement and is not run here.

<Lead>Setting.</Lead> Every measurement uses layer 5, which is where ROME and EasyEdit edit by default. Edits come from CounterFact; questions from MQuAKE-CF-3k <Cite id="zhong2023mquake" /> and RippleEdits <Cite id="cohen2024ripple" />. Appendix B lists each run with its model, its size and the directory it wrote.

## 4. Implementation

<Gist>How the readings were taken on models we do not host, and what was checked twice before any of it was believed.</Gist>

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
  near  own 0.9334  stranger 0.0842  excess +0.8439
  Unbaselined: 0 readings
```

The seed and the layer live in the config, not in argv, and every result directory carries the config and the resolved environment beside the numbers.

<Lead>What it cannot do.</Lead> Compute a new edit against a remote model. `compute_v` needs a backward pass, which nnsight 0.8.1 refuses mid-trace <Cite id="fiottokaufman2025nnsight" />. The 42 subjects everything here rests on are the ones whose edits were already cached — survivors, not a free draw.

### 4.1 A reading taken off a remote model repeats exactly in its structure, and in its magnitude only within one deployment

<Gist>Nine findings about reading numbers off hardware we do not control. Every one of them falls on one side or the other of that split.</Gist>

<Lead>Half the tickets in this project are not about editing at all.</Lead> They ask whether a number read off a remote model is the same number tomorrow, because a result that cannot be read twice is not a result.

Nine decisions came out of that work, and they sort into two kinds.

The **structural** claims are properties of the instrument, and they hold everywhere they have been tested. Every **magnitude** belongs to one deployment and travels nowhere.

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

<Lead>The partition is a property of a deployment on a day — and of the session within it.</Lead> It appeared on 1 November and did not on 3 November, when all sixteen connections landed on one GPU.<Prov id="E-009" /> It is narrower than a day, too. The run that found it was executed twice on 1 November, four minutes apart, and the second overwrote the first; both logs survive. Within each session every device returned one value, and **no device returned the same value in both** — four distinct content hashes of the raw keys over two devices and 32 readings.<Prov id="E-039" /> No tolerance may be justified by the partition alone, so every run records how many distinct devices it saw rather than assuming more than one exists.

<Lead>Batch composition is not free, and that correction was ours.</Lead> "Batch composition contributes zero" was recorded, generalised into the reference, and then narrowed: it is true of the derived ratio and false of the raw keys, which move by about **2.6% of their magnitude** when the batch is reshaped.<Prov id="E-007" /> That run's output was lost and the check was re-run on 15 November 2026 to restore it: the derived ratio moves by **0.000000** and the raw keys by **0.042969** against a magnitude of **1.656250**, which is **2.59%**. The figure reproduces thirteen days later on a different session. Any artifact comparing raw activations across runs is bounded there, not at 2.2e-04.

<Lead>No magnitude holds.</Lead> The disagreement between two arithmetic sites reads 5.3e‑06 on Llama-3.1-8B and 7.5e‑09 on GPT-J, which NDIF serves in float32 rather than bfloat16. The 8B and the 70B are one model family and disagree by an order of magnitude, while GPT-J differs because of how it is *served*. So the grouping variable is the deployment — dtype, sharding, tensor shape — not the family. A tolerance written into code is wrong on some other deployment; it has to be measured where it runs.

<Lead>One claim here was withdrawn by its own follow-up.</Lead> The arithmetic-site effect was first recorded as growing with depth in bfloat16. A sweep on the 70B at layers 0 to 79 showed it spanning two to three orders of magnitude across depth with **no predictable direction**.<Prov id="E-010" /> The instruction that follows changed from "be careful when reading deep" to "measure it at the layer you read", which is a smaller and more useful sentence.

<Figure
  src="/img/edit-reach/conformance-by-layer.svg"
  alt="A grid of six reproducibility checks down and the sampled layers across, one panel per model: Llama-3.1-8B, GPT-J-6B and Llama-3.1-70B. Darker means a larger disagreement between two readings of the same quantity. Three checks read exactly zero at every layer on every model and are drawn empty with a dot. The nonzero values run from 1.9e-09 to 2.7e-01, and they do not grow or shrink consistently with depth across models."
  caption={<>Six checks down, the sampled layers across, one panel per model. Three of them are analytic and read <b>exactly zero</b> everywhere — drawn empty with a dot rather than as the palest shade, because matching exactly is a different statement from being small. The rest span <b>1.9e-09</b> to <b>2.7e-01</b>. Depth has no direction that holds across models: on Llama-3.1-8B the matmul-site disagreement rises from 8.4e-07 to 3.7e-05, on GPT-J-6B it sits near 1e-08 throughout, and on the 70B it moves both ways. Drawn from the runs by <code>tools/figure_heatmap.py</code>.</>}
  wide
  plain
/> The full reference, with the conformance suite that found four errors in it, is [in the repository](https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/docs/ndif-reproducibility.md).

### 4.2 Four in five committed log files held nothing, and a single import was the cause

<Gist>What the kept record actually contained, and the one line of code that emptied it.</Gist>

Before any of the above could be trusted, the log files had to be worth keeping. A census found that **124 of 155 committed log files were a single line naming themselves and nothing else** — 80% of the kept record was content-free. The cause was one import: five run scripts import another as a library for its loaders, and that module calls `logs.setup()` at module scope, so every dry-run pass and every run of five other scripts created a log recording nothing. `setup()` now holds the run header and emits it immediately before the first real record, with the file handler opened lazily. Importing a module costs nothing on disk; running it still produces a self-describing log.

## 5. Results

<Gist>Seven results, in the order the evidence forced them rather than the order we wanted.</Gist>

The first two are about the number this paper proposes, and both are negative. It does not predict how far an edit moves the model, and where a question avoids the edited name it cannot tell one edit from another.

The next two say why. Most of what an edit does follows from whose fact was changed rather than from what it was changed to, so there was very little left for any predictor to find. And the effect is not one thing but two, which come apart under the same controls.

The last three take what survives. One scores a published benchmark with it. One derives a ceiling on an edit's reach and finds the ceiling forbids nothing. The last rules out a second family of explanation for how hard an edit lands.

### 5.1 A number computable before the edit tracks how far the model moved, until a control removes almost all of it

<Gist>The coefficient looks like a predictor and is not one. What it is really tracking is whether the prompt names the edited person.</Gist>

<Lead>Two things are easy to confuse here.</Lead> Everything in this section depends on keeping them apart.

The first is **delivery**. It is how much of the edit's update vector arrives at a given token. That is what the coefficient measures, and it can be worked out before the edit is made, from the model as it still stands.

The second is **effect**. It is how far the model's answer actually moved once the edit was applied. Here that is measured as the fall in the probability of the answer the model gave before the edit.

This section asks whether the first predicts the second.

The readings come from 495 probes over 42 subjects, on Llama-3.1-8B at layer 5, with the edits read from cache.<Prov id="E-001" />

<Lead>Taken at face value, the answer looks like yes.</Lead> Delivery and effect correlate at ρ = 0.522, CI (0.450, 0.587). That number is real and it will be quoted, so it needs its account.

<Lead>The account is a control.</Lead> For every probe we also apply a second edit — a **different property of the same person**, matched in size — and measure the probe again. Anything that moves under that edit as well was never specific to the edit we care about. It is what happens to this probe whenever this person's key is touched at all.

That control alone accounts for about 72% of the median movement: |movement| 0.1034 against |control| 0.0740.

What is left after it is removed is the part that belongs to this edit and no other. Correlate the coefficient against that instead, and it falls to **0.085**, CI (−0.003, 0.172) — an interval that touches zero.

<Figure
  src="/img/edit-reach/coefficient-vs-movement.svg"
  alt="Two scatter plots sharing one vertical scale, 495 probes each. On the left, the coefficient against how far the edit moved the model: the points trend upward and Spearman is 0.522. On the right, the same coefficient against what is left once a same-subject control is removed: the cloud collapses onto the zero line and Spearman is 0.085, with an interval from -0.003 to 0.172 that crosses zero. In both panels the coefficient is bimodal, 329 probes at 0.8 or above and 127 at 0.2 or below, with only 39 in between."
  caption={<>All 495 probes, both panels on one vertical scale. On the left, the coefficient against how far the edit moved the model; on the right, what is left once the same-subject control is removed, which settles onto zero. The coefficient is bimodal — <b>329</b> probes at 0.8 or above, <b>127</b> at 0.2 or below, <b>39</b> in between — so this correlation compares two groups more than it follows a trend. Drawn from the run by <code>tools/figure_scatter.py</code>.</>}
  wide
  plain
/>

<Lead>There is a second reason not to read 0.522 as a prediction.</Lead> The coefficient hardly ever takes a value in the middle of its range. Of the 495 probes, **329** sit at 0.8 or above and **127** at 0.2 or below, which leaves **39** in between.

A rank correlation over a variable shaped like that is not following a trend. It is reporting that one of two clusters moves more than the other.

And which cluster a probe falls into is decided by whether its prompt names the edited person. So the correlation is largely restating something known before the measurement: questions that name the subject move more than questions that do not. §5.2 goes inside the far cluster and finds no range there at all.

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

The same measurement has since run on two more models, and the three do not agree about anything except the sign.

<Data caption={<>The far field on three models, two architectures, all at layer 5. Same 513 instances and the same floor construction on each. The floor here is drawn from <i>any</i> other edit in the pool; the stricter floor, a stranger matched on the same relation, is in §5.2 and the percentages against it run lower.<Prov id="E-045" /></>}>
  <thead>
    <tr><th>Model</th><th className="n">own k*</th><th className="n">any-donor floor</th><th className="n">excess over it</th><th className="n">above it</th><th className="n">near field</th></tr>
  </thead>
  <tbody>
    <tr><td>Llama-3.1-8B</td><td className="n">0.0544</td><td className="n">0.0298</td><td className="n">+0.0231</td><td className="n">79.7%</td><td className="n">0.9334</td></tr>
    <tr><td>Llama-3.1-70B</td><td className="n">0.0174</td><td className="n">0.0093</td><td className="n">+0.0075</td><td className="n">72%</td><td className="n">0.9350</td></tr>
    <tr><td>GPT-J-6B</td><td className="n">0.1303</td><td className="n">0.1280</td><td className="n"><b>+0.0019</b></td><td className="n"><b>52%</b></td><td className="n">0.7985</td></tr>
  </tbody>
</Data>

The sign survives: the excess over a floor drawn from any other edit is positive on all three, as is the excess over a different-relation floor specifically, and the excess over the *same*-relation floor is zero on all three. Nothing else survives. On the two Llamas a clear majority of far-field questions sit above their floor; on GPT-J it is 52%, a coin flip, and the two quantities are 0.1303 against 0.1280 — the same number twice. Its floor is four times the 8B one, which is the same model and layer at which the depth sweep read an anchor-floor of 0.194:<Prov id="E-040" /> GPT-J's keys at layer 5 discriminate less to begin with.

That makes the GPT-J reading consistent with this section and weak evidence for it, and the difference matters. A null on a model whose floor leaves no room for a signal is not the evidence a null on a model with room would be. The two Llamas had room and still returned +0.0231 and +0.0075, and that is where the claim is carried. The near-field column says the same thing from the other side: **0.9334 and 0.9350 are Llama numbers**, and the near field is not pinned the same way on GPT-J, where it reads 0.7985.

<Lead>What the quantity actually predicts.</Lead> Not *this edit reaches this probe*, but *this probe is sensitive to an edit on this subject*. Those are different claims, and only the second survives.

Both answers had been written down before the run. If the prediction held, the result was a usable screen for evaluation items. If it did not, the quantity measures delivery rather than effect, and the screen stays a proposal. It closed on the second.

<Lead>One check worth recording.</Lead> On Llama-3.1-8B at layer 5, the `anchor-floor` family — same prompt shape, different person — returned a median coefficient of 0.0809, and a separate run reading the floor against each case's own $k^{*}$ returned 0.0809 on the same model and layer.<Prov id="E-040" /> Two routes to the same number is the cheapest evidence available that the pipeline was measuring what it claimed. It is evidence about this model at this layer and no other: the same control read elsewhere spans 0.031 to 0.388 (§3.2).

### 5.2 Where a question never names the edited person, the measure separates a real edit from a stranger's by two ten-thousandths

<Gist>In the far field the subject's own edit and an unrelated one score within two ten-thousandths of each other. The far field is where propagation lives.</Gist>

<Lead>A question can mention the edited person or avoid mentioning them.</Lead> That difference matters more than anything else in this paper.

Call the first case the **near field**: the prompt contains the edited name. *Where was Henry Mackenzie born?* is near field.

Call the second the **far field**: the question rests on the edited fact but never names the person. *The author of The Man of Feeling was born in the country of* is far field — the model has to go from the book to Henry Mackenzie, and only then to where he was born, and his name appears nowhere in the prompt.

<Lead>The far field is what propagation means.</Lead> An edit that only repairs the near field has taught the model to say a new string when it hears a name. Whether the change reached the places that never say the name is the question worth asking.

<Lead>Both regimes are read the same way.</Lead> Same code, same floor construction; only the question type differs. The two come out more than three orders of magnitude apart. Against a stranger's edit of the same size, the real edit is ahead by **+0.8439** where the prompt names the subject, and by **+0.0002** where it does not.

<Figure
  src="/img/edit-reach/near-and-far-field.svg"
  alt="Two panels on one shared scale from 0 to 1, three models in each. In the near field, where the question names the edited subject, the subject's own edit and a stranger's on the same relation sit far apart on every model: 0.9334 against 0.0842 on Llama-3.1-8B, an excess of plus 0.8436, and 0.7985 against 0.1563 on GPT-J-6B. In the far field, where the question never names the subject, the two marks are one mark on every model: 0.0543 against 0.0480 on Llama-3.1-8B, an excess of plus 0.0002."
  caption={<>The same control, applied twice, on three models. In the near field it separates the real edit from a stranger's on every one. In the far field the two marks are one mark on every one. Layer 5; MQuAKE-CF-3k, 513 single-edit two-hop instances, every hop-2 question scored against all 512 other instances' <code>k*</code>, with no edit applied.</>}
  wide
  plain
/>

<Data caption={<>Coefficient under the same-relation stranger control, Llama-3.1-8B at layer 5. Intervals are bootstrap percentile.</>}>
  <thead>
    <tr><th>Regime</th><th className="n">own k*</th><th className="n">stranger</th><th className="n">excess</th><th className="n">95% CI</th><th className="n">n</th><th className="n">run</th></tr>
  </thead>
  <tbody>
    <tr><td><b>Near field</b> — the question names the subject</td><td className="n">0.9334</td><td className="n">0.0842</td><td className="n"><b>+0.8439</b></td><td className="n">.8379–.8500</td><td className="n">639</td><td className="n">E‑004</td></tr>
    <tr><td><b>Far field</b> — the question never names it</td><td className="n">0.0543</td><td className="n">0.0481</td><td className="n"><b>+0.0002</b></td><td className="n">.0001–.0004</td><td className="n">900</td><td className="n">E‑004</td></tr>
    <tr><td>Prefix-sharing premise, 3 models × 4 depths</td><td className="n">1.000</td><td className="n">0.031–0.388</td><td className="n">—</td><td className="n">—</td><td className="n">12×42</td><td className="n">E‑040</td></tr>
    <tr><td>Renamed subject, delivered fraction vs. string similarity — 85% of these readings are RippleEdits' <code>random</code> subset</td><td className="n">ρ = +0.778</td><td className="n">—</td><td className="n">slope +0.848</td><td className="n">.736–.812</td><td className="n">371</td><td className="n">E‑042</td></tr>
  </tbody>
</Data>

<Data caption={<>The same 900 hop-2 questions per model, read against the <i>strict</i> floor: a stranger matched on magnitude <b>and on the same relation</b>. The last column counts how often a question receives more from its own edit than from that stranger's. The percentages in §5.1 are against the looser any-donor floor and run 17 to 6 points higher.<Prov id="E-045" /></>}>
  <thead>
    <tr><th>Model</th><th className="n">own k*</th><th className="n">same-relation floor</th><th className="n">excess</th><th className="n">above it</th></tr>
  </thead>
  <tbody>
    <tr><td>Llama-3.1-8B</td><td className="n">0.0543</td><td className="n">0.0480</td><td className="n">+0.00021</td><td className="n"><b>62.6%</b></td></tr>
    <tr><td>Llama-3.1-70B</td><td className="n">0.0174</td><td className="n">0.0119</td><td className="n">+0.00004</td><td className="n">59.1%</td></tr>
    <tr><td>GPT-J-6B</td><td className="n">0.1302</td><td className="n">0.1255</td><td className="n">−0.00000</td><td className="n"><b>46.1%</b></td></tr>
  </tbody>
</Data>

A majority is a direction and not a size, so the spread matters more than the percentage. On Llama-3.1-8B the per-question excess over this floor runs **−0.0003** at the lower quartile, **+0.0088** at the upper, **+0.0201** at the ninetieth percentile and **+0.1549** at its largest. So more far-field questions receive more of their own edit than of a stranger's — and the amount by which is about four thousand times smaller than the near-field excess of +0.8439. On GPT-J-6B the count falls to 46.1%, below a coin flip, which is the same reading §5.1 records as weak evidence: that model's keys leave almost no dynamic range to find.

What that count can and cannot be used for is limitation 9.

<Lead>Reading it plainly.</Lead> In the far field, a stranger's edit reaches a question as much as the real subject's edit does, to within two ten-thousandths. The far field is where multi-hop propagation lives. At layer 5 this measure has no subject-specific dynamic range there at all.

### 5.3 Whose fact an edit changes matters about sixty-three times more than what it is changed to

<Gist>Most of what an edit does follows from whose name it touched. That is why §5.1 had so little left to predict.</Gist>

§5.1 showed that the coefficient does not predict an edit's effect. This section asks a different question, and the answer explains the first one: how much edit-specific effect was there to predict in the first place?

<Lead>To find out, the same 495 probes are scored three times over.</Lead><Prov id="E-002" />

1. Under **the real edit** — the one the probe is about.
2. Under a **different fact about the same person**, matched in size. This is the control §5.1 already used.
3. Under **another person's edit** entirely, also matched in size, applied while the first person is the one being probed.

<Lead>Those three readings give the two quantities §3.4 named.</Lead> The first score minus the second is **content** — what the edit said, with the person held. The second minus the third is **identity** — whose fact it was, with the edit's shape held.

All three scores come from the same probes, so both differences are taken one probe at a time and only then summarised — paired, with a bootstrap of 10,000 resamples at seed 1538.

<Data caption={<>Median movement under each of the three edits, by probe family. The two quantities this section is about are the gaps between these columns, and they are computed probe by probe rather than from these medians — see the figure below.</>}>
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

<Lead>The two contributions, measured.</Lead> Content comes to **+0.0009**, CI (+0.0004, +0.0024). Identity comes to **+0.0583**, CI (+0.0472, +0.0732). Neither interval contains zero. So the finding is not that content does not matter. It is that content is detectable, and that it is roughly 1.5% the size of identity.

Unrounded, the two medians are 0.000930 and 0.058282, and their ratio is **62.7**.

<Figure
  src="/img/edit-reach/identity-against-content.svg"
  alt="Two panels. The top panel pools all 495 probes on one linear axis and draws two medians of per-probe differences: identity, the same-subject control minus another person's edit, at +0.0583 with a 95% interval of 0.0472 to 0.0732; and content, the real edit minus the same-subject control, at +0.0009 with an interval of 0.0004 to 0.0024. On that shared axis content is a hairline, so an inset redraws it magnified 29 times, where its interval is visible and clears zero. The ratio of the two is 63 to one. The bottom panel splits both numbers by probe family on a log axis, each family drawn as a line running from its content value to its identity value. Five of six families run rightwards, repetition by 534 times, semantics by 444 and position by 95, while exposure runs the other way, its content value twice its identity value."
  caption={<>Identity against content, and what the pooled ratio averages over. Every bar is a median of <i>per-probe</i> differences rather than a difference of the per-arm medians — the unpaired form is the one recorded below as overstating content roughly sixtyfold. Content is a hairline beside identity, so the inset redraws it on its own axis, where its interval clears zero. Underneath, the ratio is not uniform: identity is the larger of the two in five families, by <b>×95</b> on <i>position</i> and <b>×534</b> on <i>repetition</i>, and it <b>inverts on <i>exposure</i></b>, where content is about twice identity. Exposure probes ask whether the injected object shows up, so that is the one family whose question is about content. Drawn by <code>tools/figure_identity_content.py</code>.</>}
  wide
  plain
/>

<Lead>This is why §5.1 came out the way it did.</Lead> The coefficient failed to predict a particular edit's effect because almost none of that effect was particular to the edit. It followed from whose key had been touched, which is exactly what the same-subject control also touches — and so the control reproduced it.

<Lead>A statistic that nearly misled, recorded for that reason.</Lead> There is an easier way to compute the content effect, and it gives an answer sixty times too large.

Take the two medians in the table above, 0.0977 and 0.0625, and subtract them. The real edit looks 56% higher than its same-subject control — a content effect worth more than half the total.

But that is a difference between two medians drawn from skewed distributions, and the two scores come from the *same* probes. When readings are paired like that, the estimator that answers the question is the median of the per-probe differences, not the difference of the medians. That estimator gives **+0.0009**.

**The unpaired form overstates the content effect roughly sixtyfold**, which is the difference between a headline and a footnote. Report paired quantities for paired designs.

### 5.4 One edit does two jobs, and the two are carried by different things

<Gist>Breaking the old answer follows from whose fact was edited. Supplying the new one follows from what the edit said. So the right control depends on which of the two you are measuring.</Gist>

<Lead>A rank-one update does two things at once.</Lead> It **breaks** the answer the model gave before, and it **supplies** a new one to put there. Nothing says those two have to behave alike, and they do not.

Separating them needs no new experiment. The same 495 probes and the same three edits are used again, and only the readout changes: instead of asking how far the named token's probability fell, ask which word the model now puts first out of the whole vocabulary.<Prov id="E-003" />

Read that way, the two halves move in opposite directions.

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

The control and the stranger both sit at the base rate. Of the three, the real edit is the only one that puts the new answer anywhere.

<Data caption={<>The two halves of one update, on the same probes, paired, bootstrap 10,000, seed 1538. Each control is at floor for one half and carries the effect for the other.</>}>
  <thead>
    <tr><th>Half</th><th>what it asks</th><th className="n">real − same-subj</th><th className="n">same-subj − diff-subj</th></tr>
  </thead>
  <tbody>
    <tr><td><b>Destination</b></td><td>does the new answer arrive?</td><td className="n"><b>+0.2828</b><span className="f">CI (+0.2424, +0.3232)</span></td><td className="n">+0.0000<span className="f">CI (−0.0101, +0.0101)</span></td></tr>
    <tr><td><b>Destruction</b></td><td>is the old answer gone?</td><td className="n">+0.0009<span className="f">CI (+0.0004, +0.0024)</span></td><td className="n"><b>+0.0583</b><span className="f">CI (+0.0472, +0.0732)</span></td></tr>
  </tbody>
</Data>

<Figure
  src="/img/edit-reach/what-carries-each-half.svg"
  alt="Two heat map panels, six probe families down and two columns across, content and identity. Content is the real edit minus a different fact about the same person; identity is that control minus another person's edit. In the destruction panel the identity column is filled on position, repetition and semantics while content is nearly empty; in the destination panel it is the reverse. On discrimination and exposure the destruction row runs the other way, with content above identity. Every cell carries its number."
  caption={<>The same two halves, split by probe family. The table above pools all 495 probes; this is what the pooled figure averages over. The pattern holds where most of the probes are — on <i>repetition</i>, destruction is <b>+0.3585</b> identity against <b>+0.0562</b> content, and destination is <b>+0.4524</b> content against <b>0.0000</b> identity — and it <b>inverts on two families</b>: for <i>discrimination</i> and <i>exposure</i>, destruction is carried by content, not identity. Diverging scale, with the number in every cell so nothing rests on colour. Drawn by <code>tools/figure_contributions.py</code>.</>}
  wide
  plain
/>

<Lead>Destruction is subject-keyed.</Lead> It follows whose key the edit touched, and the same-subject control reproduces almost all of it.

<Lead>Destination is content-specific.</Lead> It follows what the edit said. The same-subject control lands in the injected country at 1%, which is the base rate — it delivers nothing at all rather than a little. Counting the probes where the two disagree, the real edit beats that control 142 times to 2.

<Lead>Which control is the right one depends on which half you are measuring.</Lead> That is the practical consequence, and it is easy to get wrong in exactly one direction: a same-subject control is at floor for a destination measure and reproduces 98.5% of a destruction measure. Using it on the second is using a control that has already absorbed the signal.

<Lead>What this does not establish.</Lead> The control edit injects an occupation while these probes ask for a city, so there is no arm-symmetric check that *each* edit delivers *its own* content. The claim is that content which can answer the question is what arrives — not that every edit delivers its content somewhere.

### 5.5 A published benchmark has propagation items that name the subject they were built to reach around

<Figure
  src="/img/edit-reach/direct-exposure.svg"
  alt="The item is meant to test whether an edit on Leo Arons travels two hops, through his place of death to that place's head of government. But the prompt itself contains the string Leo Arons, so the edit reaches the queried token directly."
  caption={<>The item is built to ask whether an edit travels two hops. The edited subject is sitting in the prompt, so it does not have to.</>}
  wide
  plain
/>

RippleEdits <Cite id="cohen2024ripple" /> has a test type meant to check whether an edit propagates to a *different* entity reached through the edited one. Its prompts read *"the name of the head of government of the place of death of **Leo Arons** is"* — and the edited subject is sitting inside the prompt. Those items receive a median **0.982** of the update. The floor they are read against — the same prompts scored a second time against a stranger's edit — is **0.064 to 0.070**, because which stranger scores which prompt is a choice, and re-pairing under five seeds moves it across that range. It is 0.070 at the seed this project pins everywhere.<Prov id="E-041" /> The gap carries the claim either way; the floor is quoted as a range because it is a property of a pairing and not of the corpus.<Prov id="E-038" />

<Lead>An item like that can be answered without propagating anything.</Lead> The update arrives at the mention directly, so a score on it cannot tell propagation from delivery. An editing method could score well on that test while generalising nothing at all.

<Lead>A shortcut in a multi-hop item is not a new observation; this one is a different shortcut.</Lead> <Cite id="ju2024shortcuts" narrative /> reads the same MQuAKE-CF-3K and finds that about 20% of multi-hop editing failures come from a *factual shortcut* — a learned association between the chain's first subject and its last object, found with Knowledge Neurons and tracking how often the two co-occur in the pre-training corpus.

That is a property of what the model learned. This is a property of what the benchmark wrote down: the edited name is sitting in the prompt, which can be seen before any model is run. The two also point opposite ways — theirs explains why an edit **fails** a multi-hop item, this explains how one can **pass** without propagating.

<Lead>The fault is diagnosable rather than universal.</Lead> MQuAKE names the edited subject when, and only when, the edit sits on the chain's first hop. So a clean subset already exists inside the field's own data — by construction, not by anyone's design — and this is the kind of thing the screen is for.

<Lead>The same split has been reached from the other end.</Lead> <Cite id="shi2026write" narrative /> divides multi-hop items by **which hop was edited**: when the edited hop is the last one the answer is the newly written object itself, and only when an unedited hop follows is that object merely a bridge the model has to read. That is this section's observation approached from the opposite side, by authors editing with fine-tuning rather than a rank-one update, and it is the reason to think the observation is a property of these benchmarks rather than of this project's reading of them.

It also gives the screen something to do. That paper reports lifting the two-hop curse **on RippleEdits**, and RippleEdits is where the contaminated test type is. Which of its items could have tested propagation is a question the coefficient answers before any edit is applied — and this paper does not run that check, so it is an offer rather than a result.

<Data caption={<>Direct exposure of the edited subject in two multi-hop benchmarks, counted over the released sets.</>}>
  <thead>
    <tr><th>Benchmark</th><th>Item class</th><th className="n">names subject</th><th className="n">median c</th><th className="n">floor</th></tr>
  </thead>
  <tbody>
    <tr><td>RippleEdits</td><td>built to test two-hop propagation</td><td className="n">yes</td><td className="n">0.982</td><td className="n">0.064–0.070</td></tr>
    <tr><td>MQuAKE-CF-3k</td><td>two-hop chain, edit at the head</td><td className="n">6,861 / 6,861</td><td className="n">0.933</td><td className="n">0.051</td></tr>
    <tr><td>MQuAKE-CF-3k</td><td>two-hop chain, edit downstream</td><td className="n">0 / 16,506</td><td className="n">0.054</td><td className="n">0.048</td></tr>
  </tbody>
</Data>

### 5.6 A ceiling on an edit's reach holds for every prompt, and it rules nothing out

<Gist>One line of algebra caps how much of an edit any token can receive. The cap sits above what a question naming the subject actually gets, so it cannot tell the two kinds of question apart.</Gist>

<Lead>§1 said an item set gives a lower bound on damage and never an upper bound.</Lead> That is true of item sets. It is not true of the algebra, and the difference is one line.

Because the update's direction is fixed and only $c$ varies with the token, $c$ is a projection coefficient, and Cauchy–Schwarz bounds it for **every** prompt — no enumeration, no forward pass through the edited model:

<Eq gloss="the most any token can receive, for every prompt, with no edit applied">

$$
|c(k)| \le \frac{\lVert k \rVert}{\lVert k^{*} \rVert}
\qquad\text{with equality exactly when } k \parallel k^{*}
$$

</Eq>

So the upper bound that §1 said an item set could never give is available for nothing. The question is whether it forbids anything, which is empirical.<Prov id="E-015" /> Looseness is the bound divided by the coefficient actually read; a bound never approached rules nothing out.

<Figure
  src="/img/edit-reach/bound-forbids-nothing.svg"
  alt="Two number lines, one per regime, from zero to 1.2. In the near field the coefficient read is 0.9334 and the bound above it is 0.9881, almost touching. In the far field the coefficient is 0.0544 and the bound is 1.1456 — above the near field's 0.9334, which a dotted line carried down shows."
  caption={<>The bound for a question that never names the edited subject sits above what a question that <i>does</i> name it actually receives. It cannot tell the two apart.</>}
  wide
  plain
/>

<Data caption={<>How far the bound sits above the quantity it bounds, by regime. 1,539 question-positions over 513 instances, read offline from cached keys.</>}>
  <thead>
    <tr><th>Regime</th><th className="n">median &#124;c&#124;</th><th className="n">median bound</th><th className="n">median looseness</th><th className="n">95% CI</th><th className="n">max</th></tr>
  </thead>
  <tbody>
    <tr><td>near field — the question names the subject</td><td className="n">0.9334</td><td className="n">0.9881</td><td className="n"><b>1.05</b></td><td className="n">1.05–1.06</td><td className="n">10.6</td></tr>
    <tr><td>far field — it does not</td><td className="n">0.0544</td><td className="n">1.1456</td><td className="n"><b>21.12</b></td><td className="n">20.16–22.14</td><td className="n">1715.3</td></tr>
  </tbody>
</Data>

<Lead>One number carries this.</Lead> In the far field the bound reads a median of **1.1456**, while the coefficient actually read there has a median of **0.0544**.

A ceiling of 1.1456 permits a question that never names the edited subject to receive *more* of the update than a question that does name it actually receives. It cannot tell those two apart. So it forbids nothing that happens.

<Lead>The near field's 1.05 is not a second result.</Lead> There $k \approx k^{*}$, which is the same prefix-sharing that pins the coefficient at exactly 1 in §3.2, so Cauchy–Schwarz is near-equality by construction. It is reported because it confirms the implementation. Reading it as a positive result would be reporting §3.2 a second time under a new name.

<Lead>A prediction that was right for the wrong reason.</Lead> Before the run, the far-field bound was predicted to read about 1 and therefore forbid nothing. It reads 1.15 and forbids nothing. But the reason given was that the expected squared whitened key norm equals the key dimension — which assumes the covariance is the second moment of keys. It is the identity here, so that argument does not apply. The observed value comes from keys having comparable Euclidean norms, a different fact. The number survived; the derivation that would have carried it to another setting did not.

### 5.7 Neither how well known a subject is nor how much depends on them predicts the magnitude, to within what 41 subjects can resolve

<Gist>Seven earlier candidates were all properties of the activation geometry. These two are properties of the person, and they are the first of that kind to be tested. A null at this size is an absence of evidence, not evidence of absence.</Gist>

<Lead>Something sets how hard an edit lands, and seven candidates have already been ruled out.</Lead> Every one of them was a property of the activation geometry. This is the first test of a property of the **subject** instead.<Prov id="E-016" /> For each of 41 edited subjects, damage is the median excess — real movement minus the same-subject control of §3.3 — against two subject properties: prominence, as the number of Wikipedia language editions for the subject's Wikidata item, and dependent count, as the number of distinct properties on it.

<Figure
  src="/img/edit-reach/nothing-predicts-magnitude.svg"
  alt="Eight correlations between a subject's properties and the damage an edit does, each a point with a 95% interval. Every interval crosses zero and every point sits within 0.13 of it. A shaded band from -0.37 to +0.37 marks what 41 subjects cannot see inside, and every interval lies within it."
  caption={<>Every interval crosses zero, and every estimate sits deep inside the band this study could not see into — the largest is 0.130. A point estimate on its own would not show the band.</>}
  wide
  plain
/>

<Data caption={<>Eight relationships; six of them were computed.</>}>
  <thead>
    <tr><th>Relationship</th><th className="n">ρ</th><th className="n">95% CI</th></tr>
  </thead>
  <tbody>
    <tr><td><b>prominence vs damage</b></td><td className="n"><b>+0.005</b></td><td className="n">−0.315, +0.314</td></tr>
    <tr><td><b>dependent count vs damage</b></td><td className="n"><b>−0.053</b></td><td className="n">−0.366, +0.270</td></tr>
    <tr><td>total statements vs damage</td><td className="n">−0.055</td><td className="n">−0.370, +0.259</td></tr>
    <tr><td>headroom vs damage</td><td className="n">−0.130</td><td className="n">−0.399, +0.171</td></tr>
    <tr><td>prominence, controlling dependent count</td><td className="n">+0.059</td><td className="n">−0.228, +0.336</td></tr>
    <tr><td>dependent count, controlling prominence</td><td className="n">−0.079</td><td className="n">−0.355, +0.211</td></tr>
    <tr><td>prominence, controlling both</td><td className="n">+0.038</td><td className="n">−0.266, +0.327</td></tr>
    <tr><td>dependent count, controlling both</td><td className="n">−0.047</td><td className="n">−0.340, +0.264</td></tr>
  </tbody>
</Data>

<Lead>Every interval spans zero, and every point estimate sits within 0.13 of it.</Lead>

Three controls had been set before the run, and all three came back clean.

The two predictors correlate at ρ = 0.701, below the 0.8 line at which the partial correlations would have become unstable.

Controlling for headroom — a better-known subject has more room to fall — moves prominence from +0.059 to +0.038. There was nothing there to explain away.

Recomputing over only the four probe families that every subject shares leaves prominence at +0.015 and dependent count at −0.039.

<Lead>What this excludes, and what it does not.</Lead> At 41 subjects the widest interval spans 0.64, so this rules out a monotone relationship of about **|ρ| > 0.37** and nothing smaller. It is no evidence of an effect; it is not evidence of no effect. A real effect of 0.2 would sit inside every interval above and this study would not have seen it.

<Lead>Prominence is a proxy and is labelled as one.</Lead> The question asks about how often a subject's *name* appears in text. Wikipedia language-edition count measures how well an entity is documented, which is a different thing that correlates with it. Its range is real — 0 for a subject with no Wikipedia article at all, 67 for the best covered — so it is not degenerate, but it is not the quantity named.

**Two kinds of proxy were tested, not one, and that matters more than either of them alone.** Wikipedia coverage is external: it is a fact about how the world records an entity, and the model never sees it. Headroom is internal: it is the base model's own probability on the true answer, so it is a fact about what this model learned, whatever the world wrote down. If exposure drove damage, the second should have caught it even where the first failed, because it reads the result of exposure rather than a correlate of its cause. It reads **−0.130**, the largest estimate in the table and still well inside the band.

Neither is textual frequency, and nothing here measures it. That remains the obvious thing to try, and the two nulls make it a narrower target than it was: an exposure mechanism would now have to be invisible to the model's own confidence on the fact being edited.

## 6. Findings and claims

<Gist>Every claim made here, each with the observation that would show it false.</Gist>

<Figure
  plain
  caption={<>One finding from proposal to withdrawal, with the date of each step.</>}
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
    falsifier={<><strong>Analytic.</strong> Refuted by a derivation error, or by its premise — prefix sharing — failing. The premise is what was measured: twelve readings, three models, four fractions of each model's depth, worst deviation 0.000e+00.</>}>
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
  <Finding id="F‑11" status="standing" value="×63"
    falsifier={<><strong>Refuted if</strong> the paired real-minus-same-subject difference exceeds the same-subject-minus-different-subject difference on any comparable set.</>}>
    Changing whose key an edit touches is worth about sixty-three times changing what the edit says. Both differences exclude zero, so content is detectable and is roughly 1.5% of the effect of identity.
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
  <Finding id="F‑15" status="standing" value="21.12"
    falsifier={<><strong>Analytic in its first half, empirical in its second.</strong> The bound — the delivered fraction is at most the ratio of the two key norms — is refuted by an error in its derivation or by the update ceasing to be rank one with a fixed direction. Its looseness is refuted if the far-field median falls below 10 on any model-layer pair — at which point the bound would forbid something.</>}>
    A universal upper bound on an edit's reach exists and costs one line, and its median far-field value of 1.1456 permits a question that never names the edited subject to receive more than the near field actually receives.
  </Finding>
  <Finding id="F‑16" status="standing" value="+0.005 / −0.053"
    falsifier={<><strong>Refuted if</strong> either predictor reaches a correlation of 0.37 in magnitude on a larger subject set, which is the smallest effect 41 subjects could have seen. <strong>This is no evidence of an effect, not evidence of no effect</strong>, and a reader taking it as the second is taking more than the interval gives.</>}>
    Neither a subject's prominence nor its dependent count predicts how hard an edit hits, with every partial and covariate-controlled variant also spanning zero.
  </Finding>
</Ledger>

## 7. Limitations

<Gist>What this does not show, what was not run, and the uses this result does not license.</Gist>

<Figure
  src="/img/edit-reach/delivery-is-not-effect.svg"
  alt="An edit passes through two steps. Delivery is how much of the edit arrives at a token, and the coefficient measures it. Effect is how far the model's answer moves, and the coefficient does not measure it. At one fixed coefficient the measured movement still spans a factor of 2.96."
  caption={<>The gap this project existed to close, and did not.</>}
  wide
  plain
/>

Every qualification in this paper is collected here, so the body above runs unhedged.

1. <Lead>Delivery is not effect.</Lead> Every number here says how much of the edit vector arrives at a token. None says how far the model's answer moved. At a fixed coefficient, measured movement spans a factor of 2.96. And the gap does not close one step further along: <Cite id="rosati2024long" narrative /> scores editing in long-form generation and finds those measures have very little relationship with the short-form ones they were built to extend, so short-form effect does not give long-form behaviour either.
2. <Lead>The coefficient belongs to a token, not a prompt.</Lead> Within one prompt the subject position and the final position differ by a factor of 35, and the answer is produced at the final position.
3. <Lead>Three models, two architectures, one layer, two-hop chains.</Lead> The near and far field were read on Llama-3.1-8B, Llama-3.1-70B and GPT-J-6B, all at layer 5. A layer sweep could still find far-field dynamic range at a depth other than 5. It would not rescue layer 5, which is where ROME and EasyEdit edit. The depth sweep in §3.2 moves the *floor* across four depths on three models; it does not move the far-field excess, which stays at one layer.
4. <Lead>The GPT-J reading is consistent with §5.2 and is weak evidence for it.</Lead> Its far-field own and floor are 0.1303 and 0.1280 and 52% of questions sit above the floor, so there was almost no dynamic range available to find missing. The claim rests on the two models where a majority did sit above the floor. Every near-field figure in §5 is a Llama number: 0.9334 and 0.9350 against 0.7985 on GPT-J.
5. <Lead>GPT-J-6B is below this project's own model floor.</Lead> `CLAUDE.md` asks for a model above 8B from each architecture family. NDIF serves one `gptj` deployment and it is the 6B, so for that family the rule is not met and the second architecture is covered at the only size available.
6. <Lead>The different-subject floor is not predictable, and every excess here rests on one.</Lead> It spans 0.031 to 0.388 across three models at four depths each, ordered by neither size nor depth. So an excess measured against a floor on one model says nothing about the excess on another, and any such comparison needs the floor measured where it runs.
7. <Lead>The 42 subjects are not a sample.</Lead> They are the cached survivors of a blocked path. Any magnitude here generalises no further than that set.
8. <Lead>Nothing here has been read outside the project.</Lead> Every finding was produced and reviewed by the same two parties. The self-correction record in §6 is evidence the process works, not evidence the conclusions are right.
9. <Lead>A fraction above a floor is evidence about a population, not about an item.</Lead> §5.2 reports that 62.6% of far-field questions receive more from their own edit than from a matched stranger's. That does not say the other 37.4% were untouched while these were reached: every one of these questions receives almost nothing from either edit, and the count only records which of two near-identical readings came out larger. It cannot be used to decide anything about a single evaluation item, which is the use §5.1 closed against.

10. <Lead>A null here is an absence of evidence.</Lead> §5.7 rules out a monotone relationship of about |ρ| > 0.37 between a subject's properties and the damage an edit does, because 41 subjects cannot see smaller. An effect of 0.2 would be invisible to it. Its predictors are proxies. Wikipedia language-edition count measures how well an entity is documented, not how often its name appears in text, and headroom measures the base model's confidence on the fact being edited, not the exposure behind it. The two are of different kinds — one external to the model, one internal — and both are null, which is stronger than either alone and is still not a measurement of textual frequency.
11. <Lead>§5.6's bound stops at the layer it is read in.</Lead> It bounds how much of the update arrives at a token, not how far the output moves. Crossing to behaviour needs a Lipschitz constant for the rest of the network, and §2 reports that none has been computed — not that none exists.
12. <Lead>Which ROME implementation wrote these edits is not recorded.</Lead> The 42 edits were read from a cache and the page names no implementation. <Cite id="gupta2024rebuilding" narrative /> shows that ROME's *disabling edits* — which collapse a model outright — are an artifact of irregularities in the original implementation rather than of the algorithm, and that a corrected one removes them. So the provenance of these edits is a question this paper cannot answer, and the per-run directories that would have answered it are gone (Appendix B). The anchor gate in §3.2 returning exactly 1.000 is evidence the pipeline read them correctly, not evidence that the edits themselves are well formed.

13. <Lead>This is not an offer.</Lead> The scope above is a finding about a measure, not a method anyone should adopt. Nothing here proposes a better editor, and the novelty position rests on the search described in §2.

## 8. Conclusion

<Gist>What the number turned out to be good for, which is not what it was built for.</Gist>

<Lead>A quantity computable before an edit exists tells you one thing reliably.</Lead> It tells you whether a prompt names the edited subject.

It tells you nothing about whether an edit travelled.

§5.3 says why there was so little to tell. Identity is worth about sixty-three times content, so there is very little edit-specific effect left for any measure to predict.

The two statements are not in tension. The first is why the measure looked promising. The second is why it cannot do the job it was built for.

<Lead>What survives is the first one.</Lead> A cheap screen that reads an evaluation item and says whether that item is able to test propagation at all — which one published benchmark fails.

Beside it stands a result the screen was not looking for. The two halves of a rank-one update come apart, and which control is the correct one depends on which half is being measured.

<Lead>Two negative results were added late, and both close doors rather than open them.</Lead>

The upper bound §1 said an item set could never give does exist, and it costs one line of algebra. But it permits a far-field question to receive more of the update than a near-field one actually receives. So the only universal statement available is vacuous exactly where propagation lives.

The second is about what sets the magnitude. Seven geometric candidates had already been eliminated. A second class of variable now joins them: nothing about the subject predicts it either, to within what 41 subjects can see.

**Two classes searched — the geometry of the key and the identity of the subject — and neither carries the magnitude.**

That sentence is worth more than the one it replaces, because a reader can tell from it what has *not* been searched.

Five questions stay open. Each is written so it could come back either way, and each names what would change if it did.

1. <Lead>Does a layer sweep find far-field dynamic range at some depth other than 5?</Lead> If yes, the screen is alive again at that depth and the scope sentence narrows to layer 5. If no, the negative result generalises across depth. This is the cheapest open item: one run on the cached subjects.
2. <Lead>Does a graded relation-similarity control move the +0.0002?</Lead> If the excess moves with relation distance, the categorical same/different split is too coarse and the far field has structure this one missed.
3. <Lead>Is subject-keyed movement the phenomenon rather than the confound?</Lead> It surfaced while reading the first run's output, and §5.3 has since measured it on a pre-stated test — identity is worth about sixty-three times content. What stays open is not the measurement but the choice: whether to study the subject-keyed component as the object, or keep controlling it away. *Corrected 9 Nov 2026: this item previously said the question had been deliberately not taken up, to avoid rescuing a withdrawn claim. That reason stopped being true when §5.3 ran, and the item had not been rewritten.*
4. <Lead>Does whitening make §5.6's bound informative?</Lead> The covariance is the identity throughout this paper. The bound keeps its form under a real covariance but its norm becomes a different quantity, and whitening is precisely the operation that could shrink it in the far field. If it does, the bound forbids something and this section is reopened.
5. <Lead>Does the backward-pass block lift?</Lead> If nnsight allows `compute_v` mid-trace, the delivery-to-effect gap in §7.1 can be tested on a free draw instead of 42 survivors.

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

<Gist>The derivation in full, since an analytic claim that does not show its working is only an unfalsifiable one.</Gist>

Let the edit prompt be the token sequence $s_1 \dots s_m$, where $s_m$ is the subject's last token, and let $k^{*}$ be the layer-$\ell$ key read at position $m$. Let a probe be $s_1 \dots s_m\, t_1 \dots t_n$ — the same prefix, then any continuation.

Under causal attention the hidden state at position $m$ is a function only of positions $1 \dots m$. The continuation occupies positions $m+1 \dots m+n$ and therefore cannot enter it. So the probe's key at position $m$ is $k = k^{*}$ exactly, and substituting into the coefficient:

<Eq>

$$
c = \frac{k^{*} \cdot u}{u \cdot k^{*}} = 1
$$

</Eq>

The cancellation is independent of $u$, so it holds for any whitening covariance and at any layer, and independent of $t_1 \dots t_n$, so it holds whatever the probe goes on to ask.

The empirical content is entirely in the premise — that the probe really does share the prefix through $s_m$ — which is what E‑040 measured, on three models at four fractions of each one's depth. E‑017 and E‑018 measured it first; their outputs are gone, so they are in the record and the premise does not rest on them. The tokenizer is the one place the premise can fail quietly: a leading space or a different casing produces a different token sequence and therefore a different key, with no error raised anywhere.

## Appendix B. Provenance of every number

<Gist>Each number on this page traced to the run that produced it, including the five runs whose outputs were lost.</Gist>

Each row names the run a number came from, and links the files it wrote. Config files pin the seed and the layer; argv carries only the output path.

**Five rows have nothing to link**, struck through above. Those runs wrote a dated directory rather than a single file, none of those directories was committed, and they are no longer on any machine.

Four of the five no longer carry anything. The premise [E-017] and [E-018] measured was re-measured by [E-040], on three models at four depths each. The RippleEdits readings behind [E-038] and the alias readings behind [E-026] were recomputed from a cached key file that outlived both runs, by [E-041] and [E-042]. Those four rows are kept because deleting a run that happened is not provenance, but no number in this paper rests on them.

The fifth does not come back. [E-012] is a census of every recorded reading of the floor, and the committed logs carry that quantity to four decimals where the census worked at 1e-06, so what survives cannot hold the effect it counted. [E-039] recovered 32 readings the result files had overwritten and is linked above, but it is a smaller thing than the census and says so. Nothing in §4.1 is quoted from [E-012] alone — the partition table printed there is [E-006]'s — and the sentence it supported, that the values reproduce bit-for-bit across runs and across days, is narrowed in the paragraph after it to a deployment and a session.

**What each one cost to get back, since the estimate was wrong twice.** [E-007] was restored on 15 November by re-running its two checks and its row is no longer struck. [E-017] and [E-018] were expected to be small runs and were not re-run at all: [E-040] measured the same premise on more models at more depths, which is why its row carries twelve readings rather than sixteen. [E-038] was called *the expensive one at 23,505 readings* and turned out to cost **no forward passes**, because the script behind it persists every key it reads and that cache was committed; [E-026] came off the same cache. An earlier version of this paragraph also said [E-012] was recoverable from the logs, which was written from the logs *mentioning* the quantity rather than from checking its precision.

The pattern is worth stating because it will recur. **What a lost run costs to recover depends on what it cached, not on how large it was.** The 23,505-reading run was free and the 16-anchor one needed a model.

Saying this is not an excuse for the gap. It is the difference between a record that lost something and a record that has not yet spent the compute to restore it, and a reader is entitled to know which of the two they are looking at.

<Runs caption={<>The runs behind the figures and tables above. Directories are under <code>results/</code>.</>}>
  <Run id="E‑004" model="Llama‑3.1‑8B" n="1,539" date="6 Nov" out="E-004-far-field-floor.json">Near and far field under the same-relation stranger floor</Run>
  <Run id="E‑004" model="Llama‑3.1‑70B" n="1,539" date="15 Nov" out="E-004-far-field-floor-meta-llama_Llama-3.1-70B.json">The same measurement on 70B. Shape holds, every far-field magnitude about threefold smaller</Run>
  <Run id="E‑045" model="GPT‑J‑6B" n="1,539" date="15 Nov" out="E-004-far-field-floor-EleutherAI_gpt-j-6b.json">The same measurement on a second architecture. Sign holds; 52% above floor, against 79.7% and 72%</Run>
  <Run id="E‑046" model="3 models" n="639" date="15 Nov" out="E-046-near-field-floor.json">The near-field floor, which no run had recorded — computed offline from the keys E‑004 cached</Run>
  <Run id="E‑001" model="Llama‑3.1‑8B" n="495" date="31 Oct" out="E-001-predicted-vs-measured.json">Predicted reach against measured movement, with a same-subject control</Run>
  <Run id="E‑002" model="Llama‑3.1‑8B" n="495" date="31 Oct" out="E-002-different-subject-arm.json">The different-subject arm: identity against content</Run>
  <Run id="E‑003" model="Llama‑3.1‑8B" n="495" date="1 Nov" out="E-003-destination.json">The same probes under a full-vocabulary argmax readout</Run>
  <Run id="E‑007" model="Llama‑3.1‑8B" n="8" date="2 Nov" out="E-007-shape.json">Batch reshaping against raw key magnitude</Run>
  <Run id="E‑008" model="3 models" n="36" date="3 Nov" out="E-007-conformance-llama-3.1-8b.json E-007-conformance-llama-3.1-70b.json E-007-conformance-gpt-j-6b.json">The conformance suite across two architectures</Run>
  <Run id="E‑009" model="2 models" n="32" date="3 Nov" out="E-009-partition-8b.json E-009-partition-gptj.json">Whether the GPU partition reappears on another day</Run>
  <Run id="E‑010" model="2 models" n="90" date="3 Nov" out="E-010-layers-8b.json E-010-layers-gptj.json">Five layers on each of two models, six checks each</Run>
  <Run id="E‑012" model="Llama‑3.1‑8B" n="census" date="3 Nov" out="2026-11-03-census/">Every recorded reading of one quantity, by value and device. Outputs lost and not recoverable: the committed logs hold four decimals where this worked at 1e‑06. Nothing above is quoted from it alone</Run>
  <Run id="E‑011" model="3 models" n="15" date="4 Nov" out="E-011-layers-70b.json E-010-layers-8b.json E-010-layers-gptj.json">Arithmetic-site disagreement across fifteen layer-model pairs</Run>
  <Run id="E‑017" model="GPT‑J‑6B" n="16" date="21 Oct" out="2026-10-21-pin/">Prefix-sharing premise, first pass</Run>
  <Run id="E‑018" model="4 models" n="16" date="23 Oct" out="2026-10-23-pin4/">Premise at scale; different-subject floor 0.082. Outputs lost and no runner was committed, so it is in the record and nothing rests on it</Run>
  <Run id="E‑040" model="3 models" n="42" date="15 Nov" out="E-040-premise-four-models.json">Premise re-measured at layer 5. Llama‑3.1‑405B could not be deployed and is recorded as unread</Run>
  <Run id="E‑040" model="3 models × 4 depths" n="12×42" date="15 Nov" out="E-040-depth-sweep.json">The same premise and floor at matched fractions of each model's depth</Run>
  <Run id="E‑026" model="Llama‑3.1‑8B" n="370" date="28 Oct" out="2026-10-28-alias/">Renamed subject: string similarity against delivered fraction. Outputs lost; recomputed by E‑042 from the keys E‑037 persisted</Run>
  <Run id="E‑042" model="Llama‑3.1‑8B" n="371" date="15 Nov" out="E-042-renamed-subject.json">The same correlation recomputed offline, with its interval and a per-subset split</Run>
  <Run id="E‑038" model="Llama‑3.1‑8B" n="23,505" date="1 Nov" out="2026-11-01-ripple/">RippleEdits re-run, direct exposure counted. Outputs lost; recomputed by E‑041 from the keys it persisted</Run>
  <Run id="E‑041" model="Llama‑3.1‑8B" n="23,505" date="15 Nov" out="E-041-ripple-exposure.json">The same readings recomputed offline from the cached keys, with the floor re-paired under five seeds</Run>
  <Run id="E‑015" model="Llama‑3.1‑8B" n="1,539" date="9 Nov" out="E-015-bound-looseness.json">Looseness of the Cauchy–Schwarz bound, by regime — offline over cached keys</Run>
  <Run id="E‑039" model="Llama‑3.1‑8B" n="32" date="15 Nov" out="E-039-log-census.json">Readings the result files overwrote, recovered from the committed logs</Run>
  <Run id="E‑016" model="Llama‑3.1‑8B" n="41" date="9 Nov" out="E-016-subject-properties.json">Subject prominence and dependent count against per-subject damage</Run>
</Runs>

### B.1 The values themselves

<ValueTables />

## Appendix C. Readiness

<Gist>What would have to be true before this goes anywhere, and what is not true yet.</Gist>

What a short venue note needs, against what exists today. This is a checklist for the author, not a claim about the work.

<Readiness caption={<>Readiness against a short-paper submission.</>}>
  <Check met need="A result that could have come out the other way" where="§5">The floor was fixed before the run, and the question closed against the project</Check>
  <Check met need="One figure that carries the argument" where="§5">The near-and-far-field figure does the work §5 would otherwise do in prose</Check>
  <Check met need="Reproduction path" where="§4">Config, seed and resolved environment beside every result directory</Check>
  <Check met need="Positioning against the nearest work" where="§2">He et al. (2026) read in full and distinguished; and for §5.6, Weng et al. (2020) and Kim et al. (2021) read in their problem formulations and theory sections rather than their abstracts, which overturned one claim this paper had already written down</Check>
  <Check met need="Breadth across models" where="§5.2">Three models and two architectures on the far field, four depths each on the floor</Check>
  <Check need="Read by someone outside the project" where="§7.8">Every finding produced and reviewed by the same two parties</Check>
  <Check need="Breadth across depth" where="§8.1">The far field is read at one layer on every model. The depth sweep moves the floor, not the excess</Check>
  <Check need="A delivery-to-effect link" where="§7.1">Blocked on the backward pass, which returns an empty gradient on every model served today; 42 survivors, not a sample</Check>
</Readiness>

<PlainPanel>
  <PlainBody />
</PlainPanel>

<ThreadsPanel>
  <ThreadsBody />

<Revisions caption={<>Revisions. A number that moves appears here before it appears anywhere else.</>}>
  <Rev date="18 Nov 2026" version="v0.6">§4's sample transcript still printed the near-field floor as <b>0.0506</b>. That is the figure withdrawn on 15 November, and the correction reached the §5.2 table and the figure but not this listing. It now reads <b>0.0842</b>, which is what <code>E-046</code> holds for Llama-3.1-8B. No result moves; one illustrative line catches up with the row it illustrates.</Rev>
  <Rev date="18 Nov 2026" version="v0.6">The identity-to-content ratio was published as <b>×65</b> everywhere it appears. It is the ratio of two medians, and 65 is what those medians give <i>after</i> they are rounded to four decimals for printing — 0.0583 over 0.0009. Unrounded they are 0.058282 and 0.000930, whose ratio is <b>62.7</b>. Found while generating the figure for §5.3, which computes the ratio from the run file rather than from the printed table and so could not reproduce the published number. Now <b>×63</b> in the heading, the abstract, the contributions, F‑11 and §8. The two medians and both intervals are unchanged; only the ratio derived from them moves.</Rev>
  <Rev date="15 Nov 2026" version="v0.5">The near-field stranger was printed as <b>0.0506</b> and no run produced it; the number was in no result file, and was found missing while redrawing the figure that draws it. The matched floor the excess beside it actually uses is <b>0.0842</b>. The own figure and the excess were both right — 0.9334 and +0.8439 against a recomputed +0.8436 — so one cell was wrong rather than the row. Recovered offline from the keys E‑004 had cached all along, on all three models, and the figure is now generated from the run files rather than drawn by hand.</Rev>
  <Rev date="15 Nov 2026" version="v0.5">§5.2 ran on a second architecture. The sign holds on GPT-J-6B — the excess over the different-relation floor is positive and over the same-relation floor is zero, as on both Llamas — and nothing else does. Its own and floor readings are 0.1303 and 0.1280 with 52% of questions above the floor, against 79.7% and 72% on the Llamas, so the reading is consistent with the section and weak evidence for it: there was almost no dynamic range available to find missing. Two limitations added and the near-field figures marked as Llama numbers, 0.9334 and 0.9350 against 0.7985.</Rev>
  <Rev date="15 Nov 2026" version="v0.5">The renamed-subject row was recomputed from the same cached keys. Both statistics come back on their published values — ρ +0.7780 against +0.778, slope +0.8483 against +0.847 — over 371 alias readings against a published 370, and the one-reading difference is unexplained rather than resolved. The row gains the interval it never had, and a qualification the pooled figure was hiding: 85% of those readings come from RippleEdits' <code>random</code> subset, where ρ is +0.787, while on <code>popular</code> it is +0.259 over 20 readings.</Rev>
  <Rev date="15 Nov 2026" version="v0.5">§5.5's RippleEdits floor was printed as a single <b>0.065</b>. The readings behind it survived in a cached key file even though the run's own outputs did not, so it was recomputed: the <b>0.982</b> reproduces exactly and cannot move with the pairing, because it never touches a partner, while the floor runs 0.064 to 0.070 over five pairings and is 0.070 at the pinned seed. The published 0.065 is a value this measurement produces and not the one it produces at that seed, so the floor is now quoted as a range.</Rev>
  <Rev date="15 Nov 2026" version="v0.5">§3.2's different-subject floor was a single <b>0.082</b> with no model beside it, read as though it were common to the four models named in the same sentence. It is one reading, Llama-3.1-8B at layer 5. Re-measured on three models at four fractions of each one's depth, the same control spans 0.031 to 0.388 and is ordered by neither size nor depth. The premise itself was re-measured at the same time and held at exactly 1.000 on all twelve readings. The original run behind the 0.082 could not be re-run — its outputs are gone and its script was never committed — so this is a fresh measurement rather than a reproduction, and the runner is in the repository this time.</Rev>
  <Rev date="10 Nov 2026" version="v0.4">The abstract and the masthead caught up with the body, a day late: the abstract still said "two further results" when there were four, and the masthead still read v0.3 while this table had already turned v0.4. Recorded because a paper whose front matter disagrees with its own revision log is the same fault as a ticket whose status disagrees with its closure note.</Rev>
  <Rev date="9 Nov 2026" version="v0.4">§5.6 and §5.7 added. The upper bound §1 said an item set could never give turns out to exist in the algebra and to forbid nothing, and no property of the subject predicts the magnitude either. §2 gained the certification and Lipschitz positioning, and a claim that no behavioural bound exists through a transformer was withdrawn after the theory sections were read: a compact domain makes one exist, it is simply uncomputed.</Rev>
  <Rev date="9 Nov 2026" version="v0.3">Limitations gained the delivery-is-not-effect entry, which §5 had been leaning on without stating.</Rev>
  <Rev date="6 Nov 2026" version="v0.2">F‑07 denied. Every per-family tolerance in §4.1 was removed; the section now says a tolerance must be measured where it runs.</Rev>
  <Rev date="2 Nov 2026" version="v0.2">F‑09 superseded by F‑02 once the floor was found to be the different-relation floor under another name. §3.3 rewritten around the matched floor.</Rev>
  <Rev date="31 Oct 2026" version="v0.1">The project's own question closed on its negative branch. The paper's original claim — that the quantity gates a propagation evaluation — was withdrawn and the paper re-scoped to a negative result.</Rev>
</Revisions>
</ThreadsPanel>
