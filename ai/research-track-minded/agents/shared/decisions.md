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
