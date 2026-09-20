# E-001 scoring

Every counted item is listed. I am both reviser and scorer, so the enumeration is
the only thing making this auditable — check the counts rather than trusting them.

## Results

| Metric | Baseline | Treated | |
| --- | ---: | ---: | --- |
| M1 · own-claims | 10 | 16 | +60% |
| M2 · falsifiable-as-written | **1** | **8** | **8×** |
| M3 · headings with a truth value | 0 / 1 | 1 / 2 | — |
| M4 · words | 472 | 558 | +18% |
| M5 · Tier 1 hits per 10k | 0.0 | 0.0 | control holds |
| M6 · numbers attached to an instrument | 0 | 0 | **unchanged** |

**Verdict: CONFIRM**, with one important qualification (M6) and one unexpected
result (M5 on the baseline).

---

## M1 · own-claims

Definition: could be wrong *even if every cited paper is accurately reported*.

**Baseline — 10.** "the clearest current predictor is GradSim" · "most detection
work is still diagnostic rather than preventive" · "GradSim is the main explicit
predictor now" · "use GradSim as a pre-edit risk score" · "a useful system-level
reading is that you can compute a risk estimate" · "one of the few papers that
moves beyond measuring after the fact" · "RippleEdits is still the main detector
suite" · "this is useful because it connects a detector with a predictor" · "what
is still missing is an editor-agnostic certification layer" · "today's reliability
stack is mostly detection plus GradSim prediction".

**This corrected my expectation.** I assumed the baseline made no claims of its
own. It makes ten. The defect is not *absence* of claims — it is that nine of the
ten are unfalsifiable as written.

**Treated — 16.** two jobs are being conflated · detect/predict/certify are three
objects with different success conditions · GradSim cannot serve as a pre-edit
gate · a gate requires an operating point · a correlation supplies ranking, not a
shipping decision · the source reports no threshold and no error rates · the
"certification" borrowing is inexact · formal certification means a
third-party-checkable artifact · nothing in this literature proposes one · what is
wanted is a regression suite, not a proof · certification requires enumerating
entailed neighbours first · that enumeration does not exist and is not cheap ·
entailment is open-ended, so the set is hand-written or interventionally
discovered · "certification layer" names a wish, not a programme · this is not a
criticism of Qin et al. · the conflation is downstream, in summaries.

## M2 · falsifiable-as-written

Definition: a reader can name a specific observation that would make it false,
using only what the sentence supplies.

**Baseline — 1.** Only "no editor-agnostic certification layer exists" qualifies
(exhibit one and it is false). The other nine fail on unquantified superlatives
and scope words: *clearest*, *main*, *most*, *one of the few*, *mostly*. There is
no threshold to violate.

**Treated — 8.** Each with its refutation: *three distinct objects* → show
certification reduces to detection or prediction. *Cannot serve as a gate* →
exhibit a gate. *A gate requires an operating point* → exhibit one without.
*The source reports no threshold* → point at the page. *Certification means a
checkable artifact / nobody proposes one* → cite a paper that does. *Requires
enumeration first* → a method that certifies without enumerating. *Hand-written
does not scale; intervention costs a forward pass per candidate* → a cheaper
generator. *The conflation is downstream* → show Qin et al. make the gate claim
themselves.

## M3 · headings

Baseline: "Predictors and detectors of broken entailed or ripple-neighbor facts" —
a subject area, no truth value. **0/1.**

Treated: "GradSim predicts which edits will break their neighbours; nothing yet
certifies that an edit did not" — falsified by a certification result. **1/2**;
the second is "Limits", a structural label that is arguably exempt from the rule.
Worth deciding explicitly in the skill rather than leaving ambiguous.

## M4 · length — the null did not fire

+18% (472 → 558). The pre-stated null was "longer output that is equally
unfalsifiable". Length grew modestly while M2 grew 8×, so the gain is not an
artifact of volume. Had M1 stayed flat with M4 up, this would have been a DENY
dressed as a CONFIRM.

## M5 · the negative control, and a surprise

0.0 → 0.0. Tier 2 says nothing about vocabulary and moved nothing. The arms were
isolated.

**The surprise is the baseline's own score.** This passage — which is a fair
specimen of what the skill exists to prevent — scores **0.0 hits per 10k on the
Tier 1 probes**. It contains no "delve", no "Furthermore", no hedge adverbs, no
throat-clearing. It is clean by every lintable criterion and still says nothing
that could be wrong.

That is R-003's finding reproduced on a single passage, and more sharply than the
corpus-level 9.6-versus-14.7 comparison managed. **A document can pass the entire
word list and fail completely.**

## M6 · numbers — unchanged at zero, and this is the real limit

Neither version attaches a number to an instrument, because the baseline supplies
none and the treatment was forbidden to invent any.

What Tier 2 produced instead was the *statement that the numbers are missing* —
"the baseline source reports no threshold and no error rates", and a limits entry
saying the argument would change if the correlation turns out near-deterministic.

**So Tier 2 converts missing evidence into a stated gap. It does not conjure
evidence.** That is the correct behaviour and it bounds what the skill can claim:
the questions improve the *epistemic structure* of a draft, and they cannot
improve its *evidential base*. A draft written over thin sources will come out
honestly thin. Saying so in advance is better than discovering it as a
disappointment.
