# Knowledge editing → the consistency seam: a trajectory

_Walkthrough for Arnab · 2026-08-25 · Saif Ul Islam_
_Goal of this talk: explain HOW I got here — what I tried, what it showed, why the
question changed, and what I want to build next. Slow and honest. I want your hard
questions._

_(Supersedes `DECK.md` (the geometry-predictor deck) — that framing is now archived;
this deck explains why.)_

---

## 0 · What I want out of this conversation (30s)

Not "approve my plan." I want you to **pressure-test the trajectory**: the pivot I
made, whether the new question is real, and whether the first experiment is the right
one. I've written down the hardest questions I could think of and my honest answers —
I'd like you to try to break them.

Three things I'll cover: **(1)** what I experimented with and what it actually showed,
**(2)** the reframe that changed the question, **(3)** the current goal + the one
experiment that makes-or-breaks it.

---

## 1 · Where I started (1m)

**The question:** when you edit a fact into a model (ROME/MEMIT), do its logically
**entailed** neighbours update too? (Edit "Eiffel Tower is in Rome" → does "country of
the Eiffel Tower" become Italy?)

**Why it looked important:** the field says editing *fails* here — a ROME-edited GPT-J
answers only **7.6%** of MQuAKE multi-hop questions. So editing looked like a shallow
patch, not a real belief change. My plan: **predict, from the model's internals,
which neighbours an edit will break** — a pre-flight diagnostic.

---

## 2 · What I actually built and ran (3m — take this slow)

I did the unglamorous part: got real editing running end-to-end on a laptop and
measured propagation against ground truth. Findings IDs in brackets are in
`agents/shared/findings.md`.

**Infra I had to get right first (the part that ate the time):**
- **NDIF** (remote GPT-J) regressed mid-work — a post-outage whitelist bug; I isolated
  it, reported it to your Discord, it got fixed. [E-006]
- Established empirically that **NDIF can't do iterative weight edits** — one
  forward/backward per job; real editing has to be *local*. [E-012]
- Stood up **EasyEdit** locally: isolated venv, `device=cpu`, `num_workers=0` (macOS
  spawn couldn't pickle the covariance collate_fn), and — the bug that cost the most —
  EasyEdit **silently rolls back the edit** before you can query it
  (`restore_after_edit`); monkeypatched it off. After that, **all 5 controlled ROME
  edits flipped (efficacy = YES)**. [T-015]
- gpt2-medium **NaNs at the logits** on this Mac in both stacks → had to use
  gpt2-small (weak, but real). [E-012]

**Result A — I reproduced the ripple failure on my own stack** [E-012] (FT-L, gpt2-small):

| neighbour type | propagated |
|---|---|
| paraphrase | 18.8% |
| 1-hop | 20.0% |
| **2-hop** | **0.0%** |
| locality (should NOT change) | 4.0% (preserved ✓) |

→ propagation **decays with hop distance**, locality mostly intact. The known
phenomenon, on my pipeline.

**Result B — real ROME (with covariance), 3-way per-neighbour outcome** [T-015]:

| type | outcome |
|---|---|
| paraphrase | **updated 5/5** (edit generalizes cleanly) |
| 1-hop | broken 4, stale 1 |
| 2-hop | updated 3, broken 2 |
| locality | fine 4, **broken 6 (~60% leak)** |

Three things here were *not* obvious:
1. **Non-monotone:** 1-hop (country) breaks *more* than 2-hop (language). Naive
   hop-decay is wrong.
2. **Over-propagation, wrong granularity:** the edit pushes the target *city* into the
   *country* slot (Louvre→Madrid ⇒ "country of Louvre" = "Madrid").
3. **Target-bleed:** the edit leaks into unrelated facts (Big Ben→Berlin ⇒ "Eiffel
   Tower is in" = "Berlin").

**Result C — can geometry predict propagation? Raw distance vs. structure.**
The field's insight is that it's **not raw *distance*** but ***structure*** that should
predict (Nishi: distance→shattering; Kim/Jeong: structured geometry). So I demoted raw
distance to a **baseline** and built a structured predictor. **And then I found GradSim
(Qin et al. 2024) already predicts ripple from gradient similarity** [T-016] — my
"novel core" was partly scooped.

**The structural run — did structure beat distance?**
`sep = mean(cos over propagate-types) − cos(locality)`; sep > 0 = separates.
[E-011 / E-011b, RippleEdits popular, 171 pairs]

| setting | raw distance | structured |
|---|---|---|
| gpt2-small · mean-pool | +0.006 | −0.001 |
| gpt2-medium · mean-pool | ~0 | ~0 |
| gpt2-medium · last-token | +0.007 → +0.019 | ~0 |
| GPT-J · last-token [E-007] | +0.06 | — |

**Read:** structured **never beat raw** (sep≈0 everywhere; slightly negative on gpt2-small).
Raw is only weakly informative, and only with the right **readout** (last-token; mean-pool
washes out — cos≈0.99 for every type incl. locality) and more **capacity** (GPT-J ≫
gpt2-medium). Separate per-neighbour test against *real* propagation labels: raw cosine
AUC 0.68 [E-013]. Net: no geometry predictor wins yet — this pushed me off the predictor
framing. (Proxy caveat: sep is type-separation on the *unedited* model; small n → suggestive.)

---

## 3 · The reframe — the question was wrong (2m, the crux)

Two things collided:
- The **MEMIT figure**: MEMIT holds ~90 "editing score" at 10K edits. Editing
  *isn't* broadly breaking models.
- The **ripple failure** is specifically **multi-hop**.

The resolution (the insight): **I was grading editing on RAG's exam.** [T-017]

> Editing changes what the model **believes** (persistent, on-device, removable —
> reasons *from*). RAG supplies what it **reasons over** at inference. Different
> functions, different metrics. Multi-hop composition is RAG's job. Editing succeeding
> at belief (MEMIT ~90) and failing at multi-hop are **not a contradiction** — they're
> two different jobs.

So "make editing pass the multi-hop exam" was the wrong goal. **Editing and RAG are
complementary, not competitors.** (Confirmed in the literature — Liu et al. 2025,
Zhang et al. 2025.)

---

## 4 · The real gap — and it's a systems problem (1.5m)

If real deployments use **both** stores — edit for belief, retrieve for reasoning —
then the unowned question is: **do the two stores agree?**

They can silently contradict:
- model asserts its **stale parametric belief** while the RAG index holds the fix, or
- model **retrieves the fix and ignores it** ("edit skipping", Liu et al. 2025).

**No current metric catches this.** Editing benchmarks probe weights only; RAG
benchmarks probe retrieval only. Nobody checks the **seam**.

---

## 5 · Current goal — the consistency-certifier (2m)

Build the check nobody has built: probe both stores on an update's queries, **detect**
parametric↔retrieval contradictions (+ which store the model actually uses),
optionally **reconcile**, emit a **scoped consistency certificate**.

```
update ─▶ ROUTE ─▶ APPLY ─▶ PROBE ─▶ [DETECT] ─▶ (RECONCILE) ─▶ [CERTIFY]
         └──── DMM Gov (adopted) ────┘   └──── novel: build + measure ────┘
```

**Honest positioning:** the architecture is *already specified* — Zhang et al.'s
**DMM Gov** describes exactly this coordination loop with "long-horizon consistency"
as a desideratum. **They specify it; nobody builds or measures it.** My claim is
"first to **build and empirically certify** it," never "first to conceive." [T-018]

---

## 6 · The one experiment that makes or breaks it (1.5m)

Before building the full system — the **significance gate**:

> Do realistic hybrid updates actually create silent contradictions, at a rate that
> editing-only and RAG-only metrics **miss**?

**The deliverable = one figure:** silent-contradiction rate, split three ways —
(i) what editing-metrics miss, (ii) what RAG-metrics miss, (iii) what the certifier
catches. If the problem is real, bars (i)+(ii) are tall and (iii) recovers them. **If
it's ~0, I publish the negative and stop** — cheap kill, honest result either way.

Setup: gpt2-xl/GPT-J + a small FAISS store, ROME edits, constructed contradiction
ground-truth (edit P→X, leave retrieval at Y≠X; agree-pairs as negatives).

---

## 7 · What I'm asking you (1m)

1. **Is the reframe right?** Editing = belief, RAG = composition, and the seam
   (consistency) is the real gap — do you buy it, or am I rationalizing a pivot?
2. **Systems, or systems + science?** Foreground just the certifier, or also the
   "how far does a belief-edit legitimately carry" science underneath (T-006)?
3. **Compute + prior art:** GPU substrate for gpt2-xl/GPT-J + FAISS (Colab vs cloud)?
   And — do you know work that already *builds/measures* cross-store consistency? (I
   only found it *specified*.)

---

## Appendix · Hard questions — my honest answers (be ready)

**"Why edit weights at all? Just use RAG."** Category error — different functions
(§3). And KEEP's whole point is systems use *both*; "editing vs RAG" is the wrong
question, "do they agree?" is the right one.

**"Zhang et al. already specified this. What's new?"** They specify; I build + measure.
A number for how often stores contradict, whether current metrics miss it, whether
reconcile helps. Say "first to build/certify," never "first to conceive."

**"Are you inventing a problem? Does the contradiction happen?"** That's the FIRST
experiment (§6), pre-registered with a null branch. If it doesn't happen, I say so.

**"Reconcile has its own ripple — whack-a-mole / convergence?"** Empirical, deferred
to v2; if it doesn't converge, the system degrades to detect+certify+flag — still a
deployment gate.

**"Even if stores agree, do you know what the model will answer?"** That's
`which_wins`, built on edit-skipping (Liu et al.). If unpredictable → narrow the
certificate to store-agreement, drop the behavioural claim. Honest scope, not a hollow
guarantee.

**"gpt2-small is a toy."** Agreed — v1 on it is a pipeline-validity proof, explicitly
caveated; the real regime (gpt2-xl/GPT-J, sequential) needs a GPU. Open item.

**"Does it scale to 10K edits?"** No — v1 is small-batch high-assurance (regulated /
on-device single-fact updates). A real niche, not mass editing. I don't overclaim it.

**"Isn't the evaluation circular?"** Contradiction is defined from parametric + 
retrieval answers only; the full-system answer is used *only* for which-wins, never to
define the contradiction. Firewalled in code.

**"What did the ROME/predictor work buy you if you pivoted?"** The pipeline (real edits
→ per-neighbour ground truth → evaluator), the honest negative on raw-geometry
prediction, and the reframe itself. The evaluator + slot-matcher are reused in the
certifier's detector. Nothing wasted; the trajectory produced the insight.

---

## One-line summary

> I set out to predict which edits break neighbours; the data + the MEMIT figure
> showed I was grading editing on RAG's exam; the real, unowned gap is whether a
> hybrid system's **edited belief and its retrieval store agree** — and I want to
> build the first check that measures it, starting with whether the problem is even
> real.
