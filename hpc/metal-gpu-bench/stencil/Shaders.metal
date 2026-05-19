/*
 * Shaders.metal — 2D Heat Diffusion Stencil
 * ───────────────────────────────────────────
 * Compute kernel: one GPU thread per grid cell.
 * Render shaders: fullscreen quad mapped to a heatmap texture.
 *
 * The stencil update rule (5-point, equal weights):
 *
 *   new[i][j] = alpha * (old[i-1][j] + old[i+1][j] +
 *                         old[i][j-1] + old[i][j+1])
 *             + (1 - 4*alpha) * old[i][j]
 *
 * alpha = dt * k / (dx²)  — thermal diffusivity × timestep / grid spacing²
 *
 * For stability (no oscillation): alpha ≤ 0.25
 * We use alpha = 0.24 — just inside the stability limit.
 *
 * Boundary condition: fixed temperature at edges (Dirichlet).
 * Interior cells evolve freely. A hot spot is placed at the centre.
 *
 * Ping-pong buffers
 * ──────────────────
 * The stencil reads neighbours from the current state and writes the next
 * state. You cannot read and write the same buffer in one dispatch —
 * race condition: one thread's write would corrupt another thread's read.
 *
 * Solution: two buffers A and B. Even frames: read A, write B. Odd: read B, write A.
 * The CPU swaps the buffer pointers each frame. This is the "ping-pong" pattern,
 * standard in stencil codes, image filters, and iterative solvers.
 *
 * Why 2D threadgroups for stencil?
 * ──────────────────────────────────
 * For 1D work (N-body) a 1D threadgroup is natural — one particle = one thread.
 * For 2D work (grid) a 2D threadgroup maps better to the problem topology.
 * With threadgroup size 16×16, threads in the same group cover a 16×16 tile
 * of the grid. Future optimisation: load the tile + halo into threadgroup
 * (shared) memory once, then all reads within the group are fast on-chip.
 * We start without this — reads go to device memory — to keep the code clear.
 */

#include <metal_stdlib>
using namespace metal;

/* ── Compute kernel ─────────────────────────────────────────────────────── */

struct StencilParams {
    uint  W;       /* grid width  */
    uint  H;       /* grid height */
    float alpha;   /* diffusivity coefficient */
};

/*
 * stencil_step: one thread per interior cell.
 *
 * thread_position_in_grid gives us (x, y) — column and row indices.
 * We guard the boundary cells (held fixed) and the out-of-bounds tail threads.
 */
kernel void stencil_step(
    device const float  *src    [[buffer(0)]],   /* read-only: current state  */
    device       float  *dst    [[buffer(1)]],   /* write-only: next state    */
    constant StencilParams &p   [[buffer(2)]],
    uint2 gid [[thread_position_in_grid]])
{
    uint x = gid.x;
    uint y = gid.y;

    /* guard: don't go out of bounds or touch the boundary ring */
    if (x == 0 || x >= p.W - 1 || y == 0 || y >= p.H - 1) {
        /* boundary cells: write src value unchanged (fixed temperature) */
        if (x < p.W && y < p.H)
            dst[y * p.W + x] = src[y * p.W + x];
        return;
    }

    /* 5-point stencil: read 4 neighbours + centre from src (device memory) */
    float centre = src[ y      * p.W + x    ];
    float left   = src[ y      * p.W + x - 1];
    float right  = src[ y      * p.W + x + 1];
    float up     = src[(y - 1) * p.W + x    ];
    float down   = src[(y + 1) * p.W + x    ];

    /* weighted average — explicit Euler forward in time */
    dst[y * p.W + x] = centre + p.alpha * (left + right + up + down - 4.0f * centre);
}

/* ── Render: fullscreen quad + heatmap colormap ─────────────────────────── */

struct VertOut {
    float4 pos [[position]];
    float2 uv;
};

/*
 * Fullscreen quad via two triangles (triangle strip, 4 vertices).
 * NDC corners: (-1,+1) top-left → (+1,-1) bottom-right
 * UV  corners: (0,0) top-left  → (1,1) bottom-right
 *
 * We hard-code the quad rather than passing a vertex buffer — simpler,
 * and the vertex shader only runs 4 times per frame.
 */
vertex VertOut stencil_vert(uint vid [[vertex_id]])
{
    const float2 positions[4] = {
        float2(-1.0f,  1.0f),   /* top-left     */
        float2( 1.0f,  1.0f),   /* top-right    */
        float2(-1.0f, -1.0f),   /* bottom-left  */
        float2( 1.0f, -1.0f),   /* bottom-right */
    };
    const float2 uvs[4] = {
        float2(0.0f, 0.0f),
        float2(1.0f, 0.0f),
        float2(0.0f, 1.0f),
        float2(1.0f, 1.0f),
    };

    VertOut o;
    o.pos = float4(positions[vid], 0.0f, 1.0f);
    o.uv  = uvs[vid];
    return o;
}

/*
 * stencil_frag: map temperature [0,1] → heatmap color.
 *
 * We use a 4-stop gradient that mimics the classic "hot" colormap:
 *   0.0 → black  (cold)
 *   0.3 → blue
 *   0.6 → red
 *   1.0 → white  (hot)
 *
 * The grid buffer is sampled as a 1D array indexed by UV; we convert
 * UV → (x, y) → linear index and read directly from the buffer.
 * This avoids creating a separate MTLTexture for the grid — the compute
 * output buffer IS the render input.
 */
fragment float4 stencil_frag(
    VertOut                  in    [[stage_in]],
    device const float      *grid  [[buffer(0)]],
    constant StencilParams  &p     [[buffer(1)]])
{
    uint x = (uint)(in.uv.x * (float)p.W);
    uint y = (uint)(in.uv.y * (float)p.H);
    x = clamp(x, 0u, p.W - 1);
    y = clamp(y, 0u, p.H - 1);

    float t = clamp(grid[y * p.W + x], 0.0f, 1.0f);

    /* 4-stop heatmap: black → blue → red → white */
    float3 col;
    if (t < 0.33f) {
        col = mix(float3(0.0f, 0.0f, 0.0f),
                  float3(0.0f, 0.0f, 1.0f),
                  t / 0.33f);
    } else if (t < 0.66f) {
        col = mix(float3(0.0f, 0.0f, 1.0f),
                  float3(1.0f, 0.0f, 0.0f),
                  (t - 0.33f) / 0.33f);
    } else {
        col = mix(float3(1.0f, 0.0f, 0.0f),
                  float3(1.0f, 1.0f, 1.0f),
                  (t - 0.66f) / 0.34f);
    }

    return float4(col, 1.0f);
}
