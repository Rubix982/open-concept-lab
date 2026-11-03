# Reading activations off NDIF reproducibly

What a remote activation read does and does not give you twice, measured on NDIF through nnsight 0.8.1 between 2026-10-31 and 2026-11-03, on three models and two architectures: `meta-llama/Llama-3.1-8B`, `meta-llama/Llama-3.1-70B` and `EleutherAI/gpt-j-6b`.

**Which numbers travel and which do not.** The structural facts below hold on all three. The magnitudes do not: the arithmetic-site effect spans three orders of magnitude across them, and the serving dtype differs — the two Llamas arrive as **bfloat16**, GPT-J as **float32**. So read the structure as the finding and every magnitude as a value you must re-measure on your own model. The suite does this for you and keeps the per-model numbers in one table.

**Who this is for.** Anyone whose result is a number read out of a model hosted on NDIF, and who intends to compare that number against one read on a different day — their own earlier run, or somebody else's. If your pipeline contains an equality assertion on an activation-derived quantity, it is going to fail for a reason that is not your bug, and this document says which reason and how large.

**What this is not.** It makes no claim about knowledge editing, about model behaviour, or about whether NDIF is behaving correctly. Every effect below is small, and most of them are the ordinary consequence of bf16 arithmetic on shared hardware. The point is their size, because a size is what a tolerance needs and nobody had written one down.

**Reproduce it yourself:** `tools/ndif_conformance.py` re-measures every number here on your own connection and prints yours beside ours. It is one file, imports nothing from this project, and needs only `nnsight`, `torch` and an `NNSIGHT_API_KEY`.

---

## The short version

Four things, in the order they will bite you.

1. **A ratio read inside one trace is exact.** Read both of its terms in the same `model.trace` and everything below cancels. This is the single most effective thing you can do and it costs nothing.
2. **A tensor cached from an earlier session is not the tensor you would read today.** Worst observed deviation on a quantity that is analytically 1.000: **6.382e-03**.
3. **Readings can partition by the GPU that served them — on days when more than one GPU serves you.** Observed cleanly once, on 2026-11-01. On 2026-11-03, 16 fresh connections to each of two models all landed on GPU 0 and returned one reading. Routing is a property of the deployment on the day, not a standing one.
4. **A raw activation is reproducible only within one batch shape; a ratio is not affected.** Change the number of rows, or merely the padding width, and raw keys move by about 2.6% of their magnitude. The ratio of two keys read in the same trace stays bit-identical.
5. **Depth does not change the bound that matters.** The shape effect stays under 3% of key magnitude at every layer of every model tested, from layer 0 to layer 79. The one quantity that *does* move with depth — where the arithmetic runs — swings two to three orders of magnitude in bfloat16 with no consistent direction, and sits at machine epsilon in float32. Measure that one at your own layer.
6. **Causality is not the problem, and neither is bfloat16.** Changing the *content* of the padding changes nothing, on every model tested including one served in float32. Only the tensor shape matters.
8. **Record the device, every time.** It is the only handle you have on which replica served you, and the readings in this project that predate that habit can no longer be attributed to anything. Across four sessions over two days the same 42-probe floor median spanned **2.16e-04**, of which the serving device accounts for 1.4%. The rest is unattributed. **If your claim needs reproducibility tighter than 2.2e-04, you need to resolve this before you publish it, and this document cannot resolve it for you.**

---

## 1. A quantity read inside a single trace is exact; one read across traces is not

The cleanest demonstration is a quantity that is **analytically** fixed. Take the input to an MLP output projection at some layer — in ROME's vocabulary the key `k` — and a reference key `k*` taken from the same position of the same prompt. The ratio `(k·k*)/(k*·k*)` is 1 by construction. Any deviation is instrument, not model.

Read with `k*` taken from the same trace, in float32:

```
216 cells, four models 6B-405B, worst deviation from 1.000 = 0.000e+00
```

Exact. Not approximately exact — the deviation is zero in every cell.

Read with `k*` loaded from a tensor written in an earlier session, in the activations' own dtype:

```
42 items, worst deviation from 1.000 = 6.382e-03   (25 of 42 outside a 1e-3 band)
```

Two separate causes, and they stack:

**Dtype.** Casting a float32 vector down to the activations' bf16 before a sum over `d_mlp` channels (14336 for Llama-3.1) throws away the precision the sum needs. bf16's relative precision is about `2**-8 = 3.9e-03`, which is the order of the observed error and the entire budget for a quantity that has to read exactly 1.000. Do the arithmetic in float32 and this half disappears.

**Provenance.** bf16 matmul is not deterministic across batch shapes, so a tensor written in an earlier session carries that session's shape and that session's device. Nothing you do at read time recovers it.

**What to do.** When the question is *does my pipeline read the right token*, read both terms live in one trace and take the dot product in float32. When the question is *what does this cached edit do*, the cached tensor is the correct one — it is the thing being applied — and a ~1e-03 error against a signal that ranges from 0.08 to 1.00 is negligible. These are different questions and they want different code paths. Running one path for both is how this was missed.

---

## 2. Readings can partition by the serving GPU, on days when more than one GPU serves you

Identical inputs, byte for byte, through fresh connections, on **2026-11-01**, produced exactly two distinct results:

```
16 readings of one 126-prompt batch, fresh connection each

  signature            readings   served by
  edd2b2b152de2098            8   GPU 0
  54a1755349e607dc            8   GPU 2

  floor median   within a GPU   0.000e+00
                 across GPUs    3.110e-06
```

A perfect partition in both directions: every value mapped to one device, every device to one value. Within a device the readings were bit-identical; the variation was entirely between devices.

**Two days later this did not reproduce, and the reason is the more useful fact.** On **2026-11-03**, 16 fresh connections to `Llama-3.1-8B` all landed on **GPU 0** and returned a single signature, spread 0.000e+00. Sixteen more to `GPT-J-6B` did the same. Not a weaker partition — no partition, because there was only ever one device in play.

So routing varies between days. On a day when one device serves you, the device explains nothing and a per-device tolerance buys nothing; on a day like 2026-11-01 it explains 3.11e-06. **You cannot know which kind of day you are having without looking**, which is the argument for recording the device rather than for assuming a value.

The serving device is observable from the client. `tracer.backend.meta` carries `runtime`, `max_memory_usage` and `max_mem_by_gpu`, and the keys of `max_mem_by_gpu` are GPU indices. A sharded model reports all of its devices — `Llama-3.1-70B` returns `0,1,2,3` on every call — so for large models this identifies the deployment rather than the replica.

**What to do.** Record the device on every reading you intend to compare later, and record how many distinct devices a run saw. A single-device run is not evidence that routing is stable; it is evidence about that run.

## 3. The device accounts for 1.4% of the drift actually observed

This is the part worth carrying, and it is why §2 alone is not enough.

The same 42 probes, the same floor statistic, four sessions across two days:

```
0.08087725   2026-10-31, first session
0.08094215   2026-11-01, first reading
0.08109000   2026-11-01, GPU 0
0.08109313   2026-11-01, GPU 2

observed range   2.16e-04
device spread    3.11e-06   (1.4% of it)
```

Two further candidates were measured rather than assumed:

**Batch SHAPE moves the raw activations and leaves the derived ratio alone.** This is the sharpest practical result here, and it was stated too broadly in the first draft of this document, which said batch composition "contributes zero". It does not. Three arms, each on one connection, 8 anchor pairs at layer 5:

```
                                         8B          70B       GPT-J-6B
served dtype                       bfloat16     bfloat16        float32

16 rows -> 22, width held fixed
  raw key values   max |difference| 4.297e-02   1.953e-03     5.292e-02
                   as % of magnitude    2.59%       0.91%         0.92%
  DERIVED RATIO    max |difference| 0.000e+00   0.000e+00     0.000e+00

16 rows, width 14 -> 22, padding only
  raw key values   max |difference| 4.297e-02   1.953e-03     5.292e-02

same width, DIFFERENT trailing token
  raw key values   max |difference| 0.000e+00   0.000e+00     0.000e+00
```

Read those three blocks in order, because the third is what makes the first two mean something.

Widening the pad region moves the keys, although appending padding after the text cannot reach a token to its left under causal attention. Two things could cause that, and they call for opposite responses: the model is attending to the padding — a usage fault you must fix — or the kernel path depends on the tensor shape, which is nothing to fix and everything to size a tolerance against.

**The third arm settles it.** Fill the same-width pad region with a different token and the keys are **bit-identical**, on all three models. Causality holds exactly as advertised; nothing is reading the padding. Only the shape matters, and the diagnosis is kernel path selection.

**It is not a bfloat16 artifact either.** GPT-J is served in **float32** and shows the effect at the same relative size as the 70B. Whatever selects the kernel does so above the dtype.

**It does not grow with depth, although it looks like it does.** Swept over five layers on each of three models, 135 traces:

```
                        L0       L5      L12    L24/L20   L31/L27

Llama-3.1-8B (bfloat16)
  batch_width abs  3.91e-03 4.30e-02 1.95e-02  4.69e-02  2.66e-01
  key magnitude        0.75     1.66     1.06      3.41     19.75
  AS % OF MAGNITUDE   0.52%    2.59%    1.84%     1.38%     1.34%

Llama-3.1-70B (bfloat16), layers 0/5/20/40/79
  batch_width abs  2.44e-04 1.95e-03 7.81e-03  1.17e-02  1.09e-01
  key magnitude       0.063    0.215     0.957     1.094     7.094
  AS % OF MAGNITUDE   0.38%    0.91%    0.82%     1.07%     1.54%

GPT-J-6B (float32), layers 0/5/12/20/27
  batch_width abs  0.00e+00 5.29e-02 4.40e-02  5.08e-02  4.75e-02
  AS % OF MAGNITUDE   0.00%    0.92%    1.32%     1.27%     0.91%
```

Across all fifteen layer-model pairs the relative figure runs from 0.00% to **2.59%**, and the 70B's 448-fold absolute rise over 79 layers again tracks its keys growing 113-fold.

The absolute figure rises 68-fold from layer 0 to layer 31 on the 8B and that is **entirely** the keys themselves growing — their magnitude rises 26-fold over the same span. In relative terms the effect is flat: **under 3% of key magnitude at every depth on all three models.** So the bound is one number and you do not need to re-derive it per layer.

GPT-J's layer 0 is bit-identical on every check, and `cached_reference` is correspondingly 0.000e+00 at exactly the layers where `batch_width` is — the two are the same effect seen twice, which is the closest thing to an internal consistency check this suite has.

**What this means for you.** A raw activation is reproducible only inside a fixed batch shape, to within about 1-3% of its magnitude, at any depth and on either architecture. A ratio of two activations read in the same trace is reproducible across batch shape, bit for bit, on all three models and every layer tested. If you cache activations and compare them later, that 1-3% is your floor, and it is three to four orders of magnitude worse than anything else in this document.

**Where the arithmetic runs is model-specific and spans three orders of magnitude.** Multiplying inside the trace on the GPU, against returning the vectors and multiplying on the CPU, gives a difference of medians of:

```
Llama-3.1-8B     5.319e-06      bfloat16
Llama-3.1-70B    4.969e-07      bfloat16
GPT-J-6B         7.451e-09      float32, and this is float32 epsilon scale
```

The first version of this suite reported 70B and GPT-J as "differs" purely because the documented figure came from the 8B. That is not a deployment difference, it is a different model, and the suite now keeps a per-model table so the two cannot be confused.

**It also varies by orders of magnitude with depth in bfloat16 — with no consistent direction — and not at all in float32.** Fifteen layer-model pairs:

```
                 L0        L5    L20/L12   L40/L24   L79/L31/L27

8B   (bf16)  8.41e-07  5.32e-06  1.63e-05  2.66e-05    3.68e-05
70B  (bf16)  4.84e-06  4.97e-07  9.13e-08  2.72e-05    1.65e-05
GPTJ (fp32)  1.49e-08  7.45e-09  7.45e-09  1.86e-09    7.45e-09
```

The 8B rises monotonically, a factor of 44 over 31 layers. **The 70B does not** — it falls by a factor of 53 to layer 20, then rises by 298 to layer 40. A reading of this taken from the 8B alone would have said "grows with depth", and the 70B refutes it. What survives both is weaker and still useful: in bfloat16 this spans two to three orders of magnitude across depth and you cannot predict where, and in float32 it sits at machine epsilon everywhere. So **measure it at the layer you actually read**, which is what the suite's `--layer` sweep is for.

The per-item maximum is larger and **sample-dependent** — 2.98e-03 over the original 42 probes, 6.31e-05 over the suite's 6 — so the median is the statistic to compare and the per-item figure is the one to budget for. That the median is stable is a property of the median, not evidence that the two arithmetics agree. Pick one site and stay with it.

**The remaining ~2e-04 is not drift, and calling it drift was the mistake.** On 2026-11-03 the same 42 probes were read again and the value came back **bit-identical** to the GPU 0 reading taken two days earlier — the same 16-character content hash and the same median to the last bit, `0.08109002151514136`. A census over every reading ever taken of this quantity then gives:

```
value                    readings   GPUs          days
0.08087725                      1   unrecorded    10-31
0.08094214687103357             1   unrecorded    11-01
0.08109002151514136             9   0             11-01, 11-03
0.08109313181234508            13   2             11-01

4 distinct values over 24 readings
spread WITHIN a device set        0.000e+00
spread ACROSS everything          2.159e-04
```

Twenty-four readings, four values, each one exact and each one repeating. Thirteen readings — across two different nnsight loaders and two separate experiments — return `0.08109313181234508` to the last bit.

**So there is no time component at all.** A reading is a function of which replica served it, and of nothing else that has been varied. The 2.16e-04 is not an error bar on a single quantity; it is the spread between four discrete values that each reproduce perfectly.

**What remains open is narrower than it was.** Not *what causes the drift* but *how many replicas are there*. Two of the four values were recorded before anyone thought to capture the device, so they cannot be attributed now — that information is gone. The practical rule does not depend on resolving it.

**What to do.** Record the serving device with every reading. Then a comparison between device-matched readings needs **no tolerance at all** — it is exact, across days. The 2.2e-04 below is the tolerance for comparing readings whose devices differ or are unknown, which is what every historical artifact in this project is.

**What to do.** Do not write a gate that asserts bit-identity across readings. For a quantity read across traces and compared across sessions, use a tolerance of at least **2.2e-04**. Prefer, wherever the question allows it, a ratio read inside one trace — §1 — because it cancels all of this rather than tolerating it.

---

## 4. A trace body is shipped as source, which constrains where you may write one

nnsight compiles the body of `model.trace` from the **source of the frame that entered it**. Three consequences, each of which presents as something unrelated:

**A trace needs a real file.** A trace body piped on stdin — a heredoc, `python -c`, an `exec` of a string — has no source, and nnsight raises `WithBlockNotFoundError`. Scratch experiments have to live in a `.py` file on disk.

**A trace body may not reference your own package.** The body's source is shipped to the server, which does not have your code installed. A helper imported from your project, called inside the body, arrives as `ModuleNotFoundError`. Resolve module paths and read configuration **before** the `with` block, bind the results to plain locals, and use only those inside it.

**An intervention written in a helper is silently dropped.** This is the dangerous one: an edit applied by a function called from inside someone else's trace does not raise. It does not appear in the graph, the trace succeeds, and you get unedited numbers that look like edited ones. The intervention has to be written lexically inside the `with` block that will run it.

---

## 5. Backward passes: gradients of tensors the model consumed are refused

On nnsight 0.8.1 against NDIF, a backward trace serves the gradient of a tensor the intervention block itself constructed, and refuses the gradient of any tensor the model consumed:

```
OutOfOrderError: '<id>.grad.i0' was requested but the model already ran past it
```

Measured at layers 31, 20 and 5, with and without an output swap, on leaves and non-leaves alike, using the documented idiom. **Depth is not the variable**: the layer immediately before the head fails exactly as layer 5 does, and a trace with no swap fails identically. The message names ordering, and ordering is not what is wrong — which is why rearranging the trace does not help.

Anything needing `d(loss)/d(activation)` at an interior layer is therefore unavailable remotely on this version. Pinning back does not help: the server removed the websocket route that 0.7.0 handshakes against.

*This section describes a limitation we have not reported upstream or had confirmed by NDIF. It is the one item here that may be a version-specific bug rather than a property of the instrument, and it should be read that way.*

---

## How to write a gate that survives this

In order of how much they buy:

1. **Read both terms of a ratio in one trace.** Exact, free, and immune to everything in §2 and §3.
2. **Do the arithmetic in float32**, whatever dtype the activations arrive in.
3. **Never assert bit-identity across readings.** It is unsatisfiable here, and relaxing an assertion after it fails is how a re-baseline gets filed as an upgrade.
4. **Use ≥ 2.2e-04 for a cross-trace quantity compared across sessions whose devices differ or are unknown.** With the device matched, the comparison is exact and needs no tolerance.
5. **Record the serving device** with every reading, from `tracer.backend.meta`.
6. **Size the gate to what it guards.** A gate that can fail for a reason unrelated to its subject teaches you to ignore it, which costs more than not having it.

---

## Limits

**What this does not show.** These are measurements of one deployment over four days. The structural claims were checked on three models across two architectures; the magnitudes were found NOT to generalise even across those three, which is why every one of them is tagged with the model it came from. Nothing here establishes behaviour on a different deployment, or next month.

**What was not done.** The ~2e-04 between-day remainder was not attributed; no deployment metadata beyond the GPU index was collected; the §5 backward limitation was not confirmed with NDIF; nothing was measured at a layer other than 5, or on a batch larger than 22 rows; and the kernel-selection diagnosis in §3 is an inference from the pad-content control, not an observation of the kernel itself.

**How this may not be used.** The tolerances here are floors for *this* instrument, not a general standard, and a number inside 2.2e-04 of another number is not thereby shown to be the same number. The right use is to stop a pipeline asserting a precision it does not have — not to certify that two results agree.


---

## What running the suite against this document changed

The suite is not decoration. Run against the first draft of this document on 2026-11-03 it produced three corrections, two of them to the document and one to itself, and they are recorded here rather than silently fixed because a reference that was once wrong should say where.

| What was claimed | What the suite found |
|---|---|
| "Batch composition contributes zero (bit-identical)" | True of the **derived ratio**, false of the **raw keys**, which move 4.297e-02. The original measurement was taken on a ratio and the claim was generalised past it. §3 now states both. |
| Padding width is immaterial | Not measured before. It is 4.297e-02, the same as the row-count arm. New, and recorded as new. |
| Where the arithmetic runs: "2.98e-03 per item" | Reproduces as 6.31e-05 on a different 6-pair sample. The per-item figure is sample-dependent; the **median**, 5.06e-06 against a re-measured 5.319e-06, is not. The suite gates on the median. |

Two faults in the suite itself were found the same way and are left documented in the source: a check that measured bf16 precision on near-orthogonal vectors and read 4.9e-01, which is cancellation rather than precision; and a check that measured the arithmetic-site effect on a quantity that is analytically pinned to 1.000, so it read 0.000e+00 and would have done so forever.

**A reading of this document's own §2 that the suite did not reproduce.** Four fresh connections on 2026-11-03 all landed on GPU 0 and returned one signature, so the partition is consistent with §2 and does not demonstrate it. Seeing the partition takes enough connections to land on more than one device; the documented run used sixteen.

### The second run, across three models

Running the same suite on 70B and GPT-J-6B on 2026-11-03 added three things and cost 33 remote traces.

| | What it changed |
|---|---|
| **The structure generalises** | `ratio_in_trace` 0.000e+00, `batch_rows` ratio 0.000e+00 and `pad_content` 0.000e+00 on all three, across two architectures. These are the claims this document actually rests on. |
| **The magnitudes do not** | The arithmetic-site median spans 5.3e-06 to 7.5e-09. The suite now keeps per-model references, because reporting "differs" for a correct deployment running a different model is worse than reporting nothing. |
| **The dtype question answered itself** | GPT-J is served in **float32**, which this document had listed as a hypothetical ("revisit if NDIF serves float32"). It does, for that model. §1's dtype half does not apply there — and the shape effect in §3 appears anyway, which is what rules bfloat16 out as its cause. |

The pad-content control was added during this run. Without it, §3 could only say that shape matters; with it, §3 can say why, and can say that nothing needs fixing in your masking.


### The third run: the partition did not reproduce

2026-11-03, 32 further traces. 16 fresh connections to `Llama-3.1-8B` and 16 to `GPT-J-6B`.

```
Llama-3.1-8B    16/16  ->  one signature, GPU 0,  spread 0.000e+00
GPT-J-6B        16/16  ->  one signature, GPU 0,  spread 0.000e+00
```

§2 is weakened accordingly and now states the partition as something that happens on some days rather than as a property of the instrument. The negative is worth as much as the original here: a tolerance justified by "readings partition by device" would be justified by nothing at all on a day like this one, and a reader who believed the first version of §2 would not have known to check.

**It also found a fault in the suite.** `check_session_partition` reported `clean_partition = True` for sixteen identical readings off a single GPU, because "every signature maps to one device" and "every device carries one signature" are both vacuously true when there is one of each. A check that passes on an input that cannot fail is the third instance of one fault in this suite's short life, and the third to be fixed by naming the degenerate case rather than by tightening a number. It now reports `n/a - nothing to partition`.


### The fourth run: across depth

2026-11-03, 90 traces. Five layers on `Llama-3.1-8B` (0, 5, 12, 24, 31) and five on `GPT-J-6B` (0, 5, 12, 20, 27), six checks each.

**Every structural check read exactly 0.000e+00 at all ten layer-model pairs**: the analytic ratio, the batch-row ratio, and the pad-content control. These are the claims this document rests on and they do not depend on where you read.

Two things the sweep changed:

| | |
|---|---|
| **The shape effect is flat in depth, not growing** | Its absolute size rises 68-fold over 31 layers and that is entirely the keys growing — 26-fold — underneath it. Relative, it stays under 3% everywhere. The bound in §3 is therefore one number for the whole model, which the layer-5-only version could not have claimed. |
| **The arithmetic-site effect moves with depth, and only in bfloat16** | 44-fold over 31 layers on the 8B, flat at float32 epsilon on GPT-J. Stated after the 8B and GPT-J alone as "grows with depth" — see the fifth run, where the 70B refuted the direction and left only the magnitude. |

The sweep mode is now part of the suite (`--layer 0,5,12,24,31`), with a fresh context per layer — a cached tensor from layer 5 compared against a reading at layer 24 would produce a large and entirely meaningless difference, which is the same fault class as the three this suite has already found in itself.


### The fifth run: the 70B refused the shape of the fourth

2026-11-03, 45 more traces, `Llama-3.1-70B` at layers 0, 5, 20, 40 and 79. The expectation written before it, in plain words, was that it would add a row and break nothing, because the structure had already held on three models. **Half of that was right.**

The structural checks held: `ratio_in_trace`, `batch_rows` and `pad_content` all read 0.000e+00 at all five layers, bringing those claims to **fifteen layer-model pairs across two architectures and three model sizes, every one exactly zero.** The batch-shape bound held too — 0.38% to 1.54%, inside the sub-3% band, with the 448-fold absolute rise over 79 layers again fully accounted for by the keys growing 113-fold.

What did not hold was a claim made one run earlier. The fourth run saw the arithmetic-site effect rise monotonically with depth on the 8B and concluded it "grows with depth in bfloat16". The 70B falls by a factor of 53 from layer 0 to layer 20 and then rises by 298 to layer 40. The direction was an artefact of one model.

The surviving claim is weaker and is the one now in §3: in bfloat16 this quantity spans two to three orders of magnitude across depth **and you cannot predict where**; in float32 it does not move. The practical consequence changes from "be careful deep" to "measure it at your layer", which is a different instruction and the suite exists to carry it out.
