# The Card

One card open at a time. Six fields. Nothing starts until all six are filled,
nothing else starts until this one is closed.

The heavy protocols in `~/.claude/CLAUDE.md` — ten design lenses, nine dry-run
moves, the thread tree — are for the rare question that deserves a week. This is
for everything else, which is almost everything. If a card takes more than one
sitting to fill, it is too big; cut it until it fits.

---

## The six fields

**1. WHERE WE ARE.** The last thing that was established, as a number or a fact.
Not a summary of the project. One sentence.

**2. WHAT WE ARE DOING.** One action, stated so that a second person could carry
it out without asking. If it needs "and", it is two cards.

**3. WHY.** What is not known right now that will be known after. If the answer
is "it would be good to have", there is no why and the card does not open.

**4. WHAT IS AFFECTED.** Which existing claims, files, or numbers change if this
comes back either way. Written before the work, so a silent invalidation is
impossible.

**5. CONCLUSION IF WE DO IT.** Both branches, stated in advance. *If X, then we
claim A. If not-X, then we claim B.* A card where only one branch has a
consequence is not an experiment, it is a hope.

**6. CONSEQUENCE OF NOT DOING IT.** What breaks, stalls, or stays unknown if
this is skipped forever. If the honest answer is "nothing", close the card
unstarted. That is a success.

---

## The three rules

1. **One card open.** A second idea goes in `threads.md` as one line and is not
   discussed further in that sitting.
2. **A card closes with a number or a sentence that could have come out the
   other way.** Not with "explored" or "built".
3. **Field 6 is the one that kills cards.** Fill it honestly and most ideas die
   there, which is the point — it is cheaper than killing them after the work.

---

# CURRENT CARD

_Opened 2026-10-24. Nothing else opens until this closes._

**1. WHERE WE ARE.**
The instrument works and the numbers hold: a coefficient computed from the
unedited model predicts delivery exactly (1.000 for prefix-sharing, 0.082 for a
different subject, 23,505 readings, four models). Nothing in the project has
been read by anyone outside it.

**2. WHAT WE ARE DOING.**
Sending the 350-word note in `notes/natalie-packet.md` (2026-10-15 heading) to
Natalie.

**3. WHY.**
It asks the one question that cannot be answered from inside: *is a cheap
pre-run criterion for whether a propagation item can test propagation something
the field would use, or a restatement of what benchmark authors already do by
eye?* We do not know which, and no further measurement will tell us.

**4. WHAT IS AFFECTED.**
Everything downstream of the direction choice: the write-up's framing
(`web/notebook/edit-slice/review.md` §7), whether the validation/probing
positioning is claimed at all, and which of the two next months happens —
benchmark critique or code domain. No existing number changes either way.

**5. CONCLUSION IF WE DO IT.**
If the criterion is something the field would use → this is a paper, and the
next month is the benchmark critique, with the screen as the headline.
If it is a restatement of existing practice → this is a note, the screen gets
demoted to a methods paragraph, and the next month is the code domain, where
claim 3 is still ungated by anyone else's work.

**6. CONSEQUENCE OF NOT DOING IT.**
The project keeps producing correct measurements that nobody has asked for, and
the direction question stays open indefinitely — which is what the last six
weeks already looked like. Every further experiment inherits an unresolved
framing, so the cost of not sending compounds rather than holds.

**Status:** parked, 2026-11-10.

**Why parked, not closed.** The card asks whether the field would use a cheap
pre-run criterion. That answer only arrives from outside, and it has not. The
note went as the first of three short emails instead of one 350-word note
(`notes/email-1-vlaminck.md`, sent 2026-10-31); emails 2 and 3 are written and
deliberately held until the first is answered. So the action happened and the
question did not resolve, which is neither closed nor blocked: nothing prevents
the work, it was chosen against for now.

**To resume:** a reply, or a decision to stop waiting for one. If a reply comes,
field 5 reads off it unchanged. If none comes by the time the next direction
choice is due, the card closes on the second branch by default — the criterion is
demoted to a methods paragraph — and that default should be taken deliberately
rather than by silence.

**What this cost while it sat.** Seventeen days open, during which other work ran
anyway. Rule 1 says one card open and nothing else until it closes; that was not
what happened, and the rule did not fail silently so much as go unconsulted. The
card was unresolvable from inside and should have been parked when email 1 went
out, not kept open as though it were live.

---

# CURRENT CARD

_Opened 2026-11-10. The card above is parked; this is the one open card._

**1. WHERE WE ARE.**
[R-012] read Ravfogel et al. (2605.12426) and found it predicts the opposite of
what we measure: a per-relation block account predicts perturbation stays local
to the edited relation, and [E-033] finds an edit damages everything about the
subject, worst along the injected value's type. Three explanations sit on the
table — their single-layer construction does not carry to deep models, ROME does
not act on the structure they describe, or the account is incomplete where typed
attributes would complete it — and nothing distinguishes them.

**2. WHAT WE ARE DOING.**
Reading §5.3 — the part that probes real models rather than the construction —
closely enough to say, in writing, what re-running it on our stack would require:
which models, which facts, which quantity, and whether NDIF serves those models.

**3. WHY.**
We do not know whether §5.3 is reproducible by us at all. Everything after this
depends on that answer, and it is unanswerable from the abstract — which is the
specific lesson [R-012] paid for: an abstract under-reports overlap and
over-reports applicability, because it sells the contribution and buries the
setting.

**4. WHAT IS AFFECTED.**
Nothing measured changes. What changes is whether the next card exists:
`review.md` §2 already had one claim about this paper withdrawn, and [T-086] is
still without a candidate. If §5.3 is out of reach, §2 says the tension cannot
be probed by us rather than leaving a reader to assume it will be.

**5. CONCLUSION IF WE DO IT.**
If §5.3 is reproducible on our stack → the next card runs it, and the tension
becomes testable.
If it is not — models we cannot serve, data not released, or a quantity that
needs their training setup — → we say so in §2 with the reason, and the tension
stays a tension that we have stated honestly rather than one we implied we would
resolve.

**6. CONSEQUENCE OF NOT DOING IT.**
Little, for the project: [E-033] stands on its own measurement whatever this
paper says, and "a tension" is already the honest framing. This card is open for
understanding rather than for a deliverable, which is a real reason and a weaker
one, and it is written here rather than dressed up. What it does buy is that the
central result stops being one we cannot explain when asked — which is the first
question any reader of §2 will have.

**Status:** open. Blocked on nothing. Ticket [R-020] carries the reading.

