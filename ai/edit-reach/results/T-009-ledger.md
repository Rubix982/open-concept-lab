# T-009 ledger — does the floor median move when the device set does?

Appended by `agents/engineer/workspace/run_t009.py`, one reading a day.
42 floor probes, layer 5, Llama-3.1-8B, one fresh connection each.

Floor medians are printed at **full precision**. The whole point of
this table is that values repeat to the last bit; rendering them at
eight decimals would hide exactly what it exists to show, and did,
in its first draft.

| date | time | source | GPUs | floor median | anchor control | signature |
|---|---|---|---|---|---|---|
| 2026-10-31 | — | E-001 | ? | `0.08087725` | nan | — |
| 2026-11-01 | — | E-005/language#0 | ? | `0.08094214687103357` | nan | — |
| 2026-11-01 | — | E-005/language#1 | ? | `0.08109313181234508` | nan | — |
| 2026-11-01 | — | E-005/language#2 | ? | `0.08109313181234508` | nan | — |
| 2026-11-01 | — | E-005/transformers#0 | ? | `0.08109313181234508` | nan | — |
| 2026-11-01 | — | E-005/transformers#1 | ? | `0.08109313181234508` | nan | — |
| 2026-11-01 | — | E-005/transformers#2 | ? | `0.08109313181234508` | nan | — |
| 2026-11-01 | — | E-006 | 0 | `0.08109002151514136` | nan | edd2b2b152de2098 |
| 2026-11-01 | — | E-006 | 2 | `0.08109313181234508` | nan | 54a1755349e607dc |
| 2026-11-03 | 15:33:58+0500 | T-009 | 0 | `0.08109002151514136` | 0.000e+00 | edd2b2b152de2098 |

## What the ledger says today

```

value census -- distinct values and how often each recurs

  0.08087725             n=1   GPUs unrecorded 2026-10-31
  0.08094214687103357    n=1   GPUs unrecorded 2026-11-01
  0.08109002151514136    n=9   GPUs 0          2026-11-01 2026-11-03
  0.08109313181234508    n=13  GPUs 2          2026-11-01

  4 distinct values over 24 readings
  1 of them recur across more than one day, bit-exactly

  A value that repeats to the last bit on a different day is
  not drift. It is a fingerprint of which replica served you.
readings        10  (3 with a known device set)
floor median    0.08087725 .. 0.08109313   range 2.159e-04
days            3  2026-10-31 .. 2026-11-03
device sets     ['0', '2']

  BIT-IDENTICAL ACROSS DAYS
    edd2b2b152de2098  GPUs 0        2026-11-01 and 2026-11-03   floor identical: True
    A reading reproduces exactly across days when the reported
    device matches. There is no day effect to find for a
    device-matched comparison; the drift lives in WHICH replica
    served you, and readings whose device went unrecorded cannot
    be attributed after the fact.

  GPUs 0        n=2   median 0.08109002  spread 0.000e+00
  GPUs 2        n=1   median 0.08109313  spread 0.000e+00
  spread WITHIN a device set   0.000e+00
  spread ACROSS everything     2.159e-04

  Within a device the spread is EXACTLY ZERO, across days.
  So there is no time component to find: a reading is a
  function of which replica served it and nothing else that
  has been varied. What remains open is narrower than T-009
  was opened for -- not 'what causes the drift' but 'how many
  replicas are there', and the readings that would answer it
  did not record their device and cannot be made to now.
```
