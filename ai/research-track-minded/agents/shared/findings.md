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
