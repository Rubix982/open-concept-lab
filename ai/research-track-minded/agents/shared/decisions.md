# Decisions — research-track-minded

Owned by: **Engineer**. Append-only.

---

## [E-001] Decision: Tier 2 is the skill; Tier 1 is a lint that ships beside it

_Date: 2026-09-20_

**Decision:** Build the skill around the eight Tier 2 structural questions, with
the falsifiability question ("what in this paragraph could turn out to be false?")
as the primary pass. Tier 1 ships as a separate mechanical check, not as guidance.

**Rationale:** E-001 measured a revision of a blind baseline against six
pre-registered metrics. Falsifiable-as-written claims went 1 → 8 while length grew
18%, so the gain is not volume. The pre-stated null (longer, equally unfalsifiable)
did not fire.

The decisive evidence is incidental: **the baseline passage scores 0.0 Tier 1 hits
per 10k and is still useless.** No "delve", no "Furthermore", no hedge adverbs. It
passes the entire word list. R-003 inferred this from a 9.6-vs-14.7 corpus
comparison; E-001 shows it on one passage, which is much harder to argue with.

**Alternatives rejected:** Shipping Tier 1 as the skill's main content — refuted
above. Generating a fresh baseline myself — rejected at design time as
uncontrolled, since I know the hypothesis; a real AI-generated passage is blind by
construction.

**Revisit if:** the questions are run on a draft with a rich evidential base and
fail to improve it, which would suggest they only help thin sources.

---

## [E-001] Decision: the skill will not claim to improve evidence

_Date: 2026-09-20_

**Decision:** State as a bounded limitation, in the skill itself, that the Tier 2
pass improves the epistemic *structure* of a draft and cannot improve its
*evidential base*.

**Rationale:** M6 (numbers attached to an instrument) was 0 in the baseline and 0
after treatment. The source supplies no effect sizes and the treatment was
forbidden to invent any. What Tier 2 produced instead was an explicit statement
that the numbers are absent, plus a limits entry naming how the argument would
change if they arrived.

That is the correct behaviour, and it is worth declaring rather than discovering.
A draft written over thin sources will come out honestly thin — which is an
improvement over coming out confidently thin, but it is not the same as being
well-evidenced.

**Revisit if:** a version of the pass that is allowed to *go and fetch* evidence
is built. That is T-004 territory and is still parked.

---

## [E-002] Decision: the skill is three passes, and the lint is last and labelled

_Date: 2026-09-20_

**Decision:** `skill/research-writing/`, installed by symlink at
`~/.claude/skills/research-writing` so it is available in every project while
staying version-controlled here. Structure: `SKILL.md` (111 lines, operational),
four `references/` files, one `scripts/lint.py`.

Pass 1 is the claim audit — a table with one row per paragraph: the claim, own or
attributed, and what observation would falsify it. Pass 2 is the seven structural
questions. Pass 3 is the lint, explicitly labelled a floor.

**Rationale:** the first thing this project established is that another layer of
abstract instruction changes nothing. So `SKILL.md` leads with a **measured**
claim ("a passage scored 0.0 on the whole lint and carried one falsifiable claim
in 472 words") and an **artifact** (the audit table), not with principles. Detail
lives in references so the entry point stays short enough to be followed.

**Alternatives rejected:** shipping the deletion list as the skill's main content —
refuted by E-001. Putting Tier 1 in prose instructions rather than a script — the
script is exact, free to run, and already existed.

**Open questions settled while writing, per the ticket:**

- *Is "Limits" exempt from the truth-value heading rule?* **Yes.** Structural
  labels — Limits, References, Appendix, Method — carry navigation rather than
  argument. Content headings must assert or ask.
- *Script or instructions for Tier 1?* **Script**, `scripts/lint.py`.

---

## [E-002] Decision: the lint skips mention, and says what it cannot do

_Date: 2026-09-20_

**Decision:** `lint.py` blanks backticked, emphasised and quoted spans before
matching, over the whole text rather than per line. Its footer prints the three
reference rates and the sentence "this check cannot tell a good paper from a bad
report."

**Rationale:** found by dogfooding. Running the lint on its own documentation
produced nine hits, every one inside a quoted example of a banned construction.
A style guide necessarily quotes what it bans, and so does any draft citing a
source — linting mention as use makes the tool untrustworthy exactly where it is
most used.

The first fix was per line and left 1 hit, because emphasis wraps across lines in
real prose and a split span exposes its second half. Fixed by matching over the
full text with newlines preserved so line numbers stay correct.

**Verified by regression, both directions:** skill files 0 hits; the E-001
AI-generated baseline unchanged at 58.9/10k; three hand-written documents
unchanged at 0.0/10k. A mention filter that also suppressed real hits would have
shown up as the baseline falling.

**One rule was dogfooded into the text itself.** `SKILL.md` said "the primary pass
is the claim audit" — an unquantified ranking by its own rule. Changed to "Pass 1
is the claim audit."

**Revisit if:** drafts arrive in LaTeX, where the markup assumptions do not hold.

---

## [E-004] Decision: Pass 1 has three modes, and design mode asks a different question

_Date: 2026-09-20_

**Decision:** Pass 1 opens with a mode table — revise (audit paragraphs), draft
(audit intended claims before prose), design (audit load-bearing assumptions).
Design mode's question is *"if this assumption is wrong, does the work still measure
what it claims?"*

**Rationale:** confirmed on both live uses, and E-005 showed the E-003 fix was
wrong. E-003 read this as an ordering problem — audit the claims before writing —
which works for prose. On a design there are no claims to audit: its assertions are
about what *will* be measured, and "we will sweep eight layers" cannot be false.
The falsifiability question has nothing to bite on. The assumption question does the
same job — separating load-bearing from decorative — but it is a different question,
not a re-ordering of the same one.

**Alternatives rejected:** a single mode with guidance to "adapt as needed" — the
adaptation is exactly what a first-time user will not find, and both defects came
from the skill assuming a document type it did not name.

**Feasibility absorbed here rather than as a new pass.** E-005 found nothing in the
skill asked whether the work can be run, and that a ~50% dependency failure rate
changes the artifact design. It fits design mode's table as an assumption row, which
is where it naturally landed in E-005 without being asked for.

---

## [E-004] Decision: the audit is documented as a ranking device, not only a filter

_Date: 2026-09-20_

**Decision:** Pass 1 gains a section stating that once every row has a falsifier,
which claim is load-bearing becomes visible, and that this determines document
order. It ends: *"Expect the ranking, not the filter, to be what you get."*

**Rationale:** across two live uses the documented filtering job caught **zero**
unfalsifiable claims, because both sources were already written to that standard.
The undocumented ranking job changed the structure both times — an analytic result
promoted above the measurement confirming it, and a control promoted from an
attachment into an experiment's first job. The skill documented the half that did
nothing.

**Revisit if:** a third use catches unfalsifiable claims, which would mean the
filter matters on source material not already written to this standard — likely
when the input is generated rather than hand-written.

---

## [E-004] Decision: Limits has three categories; `voice.md` is scoped, not cut

_Date: 2026-09-20_

**Decision (Limits):** entries are of three kinds — what the result does not show,
what was not done, and **how the result may not be used**. The third is called out
because no Pass 2 question generates it and it had to be added by hand on both
uses ("this is a consequence, not a method I am offering").

**Decision (`voice.md`):** scoped rather than cut, and shortened. Header now reads
"open only when drafting from nothing"; when extending a document, take the register
from the document. Its epistemic section is dissolved — two moves duplicated
`structure.md` §2 and §7 outright, and the three that were doing real work and had
no home (aspiration vs mechanism, crediting prior work for the part that is not new,
reporting error with magnitude) stay as register.

**Rationale:** unused on both live uses, but two uses of the same shape — extending
an existing document — is not evidence that evidence-backed content is dead weight.
It is evidence that its value is conditional on there being no surrounding document.
Cutting would have discarded a measured corpus profile on a biased sample.

**Revisit if:** a from-scratch draft also leaves it unopened. Then cut it.

---

## [E-004] Decision: defect 6 held, and the "false positives" may not be defects

_Date: 2026-09-20_

**Decision:** no rule added to distinguish a number-backed qualifier from a hedge.
Held for a third observation.

**Rationale, and a reading that argues against ever adding it.** There are now two
cases where a lint rule fired on arguably legitimate use: "largely determined"
summarising a measured 7% (E-003), and "the primary purpose" used descriptively
rather than as a ranking claim (found while writing this fix).

**In both cases rewording to satisfy the rule improved the sentence.** "The
experiment's first job" is more specific than "the primary purpose"; the E-003 fix
replaced a paraphrase with the quotation it was standing in for. A rule whose false
positives improve the text is not obviously worth an exception.

Across two live uses the lint's only hits were unquantified superlatives in my own
prose — 2 for 2, no genuine false positives over 2,700 words. At corpus scale that
same rule separates almost nothing (0.0 / 1.6 / 3.1 per 10k). It is a weak detector
and a good drafting check, which are different jobs.

---

## [E-006] Decision: analytic claims get a row flag, not a fourth mode

_Date: 2026-09-20 · from the third live use, the first not run by this session_

**Decision:** Pass 1 rows may carry `[A]`. For an analytic claim, column four holds
**the premise's** falsifier rather than the claim's.

**Rationale:** modes are per document; analytic-ness is per claim. The paper's abstract
carries both a derivation ("the coefficient is exactly 1 for any `u`") and a
measurement (67% against a 5% control), so a document-level mode cannot separate them.
The reporting session offered "a fourth mode, or a row-level flag" and the per-claim
scope decides it.

The substantive rule is theirs: *we measured the premise rather than the conclusion.*
An analytic claim inherits its empirical content from its premise, so that is where
the falsifier belongs. The repo already contains the worked case without the table
being able to express it — the pinning claim is analytic, its premise is prefix-
sharing, and [E-017] and [E-018] measured the premise. [E-019]'s write-up drew the
same analytic/empirical line in prose because the table could not.

**Guard against the obvious abuse:** an analytic claim must ship its derivation, in
the document or by citation. Without one it is not analytic, only unfalsifiable — and
the flag would become a way to dodge the fourth column.

**Alternatives rejected:** a fourth mode (wrong scope, per above); leaving it to prose
(which is what happened in [E-019], and it worked there only because I already knew
the distinction).

---

## [E-006] Decision: the limits section is specified by role, not by name

_Date: 2026-09-20_

**Decision:** the quarantine is the requirement and the name is free. Any section
performing the role is exempt from the truth-value heading rule.

**Rationale:** the paper's equivalent is "What to attack" — the same quarantine in an
adversarial register. Mandating the word "Limits" would have flagged a section doing
the job correctly.

**Added beyond the report:** an adversarial framing collects what a reviewer would
attack, and **nobody attacks a constraint on use**, so the third Limits category —
how the result may not be used — tends to disappear under the rename. Permitting the
rename ships with that check.

**One correction applied to myself while writing this.** The first draft said "What to
attack" is "arguably stronger". The lint flagged *arguably*, and the right fix was not
to reword the hedge but to delete the claim: there is no evidence it is stronger, only
that it does the same job.

**Revisit if:** a section named for the role turns out to drift in content as well as
framing — the use-constraint check is a prediction, not a measurement.

---

## [E-007] Decision: the audit ranks, genre orders

_Date: 2026-09-20 · from the third live use_

**Decision:** Pass 1's second job now states that the audit identifies what is
load-bearing and **does not** determine document order. Genre does: paper →
dependency, lab note or narrative → chronology, and within an argumentative section
dependency governs regardless of the document's top-level order.

**Rationale, and this is the most serious defect found so far.** The text said the
audit "fixes the order of the document" without naming a target. On a paper the
reporter correctly derived dependency order. Applied to
`web/blog/2026-09-15-five-days.mdx` the same conclusion is destructive: that document
exists to show eight claims being withdrawn **in the order they were withdrawn**, and
its standfirst says "A record rather than an argument". Dependency-ordering it removes
its function.

**Verified against the repo rather than taken on report**, and the composition rule is
ours: [E-003] added a section to that same chronological post and led with the
analytic claim over the empirical one — correct, because the post is chronological at
the top level while each section argues internally. Both were true at once and neither
was stated.

So the skill's strongest pass was giving actively harmful advice on one of the genres
its own frontmatter lists. **Alternatives rejected:** naming dependency as the default
with chronology as an exception — the blog post is not an exception, it is the other
half of what this skill is for.

---

## [E-007] Decision: the reference rates are a style measure, not an authorship test

_Date: 2026-09-20_

**Decision:** relabel — *house-style prose 0.0 / published mech interp papers 5.1 /
unedited survey-report prose 6.4* — and state in all three places that the rate
tracks style adherence rather than provenance.

**Rationale:** the old label "AI-generated reports 6.4" beside "hand-written research
prose 0.0" invites reading the lint as a detector, and the reporter has the
counterexample: both documents they tested scored **0.0 and both are AI-written**
(3,159 and 13,149 words). One of them is partly this session's own output from today.

The categories were always about register. The labels said provenance, and someone
would eventually act on that.

---

## [E-007] Decision: `SKILL.md` must stay runnable by hand

_Date: 2026-09-20_

**Decision:** recorded in the README as a standing constraint. No pass may depend on
tooling a reader has to set up.

**Rationale:** a session predating the install cannot invoke the skill and reads the
file instead. That has now happened, and all three passes ran from it without
friction. The property was never stated while the file was being cut and grown, so it
survived by luck. It means the skill degrades to a readable checklist rather than to
nothing.

**Also recorded:** Pass 2 questions 2 and 3 are the only ones to have fired in live
use — 2 twice, 3 once. `SKILL.md` says where to spend attention and explicitly does
**not** reorder the list, because n=3 does not license a ranking.

---

## [E-006] Confirmation: the use-constraint prediction fired, out of sample

_Date: 2026-09-20 · tests the prediction recorded in the second [E-006] decision_

That decision permitted the limits section to be named by role rather than by name,
and added a check the reporting session had not asked for:

> nobody attacks a constraint on **use**, so the third Limits category tends to
> disappear under the rename.

It was flagged at the time as **"a prediction, not a measurement"** with a revisit
condition. The reporting session has now checked it against the paper that prompted
the rename. **Its "What to attack" section has six entries and not one is a
use-constraint** — every entry is "what was not done" or "what the result does not
show". The missing entry, which they wrote:

> *This is not a method. The pinned coefficient explains why an edit reaches every
> prompt sharing its subject. It is a consequence of how ROME normalises, not a
> technique we are offering — "edit deeper to leak less" does not follow from
> anything measured here, and §4.3 measures a coefficient, not a behaviour.*

**This is the first rule in the skill derived by reasoning rather than from an
observed failure, and then confirmed.** Every other rule was read off something that
had already gone wrong — the case-sensitivity bug, the missing different-subject
control, the genre defect. This one was argued from what a reviewer does and does not
attack, written down as a prediction, and then held on a document I have never seen.

**Not circular**, and the sequence matters: the report described only the section's
*name*. The prediction was about its *contents*, which had not been reported and which
I had no access to. Out of sample.

**n = 1, and the mechanism is plausible enough to be true of this section rather than
of adversarial framings generally.** One confirmed prediction is not a validated rule.
What it does establish is that the reasoning behind the rule was not post-hoc — which
is a weaker claim than it feels like, and worth stating as the weaker one.

**No change to `SKILL.md`.** The rule is already there, already fired, and the file is
190 lines and due a cut. Adding a worked example of a rule that just worked would be
the growth pattern this project keeps flagging and not fixing.

**Also recorded, since it bears on where the good edits came from.** The reporting
session judged two of my additions better than its own proposals — the `[A]` flag's
derivation guard, and the "they compose" clause on genre ordering. Both were
refinements to *their* findings. Neither would exist without the report, and the
report would not have found the genre defect without running the skill on a document
I did not write. The division that produced the last two rounds is: they find defects
by use, I find the failure mode one level up. Worth keeping rather than collapsing.
