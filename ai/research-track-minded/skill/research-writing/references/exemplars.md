# Exemplars

Three published mechanistic-interpretability papers and one worked anti-exemplar.
Passages are marked by the *move* they demonstrate, not cited as authorities.

## ROME — Meng, Bau, Andonian, Belinkov (NeurIPS 2022)

*Locating and Editing Factual Associations in GPT*, arXiv:2202.05262

- **The opening question.** "Where does a large language model store its facts? In
  this paper, we report evidence that factual associations in GPT correspond to a
  localized computation that can be directly edited." Seven-word question, answered
  in the next sentence.
- **Words before symbols.** §2.1 — see `mathematics.md`.
- **Expected versus new.** "…is unsurprising, but their emergence at an early site
  at the last token of the subject is a new discovery." The paper gives away the
  predictable half of its own finding to make the other half unmissable.
- **Numbers inline.** "MLP contributions peak at AIE 6.6%, while attention at the
  last subject token is only AIE 1.6%."
- **The negative result, priced, in a footnote.** "One could also compute the
  direct effect… However, we found this effect to be noisy and uninformative, in
  line with results by Vig et al." Two sentences: the alternative a reviewer would
  ask about, named, tried, dismissed with a reason and corroboration.

## Lookbacks — Prakash, Shapira, Sen Sharma, Riedl, Belinkov, Rott Shaham, Bau, Geiger (ICLR 2026)

*Language Models Use Lookbacks to Track Beliefs*, arXiv:2505.14685

- **The opening question, again.** "How do language models represent characters'
  beliefs, especially when those beliefs may differ from reality?" Same shape as
  ROME, four years later, same group. Treat as the register's default opening.
- **Borrowed names.** pointer, address, payload, dereference — see
  `mathematics.md`.
- **The classic instance before the formalism.** The Sally-Anne test is planted
  before any mechanism is described, and every later abstraction can be checked
  against it.
- **The figure caption is the definition.** A reader who reads only Figure 1's
  caption understands the core claim. Captions carry argument, not labels.
- **Both outcomes named in advance.** "Our goal is to determine whether LMs learn a
  systematic solution to such tasks or rely on superficial statistical
  association." The paper commits, in the introduction, to a finding that could
  have gone the other way.

## Sparse Feature Circuits — Marks, Rager, Michaud, Belinkov, Bau, Mueller (ICLR 2025)

arXiv:2403.19647

- **Positioning in two sentences.** See `structure.md` §7.
- **Numbered commitments instead of signposting.** "two challenges: First… Second…"
  then solved in order, referred back to by name. No "In this section, we will"
  anywhere in the paper.
- **A footnote closing an ambiguity on first use.** "We use 'neuron' to refer to a
  basis-aligned direction in an LM's latent space (not necessarily preceded by a
  nonlinearity)." Note that the parenthetical names what is being ruled *out* —
  that is the part preventing the misreading.
- **The gap stated as a condition.** Prior methods "are not well-suited to the many
  cases where researchers cannot anticipate ahead of time how models internally
  implement their surprising behaviors." Falsifiable: if you *can* anticipate the
  mechanism, prior methods are fine, and the paper says so.

---

## The anti-exemplar — an AI-generated research report

21 pages, no authors, no venue. **It is competent, well-organised, factually
accurate, and useless.** Those properties are independent, which is the whole
lesson.

- **Topic headings, not claims.** "Background: decoder-only knowledge editing…",
  "Open gaps: coverage limits, scalability, and certification needs." Organised by
  subject coverage. None of them asserts anything.
- **Assembly, not argument.** The body is stitched verbatim quotation — in places,
  an entire published abstract pasted whole. **The document has no claim of its
  own, so nothing in it can be wrong.**
- **Gaps named, never priced.** "Open gaps" as a heading, with no statement of
  which gap matters or what closing it would cost.
- **And it passes the lint.** Measured at **0.0 hits per 10k** on the word-level
  check. No "delve", no "Furthermore", no hedge adverbs, no throat-clearing.

When a revision applied only the structural questions to one of its passages,
falsifiable-as-written claims went from **1 to 8** while length grew 18%. The
defect was never the vocabulary.

One further correction worth carrying: the passage *did* make ten claims of its
own. Nine failed on unquantified superlatives — *the clearest*, *the main*,
*most*, *one of the few*, *mostly*. The problem is not the absence of claims. It
is claims with no threshold to violate.
