# Treated — Tier 2 questions applied as the only instruction

Constraint held: no fact appears here that was not in the baseline. Where Tier 2
demanded a number the baseline does not supply, the absence is stated rather than
filled.

---

## GradSim predicts which edits will break their neighbours; nothing yet certifies that an edit did not

*(Q1: the heading now asserts something that can be shown false — a certification
result would falsify the second clause.)*

Two different jobs are being run together in this literature, and separating them
is most of the argument. **RippleEdits (Cohen et al., 2023) detects, after an edit,
that related facts were not updated. GradSim (Qin et al., 2024) predicts, before an
edit, that they probably will not be.** Neither certifies, and a certification
layer is not a better version of either — it is a third object with a different
success condition.

GradSim is the cosine similarity between the gradient of the original fact and the
gradients of its related facts. Qin et al. report that it correlates positively
with ripple-effect performance across models, editing methods, and evaluation
metrics, and that the three failure classes they examine — negation, over-ripple,
and multilingual edits — cluster at low GradSim.

**The claim I would defend: GradSim as reported cannot be used as a pre-edit gate,
and the reason is structural rather than a matter of needing more experiments.** A
gate requires an operating point — a threshold, and the false-accept and
false-reject rates at that threshold. A correlation, however strong, supplies a
ranking. Ranking tells you which edit is riskier than which; it does not tell you
whether *this* edit is safe enough to ship. The baseline source reports no
threshold and no error rates, and describes GradSim as a "risk score" and "triage
signal" without either.

*(Q2: this is the document's own claim. It is wrong if Qin et al. report an
operating point, or if a downstream paper fits one. Q5: I have not read Qin et al.
directly — only the summary quoted in the source — so the claim is about what the
summary conveys, and that limit is load-bearing here, not decorative.)*

**"Certification" is the wrong word, borrowed inexactly.** In formal verification,
certifying means producing an artifact a third party can check without repeating
the work. Nothing in this literature proposes that. What is actually wanted is
exhaustive post-edit *testing* over entailed facts — closer to a regression suite
than to a proof. The borrowing is evocative rather than exact, and it silently
imports a guarantee nobody is offering.

*(Q6: the existing vocabulary — testing, coverage, regression — already denotes
this structure, and denotes it correctly.)*

**The gap, priced.** Certifying that all entailed neighbours survive an edit
requires first enumerating them. That enumeration does not exist and is not
cheap: entailment from a single fact is open-ended, so the set has to be either
hand-written per edit (which does not scale and builds in the author's
assumptions) or discovered by intervention (which costs a forward pass per
candidate and needs a candidate generator nobody has published). **Until someone
prices that enumeration, "certification layer" names a wish rather than a
programme.** The cheap thing available now is narrower and worth saying plainly:
report GradSim's distribution alongside edit-success rates, so a reader can see
where on the ranking a result sits.

*(Q3: named gap, named requirement, named cost, and the cheaper substitute.)*

**What this is not.** This is not a criticism of Qin et al., who propose GradSim as
an indicator and demonstrate it as one. The conflation is downstream — in
summaries, including the one I am revising, that promote an indicator to a control.

*(Q8: scope fixed before the damage.)*

### Limits

- I have read Qin et al. and Cohen et al. only through a secondary summary. Every
  claim above about what they report could be overturned by the papers themselves.
- No effect size appears anywhere in the source. "Correlates positively" is the
  strongest statement the evidence here supports, and the argument about operating
  points would change if the correlation turns out to be near-deterministic.
- Su et al. (2025) is cited in the baseline as linking the two; I have not checked
  whether it already makes the detect/predict/certify distinction drawn here.

*(Q7: all qualification collected here; the body above states claims unhedged.)*
