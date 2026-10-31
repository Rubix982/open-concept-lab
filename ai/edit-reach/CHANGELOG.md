# Changelog

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
