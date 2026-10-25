# CURRENT CARD

_Opened 2026-10-25 (overnight side build). Template: `ai/edit-slice/CARD.md`._

**1. WHERE WE ARE.**
Two 2026 papers already read planted facts back from clean ROME edits (KSTER recovers
the subject using the base model and a name list; EditScope recovers the object with no
base model). Neither tests an attacker who tries to hide the edit. Our smoke test: one
edit plus 1% weight noise, and the subject still ranks #1 of 20,391.

**2. WHAT WE ARE DOING.**
Plant CounterFact facts in GPT-2 medium with ROME, apply five hiding strategies (weight
noise, fine-tuning, MEMIT-style spreading, batches, decoys), and measure whether the
subject still ranks #1 and the object still reads back, counting only edits that still work.

**3. WHY.**
We do not know whether cheap masking defeats weight-diff forensics. If it does, the
published methods are only a defense against careless attackers.

**4. WHAT IS AFFECTED.**
The README's headline claim, and which attack the follow-up should target.

**5. CONCLUSION IF WE DO IT.**
If forensics survives every attack that leaves the edit working, we claim: at GPT-2
scale, weight-diff forensics resists cheap evasion, and the attacker must pay in model
damage (perplexity) to hide. If some attack beats it while the edit still works, we
claim that attack is the open problem and report its price.

**6. CONSEQUENCE OF NOT DOING IT.**
The prior work stays untested against anyone actually trying to hide, so nobody knows
whether it is a defense.

**Status:** closed 2026-10-25, the "some attack beats it" branch.

**Closed with:** cheap masking does not hide the subject. It was #1 in every working
edit under noise up to model-wrecking levels, under 300 fine-tune steps, and under a
5-layer spread. Two attacks do beat the simple defender while the edit still works:
planting 10–100 facts at once (41–50% of subjects found) and 50 decoys (real subject
#1 in 1/20 by fire alone, 12/20 after read-back). Those are the open problem. The
direction also changed: the threat model narrowed to redistributors (see report.html),
and the next project is `../multiturn-refusal/`.
