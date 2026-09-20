# Findings — research-track-minded

Owned by: **Researcher**. Append-only.

---

## [R-001] Finding: Saif's research-writing voice

_Date: 2026-09-18_

A profile derived from two published posts (`the-check-that-was-never-there`,
1309 w; `five-days`, 10238 w) and two design documents (`edit-slice/design.md`,
`rome-neighbors/design.md`). Every move below is quoted from the corpus. The
first post is the cleanest specimen and most citations come from it.

**Confidence: high** on the sentence and epistemic layers — the patterns are
dense and consistent across sources. **Medium** on the section layer, since only
two long-form prose pieces exist and both are lab-note register rather than
paper register. A paper-shaped sample does not yet exist in the corpus, which is
a real gap: the skill is being tuned toward a target the corpus only approximates.

### The central mechanism: hedging is quarantined, not distributed

This is the finding that matters most, and it sharpens the project's working
hypothesis rather than confirming it.

The prose reads confident because **uncertainty is collected into named sections
and excluded from everywhere else**. `the-check-that-was-never-there` puts every
qualification into two blocks — "This is not a criticism of the benchmark" and
"Honest limits" — and the remaining ~1000 words carry almost no hedging adverbs
at all. Inside "Honest limits" the hedging is total and specific:

> **Levels depend on the candidate count.** Fifty candidates is harder than ten;
> more would be harder still. Ordering across models is robust, absolute levels
> are not.

> **Prompt sensitivity is not my finding.**

> **I have not run the constrained measure on GPT-2-XL.**

Generic AI prose does the opposite: it distributes a thin film of hedging across
every sentence ("may potentially suggest", "appears to somewhat indicate"). The
result is prose that is simultaneously less honest — no specific limit is ever
named — and less readable.

So the corrective is not "hedge less." It is **relocate the hedging**. Same total
epistemic content, concentrated. That is a mechanical instruction a skill can
enforce and check: count hedging tokens outside the limits section; the target is
near zero.

This partially answers T-001. The claim-sharpness hypothesis is not wrong, but it
was pointed at the wrong lever. Distributed hedging is the proximate cause of
flatness; an unsharpened claim is why a writer reaches for it.

### Sentence layer

1. **Short declaratives carry the load.** The heaviest sentences are the shortest.
   "That was wrong, and I want to lay out both the evidence and how I got it
   backwards." / "No model is consulted at any point in construction."
2. **Long sentences are built by coordination, never subordination.** Clauses are
   chained with em-dash or semicolon; there is no stack of nested "which" clauses.
   "Edit a fact, check whether the change ripples outward correctly — but if the
   model never held the fact you edited, a 'failed ripple' is an artifact of
   ignorance rather than a property of the editor."
3. **The em-dash marks the turn.** It is reserved for the pivot or the
   qualification that reverses direction. It is never decorative punctuation.
4. **Bold marks the load-bearing quantity or the claim itself — never a phrase.**
   "**ES = 22.2**", "**No model is consulted at any point in construction.**"
   Discipline here is what keeps bold meaningful; the corpus bolds roughly once
   per 120 words.
5. **Numbers appear inline, in the sentence, with their instrument.** Never "as
   shown in Table 4." "For unedited GPT-2-XL, the benchmark's own primary model:
   **ES = 22.2**." The table supports the number; it does not house it.
6. **Deltas over levels where the movement is the point.** "original broadcaster
   **13% → 87%**", "two-way 75%, constrained 61%, free generation 12%".
7. **Tense is split by kind.** Present for what is true ("Sampling ... is a sound
   way to get difficult targets"); past for what the author did ("I searched,
   found ... and withdrew the claim").
8. **Second-person imperative to hand the reader a move.** "Turn it around:" —
   used once, to make the reader perform the inversion rather than be told it.

### Paragraph and section layer

9. **Headers are plain speech, often a question.** "What made me withdraw it",
   "So how bad is it, really?", "How I got it wrong", "Honest limits". Zero
   nominalized academic headers ("Methodology", "Experimental Results").
10. **One job per section, then stop.** Sections run 1–4 paragraphs. There is no
    transitional sentence between them and no summary at the end of one.
11. **The conclusion arrives in the first two sentences.** "This is a correction
    to something I published four days ago. The short version: I withdrew a claim
    I should have kept." The piece then earns it. Nothing is withheld for suspense.
12. **The standfirst states the result, including the negative one.** "The edit
    finally ran and said no."
13. **Endings are an artifact plus a self-implicating admission, never a summary.**
    "I know that because an early version did exactly that, and inflated its own
    number by forty points."
14. **At most one lyric sentence per piece, placed at a boundary.** "The stars are
    real; the constellations were ours." It survives because it is rationed. A
    second one in the same piece would read as decoration.

### Epistemic layer

15. **Every claim carries a fate.** held / narrowed / withdrawn, tracked
    structurally (the `five-days` claims ledger: "Seven withdrawn or narrowed, one
    standing").
16. **Aspiration is separated from mechanism.** "The aspiration is real; the
    mechanism is sampling. Those are different things, and the difference is the
    whole argument." This is the corpus's most characteristic analytic move.
17. **The result's scope is stated as what it is *not* evidence for.** "That
    measures whether knowledge is *present*, not whether the model would
    spontaneously produce it."
18. **Prior work is credited for the part that is not new, explicitly.** "Prompt
    sensitivity is not my finding. ... What is new here is locating it inside an
    editing benchmark and pricing it."
19. **Error is reported with its magnitude and its cause.** Not "I made a mistake"
    but "inflated its own number by forty points", and "both were searching for
    *competing work* rather than re-reading the *primary source*."
20. **The fix is named and priced.** "The fix is cheap: **report possession
    alongside efficacy, measured on your model.**"
21. **Criticism is bounded before it is delivered.** "This is not a criticism of
    the benchmark" is its own section, placed *before* the damage is described.

### The X-not-Y construction — a signature with a budget

The paired contrast ("A rather than B", "A, not B", "A is real; B is sampling")
appears roughly **once per 190 words** in the cleanest sample — about seven
instances in 1309 words. It is load-bearing: it fixes a boundary by naming what a
thing is not, which is how most of the epistemic moves above are actually
executed.

It is also the single most imitable feature here, which makes it the most likely
to be overproduced into mannerism. The skill must encode it **with the frequency
budget attached** — roughly one per 200 words, never two in adjacent sentences.
Tracked as T-006.

### Negative space — what the corpus never does

More actionable than anything above. Across ~12k words of prose, these do not
appear even once:

- **Throat-clearing:** "It is important to note", "It is worth mentioning", "It
  should be emphasized".
- **Section pre-announcement:** "In this section, we will...", "We begin by...".
- **Additive connectives as paragraph openers:** "Moreover", "Furthermore",
  "Additionally".
- **Distributed hedging adverbs:** "arguably", "potentially", "somewhat",
  "relatively", "fairly" — absent outside the limits sections.
- **Register words:** "delve", "leverage" (as verb), "utilize", "robust" as
  filler, "crucial", "pivotal", "landscape", "realm", "underscores", "showcases".
- **Empty tricolons:** three adjectives where one carries the meaning.
- **Recap paragraphs** restating what the section just said.
- **Deferred numbers:** "as can be seen in the table above".
- **Reaction words:** "interestingly", "surprisingly", "notably", "remarkably".
- **Bullets where prose would serve.** Lists appear only for genuinely parallel
  items — the four Honest-limits entries, the model table. Argument is never
  bulleted.
- **Exclamation marks.** Zero.

### Gap this exposes

The corpus is lab notes and design documents. It has no paper-register sample —
no abstract, no related-work section, no formal notation passage. Two consequences:

- The **mathematics** half of the project (notation contract, words→symbols→
  instance ladder) has **no exemplar support at all** in Saif's own writing. It
  must come entirely from R-002's admired papers.
- The skill will initially be strongest at lab-note and blog register, weakest at
  the formal paper register that is the stated target. Worth accepting for v1 and
  naming, rather than pretending the corpus covers it.

---

## [R-002] Finding: the mech interp exemplar corpus, and what it fixes

_Date: 2026-09-19_

Three published papers marked at passage level in `corpus/papers/`, plus one
anti-exemplar. Selected from the six real PDFs under
`ai/lookback-research/docs/`; the three "papers" under `ai/rome-neighbors/` are
AI-generated Deep Research reports and are used as the negative control rather
than as exemplars.

**Confidence: high.** Every passage is quoted with a section and page. The
selection is narrow by design — three papers from overlapping author groups, so
the register is consistent rather than averaged.

### The gap R-001 exposed is now closed

R-001 found that Saif's corpus has no paper-register or notation sample, leaving
the mathematics half of the project with zero support. ROME supplies it. The
transferable finding:

**Unreadable generated mathematics is almost never a symbol problem. It is a
naming-and-ordering problem.** Two distinct mechanisms, from two papers:

1. **Ordering (ROME P2/P3).** Symbols arrive before the objects they denote have
   been named in English. ROME's ladder is strict — name each object by its
   function in words, bind a symbol explicitly, define the quantity as arithmetic
   on already-named things, give one concrete instance with real content, then
   gloss why the quantity means what it claims. Every defined quantity in ROME §2.1
   is a difference of two things named in the preceding paragraph. Nothing on the
   page requires holding more than two bindings at once.

2. **Naming (Lookbacks P2).** New machinery is named with words the reader already
   owns — `pointer`, `address`, `payload`, `dereference`, `lookback` — lifted from
   systems programming, where they denote the same structure. A mechanism given a
   coined abstraction forces the reader to carry an unanchored symbol for the rest
   of the paper; the same mechanism named `pointer` arrives with its semantics
   installed. This is the Premise Dry-Run's move 2 (rename into an existing
   formalism) applied to exposition rather than theory.

Corollary rule, from ROME P4: every abuse of notation gets one clause of
acknowledgement at the moment it is taken ("dependence on x is omitted for
notational simplicity"). Unannounced suppression is what makes generated
mathematics un-checkable — the reader cannot distinguish an omission from an error.

### The house opening is a plain question

ROME (2022) opens "Where does a large language model store its facts?" Lookbacks
(2026) opens "How do language models represent characters' beliefs…?" Same group,
four years apart, both answering in the next sentence. Treat as the register's
default opening, not a stylistic option.

### T-006 is answered: X-not-Y earns its keep by marking novelty

ROME P5: "The presence of strong causal states at a late site … **is unsurprising**,
but their emergence at an early site … **is a new discovery**." The paper gives away
the predictable half of its own finding to make the other half unmissable.

So Saif's paired-contrast habit is not a personal tic — it is how this literature
separates expected from new, and its job is pre-empting the reviewer who says "we
already knew that." The frequency budget from R-001 (~1 per 200 words) stands, but
the constraint is now sharper than a rate: **use it where the two halves are
genuinely expected-vs-new, and it will not overfire.** Used for mere emphasis, it
degrades to mannerism. A semantic test beats a token count.

### The anti-exemplar names Saif's actual complaint

The Deep Research report is **accurate and useless**, and those are independent
properties. It fails on three things, each the inverse of an R-001 finding:

| Failure | Diagnostic question | R-001 counterpart |
| --- | --- | --- |
| Organised by topic coverage, not argument | Can each heading be rewritten as a sentence with a truth value? | move 10, one job per section |
| Stitched verbatim quotation; no claim of its own | What in this document could turn out to be false? Zero fails. | move 15, every claim carries a fate |
| "Open gaps" listed, never priced | Which gap, what would closing it cost, what would it change? | move 20, the fix is named and priced |

The second is the load-bearing one. **A document with no falsifiable claim is
exactly what "you gave me a lot of text and I don't know what to do with it" feels
like from the inside** — there is no action item because there is no position.
That reframes the project's output-contract problem: the missing action items are
a symptom of a missing claim, not a formatting defect.

### Where the exemplars are weaker than Saif

ROME's limitations discussion is thinner than `the-check-that-was-never-there`'s
five-item "Honest limits". On the hedging-quarantine axis — R-001's central
finding — **Saif's own writing is the better exemplar** and the skill should not
defer to the papers there.

### Deferred, with reasons

- **MEMIT** — same authors and register as ROME; adds notation volume, not a new
  move. Pull in if the notation contract needs more worked instances.
- **NNSight / NDIF** — systems and tooling register, a different document type.
  Revisit if the skill grows a tool-paper mode.
- **Unified Concept Editing** — diffusion, not LM mech interp. Off-target for v1.

---

## [R-003] Finding: the deletion list, and why a word list is not the deliverable

_Date: 2026-09-20_

Twenty entries in `corpus/deletion-list.md`, each with the banned construction, an
invented example, and the replacement. Split into a lintable Tier 1 (12) and a
structural Tier 2 (8). R-001's negative space was a qualitative read; this ticket
measured it.

**Confidence: high** on the measurement (fifteen regex probes over 110k words,
instruments committed at `agents/researcher/findings/negspace.py` and
`control.py`, output at `logs/r003-negspace-2026-09-20.log`). **Medium** on the
Tier 2 entries, which are argued from the exemplar passages rather than measured
and are the part most likely to need revision after first use.

### The measurement confirmed R-001 and then undercut the obvious next step

| Body | Words | Hits per 10k |
| --- | ---: | ---: |
| Saif's corpus (5 documents) | 20,481 | **0.0** |
| Published exemplars (ROME, Lookbacks, SFC) | 50,819 | **9.6** |
| AI-generated reports (3, `rome-neighbors/`) | 38,773 | **14.7** |

**Saif's corpus is at literal zero**, not "almost none" as R-001 estimated. Fifteen
probes, 20k words, no hits. The three apparent matches were `<!-- truncate -->`
HTML comments (×2) and one descriptive use of "showcased". Checked by hand.

**The separation that matters is not there.** Exemplars to anti-exemplar is 9.6
against 14.7 — a factor of 1.5, which is not a usable discriminator. ROME,
Lookbacks and Sparse Feature Circuits between them use "crucial" 13 times,
"Furthermore" 9 times, and pre-announce sections 6 times. A lint tuned to flag the
AI reports flags three ICLR/NeurIPS papers nearly as hard.

So the deletion list is **Saif's house standard, stricter than the literature he
is writing toward** — a real and usable finding — but it is **not a quality
detector**, and the project should not pretend otherwise. What makes the AI
reports useless is invisible to every probe run here.

This is the R-003 equivalent of the headline-versus-components problem: the
headline ("the corpus avoids these constructions") is confirmed, and reading the
component quantities is what shows the intended application does not follow from
it.

### Consequence for the design

Tier 1 stays, as a cheap floor that runs in seconds over a finished draft. Tier 2
carries the project. Its eight entries are stated as **questions asked of the
draft's structure**, because no regex reaches them:

1. Can this heading be rewritten as a sentence with a truth value?
2. What in this paragraph could turn out to be false?
3. Which gap, what would closing it cost, what would change?
4. Was this object named in English, by its function, before it got a symbol?
5. Is every suppressed term acknowledged where it is suppressed?
6. Does an existing vocabulary already denote this structure exactly?
7. Is any qualification appearing outside the limits section?
8. Has the scope of this criticism been fixed before the damage is described?

These are closer to the design lenses than to copy-editing. **If one entry
survives into the skill it is #2** — the falsifiability question, which is the
defining absence in the anti-exemplar and the thing R-002 identified as the source
of "a lot of text and I don't know what to do with it."

### Partially answers T-007

A hedging lint would find nothing on the corpus, because the corpus is already at
zero. Its value is entirely on the **draft**, not as a corpus-derived threshold —
there is no ratio to calibrate against, only a target of zero. That makes it
cheaper to build than T-007 assumed, and less informative. A token list is
sufficient for Tier 1; the syntactic hedging T-007 worried about ("tends to suggest
that") belongs to Tier 2 entry 19 and will not be caught by a list.

### What this does not establish

The Tier 2 questions have never been run against a real draft. They are derived
from eight passages and one negative control, which is enough to state them and
not enough to know they change an output. **The first E- ticket should test them
on a draft before any of this is packaged as a skill** — otherwise the project
will have built the polished frame that the Premise Dry-Run warns about.

---

## [R-004] Finding: the gap is not search, it is the verdict — and the verdict is a claim

_Date: 2026-09-20_

[T-004] assumed design lens 2 has no search behind it. It does. The diagnosis below
replaces that premise.

**Confidence: high** on the defect, which is read off three documented events in the
repo. **Medium** on the proposed fix, which is argued rather than tested — the same
status the skill's Tier 2 had before E-001.

### The practice is already good, which changes the question

`rome-neighbors/design.md` §2 contains: three Asta probes; implementation-level
checks of the two nearest competitors (Kim et al. — no hop breakdown, no causal
metric, synthetic models only; Jeong et al. — aggregate portability, no patching);
a scoop risk **revised on evidence** from moderate-high to moderate; a new nearest
competitor surfaced on probe 2; and an explicit limit that the NDIF scan is
"CONFIRMATORY, not exhaustive". `threads.md` adds a second round described as
"verified vs source".

That is better than most published related-work sections. **A tool that searches
harder solves nothing here.**

### The three failures that did happen

**1 · Misreading a primary source, framed as a search problem.** From
`the-check-that-was-never-there`: *"Two separate literature passes and neither caught
this, because both were searching for competing work rather than re-reading the
primary source. I had the ROME paper open in a directory on my own machine the
entire time. The appendix was three pages from the sentence I misread."*

Two passes of *search* could not catch a defect in *reading*. The claim was withdrawn
and then un-withdrawn — a full round trip, four days, caused by treating a paper's
aspiration as its mechanism.

**2 · Work shelved on an unverified verdict.** From `rome-neighbors/threads.md`:
*"Fork A (removal-reliability) shelved: its scoop verdict was unverified by the
search."* A whole fork was abandoned on a verdict the notes themselves record as
unverified.

**This is the costliest failure of the three, and it is invisible.** The errors are
asymmetric: a false *"open"* verdict gets caught later, when the competing paper
turns up or a reviewer names it. A false *"scooped"* verdict kills the work
silently and no evidence of the mistake is ever generated. Nothing in the practice
prices that asymmetry.

**3 · The practice does not transfer.** `edit-slice/design.md` has no §2 with
anything like that depth. Whatever makes `rome-neighbors` good lives in one
document, not in a method.

### The unification: a prior-art verdict is a claim, so the claim audit already covers it

"Novelty confirmed" is an assertion that can be wrong. Stated bare it is exactly the
defect this skill was built to catch — a claim with no falsifier, unfalsifiable as
written, indistinguishable from an opinion.

And the good practice already satisfies the skill's own rule without naming it:

> **Lane CONFIRMED OPEN (Asta probe 1)** — Kim et al. measures logical generalisation
> as a single aggregate over entailed facts (no hop breakdown), uses only behavioural
> accuracy + probing (no causal metric), and runs on synthetic from-scratch models only.

That verdict names precisely what would refute it: a hop breakdown, a causal metric,
or a pre-trained model in Kim et al. A reader can check it. **The difference between
`rome-neighbors` §2 and `edit-slice` §2 is not search effort — it is that one states
falsifiers and the other does not.**

So [T-004]'s three-way question resolves:

- **Search tooling** — outside the skill. Asta and Semantic Scholar exist and he uses
  them. Building a search tool would be the Compass's difficulty-trap.
- **The design protocol** — keeps lens 2 as the trigger for *when* to look.
- **This skill** — owns the **verdict**, because a verdict is a claim and the claim
  audit is already the instrument for claims.

### The change, minimal

A **positioning audit** — the Pass 1 table, applied to novelty claims, with one
column the prose audit does not need:

| Verdict | What it rests on | What would refute it | If wrong, what does it cost? |

The fourth column exists only because of failure 2. It forces the asymmetry to be
visible at the moment the verdict is made:

- A wrong **"open"** verdict costs a rejection or a reviewer's citation. Recoverable.
- A wrong **"scooped"** verdict costs the project, silently, with no evidence ever
  produced that it was wrong.

**Therefore the evidence bar is asymmetric**, and that is the rule worth stating:
shelving work requires *stronger* evidence than proceeding with it. An unverified
scoop verdict is not grounds to shelve — it is grounds to verify. Fork A should have
been blocked on a verification, not shelved.

### One more rule, from failure 1

**When a verdict turns on what a paper *did*, read its methods or appendix, not its
prose.** Aspiration and mechanism live in different sections and only one is binding.
This is already written in Saif's own post as "the narrow lesson"; it has never been
in a checklist.

### What this does not establish

The positioning audit has not been run on anything. It is derived from three events
in one repository, by the author of the skill, and the fourth column in particular is
argued from a single instance of Fork A. **The honest next step is to run it on
`edit-slice`'s §2, which is the one that lacks depth** — if it produces nothing there,
the diagnosis is wrong.

Nothing here has been tested against the possibility that `rome-neighbors` §2 is good
because that project was at a stage where positioning mattered, and `edit-slice` §2 is
thin because it did not need one. That is a live alternative explanation and it is
unexamined.

---

## [R-004] Correction: failure 3 is refuted, and the fix gets smaller

_Date: 2026-09-20 · corrects the entry above, written an hour earlier_

The entry above named its own falsification test — *run the positioning audit on
`edit-slice` §2, and if it produces nothing the diagnosis is wrong.* Run. It
produced nothing, and one of the three failures does not survive.

**Failure 3 — "the practice does not transfer" — is wrong.** I claimed
`edit-slice/design.md` §2 lacks `rome-neighbors`'s depth. It does not:

> Knowledge-conflict survey 2403.08319 names editing as a cause of *intra-memory
> conflict*, but defines that as **paraphrase inconsistency**, not justification
> contradiction … Deferral literature triggers on **uncertainty**, not
> underdetermination. AGM→LLM transfer unclaimed (2608.14567 is purely symbolic).

Every one of those names what would refute it: find a paper defining intra-memory
conflict as justification contradiction, or a deferral method triggering on
underdetermination, and the positioning falls. It also carries a section
`rome-neighbors` lacks — **"Remaining scoop surface: EasyEdit and other toolkits not
inspected directly. T-003 unchecked."** — which states coverage limits at the point
of the verdict.

So the claim that one project states falsifiers and the other does not is **false**,
and the transfer story built on it goes with it. Both sections are good, in
different ways, and neither is the model for the other.

**How I got it wrong.** I read `rome-neighbors` §2 in full and `edit-slice` §2 only
by `grep`, which returned no hits for "Asta" or "scoop" in that file and I read the
absence of my search terms as the absence of the practice. `edit-slice` does the same
work under different vocabulary. **That is the identical error the [R-004] entry
above diagnoses in failure 1** — searching for the terms I expected instead of
reading the source — committed while writing the diagnosis of it.

**What survives, and it is the whole finding now:**

1. **Misreading a primary source**, documented, cost four days and a round-trip
   retraction. Search cannot catch it; reading the methods section can.
2. **Fork A shelved on a verdict the notes call unverified.** The asymmetry stands
   on its own and never depended on failure 3: a wrong *"open"* verdict surfaces
   later, a wrong *"scooped"* verdict kills the work silently and generates no
   evidence it was wrong.

**The fix shrinks accordingly.** Not a positioning audit competing with practice that
is already good — **two rules**, both about what licenses a verdict rather than about
coverage:

> **Shelving requires stronger evidence than proceeding.** An unverified scoop
> verdict is grounds to verify, not grounds to shelve.

> **When a verdict turns on what a paper *did*, read its methods or appendix, not
> its prose.** Aspiration and mechanism live in different sections and only one is
> binding.

Smaller is the right direction here — the Premise Dry-Run's rule 3 says prefer the
reframe that makes the work smaller, and a two-rule change that leaves both existing
§2 practices untouched is a much better fit to the evidence than a new audit table.

**Still unexamined**, and unchanged by this correction: whether `rome-neighbors` §2
is thorough because that project was at a stage where positioning mattered. Both
sections being good makes that alternative *more* plausible, not less — depth may
track project stage rather than any method.

---

## [R-005] Finding: borrowed names are a bet with an invisible downside

_Date: 2026-09-20_

Resolves [T-009]. The skill says borrow when the borrowing is "exact, not
evocative" and supplies no way to tell. This is the test, its derivation, and where
it fails.

**Confidence: medium.** The test reproduces four judgements, three of which were made
before it existed — which is evidence it describes the criterion actually in use, not
that the criterion is correct. All four cases are ours and none is adversarial.

### Why the rule needs a default, not just a threshold

A name is a channel for inferences the reader draws **without being told**. That is
the whole value of borrowing and the whole risk, and the two are not symmetric:

| | reader's state | cost of being wrong |
| --- | --- | --- |
| **coined term** (`Deferred Retrieval Coefficient`) | knows they do not know; goes and reads the definition | friction, and the error is caught at the definition |
| **exact borrowing** (`pointer`) | gets the semantics free and correctly | none — this is the payoff |
| **inexact borrowing** | gets the semantics free and **wrongly**, and does not know it | silent error, in the reader and usually in the writer too |

A coinage fails loudly; a bad borrowing fails quietly. **So under genuine
uncertainty about exactness, coin.** The skill currently encourages borrowing
without saying what to do when you are unsure, which is the case that matters.

### The test: enumerate the free inferences

Before borrowing a name from another domain:

1. **Write down three things a reader will infer from the name without being told.**
   Not what you mean by it — what the source domain licenses.
2. **Mark each: holds / fails / untested** in your target.
3. **If a *relied-on* inference fails, do not borrow.**
4. **If an inference fails that you do not rely on, borrow and spend one clause
   saying where the analogy stops.**
5. **If you cannot produce three, you do not know the source domain well enough to
   borrow from it.** Coin instead.

**"Relied on" is made checkable by Pass 1**, which is the only reason step 3 is not
a hand-wave: an inference is relied on if it appears in a claim you make. If it
never enters a claim, you do not rely on it. That test can be applied by a reader,
and it stops "relied on" from being gerrymandered after the verdict.

Step 5 is a competence gate and it is the cheapest of the five. Borrowing from a
field you half-know is where inexactness comes from.

### Against the four cases

**1 · `pointer` / `address` / `payload` — LICENSED.** Free inferences: dereferencing
retrieves the payload (holds, relied on); the pointer is a copy of reference
information rather than the thing itself (holds, relied on); many pointers may share
one address (untested, not relied on). One untested inference, not relied on →
borrow, note where it stops.

**2 · "history is already a simulator" — NOT LICENSED.** Free inference: replaying a
different policy over the record yields the true outcome. In Dream-RSI it holds —
every node was executed and its result recorded. In a ticket record it **fails**: the
branch not taken has no outcome. And it is exactly the inference the borrowing would
rely on. → Do not borrow. Matches [T-011], decided before this test.

**3 · Depth-psychology vocabulary for an LM — NOT LICENSED.** Free inferences:
contents inaccessible to the system yet causally active (arguable); a mechanism that
put them there, repression (**fails** — no such mechanism); they can be surfaced by
analysis (**fails**). Using the word at all relies on the second. → Do not borrow.
Matches `CLAUDE.md`.

**4 · "certification" — NOT LICENSED.** Free inference: the process yields an
artifact a third party can check without repeating the work. Nothing in the knowledge-
editing literature proposes that. "Certification layer" relies on it — the word is
doing the work of promising a guarantee. → Do not borrow; "regression suite" is the
exact term. Matches `e005/02-draft.md`.

### Where this test fails

**Four cases, all ours, none adversarial.** Three predate the test, which is the only
thing keeping this from being a post-hoc fit — but a test built to reproduce four
decisions will reproduce four decisions. It has never been run on a borrowing someone
else defended.

**Step 1 is the weak joint.** "Three things a reader will infer" depends on which
reader. A systems programmer and a statistician draw different free inferences from
`pointer`. The test gives no way to fix the reader, and in practice the writer will
imagine a reader who agrees with them.

**It cannot catch a borrowing that is exact and still bad.** A name can pass every
step and import an unhelpful *frame* — the structure holds, and the reader still
attends to the wrong thing. Nothing here addresses that.

**Untested prediction, stated so it can fail:** applied to a borrowing I have not
already ruled on, the test will most often return *untested* rather than a verdict,
because free inferences about a novel target are usually unmeasured. If that happens
the test is a prompt for experiments rather than a gate, which is a different and
less useful thing than it currently claims to be.

---

## [R-006] Finding: claim-lock does not create action items — it makes hollow ones executable

_Date: 2026-09-20_

Resolves [T-008]. Counted on [E-001]'s pair, which was run before this hypothesis
existed and treated with the Tier 2 questions only, so nothing was optimising for
action items. Definition fixed before counting, and deliberately independent of
falsifiability to avoid guaranteeing the result: *a sentence from which a reader can
write a task with a verb and an object.*

**Confidence: medium.** One document pair, scored by me, every item enumerated below
so the count can be checked rather than trusted.

### The counts

| | action items | words | per 1,000 |
| --- | ---: | ---: | ---: |
| baseline | **7** | 472 | 14.8 |
| treated, body only | **10** | ~458 | 21.8 |
| treated, incl. Limits | **13** | 558 | 23.3 |

Pre-stated CONFIRM was a material rise with a material share outside Limits. Both
hold: 7 → 13 overall, and 10 of 13 sit outside Limits. The per-word rate rises 47%
in the body alone, so this is not a length artifact.

### The premise of [T-008] was wrong, and that is the finding

**The baseline is not actionless. It has seven action items**, including a literal
imperative: *"Use GradSim as a pre-edit risk score or triage signal."* The hypothesis
— no action item because no position — predicted roughly zero. It is not what a
count shows.

What the baseline's action items lack is **executability**. Take the imperative
above. You cannot use GradSim as a pre-edit risk score, because doing so needs a
threshold and false-accept and false-reject rates at that threshold, and none exist
anywhere in the source. The instruction is well-formed and cannot be carried out.
The same holds for "compute a risk estimate before trusting an edit broadly" and
"build a certification layer" — each names a verb and an object and none can be
started tomorrow.

The treated version's items differ in **kind**, not only in number:

- read Qin et al. directly rather than through the summary
- find the effect size, which appears nowhere in the source
- check whether Su et al. already draws the detect/predict/certify distinction
- replace "certification" with "regression suite"
- report GradSim's distribution alongside edit-success rates
- price the enumeration of entailed neighbours: one forward pass per candidate, plus
  a candidate generator nobody has published

Every one of those could be done tomorrow, by a named action, with a knowable result.

**So the mechanism is not that claim-lock manufactures action items from nothing. It
is that a hollow imperative rests on a claim with no threshold to violate, and
sharpening the claim is what exposes the hollowness.** "Use GradSim as a risk score"
survives only as long as "strongly correlates" goes unexamined. Ask what would
falsify it and the missing operating point surfaces, and the instruction either
acquires a threshold or is replaced by the task of going to find one.

This connects directly to [R-002]'s observation that nine of the baseline's ten
own-claims failed on unquantified superlatives. **An unquantified claim supports an
unexecutable instruction.** They are the same defect at two removes.

### Consequence for the project

The fourth problem from the original scope split — *"you give me a lot of text, I
don't know what to do with it"* — **should not get a separate output contract.** A
contract appending "decisions and next actions" to a document with hollow imperatives
would produce a tidy list of things that cannot be done, which is worse than no list:
it looks like progress.

Pass 1 already addresses it, and the skill should say so rather than leaving the
connection implicit.

### What this does not establish

- **One pair, one topic, one scorer.** [E-003] and [E-005] produced drafts with no
  baseline to compare against, so they contribute nothing here.
- **The boundary between "hollow" and "executable" is mine and was not pre-stated.**
  The *count* was pre-registered; the kind distinction was found while counting and
  is therefore post-hoc. It is the more interesting half and the less defensible one.
- **A hostile reading:** I scored 7 for the baseline partly by counting method
  descriptions ("Qin et al. propose GradSim, the cosine similarity between…") as
  licensing "compute GradSim". A stricter scorer would put the baseline lower and the
  rise would look larger. I chose the reading less favourable to the hypothesis and
  it still confirmed, which is the only reason to trust the direction.


---

## [R-003] Correction: the lint was case-sensitive, and the reference rates were wrong twice over

_Date: 2026-09-20 · corrects the rates in the [R-003] entry above_

Found by running the skill the way a stranger would — system `python3`, unrelated
working directory, a throwaway file of deliberately bad prose. Three of six planted
constructions were missed: *"It is important to note"*, *"As shown in Table 1"*,
*"The main contribution"*. **Every rule was case-sensitive**, which exempted the
sentence-initial form of each — the form in which they most often appear.

It survived every prior test because Saif's corpus contains none of them and the
[E-001] baseline's hits all happened to fall mid-sentence. A test set drawn entirely
from real documents never exercised the capitalised case.

Fixed by compiling all rules with `re.IGNORECASE`, and by re-anchoring the additive
connective from **line**-initial to **sentence**-initial.

**Re-measured, and the rates move in the direction that argues against the lint:**

| body | words | old | **new** |
| --- | ---: | ---: | ---: |
| hand-written research prose | 27,735 | 1.3 | **0.0** |
| published mech interp papers | 50,821 | 11.6 | **5.1** |
| AI-generated reports | 38,773 | 13.9 | **6.4** |

The paper and report figures **fell by half** because the old line-anchored rule fired
on "Moreover" wherever a PDF line-wrap happened to put it, mid-sentence included. Those
numbers were a text-extraction artifact.

Two consequences. The hand-written corpus is now at **literal zero across 27.7k words**
under a stricter lint, which strengthens [R-001]. And the separation between published
papers and AI slop narrows from 1.2× to **1.25×** — no better, and now measured
correctly. **[T-010]'s answer of "no cheap discriminator" is confirmed by a cleaner
instrument, not weakened by it.**

Regressions held in both directions: the [E-001] baseline rose 58.9 → 78.6 as it began
catching *"The clearest"*, and no new hit appeared anywhere in the hand-written corpus.
