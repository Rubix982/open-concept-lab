/*
 * Shaders.metal — N-body simulation
 * ───────────────────────────────────
 * Two shader stages:
 *   1. nbody_update  — compute kernel: integrate gravity for all particles
 *   2. nbody_vert    — vertex shader: position → clip space
 *   3. nbody_frag    — fragment shader: velocity magnitude → color
 *
 * Metal Shading Language (MSL) is C++14 with GPU extensions.
 * Key additions over standard C++:
 *   [[thread_position_in_grid]]  — which thread am I? (replaces loop index)
 *   [[buffer(n)]]                — bind a CPU buffer to this argument
 *   [[position]]                 — vertex output position (required)
 *   device / constant            — address spaces (where does this pointer live?)
 *
 * Address spaces on Apple GPU
 * ────────────────────────────
 *   device   — GPU global memory (backed by unified RAM on M2 Pro)
 *              All threads can read/write. Slowest of the GPU address spaces.
 *   constant — read-only, cached. Use for params shared across all threads.
 *   threadgroup — on-chip shared memory per thread group (~32 KB on M2).
 *                 Lightning fast. Visible only to threads in the same group.
 *   thread   — private per-thread registers. Fastest. No explicit keyword needed.
 *
 * Why this compute kernel is naive (and that's intentional)
 * ──────────────────────────────────────────────────────────
 * Each thread reads ALL N positions to compute forces on its one particle.
 * That is N reads from `device` memory per thread, N threads total → O(N²) reads.
 * A threadgroup-tiled version would load blocks of positions into threadgroup
 * memory and amortise the reads across the tile — that is the "next step" noted
 * in PLAN.md. We start naive so the algorithm is readable.
 */

#include <metal_stdlib>
using namespace metal;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Data layout — must match cpu_nbody.h exactly                                */
/* ─────────────────────────────────────────────────────────────────────────── */

struct Particle {
    float2 pos;   /* x, y in [-1, 1] NDC space */
    float2 vel;   /* velocity (NDC units / second) */
    float  mass;
    float  _pad;  /* align to 16 bytes */
};

struct NBodyParams {
    uint   N;         /* particle count          */
    float  dt;        /* timestep (seconds)      */
    float  softening; /* softening factor ε²     */
    float  G;         /* gravitational constant  */
};

/* ─────────────────────────────────────────────────────────────────────────── */
/* Compute kernel — one thread per particle                                    */
/* ─────────────────────────────────────────────────────────────────────────── */

kernel void nbody_update(
    device Particle        *particles [[buffer(0)]],   /* read + write        */
    constant NBodyParams   &params    [[buffer(1)]],   /* read-only params    */
    uint                    gid       [[thread_position_in_grid]])
{
    /* Guard: last threadgroup may extend beyond N */
    if (gid >= params.N) return;

    Particle p = particles[gid];   /* load my particle into thread-local registers */

    float2 force = float2(0.0f, 0.0f);

    /*
     * For each other particle j, accumulate gravitational force on particle i.
     *
     * F = G * mi * mj / (r² + ε²)  ×  direction
     *
     * ε² (softening) prevents the force from blowing up when two particles
     * get very close (r→0). Standard technique in N-body simulations.
     *
     * This inner loop reads particles[j].pos from `device` memory.
     * On M2 Pro each read is a unified-memory access — same physical RAM
     * the CPU uses. No copy, but still subject to cache pressure at large N.
     */
    for (uint j = 0; j < params.N; j++) {
        if (j == gid) continue;
        float2 r    = particles[j].pos - p.pos;
        float  r2   = dot(r, r) + params.softening;
        float  inv  = rsqrt(r2);               /* 1/sqrt(r²+ε²) — hardware instruction */
        float  inv3 = inv * inv * inv;         /* 1/(r²+ε²)^(3/2) */
        force += params.G * particles[j].mass * r * inv3;
    }

    /* Leapfrog (symplectic Euler) integration:
     *   vel += force * dt   (force is acceleration because mass normalised)
     *   pos += vel   * dt
     * Leapfrog conserves energy better than forward Euler for orbits.       */
    p.vel += force * params.dt;
    p.pos += p.vel * params.dt;

    /* Wrap-around boundary: particles that leave [-1,1] reappear on the other side */
    p.pos = fmod(p.pos + 3.0f, 2.0f) - 1.0f;

    particles[gid] = p;   /* write back to device memory */
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Render: vertex + fragment shaders for drawing particles as point sprites    */
/* ─────────────────────────────────────────────────────────────────────────── */

struct VertexOut {
    float4 position [[position]];   /* clip-space position (required)    */
    float  speed;                   /* passed to fragment for coloring   */
    float  pointSize [[point_size]];
};

/*
 * nbody_vert: one invocation per particle.
 * vid indexes into the particle buffer — same data the compute kernel wrote.
 * No transformation matrix needed: positions are already in NDC [-1,1].
 */
vertex VertexOut nbody_vert(
    uint                    vid       [[vertex_id]],
    device const Particle  *particles [[buffer(0)]],
    constant NBodyParams   &params    [[buffer(1)]])
{
    Particle p = particles[vid];

    VertexOut o;
    o.position  = float4(p.pos, 0.0f, 1.0f);
    o.speed     = length(p.vel);
    /*
     * Point size in pixels. Larger = more visible at low N.
     * At N=100k you'd reduce this to 1.0 to avoid overdraw.
     */
    o.pointSize = 3.0f;
    return o;
}

/*
 * nbody_frag: color each particle by speed.
 * slow (speed≈0) → deep blue
 * fast (speed≈0.01+) → bright yellow/white
 *
 * Color map: blue → cyan → green → yellow → white
 * This is a simple linear ramp; a proper perceptual colormap (viridis etc.)
 * would be better for scientific use.
 */
fragment float4 nbody_frag(VertexOut in [[stage_in]])
{
    float t = saturate(in.speed * 80.0f);   /* normalise to [0,1] */

    /* Three-stop gradient: blue → cyan → yellow */
    float3 col;
    if (t < 0.5f) {
        col = mix(float3(0.1f, 0.2f, 0.9f),   /* blue  */
                  float3(0.0f, 0.9f, 0.9f),   /* cyan  */
                  t * 2.0f);
    } else {
        col = mix(float3(0.0f, 0.9f, 0.9f),   /* cyan   */
                  float3(1.0f, 1.0f, 0.4f),   /* yellow */
                  (t - 0.5f) * 2.0f);
    }

    return float4(col, 1.0f);
}
