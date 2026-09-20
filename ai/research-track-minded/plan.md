# Project: research-track-minded

_Last updated: 2026-09-18 by O-001_

## Objective

A Claude skill that makes research writing land in Saif's register — claim-locked
prose, readable mathematics, and an output contract that ends in a decision
rather than a wall of text.

## Current Phase

Phase 3 — Skill built, used three times, fixed twice, cut once. Third use was the first by another session and the first to report defects back.

## Scope decision (2026-09-18)

Tuned to **Saif's voice**, not general-purpose. The corpus is the skill; the
wrapper around it is an afternoon. Three problems were deliberately split out of
this project:

| Problem | Where it goes |
| --- | --- |
| Flat prose | **here** (claim-lock + exemplars + deletion pass) |
| Unreadable mathematics | **here** (notation contract + words→symbols→instance ladder) |
| Knowledge not persisting across papers | `responsible-ai/knowledge-graph` — not a skill; a skill has no memory |
| Prior-art / scoop checking | deferred, T-004 — tooling gap in design lens 2, not a writing problem |

## Working hypothesis

Flat AI prose is a symptom of an unsharpened claim, not of weak writing ability.
Hedging is what uncertainty looks like once it is forced into sentences. If this
is right, a style pass that does not first force the claim into one falsifiable
sentence will produce better-looking mush. T-001 tests it.

## Active Tickets

| ID    | Agent        | Title                                  | Status      |
| ----- | ------------ | -------------------------------------- | ----------- |
| O-001 | Orchestrator | Initialize project, fix scope          | closed      |
| R-001 | Researcher   | Voice profile from Saif's own corpus   | closed      |
| R-002 | Researcher   | Exemplar corpus — mech interp papers   | closed      |
| R-003 | Researcher   | The deletion list                      | closed      |
| E-001 | Engineer     | Test Tier 2 against a real draft       | closed      |
| E-002 | Engineer     | Write the skill                        | closed      |
| E-003 | Engineer     | Use the skill on live work             | closed      |
| E-005 | Engineer     | Second live use — a design document    | closed      |
| E-004 | Engineer     | Fix the recurring defects              | closed      |

## Blocked

None. E-004 unblocked by E-005.

## Hypothesis revised after R-001

The claim-sharpness hypothesis was pointed at the wrong lever. R-001 found the
proximate cause of flat prose is **distributed** hedging: generic prose spreads a
thin film of qualification over every sentence, where the corpus quarantines all
of it into named sections ("Honest limits") and leaves the rest unhedged. Same
epistemic content, concentrated. That is mechanically checkable — count hedging
tokens outside the limits section — where "sharpen the claim" was not.

An unsharpened claim remains the reason a writer reaches for distributed hedging,
so claim-lock stays in the design. It is now the upstream fix, not the lever.

## Completed This Session

- O-001 · Initialize project structure, split scope four ways
- R-001 · Voice profile — `agents/shared/findings.md`
- R-002 · Mech interp exemplar corpus — `corpus/papers/`, findings.md
- R-003 · Deletion list + negative-space measurement — `corpus/deletion-list.md`
- E-001 · Tier 2 spike — CONFIRM; `agents/engineer/workspace/e001/`
- E-002 · Skill written and installed — `skill/research-writing/`
- E-003 · First live use — `agents/engineer/workspace/e003/`; five defects logged
- E-005 · Second live use, a design document — three defects recurred, one new
- E-004 · Defects 1–4 fixed, 5 decided, 6 held — `skill/research-writing/`

## Known gap — closed by R-002

R-001 found no paper-register or notation sample in Saif's own writing. ROME
supplies it. The finding that closed it: unreadable generated mathematics is a
**naming-and-ordering** problem, not a symbol problem — symbols arrive before the
objects they denote have been named in English (ROME), and new machinery gets
coined abstractions where borrowed concrete words would install the semantics for
free (Lookbacks: pointer, address, payload, dereference).

## Remaining gap

On hedging-quarantine — the project's central finding — the published exemplars
are *weaker* than Saif's own writing. ROME's limitations discussion is thinner
than `the-check-that-was-never-there`'s five-item "Honest limits". The skill takes
notation from the papers and epistemic discipline from Saif.

## What R-003 changed

The word list does not do the work. Measured: Saif's corpus 0.0 hits/10k, published
exemplars 9.6, AI-generated reports 14.7. A 1.5× separation between good papers and
slop is not a discriminator — a lint tuned to catch the reports flags ROME almost as
hard. Tier 1 is Saif's house standard (stricter than the literature) and a cheap
floor; **Tier 2's eight structural questions carry the project.**

Corpus assembly is now complete: voice profile, 19 exemplar passages, 20 deletion
entries. The risk from here is building the skill around a frame that has never
touched a draft.

## What E-001 established

The frame survived contact. Against a blind baseline — real AI-generated prose on
GradSim and ripple effects — the eight Tier 2 questions took falsifiable-as-written
claims from 1 to 8 while adding 18% length. The pre-stated null (longer, equally
unfalsifiable) did not fire, and the vocabulary control stayed flat.

The decisive result was incidental. **The baseline scores 0.0 Tier 1 hits per 10k
and is still useless** — it passes the whole word list. R-003 inferred that from a
corpus comparison; E-001 shows it on one passage.

Bounded: M6 stayed at zero. Tier 2 converts missing evidence into a stated gap. It
does not produce evidence, and the skill must say so.

## What E-003 established

The skill works, and its documented purpose is not its main benefit. Pass 1 caught
zero unfalsifiable claims — `edit-slice/decisions.md` is already written to that
standard — and instead **reordered the section**, putting the analytic result above
the empirical one. Left to instinct the section would have opened with a null and
buried the durable finding under it. The audit's ranking use is undocumented and is
plausibly what it is for.

`voice.md` was not opened once. Extending a document makes its register available
by imitation; the voice reference may only earn its place when drafting from
nothing.

## What E-005 established

Three of five defects recurred on a second document type and are safe to fix. The
ranking effect recurred identically: **on both uses the audit's documented filtering
job caught nothing, and its undocumented ranking job restructured the document.**
The skill documents the half that did nothing.

Defect 1 changed shape. On a design, Pass 1 is not mis-ordered — it is a category
error, because a design has no claims. The working substitution is *"if this
assumption is wrong, does the experiment still measure what it claims?"* So the fix
is three modes, not two.

And the pass produced a research finding rather than a writing improvement: every
control behind [E-017]'s published claim is same-subject, and the matched
different-subject control has never been run. That is now `edit-slice` T-076, and
it should run before the layer sweep it was designed inside.

## Next Orchestrator Action

Stop working on the skill. It has had two live uses and one round of fixes, and the
next informative thing is a **third use on generated rather than hand-written
input** — the one condition under which the filtering half of Pass 1 should finally
catch something. Everything else is speculation about a tool that already works.

The more urgent item is not in this project: `edit-slice` T-076 is a single
measurement bearing on a claim published on 2026-09-20.
