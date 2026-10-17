# Review queue

## 1. Needs you
- **Borrow porcupine** (github.com/anishathalye/porcupine, MIT, the checker MIT 6.5840 uses) for linearizability checking? Yes: type `/charter approve porcupine`. No: I write a Wing–Gong checker in `internal/check` (about 200 lines, plus must-fail tests). Until you answer I build the parts that don't depend on it.

## 2. What moved
- Raft node (election, replication, commit, conflict back-up, fsynced state file) with 7 tests, including a deposed leader losing its uncommitted entries and a full-cluster restart from disk. `go test -race` passes.
- Key-value store over Raft (reads go through the log; retried writes apply once) and its client, tested over real localhost TCP.
- `faultnet`: a TCP proxy on each of the 20 one-way links; a cut resets open connections and refuses new ones.
- `cmd/node` (one process per node) and `cmd/torture`. A 10 s dry run: 5 processes, 4 faults (3 crash, 1 partition+crash), 458 completed operations, 1 with unknown outcome. It then stopped at the checker, as it must.
- 2026-10-17: contract written from your picks (Raft KV; miniatures and brick-check loved, janaan days 2-8 rejected).

## 3. Waiting
- **The checker** (`internal/check`), and with it machine checks M3 and M4: blocked on the porcupine question above. Everything else in the deliverable is built.
- The README, which needs M4's numbers.
