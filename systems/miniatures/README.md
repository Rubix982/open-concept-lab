# Systems in Miniature

Seven small simulations of problems from today's AI infrastructure and
backends. Each page shows the failure, then the fix, with numbers.

| # | Page | Go package | The idea underneath |
| - | ---- | ---------- | ------------------- |
| 1 | Routing for a shared prompt cache | `sims/cacherouter` | consistent hashing with bounded loads |
| 2 | Continuous batching | `sims/batching` | iteration-level scheduling |
| 3 | Splitting prompt reading from writing | `sims/disagg` | interference and isolation |
| 4 | The one slow GPU | `sims/straggler` | stragglers, Young–Daly checkpointing |
| 5 | The agent that charged twice | `sims/doublecharge` | idempotency keys and their race |
| 6 | A hundred agents, one rate limit | `sims/herd` | thundering herd, backoff with jitter |
| 7 | Local-first sync | `sims/localfirst` | CRDTs (RGA) |

Every simulation is plain Go with tests that assert its page's claims. The
same code compiles to WebAssembly (`site/mini.wasm`), so the pages run the
real simulation in the browser.

## Run

```bash
go run ./cmd/mini                  # list them
go run ./cmd/mini cache-router     # broken vs fixed, side by side
./build.sh                         # vet, test, rebuild site/mini.wasm, re-bake saved runs
cd site && python3 -m http.server  # then open http://localhost:8000
```

Served over HTTP (or on the site), every page runs the simulation live and
every slider re-runs it. Opened straight from disk, browsers won't load the
WebAssembly, so the pages fall back to saved runs in `site/baked/`: the default
settings plus each option button changed once, recorded by `node bake.mjs`
from the real simulation. A setting that wasn't saved says so instead of
breaking.

## Layout

```
sims/<name>/      one simulation each, with its tests
sims/registry/    every simulation registers itself by name
sims/bridge/      exposes them to the browser as miniRun(name, params)
cmd/mini/         terminal runner
cmd/wasm/         the browser build
site/             the pages; mini.js and common.css are shared
site/baked/       saved runs for opening the pages from disk (bake.mjs)
bake.mjs          records them by driving each page in headless Chrome
```

## Known rough edges

- The models are small on purpose. They show why a fix works, not how fast
  any real system is.
- `site/mini.wasm` is committed (about 3 MB, ~1 MB compressed) because the site
  build doesn't run Go. Rebuild it with `./build.sh` after changing a sim.
