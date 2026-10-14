# dryruns

Verdict bands exercised on known-answer data, kept in the repository and **executed** by
`tools/preflight.py` — not merely checked for. A dry-run in a scratch directory is a claim,
not a check: the next person cannot re-run it.

Each file's first case feeds a **published** result back through the reporting path and
requires its published verdict. The dangerous bug is the one that agrees with you, and a
path verified only on data you invented can still agree with you.

## What a dry-run cannot do

[E-036] passed every gate — preflight 6/6, all four verdict branches exercised, zero
unsorted triage lines — and still measured two of its six criteria in ways that could not
answer their own questions. One of those confounds was named in the ticket *before* the run.

**Gates catch broken code and broken process. A construct-validity error passes all of
them**, because the code does exactly what it was asked and the question was wrong. The
only thing that catches it is a person reading the numbers and asking whether the
measurement could have come out any other way.

Write the dry-run anyway. Just do not mistake a green harness for a sound experiment.
