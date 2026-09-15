# Run logs

Kept deliberately. A results file records *what a run produced*; only a log records
*what it did* — which model, which parameters, which retries, which batches were
split after an out-of-memory response, which items were skipped and why.

Every log's first two lines are the run name and its config, so the file is
self-describing without reference to the code that has since changed.

Written by `src/logs.py`. The console view may be filtered; this is not.
