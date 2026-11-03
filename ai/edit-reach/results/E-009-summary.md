# [E-009] The partition did not reproduce — 2026-11-03

32 remote traces, 16 fresh connections per model, layer 5.

```
                 connections   distinct signatures   devices   spread
Llama-3.1-8B              16                     1   GPU 0     0.000e+00
GPT-J-6B                  16                     1   GPU 0     0.000e+00
```

[E-006] on 2026-11-01, same 16 connections, same model: **two** signatures, 8 on GPU 0 and 8 on GPU 2, clean partition in both directions.

**What changed is the deployment, not the measurement.** Two models both served entirely from GPU 0 means one device was in play on 2026-11-03. The partition is a property of a deployment on a day.

**Why the negative is worth the traces.** A tolerance justified by "readings partition by device" is justified by nothing on a day like this, and a reader of the first version of section 2 would have had no reason to check which kind of day they were having.

**It promotes a T-009 candidate.** The device set serving Llama-3.1-8B changed between 11-01 and 11-03, which is an observed deployment change sitting between the sessions whose floor medians differ by the unattributed ~2e-04. Not a measurement of the drift — nothing shows the two move together — but no longer a guess.

**A fault in the suite, the third of its kind.** `clean_partition` read `True` for sixteen identical readings off one GPU, both conditions being vacuously true with one of each. Now reports `n/a - nothing to partition`.
