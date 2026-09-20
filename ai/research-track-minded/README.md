# research-track-minded

A Claude skill for research writing. The source lives here; the installed copy is a
symlink at `~/.claude/skills/research-writing`, so **editing this repo updates the
skill immediately** — there is no reinstall step.

---

## Using it

### 1 · Automatically

The skill's `description` frontmatter lists its triggers: drafting or revising papers,
lab notes, design documents, research blog posts, related-work sections — and
complaints that a draft is *vague, hedged, hard to act on, or reads like AI output*.
A session doing that work should load it without being asked.

### 2 · By name

```
/research-writing
```

It is a **personal** skill, so it is available in every project, not only this repo.

### 3 · The lint, standalone

No virtualenv and no dependencies — standard library only, any `python3`:

```bash
python3 ~/.claude/skills/research-writing/scripts/lint.py --rate DRAFT.md
python3 ~/.claude/skills/research-writing/scripts/lint.py --all DRAFT.md   # do not skip quoted text
```

Reference rates: hand-written research prose **0.0** per 10k over 27.7k words,
published mech interp papers **5.1**, AI-generated reports **6.4**.

**The gap between the last two is 1.25×. The lint cannot tell a good paper from a bad
report** — it catches house-style slips and nothing else. A clean lint is not evidence
of quality, and the skill says so in three places on purpose.

### The one catch

**Skills are discovered at session start.** A session already running when the skill
was installed or renamed will not see it; start a new one. Content edits to `SKILL.md`
and `references/` do not need a restart.

---

## What it actually does

Three passes, in order.

| Pass | What | Notes |
| --- | --- | --- |
| **1 · The claim audit** | One row per unit: the claim, own or attributed, what would falsify it | The whole point. Three modes — revise, draft, design |
| **2 · Seven structural questions** | Headings, gaps, symbols, suppression, naming, hedging, criticism | Not lintable; asked of the draft |
| **3 · The lint** | 13 regex rules | A floor. Run last, believe least |

**Pass 1 has three modes and picking the wrong one produces nothing.** Revising audits
paragraphs; drafting audits intended claims before prose exists; **designing audits
load-bearing assumptions**, because a design has no claims — "we will sweep eight
layers" cannot be false.

**Expect the ranking, not the filter.** Across two live uses, Pass 1 caught *zero*
unfalsifiable claims and restructured the document both times. If it catches nothing
it has not failed — read the table for what outranks what.

---

## What it will not do

- **It cannot improve a draft's evidential base**, only its epistemic structure.
  Measured: it added seven falsifiable claims and zero new numbers, because the source
  had none. Over thin evidence it states plainly that the evidence is thin.
- **It does not search the literature** or decide whether the work is worth doing. It
  owns the *verdict* — a novelty claim is a claim — not the search.
- **It has never been used by anyone but Claude**, and never on generated input. The
  filtering half of Pass 1 is therefore the least tested part of it.

---

## Editing it

| Path | Contents |
| --- | --- |
| `skill/research-writing/SKILL.md` | Entry point, 154 lines. **Cut before adding** |
| `skill/research-writing/references/` | `structure`, `mathematics`, `voice`, `exemplars` |
| `skill/research-writing/scripts/lint.py` | The Tier 1 rules |
| `corpus/` | Derivation: marked exemplar passages, the 20-entry deletion list |
| `agents/shared/findings.md` | Every finding, with its corrections appended |

After changing `lint.py`, run the regression in **both** directions — a rule that stops
firing on slop and a rule that starts firing on good prose are equally bad:

```bash
# must stay at 0.0
python3 skill/research-writing/scripts/lint.py --rate ../../web/blog/2026-09-14-the-check-that-was-never-there.md
# must stay high (78.6/10k)
python3 skill/research-writing/scripts/lint.py --rate agents/engineer/workspace/e001/01-baseline.md
# must stay at 0 — the skill quotes the constructions it bans
python3 skill/research-writing/scripts/lint.py skill/research-writing/SKILL.md skill/research-writing/references/*.md
```

**Test with planted defects, not only with real documents.** Every rule was
case-sensitive for a day — missing *"It is important to note"* and every other
sentence-initial form — and survived because no document in the corpus contained one.
A throwaway file of deliberately bad prose caught it in a single run.

`.venv` here is only for `pypdf`, used to extract the exemplar papers. The skill itself
needs nothing.
