---
title: edit-reach
sidebar_label: Overview
sidebar_position: 1
description: Testing whether an edit's reach can be predicted before the edit is applied. It cannot — and what the measure does detect, and what the project found while looking, is worth saying precisely.
---

# edit-reach

[edit-slice](/notebook/edit-slice/) found that a ROME edit reaches everything sharing its subject by arithmetic rather than by inference. This project asked whether that finding could be turned into a tool: a number, computed in one forward pass through the **unedited** model, that says in advance how far an edit will travel.

The two are kept apart on purpose. edit-slice accumulates findings. This one was to produce a working screen or show that it cannot.

It showed that it cannot. [The paper](./paper) is where the line falls; this page is the state of the work around it.

<Claim
  label="What the instrument is"
  superseded="The coefficient screens whether a benchmark item can test propagation, so it can be used as a pre-run gate on propagation evaluations."
  record={{
    "What replaced it": "It detects contamination — that a prompt names the edited subject, and which relation it asks about. It does not detect propagation.",
    "Why the first version failed": "C-001 (the coefficient does not predict measured movement) and E-004 (in the far field, a stranger's edit on the same relation reaches a question as much as the real subject's edit does).",
    Confidence: "High on the near field, which is analytic. The far-field result is one model, one layer, two-hop chains.",
  }}
>
  A contamination detector, not a propagation detector.
</Claim>

<Glance>
  <Stat value="6" label="cards closed" note="none open" />
  <Stat value="15" label="decisions" note="in the shared record" />
  <Stat value="14" label="runs" note="all with config and seed" />
  <Stat value="42" label="subjects" note="cached survivors, not a sample" />
  <Stat value="4" label="models" note="6B to 405B, via NDIF" />
  <Stat value="1,900" label="lines" note="editreach 0.1.0, ten modules" />
</Glance>

## How the question moved

The project set out to build a screen and did not build one. What it has instead came from the answers: each denial named the thing that made the next question worth asking. That chain is the honest account of the work, and it is not visible in the paper, which is ordered by argument rather than by what happened.

<Figure
  wide
  plain
  caption={<>Four questions, each raised by the answer before it. The first was the project's own, and it came back negative; the three that follow were not planned and are where the positive results are.</>}
>
  <svg viewBox="0 0 900 300" role="img" aria-label="Four questions in a chain. Can predicted reach predict an edit's effect? Denied. Which raised: then what does the coefficient detect? Contamination, that a prompt names the edited subject. Which raised: why is there so little effect to predict? Because identity is worth about sixty-five times content. Which raised: then what does one update actually do? It breaks the old answer by identity and supplies the new one by content.">
    <g fontFamily="Lato, sans-serif" fontSize="10.5" fontWeight="900" letterSpacing="0.9" fill="var(--ocl-ink-faint)">
      <text x="14" y="22">THE PROJECT'S OWN QUESTION</text>
      <text x="14" y="112">WHAT THE DENIAL RAISED</text>
    </g>

    <rect x="14" y="32" width="268" height="54" fill="none" stroke="var(--ocl-oxide)" strokeWidth="1.5" />
    <text x="28" y="54" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">Does predicted reach predict</text>
    <text x="28" y="72" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">an edit's measured effect?</text>
    <text x="296" y="64" fontFamily="IBM Plex Mono, monospace" fontSize="13" fontWeight="600" fill="var(--ocl-oxide)">denied</text>
    <text x="296" y="80" fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-faint)">C‑001 · 31 Oct</text>

    <path d="M148 86 V122" stroke="var(--ocl-rule-strong)" strokeWidth="1.5" fill="none" />
    <path d="M143 114 l5 8 l5 -8" stroke="var(--ocl-rule-strong)" strokeWidth="1.5" fill="none" />

    <rect x="14" y="124" width="268" height="54" fill="none" stroke="var(--ocl-rule-strong)" strokeWidth="1" />
    <text x="28" y="146" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">Then what does it detect?</text>
    <text x="28" y="164" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-ink-muted)">Contamination — that a prompt</text>
    <text x="28" y="180" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-ink-muted)">names the edited subject.</text>
    <text x="296" y="150" fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-faint)">C‑004 · 1 Nov</text>

    <path d="M296 150 H330" stroke="var(--ocl-rule)" strokeWidth="1" strokeDasharray="2 4" fill="none" />

    <rect x="346" y="124" width="268" height="54" fill="none" stroke="var(--ocl-rule-strong)" strokeWidth="1" />
    <text x="360" y="146" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">Why so little effect to predict?</text>
    <text x="360" y="164" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-ink-muted)">Identity is worth about sixty-five</text>
    <text x="360" y="180" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-ink-muted)">times content.</text>
    <text x="628" y="150" fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-faint)">C‑002 · 31 Oct</text>

    <path d="M628 150 H662" stroke="var(--ocl-rule)" strokeWidth="1" strokeDasharray="2 4" fill="none" />

    <rect x="678" y="124" width="208" height="54" fill="none" stroke="var(--ocl-link)" strokeWidth="1.5" />
    <text x="692" y="146" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">So what does one</text>
    <text x="692" y="164" fontFamily="Lato, sans-serif" fontSize="12.5" fill="var(--ocl-ink)">update actually do?</text>
    <text x="692" y="192" fontFamily="Lato, sans-serif" fontSize="11.5" fill="var(--ocl-link)">Two things, separably.</text>
    <text x="692" y="208" fontFamily="Lato, sans-serif" fontSize="10" fill="var(--ocl-ink-faint)">C‑003 · 1 Nov</text>

    <path d="M14 240 H886" stroke="var(--ocl-rule)" strokeWidth="1" fill="none" />
    <text x="14" y="262" fontFamily="Lato, sans-serif" fontSize="11" fill="var(--ocl-ink-muted)">The screen the project set out to build does not exist. The three boxes after the first were not planned, and they are where the results are.</text>
    <text x="14" y="282" fontFamily="Lato, sans-serif" fontSize="10.5" fill="var(--ocl-ink-faint)">A fifth and sixth card — is the loader the same instrument, and do readings partition by serving GPU — were about whether any of it could be read twice.</text>
  </svg>
</Figure>

## The cards

Every question was written with both branches before the run, so a denial costs a card and not a month.

<Cards caption={<>The six cards this project opened. None is open now.</>}>
  <Card id="C‑001" outcome="denied" date="31 Oct" denied>Does predicted reach predict measured movement? <i>If yes, a pre-run screen; if no, the quantity measures delivery and the screen is a proposal.</i></Card>
  <Card id="C‑002" outcome="identity" date="31 Oct">Does an edit's effect depend on what it said, or only on whose key it touched? <i>Branch 1: identity dominates, and the coefficient has little to predict.</i></Card>
  <Card id="C‑003" outcome="two routes" date="1 Nov">Does an edit break the old answer and supply the new one by two different routes? <i>Measured on one probe set rather than read across three experiments.</i></Card>
  <Card id="C‑004" outcome="at floor" date="1 Nov">Is the hop-2 coefficient at floor, when the floor is read on the hop-2 prompts themselves? <i>The relation-matched floor is the whole question.</i></Card>
  <Card id="C‑005" outcome="same" date="1 Nov">Is <code>TransformersModel</code> the same instrument as the deprecated <code>LanguageModel</code>? <i>If not, every number so far is a re-baseline rather than an upgrade.</i></Card>
  <Card id="C‑006" outcome="routing" date="1 Nov">Do the two observed values partition by the GPU that served the request? <i>If yes, the tolerance is a property of the deployment, not of the instrument.</i></Card>
</Cards>

## What is still open

The thread ledger carries questions that are not yet work. Four are open; four were answered by the cards above and are kept so the tree stays navigable.

<Threads>
  <Thread id="T‑001" status="open">Can any screen bound an edit's damage from <i>above</i>, or only from below? A benchmark finds what it contains. A per-prompt quantity removes the enumeration problem but is still evaluated on prompts we happen to hold. If an upper bound is structurally unavailable, that should be stated once and loudly rather than implied away.</Thread>
  <Thread id="T‑002" status="open">Is subject-string frequency the operative variable rather than dependent count? Check KnowledgeSmith first — it already tested the out-degree hypothesis, and this is only interesting where it departs from that.</Thread>
  <Thread id="T‑003" status="open">Do "modify internal mechanisms" and "extract latent knowledge" bottom out in the same requirement — a way to tell what the model holds that is independent of what the asker put in? Is that one instrument or two, and does this screen serve both or only the first?</Thread>
  <Thread id="T‑009" status="narrowed">The serving GPU accounts for 1.4% of the observed spread. The rest was shown not to be drift but four exact values across two days, and what separates 31 October from 1 November is still unattributed.</Thread>
  <Thread id="T‑005" status="answered">Is the coefficient blind in exactly the regime propagation lives in? Yes — §5.2.</Thread>
  <Thread id="T‑007" status="answered">Does an edit break the old answer and supply the new one by two routes? Yes, and on one probe set — §5.4.</Thread>
  <Thread id="T‑008" status="answered">Readings differ between NDIF serving sessions on byte-identical inputs. It is routing, and it is exact — §4.1.</Thread>
  <Thread id="T‑006" status="answered">Is the deprecated loader the same instrument as its replacement? Yes; the switch is available and deliberately not taken.</Thread>
</Threads>

## What is here

| | |
| --- | --- |
| [The paper](./paper) | Eight sections and three appendices: the method, the control, five results, the findings ledger with every claim this project withdrew, and the provenance of every number. |
| [`editreach` 0.1.0](https://github.com/Rubix982/open-concept-lab/tree/main/ai/edit-reach) | Ten modules, about 1,900 lines. The coefficient is an object rather than an expression, and a reading without a control does not type-check. |
| [NDIF reproducibility reference](https://github.com/Rubix982/open-concept-lab/blob/main/ai/edit-reach/docs/ndif-reproducibility.md) | What reproduces off a shared inference fabric and what does not, with the conformance suite that found four errors in it. |
| [The record](https://github.com/Rubix982/open-concept-lab/tree/main/ai/edit-reach/agents) | Fifteen decisions, fourteen engineer tickets, the card ledger and the thread tree. Every number on the paper traces to a run here. |

## Where it stands

The question has an answer and the answer is negative, which closes the project's own card and leaves three results it was not looking for. What it does not have is a reader: every finding was produced and reviewed by the same two parties, which is the first item on the paper's readiness list and the one that cannot be fixed from inside.

The cheapest thing that would change the scope sentence is a layer sweep on the cached subjects — if far-field dynamic range exists at some depth other than 5, the screen is alive there and the negative result narrows to layer 5. The most valuable is lifting the backward-pass block, which would let the delivery-to-effect link be tested on a free draw instead of 42 survivors.
