# Overnight log (2026-10-25)

What changed during the run, and why. Kept so a fixed method doesn't look like it was
never wrong.

1. **Object read-back, v1 → v2.** v1 took the token with the largest absolute
   probability gain at any relation prompt. On the first two E1 rows it returned "the"
   both times: common words move a lot in absolute terms. v2 scores each token by its
   positive pointwise KL, p_s·log(p_s/p_b), summed over all 34 relation prompts and 3
   prefixes. On a dev split of 25 edits (seed 7, no overlap with E1's seed-0 sample),
   five rules scored 18–20/25 on exact first-token match. Rule B (summed pointwise
   KL) tied for best and is the simplest, so it was adopted. Most misses are near
   misses (chemist→"chemistry", Ukrainian→"Ukraine"), so the reports give both top-1
   and top-3. E1 was restarted after the change; no v1 numbers are reported.

2. **Open-vocabulary subject search, v1 → v2.** v1 used a greedy right-to-left beam
   scored by raw fire strength ||kᵀΔ||/||k||. It returned junk ("の魔 LakshRepl"):
   off-distribution keys can fire harder than the real subject. Switching the score to
   |cos(k, k̂)| with k̂ = C·u₁ (the key ROME built the update for) fixed the score: the
   true subject scores 0.94–0.98 versus 0.43–0.59 for the best string the beam found.
   That left the search as the failure. Replacing the beam with gradient-guided token
   search (GCG) recovers the subject's last word on 4/4 dev edits, but first names come
   out garbled.

3. **One job at a time.** Running two experiments at once pushed the machine into
   heavy swap (28.6 of 29.7 GB used). Other apps hold much of that memory and were left
   alone. Everything now runs from `experiments/queue.sh`, one job at a time.

4. **Batch score, fire → subspace.** On the original batch trials, fire strength was
   fooled by look-alike names ("Amiata Records", "Nilva Records" when one "…Records"
   was planted). Scoring each candidate by the share of its key inside span(C·U) took
   the worst trial from 13% to 90% (`experiments/batch_dev.py`). The score was picked
   on those trials, so a held-out re-run on fresh seeds (`exp2_evasion.py batch2`) was
   written but **not run**. The report counts only the fire-strength numbers.

5. **Self-ablated reference for read-back.** Under noise or fine-tuning, comparing the
   suspect against the clean base shows changes everywhere. Removing the top rank-one
   part of the suspect's own diff gives a reference with the same noise. It was added
   for the fine-tune run (8/12 → 10/12 at 300 steps). The noise re-run with it was not run.

6. **Stopped early (12:18).** After the fine-tune job, the direction changed (threat
   model narrowed; next project is multi-turn refusal on NDIF). Not run: gpt2 and
   gpt2-large replications, exp3 full open-vocab run, exp4 base-free self-comparison,
   noise re-run, batch2 held-out. Each script still works; `experiments/queue.sh` lists them.
