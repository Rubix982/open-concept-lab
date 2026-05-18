# Plan: Metal GPU Compute Demos — N-body + Heat Stencil

_Status: ready to implement_

## Objective

Build two HPC demos that run the same workload on CPU (pure C + pthreads)
and GPU (Metal compute shader) on an Apple M2 Pro (12-core CPU, 18-core GPU,
unified memory), with live Metal rendering and real-time benchmark numbers.

---

## Why unified memory matters

On a discrete GPU: CPU → GPU data copy is a measurable bottleneck that
inflates GPU benchmark times and muddles the comparison.

On M2 Pro: CPU and GPU share the same physical memory pool. No copy.
We measure pure compute throughput difference, not transfer overhead.
This makes the CPU vs GPU comparison honest.

---

## Demo 1 — N-body Gravity Simulation (build first)

**Algorithm:** N particles, each exerts gravitational force on every other → O(N²)

| | CPU | GPU |
|---|---|---|
| Implementation | Double nested loop + pthreads (12 cores) | Metal compute shader — 1 particle = 1 GPU thread |
| Parallelism | 12 threads, work split by particle index | ~576+ concurrent threads (18 cores × 32/core minimum) |
| Render | Metal render pipeline — particles as colored points | velocity magnitude → color gradient (slow=blue, fast=red) |
| Scale | N=1 000 baseline → N=100 000 to stress | CPU falls over around N=10k; GPU shrugs |

**Why build first:** most dramatic visual, clearest O(N²) scaling story,
best introduction to GPU parallelism as a concept.

---

## Demo 2 — 2D Heat Diffusion Stencil (build second, reuses boilerplate)

**Algorithm:** Iterative 5-point stencil — each cell becomes weighted average
of itself and its 4 neighbours. Models heat spreading across a 2D plate.

```
new[i][j] = 0.25 * (old[i-1][j] + old[i+1][j] + old[i][j-1] + old[i][j+1])
```

| | CPU | GPU |
|---|---|---|
| Implementation | Nested loop + pthreads | Metal compute shader — 1 cell = 1 GPU thread |
| Render | Grid as a live heatmap texture — hot=red, cold=blue | |
| Scale | 512×512 baseline → 4096×4096 to stress | CPU becomes slideshow; GPU stays real-time |

**Why build second:** shares 80% of Demo 1's Metal boilerplate. Swap the
shader and data layout; everything else is the same.

---

## Shared Architecture (the 80% boilerplate)

```
MetalBase (.m / .h)
├── MTLDevice acquisition
├── MTLCommandQueue setup
├── CAMetalLayer + NSWindow + AppKit run loop
├── Render pass descriptor (clear + present)
├── Benchmark overlay (FPS, CPU ms, GPU ms drawn as text)
└── Results logger → results/<timestamp>_<cpu>.txt
```

Both demos instantiate MetalBase and add their own:
- Compute pipeline (their .metal shader)
- Data buffers (particles or grid)
- CPU thread pool (pthreads)

---

## Directory Structure

```
hpc/
└── metal-gpu-bench/
    ├── PLAN.md                  ← this file
    ├── common/
    │   ├── MetalBase.h          ← shared Metal boilerplate header
    │   └── MetalBase.m          ← device, window, render loop, benchmark overlay
    ├── nbody/
    │   ├── main.m               ← N-body app entry point
    │   ├── NBodySimulator.h/m   ← CPU pthreads + GPU dispatch coordination
    │   ├── Shaders.metal        ← compute kernel (gravity) + render (point sprites)
    │   └── Makefile
    ├── stencil/
    │   ├── main.m               ← stencil app entry point
    │   ├── StencilSimulator.h/m ← CPU pthreads + GPU dispatch coordination
    │   ├── Shaders.metal        ← compute kernel (5-pt stencil) + heatmap render
    │   └── Makefile
    └── results/                 ← auto-saved benchmark outputs (gitignored)
```

---

## Metal Pipeline Stages

### N-body
```
each frame:
  [Compute pass]
    kernel nbody_update(particles[], N, dt)  — reads all, writes velocities + positions
  [Render pass]
    vertex:   particle position → clip space
    fragment: velocity magnitude → color
  [Present]
```

### Stencil
```
each frame (ping-pong between two grid buffers):
  [Compute pass]
    kernel stencil_step(gridA[], gridB[], W, H)  — reads A, writes B
  [Render pass]
    vertex:   fullscreen quad
    fragment: sample gridB as texture → heatmap color
  [Present]
  swap gridA ↔ gridB
```

---

## Tech Stack

- **Language:** Objective-C (.m) + MSL Metal Shading Language (.metal) + pure C (.c)
- **Frameworks:** Metal, MetalKit, AppKit, Foundation — nothing external
- **Build:** `clang` + `xcrun -sdk macosx metal` / `metallib`
- **M2 Pro threadgroup size:** 32×1 for N-body (1D), 16×16 for stencil (2D)

---

## Build Order (incremental, testable at each step)

1. `common/MetalBase` — window opens, clears to black, FPS counter visible
2. `nbody/` CPU only — particles move on screen, no GPU yet
3. `nbody/` GPU compute shader — switch between CPU/GPU with keypress
4. `nbody/` benchmark overlay — live CPU ms vs GPU ms
5. `stencil/` — reuse MetalBase, add stencil shader + heatmap render
6. `stencil/` benchmark overlay + stress test

---

## Risks / Tricky Parts

| Risk | Mitigation |
|---|---|
| MSL threadgroup size must divide evenly into grid | pad grid to nearest multiple of threadgroup size |
| N-body GPU reads all N particles per thread — shared memory optimisation possible later | start naive (global memory), note it as a next step |
| CPU pthreads timing vs GPU command buffer timing are measured differently | use `mach_absolute_time` for CPU; `MTLCommandBuffer` completion handler for GPU |
| AppKit + Metal layer setup is verbose | encapsulate fully in MetalBase so demos stay clean |

---

## Next Steps After This

- Add SIMD intrinsics to the CPU path (NEON on ARM) for a fairer CPU ceiling
- N-body GPU shared memory tiling (threadgroup memory optimisation)
- Export final frame as PNG for the results archive
