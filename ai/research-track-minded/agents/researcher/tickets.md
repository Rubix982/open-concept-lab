# Researcher Tickets — research-track-minded

### R-001 · Voice profile from Saif's own corpus

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-18
**Updated:** 2026-09-18
**Estimated:** 3h

**Description:**
Derive an explicit, citable profile of Saif's research-writing voice from the
strongest existing samples in `open-concept-lab`. Not impressions — named moves,
each with a quoted instance and a file citation, so the skill can be written
against evidence rather than taste.

Sources (ranked by quality of sample, all paths relative to `open-concept-lab/`):

1. `web/blog/2026-09-14-the-check-that-was-never-there.md` — 1.3k words, the
   single cleanest specimen. Complete argument arc: correction → evidence →
   mechanism → limits.
2. `web/blog/2026-09-15-five-days.mdx` — 10k words, the accumulating record.
   Shows the register at length and under structure (Claim components, figures).
3. `ai/edit-slice/design.md` — 8.1k words, design-register rather than prose.
4. `ai/rome-neighbors/design.md` — 2.5k words, same.
5. `ai/lookback-research/sections/synthesis.md` and
   `ai/lookback-research/thoughts/*.md` — earlier, more exploratory register.

Output must cover three layers:

- **Sentence** — rhythm, length distribution, connective habits, tense.
- **Paragraph & section** — how an argument opens, turns, and closes; header style.
- **Epistemic** — how claims, numbers, uncertainty, and error are handled. This
  is the layer most likely to be the actual differentiator.

Must also record the **negative space**: constructions the corpus never uses.
That list seeds R-003 and is more actionable than anything on the positive side.

**Blockers:** —

**Artifacts:**

- `agents/shared/findings.md` → "[R-001] Finding: Saif's research-writing voice"

**Closed:** 2026-09-18 — 21 named moves with citations, an 11-item negative-space
list, and a frequency budget for the X-not-Y signature. Exposed one gap: the
corpus has no paper-register or notation sample, so the mathematics half of the
project has no exemplar support until R-002 lands.

---

### R-002 · Exemplar corpus from admired papers

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-18
**Updated:** 2026-09-18

**Description:**
Assemble 3–5 papers Saif would be content to be mistaken for, and mark the
specific passages that earn the choice. Passage-level, not paper-level: the unit
the skill consumes is a paragraph with a note on what it is doing, not a citation.

For each paper, record: full reference, PDF or local path, 2–4 marked passages,
and one sentence per passage naming the move it demonstrates (e.g. "states the
null before the result", "introduces notation with a worked instance").

Store under `corpus/papers/<short-name>.md`.

**Blockers:** — (cleared 2026-09-19: Saif scoped it to mechanistic
interpretability and pointed at the PDFs under `ai/`)

**Artifacts:**

- `corpus/papers/README.md` — index and selection rationale
- `corpus/papers/rome.md` — 7 passages, the notation exemplar
- `corpus/papers/lookbacks.md` — 5 passages, naming and framing
- `corpus/papers/sparse-feature-circuits.md` — 4 passages, positioning
- `corpus/papers/_anti-exemplar-deep-research.md` — 3 passages, negative control
- `agents/shared/findings.md` → "[R-002] Finding: the mech interp exemplar corpus"

**Closed:** 2026-09-19 — 19 marked passages across four documents. Closes R-001's
notation gap and answers T-006. Three of the six available PDFs deferred with
reasons recorded in the index.

---

### R-003 · The deletion list

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-18
**Updated:** 2026-09-18

**Description:**
Produce the finite list of constructions the skill deletes on sight. Derived from
R-001's negative-space section plus the R-002 passages — from what good writing
demonstrably avoids, not from a generic LLM-slop list.

Each entry: the banned construction, one invented example of it, and the
replacement move. A ban with no replacement re-houses nothing and will be ignored
(Premise Dry-Run move 9 — salvage the reason from anything cut).

Target length 12–20 entries. A longer list is not enforceable in one pass.

**Blockers:** — (R-001 and R-002 both closed; unblocked 2026-09-19)

**Artifacts:**

- `corpus/deletion-list.md` — 20 entries, Tier 1 (12 lintable) + Tier 2 (8 structural)
- `agents/researcher/findings/negspace.py`, `control.py` — measurement instruments
- `logs/r003-negspace-2026-09-20.log` — run output
- `agents/shared/findings.md` → "[R-003] Finding: the deletion list"

**Closed:** 2026-09-20 — 20 entries against a target of 12–20. Measurement
confirmed the corpus is at literal zero on all fifteen probes, and showed the
exemplar/anti-exemplar separation is only 1.5×, so Tier 1 is a house standard
rather than a quality detector. Tier 2 carries the project and is untested against
a real draft.

---

### R-004 · Prior-art with teeth — what is actually missing?

**Status:** closed
**Type:** research
**Priority:** high
**Created:** 2026-09-20
**Updated:** 2026-09-20
**Estimated:** 2h

**Description:**
Unparks [T-004], which asked whether prior-art checking belongs in this skill, a
separate one, or wired into the design protocol.

**The thread's premise is wrong and that has to be established first.** It says
"design lens 2 is protocol with no search behind it." In `rome-neighbors` there is
substantial search behind it: three Asta probes, implementation-level checks of the
two nearest competitors, a scoop risk revised moderate-high → moderate on evidence,
a new nearest competitor surfaced on the second probe, and an explicit honesty note
that an NDIF scan is "CONFIRMATORY, not exhaustive". That is better prior-art
practice than most papers document.

So the ticket is a **diagnosis**, not a build: given that the practice exists and is
good, what is the defect that still lets things through?

Evidence to work from, all already in the repo:

1. `rome-neighbors/design.md` §2 and `threads.md` T-018 — the practice at its best.
2. `web/blog/2026-09-14-the-check-that-was-never-there.md` — "Two separate
   literature passes and neither caught this, because both were searching for
   *competing work* rather than re-reading the *primary source*."
3. `rome-neighbors/threads.md` — "Fork A (removal-reliability) shelved: its scoop
   verdict was unverified by the search."
4. `edit-slice/design.md` — has no equivalent §2 depth. Whatever `rome-neighbors`
   does is not transferring between projects.

**Deliverable.** An answer to [T-004]'s three-way question, with the defect named
from evidence rather than assumed, and the minimal change that addresses it. If the
answer is "no tool, a discipline", say so — a search tool nobody needed would be the
difficulty-trap the Compass warns about.

**Blockers:** —

**Artifacts:**

- `agents/shared/findings.md` → "[R-004] Finding" and "[R-004] Correction"
- `skill/research-writing/SKILL.md` — two positioning rules, scope boundary revised

**Closed:** 2026-09-20 — [T-004]'s premise was wrong; the search practice is good in
**both** projects, not one. The first diagnosis claimed `edit-slice` §2 lacked depth
and its own prescribed test refuted that within the hour. Two failures survive, both
about what licenses a verdict: misreading a primary source, and shelving on an
unverified scoop verdict. Fix is two rules, not a tool — the asymmetric evidence bar
and read-the-methods-not-the-prose.
