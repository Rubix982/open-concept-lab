# Reading activations off NDIF reproducibly

What a remote activation read does and does not give you twice, measured on NDIF against `meta-llama/Llama-3.1-8B` and `Llama-3.1-70B` through nnsight 0.8.1, 2026-10-31 to 2026-11-01.

**Who this is for.** Anyone whose result is a number read out of a model hosted on NDIF, and who intends to compare that number against one read on a different day — their own earlier run, or somebody else's. If your pipeline contains an equality assertion on an activation-derived quantity, it is going to fail for a reason that is not your bug, and this document says which reason and how large.

**What this is not.** It makes no claim about knowledge editing, about model behaviour, or about whether NDIF is behaving correctly. Every effect below is small, and most of them are the ordinary consequence of bf16 arithmetic on shared hardware. The point is their size, because a size is what a tolerance needs and nobody had written one down.

**Reproduce it yourself:** `tools/ndif_conformance.py` re-measures every number here on your own connection and prints yours beside ours. It is one file, imports nothing from this project, and needs only `nnsight`, `torch` and an `NNSIGHT_API_KEY`.

---

## The short version

Four things, in the order they will bite you.

1. **A ratio read inside one trace is exact.** Read both of its terms in the same `model.trace` and everything below cancels. This is the single most effective thing you can do and it costs nothing.
2. **A tensor cached from an earlier session is not the tensor you would read today.** Worst observed deviation on a quantity that is analytically 1.000: **6.382e-03**.
3. **Readings partition by the GPU that served them.** Reconnect and you may land somewhere else. Within a device, bit-identical; across devices, a floor median moved by 3.110e-06.
4. **A raw activation is reproducible only within one batch shape; a ratio is not affected.** Change the number of rows, or merely the padding width, and raw keys move by about 2.6% of their magnitude. The ratio of two keys read in the same trace stays bit-identical.
5. **The device is not the whole story.** Across four sessions over two days the same 42-probe floor median spanned **2.16e-04**, of which the serving device accounts for 1.4%. The rest is unattributed. **If your claim needs reproducibility tighter than 2.2e-04, you need to resolve this before you publish it, and this document cannot resolve it for you.**

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

## 2. Readings partition by the serving GPU

Identical inputs, byte for byte, through fresh connections, produced exactly two distinct results:

```
16 readings of one 126-prompt batch, fresh connection each

  signature            readings   served by
  edd2b2b152de2098            8   GPU 0
  54a1755349e607dc            8   GPU 2

  floor median   within a GPU   0.000e+00
                 across GPUs    3.110e-06
```

A perfect partition in both directions: every value maps to one device, every device to one value. Within a device the readings are bit-identical; the variation is entirely between devices.

The serving device is observable from the client. `tracer.backend.meta` carries `runtime`, `max_memory_usage` and `max_mem_by_gpu`, and the keys of `max_mem_by_gpu` are GPU indices. Recording it costs nothing and is the only handle the client has on this.

**What to do.** Record the device on every reading you intend to compare later. Do not assume a reconnection lands where the last one did.

---

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

**Batch composition moves the raw activations and leaves the derived ratio alone.** This is the sharpest practical result here and it was stated too broadly in the first draft of this document, which said batch composition "contributes zero". It does not. Measured on 2026-11-03 by the conformance suite, one connection, 8 anchor pairs at layer 5:

```
16 rows -> 22 rows, padded width held fixed at 14
  raw key values     max |difference|  4.297e-02   (2.59% of the key magnitude)
  derived ratio      max |difference|  0.000e+00   (bit-identical)

16 rows, padded width 14 -> 22, same content, extra padding only
  raw key values     max |difference|  4.297e-02   (2.59%)
```

Appending padding after the text cannot reach a token to its left under causal attention, so the second arm is zero by the mathematics and is not zero in practice. That is bf16 matmul kernels selecting a different path for a different tensor shape. Both arms produced the identical maximum, which suggests one quantised step on one worst element rather than two independent effects; it has not been checked further.

**What this means for you.** A raw activation is reproducible only inside a fixed batch shape. A ratio of two activations read in the same trace is reproducible across batch shape. If you are caching activations and comparing them later, this bounds you at about 2.6% of their magnitude — which is far larger than anything else in this document and is the first thing to fix.

**Where the arithmetic runs contributes 5.06e-06 at the median.** Multiplying inside the trace on the GPU, against returning the vectors and multiplying on the CPU over 14336 channels, barely moves the median while moving individual values far more — 2.98e-03 per item over the original 42 probes, 6.31e-05 over the suite's 6. The per-item figure is sample-dependent and the median is not, which is why the suite compares the median. That the median is stable is a property of the median, not evidence that the two arithmetics agree. If you report per-item values rather than an aggregate, this is the dominant term and it is under your control: pick one site and stay with it.

The remaining ~2e-04, between the two days, **is not attributed.** Candidates not yet tested: a deployment or driver change between sessions, a model-weight reload, a change in how the batch was sharded. It is logged as an open question (T-009) rather than explained.

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
4. **Use ≥ 2.2e-04 for a cross-trace quantity compared across sessions.** Smaller than that and you are gating on noise you cannot attribute.
5. **Record the serving device** with every reading, from `tracer.backend.meta`.
6. **Size the gate to what it guards.** A gate that can fail for a reason unrelated to its subject teaches you to ignore it, which costs more than not having it.

---

## Limits

**What this does not show.** These are measurements of one deployment over two days, on two model sizes and one architecture family. Nothing here establishes that the magnitudes generalise to other NDIF models, to a different deployment, or to next month.

**What was not done.** The ~2e-04 between-day remainder was not attributed; no deployment metadata beyond the GPU index was collected; nothing was measured on a float32-served model, which would make the dtype half of §1 moot; the §5 backward limitation was not confirmed with NDIF.

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
