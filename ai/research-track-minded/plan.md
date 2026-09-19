# Project: research-track-minded

_Last updated: 2026-09-18 by O-001_

## Objective

A Claude skill that makes research writing land in Saif's register — claim-locked
prose, readable mathematics, and an output contract that ends in a decision
rather than a wall of text.

## Current Phase

Phase 1 — Corpus assembly

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
| R-003 | Researcher   | The deletion list                      | open        |

## Blocked

None.

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

## Next Orchestrator Action

R-003 (deletion list) is unblocked and has both inputs it needs. After it closes,
open the first E- ticket to assemble the skill itself.
