---
title: "A cheap pre-edit estimate of an edit's reach detects contamination, not propagation"
sidebar_label: Paper
sidebar_position: 2
hide_title: true
description: A quantity computable before the edit exists is exactly 1 where the prompt names the edited subject, and blind everywhere else — including where propagation lives.
toc_max_heading_level: 2
---

<PaperHead
  kind="Working paper"
  docId="OCL-2026-07"
  version="v0.3"
  title="A cheap pre-edit estimate of an edit's reach detects contamination, not propagation"
  author="Saif Ul Islam"
  affiliation={<>Open Concept Lab · Karachi</>}
  started="30 Sep 2026"
  updated="9 Nov 2026"
  buildsOn={<a href="/notebook/edit-slice/">edit-slice</a>}
/>

<Abstract keywords={["model editing", "ROME", "knowledge propagation", "benchmark contamination", "negative result"]}>

A rank-one weight edit, as ROME applies it <Cite id="meng2022rome" />, divides its update by a fixed inner product. The fraction of that update arriving at any token is therefore computable in one forward pass through the *unedited* model — before the edit exists, and for any prompt rather than for a list written in advance. This paper asks whether that quantity can screen an evaluation item before the item is run, and finds that it cannot, for a reason worth stating precisely.

The quantity is exactly 1 wherever the prompt opens with the edited subject. That is a derivation rather than a fit; its premise — prefix sharing under causal attention — holds on four models from 6B to 405B.<Prov id="E-018" /> It is blind where propagation lives: for questions that never name the edited subject, an edit on a *stranger* sharing the question's relation reaches the question as much as the real subject's edit does, excess **+0.0002** against **+0.8439** for the same control in the other regime.<Prov id="E-004" /> The quantity is a contamination detector — it reports that an item names the edited subject, not that an edit travelled. One published benchmark <Cite id="cohen2024ripple" /> has items that fail on exactly that ground, receiving a median 0.982 of an update they were built to test the propagation of.

This is reported as a negative result with a working control. §6 records what the control cost to get right, including one floor this project built, believed, and had to retire.

</Abstract>

<Contributions>

1. A reach coefficient read off the edit's own rank-one update, computable in one forward pass through the unedited model.
2. A derivation that it is exactly 1 on any prefix-sharing prompt, with its premise measured on four models from 6B to 405B.
3. Evidence that it does not detect propagation: a same-relation stranger control separates the near field by +0.8439 and the far field by +0.0002.
4. The measure repurposed as a contamination screen, with one published benchmark scored on it, released as `editreach`.

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

### 3.1 The coefficient

<Figure
  src="/img/edit-reach/two-regimes.svg"
  alt="Three prompts drawn as strips. The edit prompt opens with Maurice de Vlaminck. A probe opening with the same name shares every token the subject's last token can see under causal attention, so its key is identical and the coefficient is exactly 1.000. A probe opening with a different person reads 0.082."
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

A coefficient of 1.000 means nothing on its own, because a pipeline hardwired to return 1 looks identical. Every reading is therefore paired with a floor: the same prompt scored against a *different* subject's edit. The floor has to match the real edit on everything except the subject — the relation included. Getting that wrong is not hypothetical. It is what this project did first, and §6 records it as F‑09.

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

Half the tickets in this project are not about editing at all. They ask whether a number read off a remote model is the same number tomorrow, because a result that cannot be read twice is not a result.

<Lead>Structure holds exactly.</Lead> A ratio whose two terms are read inside one trace came back at **0.000e+00** on every one of fifteen layer-model pairs, across three models, two architectures and depths 0 to 79.<Prov id="E-011" />

<Lead>No magnitude holds.</Lead> The same disagreement between two arithmetic sites reads 5.3e‑06 on Llama-3.1-8B and 7.5e‑09 on GPT-J, which NDIF serves in float32 rather than bfloat16. The 8B and the 70B are one model family and disagree by an order of magnitude, while GPT-J differs because of how it is *served*. So the grouping variable is the deployment — dtype, sharding, tensor shape — not the family, and any tolerance written into code is wrong on some other deployment. It has to be measured where it runs. The full reference, with the conformance suite that found four errors in it, is [in the repository](https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/docs/ndif-reproducibility.md).

## 5. Results

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

### 5.1 What this says about a published benchmark

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
  <svg viewBox="0 0 400 150" role="img" aria-label="Timeline of finding F-08. Proposed 12 October. First floor built 24 October. Denied as C-001 on 31 October. Replaced by F-02 on 2 November.">
    <text x="4" y="12" fontFamily="Lato, sans-serif" fontSize="8" fontWeight="900" letterSpacing="0.8" fill="var(--ocl-ink)">F‑08 · LIFE OF A CLAIM</text>
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
      <text x="70" y="93" fill="var(--ocl-oxide)" fontWeight="700">C‑001 denied · 495 probes</text>
      <text x="70" y="122">replaced by F‑02 (same-relation floor)</text>
    </g>
    <text x="70" y="104" fontFamily="Lato, sans-serif" fontSize="7.4" fill="var(--ocl-ink-faint)">at fixed c, movement still spans ×2.96</text>
    <text x="70" y="133" fontFamily="Lato, sans-serif" fontSize="7.4" fill="var(--ocl-ink-faint)">the old floor was the different-relation floor</text>
  </svg>
</Figure>

A paper states what its author believes now. A page revised in place has to state what they believed before and why it changed, otherwise a reader who meets the old claim elsewhere has no way to know it was retired. The ledger below is every claim this paper has made, with the observation that would refute it. Struck rows are claims this project withdrew.

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
  <Finding id="F‑07" status="denied" value="5.3e‑06"
    falsifier={<><strong>Denied 4 November.</strong> The 8B and 70B are one family and disagree by an order of magnitude; GPT-J differs because it is served in float32. The grouping variable is the deployment.</>}>
    The magnitude of that disagreement is a property of the model family, so a tolerance can be written once per family.
  </Finding>
  <Finding id="F‑08" status="withdrawn" value="denied"
    falsifier={<><strong>Withdrawn 31 October (C‑001).</strong> 495 probes, 42 subjects. At a fixed coefficient, measured movement still spans a factor of 2.96.</>}>
    Predicted reach predicts how far the answer moves, so the quantity can gate a propagation evaluation before it runs.
  </Finding>
  <Finding id="F‑09" status="superseded" value="+0.0232"
    falsifier={<><strong>Superseded 2 November.</strong> Nearly all donors carried a different relation, so that floor was the different-relation floor under another name. F‑02 replaces it.</>}>
    There is real far-field signal: scored against all donors, the subject's own edit reaches its hop-2 question more than a stranger's does.
  </Finding>
</Ledger>

<Revisions caption={<>Revisions. A number that moves appears here before it appears anywhere else.</>}>
  <Rev date="9 Nov 2026" version="v0.3">Limitations gained the delivery-is-not-effect entry, which §5 had been leaning on without stating.</Rev>
  <Rev date="6 Nov 2026" version="v0.2">F‑07 denied. Every per-family tolerance in §4.1 was removed; the section now says a tolerance must be measured where it runs.</Rev>
  <Rev date="2 Nov 2026" version="v0.2">F‑09 superseded by F‑02 once the floor was found to be the different-relation floor under another name. §3.3 rewritten around the matched floor.</Rev>
  <Rev date="31 Oct 2026" version="v0.1">C‑001 closed denied. The paper's original claim — that the quantity gates a propagation evaluation — was withdrawn and the paper re-scoped to a negative result.</Rev>
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

A quantity computable before an edit exists tells you, reliably, whether a prompt names the edited subject. It tells you nothing about whether an edit travelled. The two statements are not in tension: the first is why the measure looked promising, the second is why it cannot do the job it was built for. What survives is the first one — a cheap screen that reads an evaluation item and says whether that item can test propagation at all, which one published benchmark fails.

Four questions stay open. Each is written so it could come back either way, and each names what would change if it did.

1. <Lead>Does a layer sweep find far-field dynamic range at some depth other than 5?</Lead> If yes, the screen is alive again at that depth and the scope sentence narrows to layer 5. If no, the negative result generalises across depth. This is the cheapest open item: one run on the cached subjects.
2. <Lead>Does a graded relation-similarity control move the +0.0002?</Lead> If the excess moves with relation distance, the categorical same/different split is too coarse and the far field has structure this one missed.
3. <Lead>Is subject-keyed movement the phenomenon rather than the confound?</Lead> Raised in passing by E‑001 and deliberately not taken up, because working on it now would be a rescue of F‑08 rather than a question.
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
  <Run id="E‑011" model="3 models" n="15" date="4 Nov" out="2026‑11‑04‑ndif/">Arithmetic-site disagreement across fifteen layer-model pairs</Run>
  <Run id="E‑017" model="GPT‑J‑6B" n="16" date="21 Oct" out="2026‑10‑21‑pin/">Prefix-sharing premise, first pass</Run>
  <Run id="E‑018" model="4 models" n="16" date="23 Oct" out="2026‑10‑23‑pin4/">Premise at scale; different-subject floor 0.082</Run>
  <Run id="E‑026" model="Llama‑3.1‑8B" n="370" date="28 Oct" out="2026‑10‑28‑alias/">Renamed subject: string similarity against delivered fraction</Run>
  <Run id="E‑038" model="Llama‑3.1‑8B" n="23,505" date="1 Nov" out="2026‑11‑01‑ripple/">RippleEdits re-run, direct exposure counted</Run>
</Runs>

## Appendix C. Readiness

What a short venue note needs, against what exists today. This is a checklist for the author, not a claim about the work.

<Readiness caption={<>Readiness against a short-paper submission.</>}>
  <Check met need="A result that could have come out the other way" where="§5">Pre-registered floor; C‑001 closed denied and recorded</Check>
  <Check met need="One figure that carries the argument" where="§5">The near-and-far-field figure does the work §5 would otherwise do in prose</Check>
  <Check met need="Reproduction path" where="§4">Config, seed and resolved environment beside every result directory</Check>
  <Check met need="Positioning against the nearest work" where="§2">He et al. (2026) read in full and distinguished</Check>
  <Check need="Read by someone outside the project" where="§7.5">Every finding produced and reviewed by the same two parties</Check>
  <Check need="Breadth across depth" where="§8.1">One layer. A sweep on the cached subjects is the cheapest fix</Check>
  <Check need="A delivery-to-effect link" where="§7.1">Blocked on the backward pass; 42 survivors, not a sample</Check>
</Readiness>
