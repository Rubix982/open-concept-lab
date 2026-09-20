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
