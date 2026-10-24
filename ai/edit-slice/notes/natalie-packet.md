# Packet for Natalie

_Prepared 2026-10-03 · edit-slice · Saif Ul Islam_
_Internal note. The covering message is the block below; everything after it is the
checklist used to assemble the packet and the answers to questions likely to come up._

---

## The covering message

> Hi Natalie,
>
> Ahead of our call — here is the edit-slice work, written to be judged rather than
> admired. Three artifacts, in the order I would read them:
>
> **1. The paper** — `/notebook/edit-slice/review` (~20 min)
> An arithmetic account of why a ROME edit reaches everything sharing its subject, with
> the boundary of that account measured rather than asserted. **Section 6 is the attack
> surface**, ordered by how much damage each objection does. **Section 5** lists every
> claim the project withdrew — twelve claims, nine withdrawn or narrowed. If you are
> deciding whether to spend time on this, read the abstract and then section 6.
>
> **2. The evidence ledger** — `/notebook/edit-slice/ledger`
> Every decision, finding and thread, generated from the repository so it cannot drift
> from it. 38 decisions, 18 findings, 68 threads. Most went nowhere, which is why the
> whole list is published rather than the nine claims the paper defends.
>
> **3. A plain-language version** — `/writing/five-days`, and a short deck if a call is
> easier than a read.
>
> **The one-paragraph version.** ROME divides its update by `u·k*`. For any prompt
> beginning with the edited subject, the key at that token is identical to `k*` under
> causal attention, so the update coefficient is **exactly 1** — for any covariance, at
> every layer, whatever relation the prompt asks about. Measured at exactly 1.000 across
> four models from 6B to 405B. What reads as an edit "propagating to related facts" is
> displacement keyed on the subject string: editing where a person *works* relocates their
> *birthplace* at an identical rate, 28/42 in both arms, paired difference +0.0 pp.
>
> **What I would most like from you**, in priority order:
>
> 1. **Is the pinned-coefficient result already known?** It is a line of algebra.
>    Practitioners may simply assume it, and "we could not find it stated" is the weakest
>    form of novelty claim. You can probably answer this in a sentence; I cannot answer it
>    at all from inside.
> 2. **Is the benchmark consequence worth a week?** Every ripple benchmark I know of probes
>    with prompts that begin with the subject — exactly the prompts that receive the full
>    update mechanically. Re-scoring one published benchmark with subject-final probes
>    either clears it or shows that a share of reported ripple is arithmetic. It is the only
>    item here that changes what other people do. Which benchmark would save me the most
>    wasted effort?
> 3. **Is a careful existence claim at n≈30–42 publishable anywhere**, or does this need
>    the frequency work it currently forbids itself?
> 4. **Is it a contribution to show a standard check cannot support the inference drawn
>    from it?** A prior-art sweep while assembling this packet turned up He et al. (arXiv
>    2601.04600, January 2026). Reading it properly, they have more of my work than I
>    first credited: the depth phenomenon in §4.4 *and* the cosine decay in §4.3 — 0.80 at
>    layer 5 to 0.50 at 25, against my 0.98 to 0.47. Eight months earlier.
>
>    What they do not have is a working control. They read the effect as depth because
>    "ROME achieves stable and high edit success rates" across layers — and §4.4 shows
>    edit success cannot measure edit strength, spanning 0.17 nats where real displacement
>    spans 5.70. Matching on displacement instead, at a 16x step budget, the effect
>    survives. So what I have is not the phenomenon and not the mechanism, but the
>    demonstration that the field's standard efficacy check cannot license the conclusion
>    people draw from it. Is that worth anything on its own? I have left everything in
>    with the prior work cited beside it rather than quietly dropping it.
>
> **The honest framing:** most of what I found is what does not work. Section 5.1
> separates the eliminations — which constrain the space for anyone — from my own
> mistakes, which constrain nothing. What survives is one boundary:
>
> > We can say **which** facts an edit touches. We cannot say **how hard**.
>
> Nothing here has been judged by anyone outside the project. That is the actual risk and
> it is why I am writing.
>
> Saif

---

## Assembly checklist — run before sending

- [x] **§4.5 corrected.** It asserted a general "floor" for nine days on one relation;
      [E-033]'s crossover refuted it at 1 of 6 arms. The paper would otherwise have
      contradicted its own §5.1.
- [x] **Table 5 count** matches its prose (twelve / nine) in the paper, the deck and
      `DECK.md`.
- [x] **Banned word** absent from paper, narrative and deck.
- [x] **Ledger regenerated** from the repository — 38 decisions, 18 findings, 68 threads.
- [x] **`yarn build` clean · `yarn design:check` all decidable criteria pass** — 124
      evidence records, every link resolves.
- [x] **No work in flight.** All six [E-033] arms complete; nothing half-written.

## Questions she is likely to ask, and the short answers

**"Why n = 29–42?"** Possession gating. A chain is usable only if the model holds all
three facts; 136 mined → 78 usable → 42 edited, and 29 of those carry all three attribute
labels. [O-004] licenses existence claims and never a rate, and the artifacts are written
to avoid implying one.

**"Why layer 5?"** It is EasyEdit's shipped `llama3-8b.yaml`. [E-028] then varied it and
found propagation changes 2.96× per nat displaced between layer 5 and layer 20 — which is
how we learned the coefficient does not predict effect.

**"Isn't 405B instruction-tuned a confound?"** Yes, and it is flagged everywhere it
appears. It is the only 405B hosted, so that arm varies scale *and* post-training. The
clean scale comparison is 70B base.

**"What would change your mind?"** On the central claim, a prefix-sharing probe measuring
anything other than exactly 1.000 — it has not happened in 216 cells on GPT-J or at any
layer of four models, and it would mean the derivation or the implementation is wrong.

**"What is the weakest part?"** §6.2 — the mechanism is a line of algebra and may be
assumed by practitioners. That is question 1 above, and it is the reason for the call.

**"Has anyone seen the main result before?"** Partly, and it is worth being precise.
ROME's own paper observes qualitatively that an edit generalizes to *"new
prompts/sentences that include the subject tokens"* — so the phenomenon is in the original
work. A search found nobody stating the **arithmetic**: that the coefficient is exactly 1
on those prompts, for any covariance, at every layer, whatever relation is asked. So the
question is not "has anyone seen this" but "has anyone said why, and noticed it is exact".

---

# Update — 2026-10-15

_Drafted by the autonomous loop. **Not sent, and not to be sent without Saif's decision**
— `LOOP.md` forbids outward messages. Listed in `out/RATIFY.md`._

The 2026-10-03 packet led with the mechanism. Everything since points at one small
instrument, and that is a better thing to put in front of someone than three findings.

## The covering message, as drafted

> Hi Natalie,
>
> Since we last spoke the work has converged on one question I would value your read on,
> and it is smaller than what I sent before.
>
> **A propagation test can only measure propagation if its test prompt's key does not
> overlap the edit's key** — and ROME's own normalisation makes that computable *before any
> edit is applied*, from a single forward pass through the unedited model. Call it a screen.
>
> It finds real cases. RippleEdits has a test type meant to check whether an edit
> *propagates* to a different entity reached through the edited one. Their prompt is
> *"the name of the head of government of the place of death of **Leo Arons** is"* — and the
> edited subject is in it. We measured what fraction of the edit vector arrives at that
> token: **0.982**, against a floor of **0.070** built by scoring the same prompts against a
> stranger's edit. The update gets there by arithmetic. An editor could score well on that
> test without generalising at all.
>
> It is not a universal law of multi-hop tests, which is what makes it a screen rather than
> a complaint: MQuAKE names the edited subject **iff** the edit sits on the chain's first
> hop — 6,861 of 6,861, and 0 of 16,506. So benchmarks that pass already exist, in the
> field's own data, by construction rather than design.
>
> The nearest published work is ChainEdit (arXiv 2507.08427), which finds a *different*
> flaw in the same benchmark — their questions need external-KG knowledge the model may not
> hold. Their repaired variants do not remove the edited subject; one of them injects *more*
> context into the prompt. So a benchmark fixed for their problem still fails this screen.
>
> **What I want decided:** is a cheap pre-run criterion for whether a propagation item can
> test propagation something the field would use — or is it a restatement of what benchmark
> authors already do by eye? I cannot answer that from inside, and it determines whether
> this is a paper or a note.
>
> The write-up is at `/notebook/edit-slice/review`; §7 opens with the screen and §6 is the
> attack surface. Twenty minutes if you read only those.
>
> Saif

## What is deliberately not in it

- **The ES-margin identity**, which is the most novel single claim — ROME's optimiser
  saturates its target, so the efficacy *margin* is rank-identical to true-answer
  suppression at ρ = 1.000. It is a stronger result and a weaker opener: it needs two
  sentences of setup and it is about a different instrument. Hold it for the reply.
- **The elimination arc** (seven candidates, ceiling 0.534). It is rigorous and it is a
  negative; leading with it invites a shorter read.
- **Any novelty claim stronger than "we have not found it stated."** [R-017] searched,
  [R-018] read the one neighbour in full. That is enough to write the sentence above and not
  enough to write a stronger one.

## Before this goes anywhere

1. **ChainEdit's venue is unverified.** A search summary said ACL 2025; the arXiv record was
   not checked for it. The message above cites only the identifier, which is verified.
2. The 0.982 is **delivery, not effect** — [E-028d] put those 2.96× apart. The message says
   "arrives", never "changes the answer". Keep it that way.
3. [O-004]: 0.982 is a median over their prompts, not a rate about the benchmark.

---

# Outward messages — prepared 2026-10-24

_Prepared at Saif's request. **Still unsent — sending is his action, not the loop's.**
Links resolved to absolute URLs against `https://rubix982.github.io/open-concept-lab/`.
Two messages, because the two readers are being asked different questions: Natalie is
asked whether the field would use the screen; Arnab is asked to break it._

## A · Natalie — the decision

**Subject:** One question before the next step — a pre-run screen for propagation tests

> Hi Natalie,
>
> Since we last spoke the work has converged on one question I would value your read on,
> and it is smaller than what I sent before.
>
> **A propagation test can only measure propagation if its test prompt's key does not
> overlap the edit's key** — and ROME's own normalisation makes that computable *before any
> edit is applied*, from a single forward pass through the unedited model. Call it a screen.
>
> It finds real cases. RippleEdits has a test type meant to check whether an edit
> *propagates* to a different entity reached through the edited one. Their prompt is
> *"the name of the head of government of the place of death of **Leo Arons** is"* — and the
> edited subject is in it. We measured what fraction of the edit vector arrives at that
> token: a median of **0.982** across their prompts, against a floor of **0.070** built by
> scoring those same prompts against a stranger's edit. The update gets there by arithmetic.
> An editor could score well on that test without generalising at all.
>
> It is not a universal law of multi-hop tests, which is what makes it a screen rather than
> a complaint: MQuAKE names the edited subject **iff** the edit sits on the chain's first
> hop — 6,861 of 6,861, and 0 of 16,506. So benchmarks that pass already exist, in the
> field's own data, by construction rather than design.
>
> The nearest published work I have found is ChainEdit (arXiv 2507.08427), which finds a
> *different* flaw in the same benchmark — their questions need external-KG knowledge the
> model may not hold. Their repaired variants do not remove the edited subject; one injects
> *more* context into the prompt. So a benchmark fixed for their problem still fails this
> screen.
>
> **What I want decided:** is a cheap pre-run criterion for whether a propagation item can
> test propagation something the field would use — or is it a restatement of what benchmark
> authors already do by eye? I cannot answer that from inside, and it determines whether
> this is a paper or a note.
>
> The write-up: https://rubix982.github.io/open-concept-lab/notebook/edit-slice/review
> §7 opens with the screen, §6 is the attack surface. Twenty minutes if you read only those.
> Every decision and withdrawn claim, generated from the repo:
> https://rubix982.github.io/open-concept-lab/notebook/edit-slice/ledger
>
> Thank you,
> Saif

## B · Arnab — the attack

**Subject:** Something to break: ROME's coefficient is pinned at 1, and I think it
indicts RippleEdits

> Hi Arnab,
>
> I have a result I would rather you attacked than agreed with, and it sits close to two
> things I know you are sceptical about.
>
> **The claim is analytic, which is why I want it hit hard.** ROME divides its update by
> `u·k*`. For any prompt beginning with the edited subject, the key at that token is
> identical to `k*` under causal attention — so the coefficient is **exactly 1**, for any
> covariance, at every layer, whatever relation the prompt asks about. There is no fitting
> and no tuning in that sentence. Measured at 1.000 across four models from 6B to 405B, with
> a different-subject floor of 0.082 computed on the same materials, non-overlapping
> distributions, 23,505 readings.
>
> **Where it bites.** RippleEdits' compositionality items put the edited subject *inside*
> the test prompt — *"the name of the head of government of the place of death of Leo Arons
> is"*. Median delivery to that token is 0.982 against a 0.070 floor. The update arrives by
> arithmetic rather than by the model composing anything, so a method can score on that test
> without generalising. It is not a blanket indictment of multi-hop evaluation: MQuAKE names
> the edited subject iff the edit is on hop 1, 6,861/6,861 and 0/16,506.
>
> **What I am explicitly not claiming.** Delivery is not effect — at a coefficient held at
> exactly 1.000 the downstream reach still varies by 2.96×, and the best account I have of
> *how far* an edit travels explains 28.5% of variance. So none of this says an answer
> changed. It says the test cannot distinguish the two cases it was built to distinguish.
> The 0.982 is a median over their prompts, not a rate about the benchmark.
>
> **What I want from you:** the one objection that kills it, not a list. §6 of the write-up
> is my own attack surface, ordered by damage, and §5 lists the nine claims this project has
> already withdrawn — if the fatal objection is already in there and I have under-weighted
> it, saying which one is the most useful thing you could tell me.
>
> https://rubix982.github.io/open-concept-lab/notebook/edit-slice/review
>
> Saif

## Checks applied to both

- "Arrives" / "delivery" throughout; never "changes the answer" ([E-028d]: 2.96× apart).
- 0.982 stated as a **median over their prompts**, never as a rate about the benchmark ([O-004]).
- ChainEdit cited by identifier only — its venue remains unverified.
- No novelty claim stronger than "the nearest published work I have found" ([R-017], [R-018]).
- The ES-margin identity and the elimination arc are held back for the reply, as in the
  2026-10-15 draft.
