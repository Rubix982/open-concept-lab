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
