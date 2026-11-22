---
title: Mech interp in 2026
sidebar_label: The field in 2026
sidebar_position: 4
hide_table_of_contents: true
description: Where work on model internals can be submitted in 2027, soonest deadline first, and looking back, where it was judged in 2026, what each venue asked for, and which of those asks this notebook has nothing on.
---

<PageArt name="notebook" />

# Mech interp in 2026

**Where a result on model internals can be sent in 2027, and where such work was judged in 2026.**

## Where it can go in 2027

Conferences, journals, workshops and competitions, soonest deadline first, with the days left counted from today.

<Venues year={2027} view="timeline" />

<div className="ocl-wide ocl-pair">

<Notice>
  <strong>Read on 15 November 2026, when most 2027 calls were not out.</strong>
  Seven were read off the venue's own page or its own announcements: the
  ICLR blogpost track, ACL, ICML, SemEval, the MIB leaderboard and the two
  journals. Every other date was worked out from the last edition, shows only
  its month, and is marked <em>unchecked</em>. Each of those needs reading again
  once its call is published.
</Notice>

<details>
<summary>How to read these: archival, ARR, journals, ICML's new rule, and where competitions run</summary>

**Archival or not.** A non-archival workshop does not use up a result: the same paper can go to a conference afterwards. An archival venue publishes it, and conferences do not take work already published at another archival venue.

**ACL, NAACL, EACL and EMNLP all review through ARR.** A paper is reviewed once in an ARR cycle and then committed to one conference, so the cycle sets the date, not the conference. ARR had not published its 2027 cycles; ACL's own page gives 4 January 2027.

**Journals have no deadline.** TMLR takes submissions at any time, and its Journal-to-Conference certification can still put a paper in front of NeurIPS, ICML or ICLR. TACL closes on the 1st of each month, and its accepted papers can be presented at an ACL conference. A paper cannot be under review at TACL and ARR at the same time.

**ICML has a new reviewing rule.** Each ICML 2027 submission must name one author who is eligible to review and who will. An author who is not eligible can appear on only one submission in which nobody is.

**Where competitions run.** A competition on a fixed problem lives on a platform that holds the data and scores each entry, usually against a test set the entrants never see. Kaggle hosts the large prize competitions, such as the ARC Prize and the AIMO prizes. Codabench hosts most academic shared tasks, SemEval's among them. NeurIPS competitions each pick their own, and have used Kaggle, Codabench, EvalAI and AIcrowd. Standing research leaderboards, like MIB's, often sit in a Hugging Face Space. Red-teaming has platforms of its own, such as Gray Swan's Arena.

</details>

</div>

## Where it gets judged

Looking back at 2026: this field has **no competition culture to speak of** — one competition ran, against five workshops — and most of its venues are **non-archival**, so unfinished work is welcome and a submission does not spend the result.

<Venues view="lookback" />

<div className="ocl-wide ocl-pair">

<Notice>
  <strong>Every entry carries its own source, and unverified ones say so.</strong>
  A description read off a search result is not a verified fact even when the
  name is right; this project has made that mistake twice. One of the seven is
  unchecked, a funding programme that exists only on grant aggregators, and it
  must not be cited or planned around until somebody has opened the primary page.
</Notice>

NeurIPS 2026 runs across three sites, Sydney from 6 December and Atlanta and Paris from 9 December, so its two interpretability workshops and its competition are on three continents. Its [official workshop announcement](https://blog.neurips.cc/2026/08/10/announcing-the-neurips-2026-workshops/) calls the list preliminary and warns against informal lists, and this page is one of those.

</div>

## What these venues asked for that nothing here answers

Read against the work, five of the six venues name something this notebook has no evidence for.

<div className="ocl-wide ocl-gaps">

| Asked for | Asked by | Here |
| --- | --- | --- |
| **Features and circuits** | NEMI, first on its topic list | **Nothing.** The work measures what a weight edit reaches, which is a different object. The largest gap and the most expensive to close, and not the next thing. |
| **Reasoning that is robust, against reasoning that is spurious** | AIMO Interpretability Challenge, its whole task | **Nothing.** Nothing here touches reasoning. |
| **Interpretability for discovery**: finding something out about the world, not the model | Interpretability for Discovery, NeurIPS | **Nothing.** |
| **Reproducing someone else's result** | BlackboxNLP's reproducibility track | **Not yet, and the work is shaped for it.** It is built around controls, null distributions, digest-checked records and claims withdrawn in public. |
| **Probes** | NEMI, and two industry postings read on 10 November 2026 | **Partly, under another name.** edit-forensics ([built](/built)) finds a planted fact in a suspect checkpoint: the layer from a weight diff, the subject from how hard the update fires on its name, and with no base model, from outsized MLP writes. That is a monitor, and it has never been called one. |

</div>

## What this page is for

This is not a reading list. [Reading](/reading) is that, and it answers a different question — what I go back to, and for what. This page answers where a finished result goes to be read by people who can say it is wrong, which is a thing the reading list cannot tell me.

It does that in two directions. Looking forward, the 2027 list is fixed dates to pace work against, and each entry says what its venue asks for, so a result can be aimed at a deadline and checked against the ask before it is written up. Looking back, a heading-check: the 2026 venues say what the field thinks is worth judging, and reading my own work against that list is cheaper than discovering the mismatch at submission time.

The honest finding from the first pass is that **the heading is not wrong and the names are.** Two finished projects here answer things on this list under words nobody searching would use. That is a positioning problem, and positioning is a paragraph, not a project.
