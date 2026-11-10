---
title: Mech interp in 2026
sidebar_label: The field in 2026
sidebar_position: 4
description: Where work on model internals was judged in 2026, what each venue asked for, and which of those asks this notebook has nothing on.
---

<PageArt name="notebook" />

# Mech interp in 2026

**Where work on model internals was judged this year, what each venue asked for, and which of those asks nothing here answers.**

This is not a reading list. [Reading](/reading) is that, and it answers a different question — what I go back to, and for what. This page answers where a finished result goes to be read by people who can say it is wrong, which is a thing the reading list cannot tell me.

<Notice>
  <strong>Every row carries its own source, and unverified rows say so.</strong>
  A description read off a search result is not a verified fact even when the
  name is right — that is a mistake this project has made twice and corrected in
  writing. A row marked unverified must not be cited or planned around until
  somebody has opened the primary page.
</Notice>

## Where it gets judged

Two things worth keeping in view before the list: this field has **no competition culture to speak of** — one competition ran in 2026, against five workshops — and most of its venues are **non-archival**, which means unfinished work is welcome and a submission does not spend the result.

**[Mechanistic Interpretability Workshop](https://mechinterpworkshop.com/)** · ICML · 10 July, Seoul, COEX Hall C · non-archival

Work at any stage. Accepted ICML papers welcome, and papers under review at COLM or NeurIPS welcome; anything already accepted at another archival venue is not. Papers were due 8 May, and 23 of the accepted posters were spotlights.

**[BlackboxNLP](https://blackboxnlp.github.io/2026/)** · EMNLP · 9th edition, 29 October, Budapest · archival or not, author's choice

Analysing and interpreting neural networks for NLP. It runs a separate **Reproducibility Challenge** track for reproducing established interpretability results — 6 pages, double-blind.

**[NEMI](https://nemiconf.github.io/summer26/)** · 3rd edition, 14 August, Boston University · non-archival

Regional by design: academic and industry work from New England and nearby. Its own topic list names neural circuits, probe-based analysis, feature attribution, model simplification, actionable interpretability, and interpretability for science.

**[Interpretability as a Science](https://interpscience.github.io/)** · NeurIPS · 11 December, Sydney · non-archival

Rigorous foundations for understanding LLMs.

**[Interpretability for Discovery](https://interpretability4discovery.github.io/)** · NeurIPS · 12 December, Atlanta · non-archival

Using interpretability to uncover new scientific knowledge.

**[AIMO Interpretability Challenge](https://aimo-interp.github.io/)** · NeurIPS competition track · submissions closed 1 November, competition workshop 12 December, Paris · [arXiv 2607.13899](https://arxiv.org/abs/2607.13899)

Judge from a model's internals whether its correct answer to an olympiad problem survives perturbation, or rests on a spurious pattern. Ranked on how accurately each problem–model pair is classified as robust or spurious. $12,500 prize pool.

NeurIPS 2026 runs across three sites — Sydney from 6 December, with Atlanta and Paris from 9 December — so its two interpretability workshops and its interpretability competition are on three different continents. The [official workshop announcement](https://blog.neurips.cc/2026/08/10/announcing-the-neurips-2026-workshops/) calls its list preliminary and warns against the informal lists circulating elsewhere, which is worth repeating here: this page is one of those lists.

## Unverified, and recorded as such

**AI Forge — a DARPA/NSF joint program said to fund university work on interpretability, control and adversarial robustness, announced 1 June 2026.** Every description of this I could find is on a grant aggregator. No NSF or DARPA page confirms it, the aggregators disagree with each other on eligibility — one says universities only, another says academia, industry and government — and the figures quoted for a Project Venture ($750k–$3M, one-year terms) are unconfirmed. `TODO(cite)`.

It stays on the page because deleting it would lose the lead, and it stays marked because a funding programme is exactly the kind of claim that gets repeated into being true.

## What these venues asked for that nothing here answers

The list above is only useful read against the work, so: five of the six venues name something this notebook has no evidence for.

**Features and circuits.** NEMI's topic list opens with neural circuits and feature attribution. Nothing here decomposes a representation into features; the work measures what a weight edit reaches, which is a different object. This is the largest gap and the most expensive to close, and it is not the next thing.

**Reasoning that is robust against reasoning that is spurious.** The AIMO challenge's whole task. Nothing here touches reasoning at all.

**Interpretability for discovery** — using model internals to find something out about the world rather than about the model. Nothing.

**Reproducing someone else's interpretability result.** BlackboxNLP runs a track for exactly this, and it is the one gap on this list that the existing work is already shaped for: the discipline here is built around controls, null distributions, digest-checked records and claims withdrawn in public. That track rewards the thing this project has been practising on itself.

**Probes.** Named by NEMI, and named twice in industry postings read on 10 November 2026. Partly answered, under another name: edit-forensics (the report is on [built](/built)) detects a planted fact in a suspect checkpoint — the edited layer from a weight diff, the subject by scoring names on how hard the update fires, and, with no base model at all, the subject from outsized MLP writes. That is a monitor. It has never been called one.

## What this page is for

Not a calendar. A heading-check: the venues say what the field thinks is worth judging, and reading my own work against that list is cheaper than discovering the mismatch at submission time.

The honest finding from the first pass is that **the heading is not wrong and the names are.** Two finished projects here answer things on this list under words nobody searching would use. That is a positioning problem, and positioning is a paragraph, not a project.
