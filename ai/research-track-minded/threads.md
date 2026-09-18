# Threads — research-track-minded

### T-001 · Is flat prose a symptom of an unsharpened claim?

**Status:** answered
**Parent:** —
**Opened:** 2026-09-18
**Question:** The design assumes hedged, surveyed prose is what uncertainty looks
like when forced into sentences — so the fix is claim-locking, not style rules.
Cheap test: take one piece of writing that disappointed, sharpen only the claim,
re-generate, and see whether the prose improves without any style guidance. If it
doesn't, the skill's first move is wrong and the whole design shifts to exemplars
alone.
**Answer:** Partially, and the lever was wrong. R-001 (`agents/shared/findings.md`
§ "hedging is quarantined, not distributed") found the proximate cause is
distributed hedging, not claim-sharpness. The corpus concentrates all
qualification into named sections and leaves everything else unhedged. That is
mechanically checkable; "sharpen the claim" was not. Claim-lock survives as the
upstream cause, demoted from first move. Spawns T-007.

### T-007 · Can the hedging-quarantine rule be checked automatically?

**Status:** open
**Parent:** T-001
**Opened:** 2026-09-18
**Question:** If the rule is "hedging tokens outside the limits section ≈ 0", it
is a lint, not a prompt — and a lint the skill could run on its own draft. Is a
token list enough, or does it need to catch syntactic hedging ("tends to suggest
that") that no word list will? Cheapest version: run the count over the corpus
first and confirm the ratio is actually as lopsided as the qualitative read says.
**Answer:** —

### T-002 · What is the deletion list, concretely?

**Status:** open
**Parent:** T-001
**Opened:** 2026-09-18
**Question:** Which specific constructions get deleted on sight? The claim is that
a finite list of banned moves outperforms abstract instruction to "write clearly."
Needs to be derived from what the corpus *never* does, not from taste.
**Answer:** — (R-003)

### T-003 · Which exemplars, and why those?

**Status:** active
**Parent:** —
**Opened:** 2026-09-18
**Question:** Two halves. (a) Saif's own best writing — sampling now under R-001.
(b) 3–5 admired papers with marked passages — blocked on external input (R-002).
**Answer:** — (R-001 in progress)

### T-004 · Prior-art checking with actual teeth

**Status:** parked
**Parent:** —
**Opened:** 2026-09-18
**Question:** Design lens 2 (prior art & scoop risk) is protocol with no search
behind it. Does that belong in this skill, a separate one, or wired into the
existing design protocol? Parked because it is not a writing problem and would
bloat v1.
**Answer:** —

### T-005 · Does the writing skill ever read the claim KG?

**Status:** parked
**Parent:** T-004
**Opened:** 2026-09-18
**Question:** The cross-paper memory problem lives in
`responsible-ai/knowledge-graph`. Should the writing skill eventually read from
it, or stay deliberately independent? Deciding now would couple two projects
before either is proven.
**Answer:** —

### T-006 · Is X-not-Y a signature or a tic?

**Status:** open
**Parent:** T-003
**Opened:** 2026-09-18
**Question:** "A record rather than an argument." "falsified by measurement rather
than argument." "The stars are real; the constellations were ours." The
paired-contrast construction appears constantly in the corpus. It is doing real
work — it fixes a boundary by naming what a thing is *not*. But a skill that
encodes it will overuse it, and overused it reads as mannerism. Needs a frequency
budget, not a ban.
**Answer:** —
