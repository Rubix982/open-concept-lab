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
