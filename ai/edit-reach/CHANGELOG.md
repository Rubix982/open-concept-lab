# Changelog

## 2026-11-09 · Session 5 — the page becomes a paper

- [D-007] The notebook sidebar written by hand and the edit-reach page split — `web/sidebars.ts`, `web/notebook/edit-reach/`
- [D-008] The notebook page shaped as a paper — `web/notebook/edit-reach/note-01.md`, components in `web/src/components/Paper.tsx`, conventions in `web/notebook/writing-here.md`
- [D-008] The four `TODO(cite)` in `paper/note.md` resolved; all four were already verified in `web/data/papers.yml`
- [D-009] Front matter, abstract and contributions; the notebook rail now shows each project's stage, read from `web/data/projects.yml`
- [D-006] `web/scripts/paper_pdf.py` — a two-column PDF built from the page, which is the only source
- [D-019] `web/blog/2026-11-09-three-checks-that-could-not-have-failed.md` — the fault class, verified down from five to three
- [D-003] Split into D-019 — the paper absorbed three of its five items; the two that survive are not about edit-reach
- [D-018] A legibility pass over both edit-reach pages — words before symbols, probe families defined, identifiers out of the prose
- [D-017] The edit-reach overview rebuilt from `CARD.md` and `threads.md`
- [D-016] `ocl-abstract` was already taken by edit-slice/review; the paper component renamed
- [D-015] The paper body set in two columns, balanced per section
- [D-014] Charts, run outputs and a two-column front matter — `web/notebook/edit-reach/paper.md`
- [D-013] The paper filled out from `agents/shared/decisions.md` — four of fifteen decisions were on the page; now most are
- [D-012] Renamed to Paper; two widths on one centre line; equations rendered with KaTeX
- [D-011] Paper-mode layout — wide container, narrow text; the `float` prop removed
- [D-010] Note 01 reorganised under the section names a reviewer expects — `web/notebook/edit-reach/note-01.md`; the rule in `web/notebook/writing-here.md`

D-008 reversed part of D-007 on the same day: the three pages D-007 split out are
now one paper. The sidebar fix held; the content's shape was the thing that was
wrong. Recorded on the ticket rather than quietly re-split.

## 2026-11-08 · Session 4 — the documentation effort

The project's question has an answer. This session is about it having a reader.

- [E-014] Repaired a record gap: thirteen decisions, twelve tickets. E-002 ran on 2026-10-31 with its artifacts and two decision entries, and its ticket was never written. Written now, marked reconstructed, and not back-dated — `agents/engineer/tickets.md`
- [D-001] edit-reach has a page. The scope statement from [E-004] — *a contamination detector, not a propagation detector* — written where a reader can reach it, which it had not been anywhere — `web/notebook/edit-reach/index.md`
- [D-002] Five figures, four drawn and one reused from edit-slice. Also a section the overview had been missing entirely, on whether a remote reading reproduces — `web/static/img/edit-reach/`
- [D-004] Paper skeleton: nine sections, five figure slots, every number carrying its ticket, prose deferred — `paper/skeleton.md`

**A number was found welded together.** `edit-slice/notes/where-this-stands.md` says the two coefficient groups "do not overlap across 23,505 readings". The non-overlap is [E-018] — 16 chains, highest different-subject 0.153 below lowest same-subject 0.483. The 23,505 readings are [E-038]'s RippleEdits re-run, a different experiment. The welded version had already reached a figure drawn earlier the same day. Corrected in `two-regimes.svg` and in the skeleton; the note itself is Saif's file.

**Opened and not started:** D-003 (the notebook page on what it was like to be wrong), D-005 (the paper's prose). D-006 (PDF build) is blocked on a toolchain decision — this machine has no `pdflatex`, `tectonic`, `typst` or `pandoc`. Every figure is an SVG, which Typst includes natively and LaTeX does not.

## 2026-10-31 · Session 1

- [O-001] Project initialised — CLAUDE.md, CARD.md, plan.md, threads.md, shared surface, venv, MIT licence
- [O-001] Extracted `editreach` as an installable package: `remote`, `rome`, `whiten`, `local`, `data`, `logs` lifted unchanged from `ai/edit-slice/src`
- [O-001] Added `coefficient.py` (the coefficient as a first-class object, computable on the unedited model) and `control.py` (a reading without a baseline does not construct)
- [O-001] `_quiet_stdout` promoted to `quiet_stdout`; old name kept as an alias, since 26 edit-slice scripts import it by the private name
- [O-001] edit-slice's six flat modules replaced with forwarding shims; its 79 consumer scripts left untouched
- [O-001] 13 tests pass; 24 of 25 distinct consumer import lines verified. The failure (`apply_delta`, `agents/engineer/workspace/debug_apply2.py`) predates this change and is a dead debug script from the APPLY_IDIOM investigation
- [O-001] Opened C-001 · Does predicted reach predict measured movement? — six fields filled
- Threads opened: T-001 upper vs lower bound, T-002 subject-string frequency (carried from edit-slice), T-003 shared prerequisite of modify and extract, T-004 cross-project elicitation result in ~/code/style

### Hardening, same session

Things done in a hurry on the way in, found and fixed before any of them reached a number:

- **Padding bug.** `coefficient_for` batched with `tok(..., padding=True)`, which uses the tokenizer's `padding_side` — LEFT on Llama. Token indices are computed on the unpadded prompt, so every reading would have come from the wrong token, silently. Fixed by `remote.encode_prompts`, which right-pads, matching the convention `_encode_pairs` already used. Regression-tested.
- **Architecture hard-coding.** `coefficient_for` assumed Llama's `model.layers[L].mlp.down_proj`. GPT-J's key lives at `transformer.h[L].mlp.fc_out`, and GPT-J is one of the four models the headline claim rests on. The resolution existed only inside `edit-slice/agents/engineer/workspace/run_e027.py`; it is now `arch.py` and raises on an unknown architecture rather than guessing, because a wrong module path returns plausible numbers instead of failing.
- **Double timeout.** `retrying` already applies `CALL_TIMEOUT_S`; the extra `deadline(...)` wrapper is gone.
- **`regime` was a free string.** Now `Regime`, an enum, so a typo cannot turn an analytic reading into an empirical one.
- **The function had never run.** It was imported but never executed. `tests/conftest.py` supplies a stand-in model and `tests/test_coefficient_runs.py` exercises it; the padding test fails loudly against the old code. This tests arithmetic, indexing and padding — **not** nnsight, which only a real model tests.
- Guards added for a zero denominator, a `u` of the wrong width, a layer outside the model, and a position past the end of its prompt.
- `py.typed` added; dependencies installed into this project's own venv.

25 tests pass.

### The diagnostic set, and what building it found

`probes/diagnostic.py` — 16 items in 7 families, each carrying a prediction and the reason for it. Seven have a band they can violate; nine are marked OPEN, which means no prior reading exists and the item is a question rather than a check. It is a set built to break the instrument, not to score a method, and it needs **no edits** — every quantity is read from the unedited model.

Building it found two defects that no amount of reading the code would have shown:

- **`subject_last_index` read the FIRST mention, silently.** `prompt.index` takes the first occurrence, and `fact_token: subject_last` never said which mention because the prompts it was written for contain one. On `"X painted in Chatou. X was born in the country of"` that reads the prefix mention and returns a confident, pinned 1.000 while the question hangs off the second. `occurrence` is now an explicit parameter, defaulting to first so every recorded edit-slice number stays reproducible, and an absent subject now raises `SubjectNotInPrompt` instead of being assigned a position — a far-field probe reaches its entity by description and legitimately has none.
- **The regime is a property of the mention read, not of the prompt.** The dry-run failed the repetition family for being labelled `PRECEDED` with a prompt that begins with its subject. Both were true of the prompt and neither was true of the reading. `Item.occurrence` and `Item.reads_at_prefix` now carry that, and the repetition family became *pairs* — one prompt read two ways, where the gap between the readings is the measurement.

`tools/dryruns/dryrun_diagnostic.py`: 63 structural checks, zero remote calls. It caught three faults in the set on its first run, including the two above.

31 tests pass.

### The families at scale

`probes/generate.py` instantiates the diagnostic families over subjects drawn from pinned CounterFact: **491 items, 42 subjects, relation P19, seed 1538**. The shapes are enumerated — there are finitely many ways a subject can sit in a prompt — while the subjects come from the pool. That is the split CLAUDE.md asks for, and it is what moves the set from an existence claim about one man to something that can carry a rate.

It also gives C-001 what it needs. A correlation between predicted reach and measured movement is weak if every probe sits in the same narrow band; these families span it by construction, from pinned 1.000 down to the floor.

**One family is not generated and is not faked.** A far-field probe reaches its entity by description, CounterFact has no descriptions, and writing them myself would put the items back in the hand-built category while looking like data. It stays hand-built and existence-only; scale for it comes from MQuAKE's later-hop items, where 16,506 of 16,506 name no subject (T-005).

`tools/dryruns/dryrun_generated.py`: 1,199 structural checks, zero remote calls. It found four faults, three of them mine:

- **The floor was sometimes another subject's anchor.** `anchor-floor` drew a name at random from the whole relation pool, so in a 42-subject draw three floor items turned out to be a different subject's own pinned `anchor-prefix`, measured a second time. Floors are now drawn without replacement from subjects *outside* the set under test.
- **A bare given name is not a referring expression.** `alias-given` produced `"John was born in the city of"` three times, because three subjects were called John. The probe does not identify anyone, so it is now kept once rather than counted per person — and the item's own note says that a high reading there would mean the coefficient responds to tokens rather than to entities, which is worth knowing and is why it stays.
- **Confusables were drawn from one relation.** Searching only P19's 779 records found a near-name for 14 of 42 subjects. Drawn from the whole 21,919-record corpus it is 31 — a coefficient reading needs no ground truth about the confusable person, only a key.
- **The dry-run's own duplicate check was wrong.** It keyed on the prompt alone and failed the repetition family, which shares a prompt by design. A measurement's identity is `(prompt, subject, occurrence)`. Cross-subject prompt collisions are now reported rather than failed, with the effective n, since one reading serving two items inflates a rate.

### A regression the move introduced, found here

`data.py` resolved the pinned corpus as `Path(__file__).parent.parent / "data"`. That worked while the module sat inside the project that owned the data and broke the moment it became an installed package, resolving to `site-packages/data/`. A library has no business assuming it sits next to a dataset. There is now `EDITREACH_DATA`, falling back to a search upwards from the working directory, and it raises with the variable's name rather than a `FileNotFoundError` naming a directory nobody recognises. Verified: 21,919 records, checksum intact.

## 2026-11-01 · Session 2

- [E-003] Destination readout on [E-002]'s probe set — destruction and destination separate in opposite directions on the same 495 probes; `results/E-003-summary.md`, `agents/shared/decisions.md` → [E-003]
- [C-003] Closed on branch 1; T-007 answered in `threads.md`
- `editreach.logs` resolved its log directory from the package's own location, a leftover from edit-slice where the module sat one level higher. Today's logs went to `src/logs/` while every earlier session's sat in `logs/`. Now found from the working directory by an `agents/` marker; `.git` is deliberately not a marker, since this workspace is one repository holding several projects.
- [E-004] Far-field floor measured on the far-field prompts — the coefficient has no subject-specific range there (+0.0002 over a same-relation floor); `results/E-004-summary.md`, `agents/shared/decisions.md` → [E-004]
- [C-004] Closed on branch 1, reached through branch 2 and a relation confound; T-005 answered
- `editreach.coefficient.keys_at` added — raw key vectors in one remote pass, so n×n donor floors are offline arithmetic
- [E-005] Loader parity — `LanguageModel` and `TransformersModel` are the same instrument; the switch is safe and deliberately not taken; `results/E-005-summary.md`
- [C-005] Closed on branch 1 after its own bit-identity criterion proved unsatisfiable; T-006 answered, **T-008 opened** (readings differ between NDIF serving sessions on byte-identical inputs)
- [E-006] Session variation partitions cleanly by serving GPU — 16 readings, two devices, one value each; `results/E-006-summary.md`
- [C-006] Closed on branch 1; T-008 answered, **T-009 opened** (the device is 1.4% of the observed 2.16e-04 drift)
- Adopted: no gate asserts bit-identity across readings; cross-trace quantities need a tolerance of at least 2.2e-04; prefer a ratio read inside one trace

## 2026-11-03 · Session 3

- [E-007] NDIF reproducibility reference and conformance suite — docs/ndif-reproducibility.md and tools/ndif_conformance.py; running the suite against the reference narrowed [E-006]'s batch-composition claim to derived ratios and bounded raw-activation reuse at 2.6%
- [E-008] Conformance suite run on Llama-3.1-70B and GPT-J-6B — structure held on all three across two architectures, every magnitude was model-specific; GPT-J is served in float32, which answers [E-001]'s open "revisit if"
- Correction: [E-008]'s commit message says "10/10 dry-runs pass". There are **9** dry-run files; 10 was the count of selected *checks* inside the conformance suite. All 9 pass. Recorded here because the commit is pushed and a record that was wrong should say where.
- [E-009] Serving-GPU partition did not reproduce at 16 connections on 2026-11-03 — 32/32 landed on GPU 0 across two models; section 2 of the reference weakened to a property of a deployment on a day, and the observed device-set change between 11-01 and 11-03 promoted to a named T-009 candidate
- [E-010] Conformance suite swept over five layers on two models — all three structural checks read 0.000e+00 at every layer-model pair; the batch-shape effect is flat under 3% of key magnitude once normalised, and the arithmetic-site effect's 44-fold growth with depth is bfloat16 accumulation, absent in float32
- [E-011] Llama-3.1-70B swept at layers 0/5/20/40/79 — structure now holds at fifteen layer-model pairs, every one exactly zero; withdrew [E-010]'s claim that the arithmetic-site effect grows with depth, which the 70B refutes by falling 53-fold then rising 298-fold
- [E-012] T-009's daily reading built and taken once — it came back bit-identical to [E-006]'s GPU 0 value two days earlier, and a census over all 24 recorded readings gives four discrete values with a within-device spread of exactly zero; "unattributed drift" withdrawn as a description, T-009 narrowed from "what causes it" to "how many replicas exist"
- [E-013] 124 of 155 committed log files were header-only — `setup()` announced the run at import time, so importing a run module created a one-line log; header now held until a real record arrives and the file handler opened with `delay=True`; stubs removed (recoverable from history), and two further faults found on the way: `EDITREACH_LOGS` crashed `setup()`, and the new dry-run's first assertion tested the wrong property
- [O-003] The ticket files and `plan.md` reconciled — six tickets marked open or in-progress were all finished; D-004's lost heading restored; `Next Orchestrator Action` rewritten (it still said "run the documentation effort, D-001 first")
