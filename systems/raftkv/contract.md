# Contract: raftkv

_Opened: 2026-10-17 · Gate rhythm: at each turn end while the person is here · Budget before mandatory review: one session · Parallel streams: ≤ 1_

## Deliverable
`systems/raftkv`: a 5-node Raft key-value store, each node its own OS process talking TCP, that survives crash, restart and partition faults with every recorded client history checked linearizable, by 2026-10-18.

## Machine checks
| id | Check | Command / measure | Cannot see | Status |
|---|---|---|---|---|
| M1 | vets and builds | `go vet ./... && go build ./...` | whether the design is right | provisional |
| M2 | unit tests under the race detector | `go test -race -count=1 ./...` | real processes, real sockets, real timing | provisional |
| M3 | the checker fails histories it must fail | `go test -count=1 -run MustFail ./internal/check/...` | bugs unlike the planted ones | provisional |
| M4 | 5 real processes under crash, restart and partition faults: every history linearizable, and progress made | `go run ./cmd/torture -nodes 5 -clients 8 -duration 20s -seed 1` | other seeds, longer runs, performance under load | provisional |

## Human criteria
| id | Criterion | Exemplars |
|---|---|---|
| H1 | The README states what was shown, with numbers, and how to rerun it, the way miniatures does | loved: systems/miniatures · rejected: janaan days 2–8 |
| H2 | The code reads like the surrounding Go in miniatures: small packages, plain names, tests that assert the claims | loved: systems/miniatures/sims |
| H3 | It is honestly "real distributed": separate processes, real network, real faults, not a simulation in one process | loved: brick-check · rejected: a green gate standing in for the claim |

## Exemplars
- Loved: systems/miniatures — "Every simulation is plain Go with tests that assert its page's claims."
- Loved: projects/brick-check — "The design is only as trustworthy as its checker, so the checker is the part with tests."
- Rejected: janaan, days 2–8 (2026-10-11..17) — every gate passed, all five pieces failed the standard, and nothing was finished.

## Non-goals
- Membership changes, log compaction and snapshots
- Byzantine faults, disk corruption, clock skew
- Production performance tuning, or a client library for other languages
- A web page (miniatures has those; this one is a CLI and a README)

## Approved changes
<!-- Direction changes the person said yes to. Only the person adds lines here (with the plugin: /charter approve <what>). -->

## Assumptions the agent made (queued for the next gate)
- Go, standard library first. A linearizability checker is the one part worth borrowing (porcupine); that needs the person's approval.
- Nodes persist term, vote and log to a file per node, fsynced, so a restarted process recovers.
- "Progress" in M4 means at least 200 completed client operations across the run.

## Amendments
<!-- The only way the objective changes. One dated line each. If the aim changes, restate the deliverable and its date. -->
