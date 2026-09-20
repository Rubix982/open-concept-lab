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

**Status:** answered
**Parent:** T-001
**Opened:** 2026-09-18
**Question:** Which specific constructions get deleted on sight? The claim is that
a finite list of banned moves outperforms abstract instruction to "write clearly."
Needs to be derived from what the corpus *never* does, not from taste.
**Answer:** `corpus/deletion-list.md` — 20 entries, 12 lintable and 8 structural, each
with a banned construction, an example and a replacement. Derived by measurement: the
reference corpus scores 0.0 hits per 10k across fifteen probes. [R-003] also found the
list does **not** discriminate quality — published papers 9.6/10k against AI reports
14.7 — so Tier 1 is a house standard and Tier 2 carries the work. Shipped as
`skill/research-writing/`.

### T-003 · Which exemplars, and why those?

**Status:** answered
**Parent:** —
**Opened:** 2026-09-18
**Question:** Two halves. (a) Saif's own best writing — sampling now under R-001.
(b) 3–5 admired papers with marked passages — blocked on external input (R-002).
**Answer:** Both halves done. R-001 profiled Saif's own register; R-002 marked 19
passages across ROME, Lookbacks, Sparse Feature Circuits, and one AI-generated
report kept as a negative control. `corpus/papers/`.

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

**Status:** answered
**Parent:** T-003
**Opened:** 2026-09-18
**Question:** "A record rather than an argument." "falsified by measurement rather
than argument." "The stars are real; the constellations were ours." The
paired-contrast construction appears constantly in the corpus. It is doing real
work — it fixes a boundary by naming what a thing is *not*. But a skill that
encodes it will overuse it, and overused it reads as mannerism. Needs a frequency
budget, not a ban.
**Answer:** A signature, and the budget should be semantic rather than numeric.
ROME does the same thing ("strong causal states at a late site is unsurprising,
but their emergence at an early site is a new discovery") — the construction's job
in this literature is separating **expected from new**, which pre-empts the
reviewer who says "we already knew that." Rule: use it where the two halves are
genuinely expected-vs-new and it will not overfire; used for emphasis it becomes
mannerism. The ~1/200-words rate from R-001 is a symptom of the semantic rule, not
the rule itself.

### T-008 · Are the missing action items a symptom of a missing claim?

**Status:** open
**Parent:** T-001
**Opened:** 2026-09-19
**Question:** The anti-exemplar is accurate and useless, and its defining property
is that **nothing in it could turn out to be false**. That is plausibly the same
thing Saif experiences as "you gave me a lot of text and I don't know what to do
with it" — no action item because no position. If so, the output contract (#4 in
the original scope split) is not a formatting fix at all; it is downstream of
claim-lock, same as the hedging finding. Worth testing before building a separate
contract: does forcing a falsifiable claim produce the action items for free?
**Answer:** —

### T-009 · Does the naming rule generalise past borrowed vocabulary?

**Status:** open
**Parent:** T-003
**Opened:** 2026-09-19
**Question:** Lookbacks works because `pointer`/`address`/`payload` denote the
same structure in systems programming — the borrowing is *exact*, not merely
evocative. An inexact borrowing would be worse than a coined term, since it
imports wrong intuitions silently. So the rule needs a test for when a borrowing
is licensed. Related: CLAUDE.md's Premise Dry-Run rule 6 already warns about
structural resemblance as a false friend, which is the same hazard one level up.
**Answer:** —

### T-010 · Is there any cheap discriminator of research-worthiness?

**Status:** open
**Parent:** T-002
**Opened:** 2026-09-20
**Question:** R-003 measured the obvious candidate and it failed: word-level
probes separate Saif from everyone (0.0 vs 9.6 vs 14.7 per 10k) but barely
separate ICLR papers from AI-generated reports. So surface vocabulary does not
carry research quality. Is there a *measurable* proxy that does — density of
falsifiable claims, ratio of asserted-to-cited sentences, count of numbers
attached to an instrument, presence of a named negative result? Or is this
irreducibly a judgement call, in which case the skill should stop pretending
otherwise and say so. Worth one cheap pass before conceding.
**Answer:** Partially, and the answer is still no. E-002 added an
**unquantified-superlative** rule, derived from E-001's finding that nine of the
baseline's ten own-claims failed on *clearest / main / most / one of the few /
mostly*. On the single E-001 passage it looked decisive — 58.9 per 10k against
0.0 for hand-written prose. At corpus scale it is not: 0.0 hand-written, 1.6
published papers, 3.1 AI reports. A 2x separation, better than the 1.5x of the
original probes and still not a gate. The single-passage number was a hot spot,
not a rate. Surface features remain unable to separate good research writing from
competent filler; the claim audit is still the only thing that does. Thread stays
open for a non-surface proxy — density of falsifiable claims is the obvious
candidate and is exactly what E-001 hand-counted.

### T-011 · Dream-RSI — is "history is already a simulator" borrowable here?

**Status:** dropped
**Parent:** T-009
**Opened:** 2026-09-20
**Question:** Dream-RSI (Google/DeepMind/UMD/UVA, released 2026-09,
https://www.dream-rsi.com/, code at github.com/zhengkid/Dream-RSI) self-improves an
*exploration policy* by replaying completed discovery trees as zero-cost exact
simulators. Raised as possibly aligned with this project. Does the reframe transfer to
the ticket/thread record?
**Answer — dropped, and the reason is the T-009 test.** Not aligned with the writing
skill: they optimise a search policy against a measurable objective where execution is
the expensive thing (GPU kernels, Lasso paths, circle packing); the skill improves the
epistemic structure of prose. No scoop risk — different field entirely.

The tempting mapping is that `tickets.md` + `threads.md` + `decisions.md` already form a
discovery tree. It fails on the property their own page names as the limitation: *"a
policy can only be dreamt where history actually went."* Their replay is exact because
every node was executed with a recorded outcome. A research record has no outcome for the
branch not taken — [E-005] asked what would have happened had the different-subject
control run first, and that is simply unknown. Scale kills it too: off-policy evaluation
pays when thousands of alternatives can be tested, and there are ~20 tickets here.

So the borrowing is **evocative, not exact** — which by T-009's own rule makes it worse
than no borrowing, since it imports an intuition the record cannot cash. Dropped as
machinery. Kept as a move: "history is already a simulator" is Premise Dry-Run move 3
(invert the difficulty), turning a sunk cost into an asset, and that is worth stealing
independently of this paper.

Separately a **heading-check** datum, not a thread: agentic discovery with RSI is where
one large group is putting people. Read against the Compass, not chased.
