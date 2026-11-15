---
title: Mech interp in 2026
sidebar_label: The field in 2026
sidebar_position: 4
description: Where work on model internals was judged in 2026, what each venue asked for, which of those asks this notebook has nothing on, and where work can be submitted in 2027.
---

<PageArt name="notebook" />

# Mech interp in 2026

**Where work on model internals was judged this year, what each venue asked for, which of those asks nothing here answers, and where a result can be sent in 2027.**

This is not a reading list. [Reading](/reading) is that, and it answers a different question — what I go back to, and for what. This page answers where a finished result goes to be read by people who can say it is wrong, which is a thing the reading list cannot tell me.

<Notice>
  <strong>Every card carries its own source, and unverified cards say so.</strong>
  A description read off a search result is not a verified fact even when the
  name is right — that is a mistake this project has made twice and corrected in
  writing. A card marked <em>unchecked</em> must not be cited or planned around
  until somebody has opened the primary page. One of the seven is unchecked: a
  funding programme that exists only on grant aggregators.
</Notice>

## Where it gets judged

Two things worth keeping in view before the cards: this field has **no competition culture to speak of** — one competition ran in 2026, against five workshops — and most of its venues are **non-archival**, which means unfinished work is welcome and a submission does not spend the result.

<Venues />

NeurIPS 2026 runs across three sites — Sydney from 6 December, with Atlanta and Paris from 9 December — so its two interpretability workshops and its interpretability competition are on three different continents. The [official workshop announcement](https://blog.neurips.cc/2026/08/10/announcing-the-neurips-2026-workshops/) calls its list preliminary and warns against the informal lists circulating elsewhere, which is worth repeating here: this page is one of those lists.

## What these venues asked for that nothing here answers

The cards above are only useful read against the work, so: five of the six venues name something this notebook has no evidence for.

**Features and circuits.** NEMI's topic list opens with neural circuits and feature attribution. Nothing here decomposes a representation into features; the work measures what a weight edit reaches, which is a different object. This is the largest gap and the most expensive to close, and it is not the next thing.

**Reasoning that is robust against reasoning that is spurious.** The AIMO challenge's whole task. Nothing here touches reasoning at all.

**Interpretability for discovery** — using model internals to find something out about the world rather than about the model. Nothing.

**Reproducing someone else's interpretability result.** BlackboxNLP runs a track for exactly this, and it is the one gap on this list that the existing work is already shaped for: the discipline here is built around controls, null distributions, digest-checked records and claims withdrawn in public. That track rewards the thing this project has been practising on itself.

**Probes.** Named by NEMI, and named twice in industry postings read on 10 November 2026. Partly answered, under another name: edit-forensics (the report is on [built](/built)) detects a planted fact in a suspect checkpoint — the edited layer from a weight diff, the subject by scoring names on how hard the update fires, and, with no base model at all, the subject from outsized MLP writes. That is a monitor. It has never been called one.

## Where it can go in 2027

The cards above are workshops, one competition and a funding lead. A result that is meant to be cited also needs the main conferences and the journals, so the 2027 list has those too, in the order their deadlines arrive.

<Notice>
  <strong>Read on 15 November 2026, when most 2027 calls were not out.</strong>
  Five cards were read off the venue's own page: the ICLR blogpost track, ACL,
  ICML, and the two journals. Every other date was worked out from the last
  edition and says <em>estimated</em>. Those cards are marked unchecked, and
  each one needs reading again once its call is published.
</Notice>

<Venues year={2027} />

**Archival or not.** A non-archival workshop does not use up a result: the same paper can go to a conference afterwards. An archival venue publishes it, and conferences do not take work already published at another archival venue.

**ACL, NAACL, EACL and EMNLP all review through ARR.** A paper is reviewed once in an ARR cycle and then committed to one conference, so the cycle sets the date, not the conference. ARR had not published its 2027 cycles; ACL's own page gives 4 January 2027.

**Journals have no deadline.** TMLR takes submissions at any time, and its Journal-to-Conference certification can still put a paper in front of NeurIPS, ICML or ICLR. TACL closes on the 1st of each month, and its accepted papers can be presented at an ACL conference. A paper cannot be under review at TACL and ARR at the same time.

**ICML has a new reviewing rule.** Each ICML 2027 submission must name one author who is eligible to review and who will. An author who is not eligible can appear on only one submission in which nobody is.

## What this page is for

Two things. Looking back, a heading-check: the venues say what the field thinks is worth judging, and reading my own work against that list is cheaper than discovering the mismatch at submission time. Looking forward, the 2027 cards are fixed dates to pace work against, and each one says what its venue asks for, so a result can be aimed at a deadline and checked against the ask before it is written up.

The honest finding from the first pass is that **the heading is not wrong and the names are.** Two finished projects here answer things on this list under words nobody searching would use. That is a positioning problem, and positioning is a paragraph, not a project.
