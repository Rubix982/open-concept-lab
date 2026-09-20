# Changelog

## 2026-09-18 · Session 1

- [O-001] Initialize project structure; scope split four ways — `plan.md`
- [R-001] Voice profile from ~12k words of Saif's own corpus — `agents/shared/findings.md`
- Threads opened: T-001 (answered), T-002, T-003, T-004, T-005, T-006, T-007 — `threads.md`

**Provenance note.** The four files above were committed in `41a3c507`, whose
message is entirely about `edit-slice` E-016. A concurrent session working in that
project ran a repo-wide `git add` and swept this project's files in. The commit was
pushed before it was noticed, so the history is left as-is rather than rewritten
under another session's active work. The files are intact; only the commit message
is misattributed. This entry is the record.

## 2026-09-19 · Session 2

- [R-002] Mech interp exemplar corpus — 19 marked passages in `corpus/papers/`,
  finding in `agents/shared/findings.md`
- Threads: T-003 and T-006 answered; T-008 and T-009 opened — `threads.md`

## 2026-09-20 · Session 3

- [R-003] Deletion list — 20 entries in `corpus/deletion-list.md`; measurement
  instruments in `agents/researcher/findings/`, output in `logs/`
- [O-002] Opened E-001 — spike to test Tier 2 against a real draft before packaging
- Threads: T-007 partially answered; T-010 opened — `threads.md`

## 2026-09-20 · Session 3 (cont.)

- [E-001] Tier 2 spike — CONFIRM; falsifiable claims 1→8 against a blind baseline.
  Artifacts in `agents/engineer/workspace/e001/`, decisions in `agents/shared/decisions.md`
- [O-003] Opened E-002 — write the skill

## 2026-09-20 · Session 3 (cont. 2)

- [E-002] Skill written and installed — `skill/research-writing/`, symlinked to
  `~/.claude/skills/research-writing`; decisions in `agents/shared/decisions.md`
- [O-004] Opened E-003 — use the skill on live work before extending it
- T-010 partially answered: unquantified superlatives give 2x separation at corpus
  scale, not a gate

## 2026-09-20 · Session 3 (cont. 3)

- [E-003] First live use of the skill — new section in `web/blog/2026-09-15-five-days.mdx`
  covering E-016/E-017, published gap statement retracted and replaced, standfirst
  updated; defect list in `agents/engineer/workspace/e003/`
- [O-005] Opened E-004 — blocked on a second live use

## 2026-09-20 · Session 3 (cont. 4)

- [E-005] Second live use, a design document — `edit-slice/design.md` Part IV;
  three of five defects recurred; record in `agents/engineer/workspace/e005/`
- [O-006] E-004 unblocked
- T-011 opened and dropped — Dream-RSI reframe is evocative, not exact; kept the move, not the machinery

## 2026-09-20 · Session 3 (cont. 5)

- [E-004] Skill defects 1–4 fixed, 5 decided, 6 held — `skill/research-writing/`,
  four decisions in `agents/shared/decisions.md`

## 2026-09-20 · Session 3 (cont. 6)

- [R-004] T-004 answered — the gap is the verdict, not the search; two positioning
  rules added to `skill/research-writing/SKILL.md`. Finding plus a self-refuting
  correction in `agents/shared/findings.md`
- T-002 marked answered (stale since R-003)
- [R-005] T-009 answered — the free-inference test, and a reversed default: coin under
  uncertainty. `skill/research-writing/references/mathematics.md`
- [R-006] T-008 answered — action items 7→13, but the baseline was never actionless;
  claim-lock exposes hollow instructions rather than creating items. Output contract
  cancelled. `agents/shared/findings.md`, `skill/research-writing/SKILL.md`
