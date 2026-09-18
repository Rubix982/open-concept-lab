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
