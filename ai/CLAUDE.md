# Research projects

Applies to every project under `ai/`. Each project's own `CLAUDE.md` governs its
question, its scope and its vocabulary; this file governs what happens when any of
them is written up.

## Writing a project up

A project reaches this point when its results are going onto a notebook page, a blog
post, a paper, a portfolio entry or a submission — anywhere a reader outside the
project will meet them.

Two passes run then, in order, and neither is optional.

1. **`/research-writing`** — the claim audit. Every assertion falsifiable as written,
   hedging quarantined into a limits section, analytic claims shipping their
   derivation.
2. **`/research-legibility`** — the vocabulary census. Every term, identifier and
   internal noun counted at its first use and checked against its first definition.

The order matters: there is no point making an unfalsifiable claim legible.

Source for both: [`research-craft`](https://github.com/Rubix982/research-craft), a
submodule at `projects/research-craft`. The two skills are installed by symlink from
`~/.claude/skills/` into `projects/research-craft/skill/`, so a change made while working
in this repo is a change to the skill itself — commit and push it there, not here. This
repo only records which commit of it is in use.

## What the second pass exists to catch

Measured on two pages of `edit-reach`, 9 November 2026. The word-level lint scored
**0.0 hits per 10k before and after** revision, and the claim audit found **zero**
unfalsifiable claims. The same two pages carried **forty-odd internal identifiers in
running prose**, **six terms of art holding up two tables and a chart with no
definition anywhere**, and a central term whose first appearance was a section
heading.

So a clean lint and a clean audit say nothing about whether a reader can follow the
page. That is why the second pass is named separately rather than folded into the
first, and why it is listed here rather than left to be remembered.

## Three rules that outlive any single project

**Name every object in English, by what it does, before it takes a symbol or a term.**
A section that opens on its notation has already lost the reader it was written for.

**Identifiers are bookkeeping and leave the prose.** `C-001`, `E-004`, `T-009` tell a
reader nothing. In a sentence, state the thing itself. As a pointer beside a number
they stay, with one sentence somewhere saying what they point at.

**Process vocabulary never enters the argument.** *Card*, *thread*, *ledger*, *run* —
these describe how the work is organised, not what it found. They belong on the page
that describes the state of the work, defined there, followed by a line telling the
reader they can be ignored. If that line cannot be written truthfully, the argument is
still leaning on them.
