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
