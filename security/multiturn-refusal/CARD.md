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

_Opened 2026-10-25. Nothing else opens until this closes._

**1. WHERE WE ARE.**
We have no number of our own yet. From prior work: Zhao et al. (NeurIPS 2025) found that
single-message jailbreaks lower a model's refusal reading while its harmfulness reading
stays high; SafeDream (arXiv 2604.16824) found a trained refusal-based detector fires
about 1.1 turns before a multi-turn attack succeeds. Both directions are defined on
single short prompts, and no one has checked that they still mean the same thing deep
in a conversation.

**2. WHAT WE ARE DOING.**
On Llama-3.1-8B-Instruct (NDIF), measure whether harmfulness and refusal directions
computed from single prompts still separate held-out harmful from harmless requests
when each request comes after 0, 2, 4 or 8 turns of innocent conversation.

Fixed before running, so the result cannot be tuned after the fact:
- *Directions:* difference of means, harmful minus harmless, on 128 + 128 single-turn
  requests. Harmful: AdvBench/HarmBench behaviours. Harmless: Alpaca instructions.
  Harmfulness is read at the last token of the user request; refusal at the last
  chat-template token before the reply (Zhao et al.'s two positions).
- *Layer:* the one that best separates a separate 64 + 64 single-turn split. Chosen once
  and frozen.
- *Test:* 100 + 100 fresh requests, each placed after 0 / 2 / 4 / 8 turns of innocent
  filler. The filler is UltraChat conversations with their own assistant replies; the
  same filler goes in front of both the harmful and the harmless request, so only the
  final request differs.
- *Score:* AUROC of each projection (harmful vs. harmless) at each depth, with
  bootstrap 95% CIs.

**3. WHY.**
We do not know whether a "harm" or "refuse" reading taken at turn 8 measures the same
thing as at turn 0. Every later claim about refusal fading while harm stays high rests on
this. If the directions drift with conversation length alone, a falling refusal reading
during an attack would mean nothing.

**4. WHAT IS AFFECTED.**
Whether the main experiment (thread T-001) can run as designed, and which reading it
can trust. No existing number changes; this is the first one.

**5. CONCLUSION IF WE DO IT.**
If both AUROCs stay ≥ 0.90 at depth 8 and fall less than 0.05 from depth 0 → claim:
"single-prompt harm and refusal directions remain valid readouts deep in a
conversation," and T-001 proceeds with them as they are.
If either falls below 0.90 or drops 0.05 or more → claim: "conversation length alone
shifts this readout," and the readout must be re-fitted per depth (or matched by depth)
before any attack result means anything. That re-fit is the next card, and the size of
the drop is itself worth reporting, since SafeDream and others assume it doesn't happen.

**6. CONSEQUENCE OF NOT DOING IT.**
The main experiment would report refusal and harm readings across turns without
knowing whether a change comes from the attack or just from the conversation getting
longer. That's exactly the confound PsychoPass (arXiv 2606.03136) found in naive
multi-turn detectors.

**Status:** closed unstarted, 2026-10-25.

**Closed with:** not a direction Saif is committing to. Knowledge editing (ai/edit-slice)
is the main line, and this would compete with it. The design above and the prior-art
notes stay here in case it's ever the right time; nothing was run, and nothing was sent to NDIF.
