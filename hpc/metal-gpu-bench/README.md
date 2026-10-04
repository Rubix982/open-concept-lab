# Metal GPU Bench

The same two workloads on an Apple Silicon GPU and CPU: **N-body gravity**
(compute-bound, O(N²)) and a **2D heat stencil** (memory-bound). See
[PLAN.md](PLAN.md) for the design.

## The web page

Open `site/index.html`. It works straight from disk (`file://`) or over HTTP.

- **Top:** a live GPU render, either a galaxy collision or heat on a plate. On
  WebGPU it runs on your GPU (tiled N-body kernel, additive glow, trails;
  stencil kernel with paintable heat), and "Run the same on one CPU core"
  runs the same JavaScript on one core for comparison. Without WebGPU it
  plays the recording made on this Mac's GPU with Metal, drawn with WebGL2.
- **Below:** the measured results from `data/native.js`, with no computation:
  native Metal vs C on all cores, the browser engines, and the top animation
  measured at full size.

## Measure (macOS, Command Line Tools are enough)

```bash
cd bench
make                    # builds ./bench
./bench                 # CPU (C, all cores) vs GPU (Metal) timings -> results/bench-<date>.json
./bench --frames        # records both kernels on the GPU            -> results/frames-<date>.json
node browser-bench.mjs  # WebGPU vs JavaScript in headless Chrome    -> results/browser-<date>.json
python3 export.py       # bakes them into site/data/native.js and site/data/frames.js
```

`./bench` compiles `nbody/Shaders.metal` and `stencil/Shaders.metal` from
source at runtime, so Xcode's offline `metal` compiler isn't needed.
`browser-bench.mjs` needs Node 22+ and Chrome (or set `CHROME=`).

## The interactive apps

`nbody/` and `stencil/` are windowed AppKit demos (press G to switch CPU/GPU).
They load a precompiled `Shaders.metallib`, which needs Xcode's `metal` tool:
`cd nbody && make run`.

## Known rough edges

- The 2026-10-04 numbers were taken while the machine was busy with other
  work (load average about 6–12 on 12 cores). Large sizes held steady across
  runs; small sizes are noisy. Rerun on a quiet machine for cleaner numbers.
- The page's galaxy and heat scenes differ from the native apps on purpose:
  no wrap-around, a galaxy-collision set-up, held-hot heat sources. The
  measured tables use the projects' own kernels.
- The recording is 2,048 bodies and a 64 × 64 downsample of the plate, to
  keep `frames.js` under 2 MB.
