# edit-reach

One question, and nothing else: **how far do an edit's reverberations travel, and how much of that can we see before we run the edit?**

This is the instrument project. `ai/edit-slice` is the record of what was found; this is the attempt to turn one of those findings into something that can be used. The two are kept apart on purpose — edit-slice keeps accumulating findings, this one either produces a working screen or shows that it cannot.

---

## The thing being tested

A benchmark gives a **lower bound** on an edit's damage and never an upper bound. It can show that an edit broke something; it can never show that an edit broke nothing, because an absent item and an absent failure look identical. Writing a larger item set does not fix this — a hand-written set measures the limits of whoever wrote it.

The alternative is to **replace enumeration with measurement**: a quantity defined for any prompt rather than for a listed set, so an item can be scored without having been anticipated. Note what that does and does not buy — the quantity is still *evaluated* on prompts we happen to have, so it removes the need to foresee which items matter, not the need to have items. Whether it has useful range outside the near field is open (T-005).

[E-036] gives a candidate (`edit-slice/results/E-036-ripple-coefficients.json`, and the decision behind it in `edit-slice/agents/shared/decisions.md`). ROME's update is rank-one, so the coefficient `(k·u)/(u·k*)` says how much of the edit arrives at a token, and it is computable in one forward pass through the **unedited** model.

**The gap this project exists to close:** the coefficient measures *delivery*, not *effect*. It says how much of the edit vector arrives, not how far the model's answer moves. Until that link is established, the screen is a proposal and not an instrument, and no threshold can be set on it.

---

## Inherited, treat as binding

From `ai/edit-slice/CLAUDE.md` and `notes/definitions.md`, unchanged:

- `update` / `damage` / `orphan` keep their meanings and stay distinct in every metric name.
- **Delivery is never effect.** A coefficient is not a behavioural claim. This project may only stop saying that by measuring it.
- Hand-built or mined probe sets license an **existence** claim, never a rate. `[O-004]`.
- **Controls are mandatory.** Every reading carries its baseline: the different-subject floor (0.082 at layer 5) is what makes 1.000 mean anything, and a pipeline hardwired to return 1 looks identical without it.
- Never generate a citation from memory. Look it up or leave `TODO(cite)`.

---

## Scope

**In.** Predicting, screening, and bounding an edit's reach. Measuring whether a pre-edit quantity predicts post-edit behaviour. Characterising what a screen can and cannot bound.

**Out.**

- Proposing or tuning an editing method. Same rule as edit-slice: proposing a method means owning the burden of beating JNO.
- Reporting a rate from a hand-built set.
- Any claim that a screen bounds damage from **above** without a proof or a measurement that supports it. This is the project's own most likely overclaim and it is named here so it cannot be made quietly.

---

## The package

The measurement code lives here, in `src/editreach/`, as an installable package. Six modules were lifted **unchanged** from `ai/edit-slice/src` — `remote`, `rome` (was `edit`), `whiten`, `local` (was `probing`), `data`, `logs`. Unchanged is deliberate: a rewrite would have moved the numbers, and the numbers being comparable across both projects is the only reason to share the code.

edit-slice's old flat module names are now shims that forward here, so its 79 existing scripts keep working and there is one copy of the code rather than two. **New code imports `editreach` directly.** Nothing is added to the shims.

Two things this package has that edit-slice did not, and they are the reason it is a package rather than a move:

- `coefficient.py` — the coefficient is an object. In edit-slice it was an expression written inline inside each run script. It is the thing being claimed, so it has a name, and it is computable on the unedited model.
- `control.py` — a reading without its baseline **does not construct**. edit-slice stated that rule in prose and relied on the next author having read it. `require_baseline` raises `Unbaselined`, and `Reading.discriminates()` reproduces the [T-075] layer-31 case where the floor rose to meet the signal.

Same venv rule as everywhere: `.venv/` in this directory, never system Python.

## Process

`CARD.md` is the file to open at the start of a sitting. One card at a time; it closes with a number or with a sentence that could have come out the other way, never with "explored". `threads.md` is where a branch goes to be silent, not a menu to browse.

---

## Models: one 8B+ model from each family, every time

Standing rule from 2026-11-15, after [E-040] measured the same quantity on three models and got three different answers.

**Every experiment runs on at least one model above 8B from each architecture family available to it.** Not as a follow-up once the result looks good — in the run that produces the result. A number from one model is a number about that model until a second family says otherwise, and the paper has no way to tell the two apart after the fact.

The reason is measured, not assumed. The different-subject floor in [E-040] reads **0.194 on GPT-J-6B, 0.081 on Llama-3.1-8B, 0.031 on Llama-3.1-70B** — a factor of six across three models, on identical prompts. The analytic anchor sat at exactly 1.000 on all three, which is the useful contrast: what follows from the algebra travels, and what is read off the model's keys does not. Only the 8B → 70B step is a clean size comparison; 6B is a different architecture, so that step confounds the two. One family at two sizes cannot separate them, which is the whole reason the rule says *each family* and not *several sizes*.

**Every runner records per model, never in aggregate.** One row per model carrying the model id, the resolved architecture, layer count, the layer read, and every quantity the run reports. A median taken across models hides exactly the effect the rule exists to find. A model that could not be read is recorded as a row with its reason, not dropped — [E-040]'s first draft let one unservable model take three completed ones down with it, because the result file is written at the end.

**A reference number belongs to the model it was measured on.** A gate comparing against a published figure must name that model and skip itself elsewhere rather than fail. On a different model "something moved between runs" is the wrong diagnosis, and a gate that fails for the wrong reason costs more than no gate.

**What is actually reachable.** Run `tools/ndif_catalogue.py` rather than trusting a model list typed into a script; it reads `https://api.ndif.us/status`. As of 2026-11-15 NDIF serves 181 deployments, 75 of them above 8B, and **six are readable here** — Llama-3.1-70B, 3.1-70B-Instruct and 3.3-70B-Instruct, all HOT. Llama-3.1-405B is served but COLD, which is what `CANT_ACCOMMODATE` means.

So the rule is currently blocked above 8B for every family but one, and the blocker is ours: `editreach.arch.ARCH` holds paths to the MLP output projection for `llama` and `gptj` only. Reading the wrong module **does not raise — it returns plausible wrong numbers**, so no family is added by guessing from a config field. Each new entry is verified against that architecture's own module layout before any run uses it. Qwen opens the most at once (`Qwen2.5-72B-Instruct` and `Qwen3.5-122B-A10B`, both HOT), then gemma, seed_oss, nemotron_h and gpt_oss.

Until a family's path is in `ARCH`, a result is stated for the families it was measured on and for no others.
