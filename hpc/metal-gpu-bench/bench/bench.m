/*
 * bench.m — headless CPU vs GPU timing for both demos, no window.
 *
 * The interactive apps need an offline-compiled .metallib (Xcode's `metal`
 * tool). This tool doesn't: it compiles the very same nbody/Shaders.metal and
 * stencil/Shaders.metal from source at runtime (newLibraryWithSource), which
 * works with only the Command Line Tools installed.
 *
 * CPU side: the same per-element math as NBodySimulator.m / StencilSimulator.m,
 * split across one pthread per core.
 * GPU side: the same compute kernels, one dispatch per step, timed with the
 * command buffer's GPUStartTime / GPUEndTime (GPU execution only).
 *
 * Output: results/bench-<date>.json (and a table on stdout).
 *
 *   make && ./bench           timings  -> results/bench-<date>.json
 *   ./bench --frames          recorded playback -> results/frames-<date>.json
 *   python3 export.py         bakes both into site/data/ for the page
 */

#import <Foundation/Foundation.h>
#import <Metal/Metal.h>
#include <mach/mach_time.h>
#include <pthread.h>
#include <sys/sysctl.h>
#include <math.h>

typedef struct { float pos[2]; float vel[2]; float mass; float _pad; } Particle;
typedef struct { uint32_t N; float dt; float softening; float G; } NBodyParams;
typedef struct { uint32_t W; uint32_t H; float alpha; } StencilParams;

static double now_ms(void) {
    static mach_timebase_info_data_t tb;
    if (!tb.denom) mach_timebase_info(&tb);
    return (double)mach_absolute_time() * tb.numer / tb.denom / 1e6;
}

static int cmp_double(const void *a, const void *b) {
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

/* Best of the repeats: other work on the machine only ever makes a step
   slower, so the minimum is the least disturbed measurement. */
static double best(double *v, int n) {
    qsort(v, n, sizeof(double), cmp_double);
    return v[0];
}

/* ── CPU N-body: copied from nbody/NBodySimulator.m ─────────────────────── */
typedef struct { Particle *ps; NBodyParams *pr; uint32_t start, end; } NBArgs;

static void *nbody_worker(void *arg) {
    NBArgs *w = arg; Particle *ps = w->ps; NBodyParams *pr = w->pr; uint32_t N = pr->N;
    for (uint32_t i = w->start; i < w->end; i++) {
        float fx = 0.f, fy = 0.f;
        for (uint32_t j = 0; j < N; j++) {
            if (j == i) continue;
            float dx = ps[j].pos[0] - ps[i].pos[0];
            float dy = ps[j].pos[1] - ps[i].pos[1];
            float r2 = dx*dx + dy*dy + pr->softening;
            float inv = 1.f / sqrtf(r2);
            float inv3 = inv * inv * inv;
            float f = pr->G * ps[j].mass * inv3;
            fx += f * dx; fy += f * dy;
        }
        ps[i].vel[0] += fx * pr->dt; ps[i].vel[1] += fy * pr->dt;
        ps[i].pos[0] += ps[i].vel[0] * pr->dt; ps[i].pos[1] += ps[i].vel[1] * pr->dt;
        ps[i].pos[0] = fmodf(ps[i].pos[0] + 3.f, 2.f) - 1.f;
        ps[i].pos[1] = fmodf(ps[i].pos[1] + 3.f, 2.f) - 1.f;
    }
    return NULL;
}

/* ── CPU stencil: copied from stencil/StencilSimulator.m ────────────────── */
typedef struct { const float *src; float *dst; StencilParams *p; uint32_t r0, r1; } STArgs;

static void *stencil_worker(void *arg) {
    STArgs *w = arg; uint32_t W = w->p->W, H = w->p->H; float a = w->p->alpha;
    for (uint32_t y = w->r0; y < w->r1; y++) {
        if (y == 0 || y == H - 1) { memcpy(w->dst + y*W, w->src + y*W, W*sizeof(float)); continue; }
        w->dst[y*W] = w->src[y*W]; w->dst[y*W + W-1] = w->src[y*W + W-1];
        for (uint32_t x = 1; x < W - 1; x++) {
            float c = w->src[y*W + x];
            w->dst[y*W + x] = c + a * (w->src[y*W + x-1] + w->src[y*W + x+1] + w->src[(y-1)*W + x] + w->src[(y+1)*W + x] - 4.f*c);
        }
    }
    return NULL;
}

static id<MTLComputePipelineState> pipeline(id<MTLDevice> dev, NSString *file, NSString *fn) {
    NSError *err = nil;
    NSString *src = [NSString stringWithContentsOfFile:file encoding:NSUTF8StringEncoding error:&err];
    if (!src) { fprintf(stderr, "cannot read %s\n", file.UTF8String); exit(1); }
    id<MTLLibrary> lib = [dev newLibraryWithSource:src options:nil error:&err];
    if (!lib) { fprintf(stderr, "compile %s: %s\n", file.UTF8String, err.localizedDescription.UTF8String); exit(1); }
    id<MTLComputePipelineState> ps = [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:fn] error:&err];
    if (!ps) { fprintf(stderr, "pipeline %s: %s\n", fn.UTF8String, err.localizedDescription.UTF8String); exit(1); }
    return ps;
}

/* Apple GPUs ramp their clock with load; time only after ~500 ms of work so
   small sizes aren't measured at idle clocks. */
static void warm(id<MTLCommandQueue> q, void (^encode)(id<MTLComputeCommandEncoder>)) {
    double t0 = now_ms();
    while (now_ms() - t0 < 500) {
        id<MTLCommandBuffer> cb = [q commandBuffer];
        id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
        encode(enc);
        [enc endEncoding];
        [cb commit]; [cb waitUntilCompleted];
    }
}

static NSString *sysctl_str(const char *name) {
    char buf[256]; size_t n = sizeof buf;
    return sysctlbyname(name, buf, &n, NULL, 0) == 0 ? [NSString stringWithUTF8String:buf] : @"unknown";
}

/* ── --frames: record the kernels running on the GPU, for the web page ────
 *
 * Stencil: the project's stencil_step on a 1024 x 1024 plate that starts with
 * five hot discs (the native kernel has no heaters, so they spread and fade),
 * snapshotted at growing intervals, each frame averaged down to 64 x 64 and
 * stored as round(255 * sqrt(temperature)) so faint warmth stays visible.
 * N-body: a galaxy collision of 2,048 bodies (the same force law as
 * nbody_update, without the wrap-around), positions as int16.
 * Each frame's steps run in one command buffer; GPU time per step is the sum
 * of GPUEndTime - GPUStartTime over all frames divided by the steps.
 */
static NSDictionary *record_stencil(id<MTLDevice> dev, id<MTLCommandQueue> q, id<MTLComputePipelineState> ps) {
    const uint32_t W = 1024, D = 64, B = W / D;
    const int frames = 40;
    size_t bytes = (size_t)W * W * sizeof(float);
    id<MTLBuffer> buf[2] = {[dev newBufferWithLength:bytes options:MTLResourceStorageModeShared],
                            [dev newBufferWithLength:bytes options:MTLResourceStorageModeShared]};
    float *g = buf[0].contents;
    memset(g, 0, bytes);
    float discs[5][3] = {{300, 330, 46}, {690, 260, 30}, {560, 640, 70}, {240, 760, 24}, {820, 820, 38}};
    for (int k = 0; k < 5; k++)
        for (uint32_t y = 1; y < W - 1; y++)
            for (uint32_t x = 1; x < W - 1; x++) {
                float dx = x - discs[k][0], dy = y - discs[k][1];
                if (dx*dx + dy*dy < discs[k][2]*discs[k][2]) g[y*W + x] = 1.f;
            }
    StencilParams p = {W, W, 0.24f};
    id<MTLBuffer> pbuf = [dev newBufferWithBytes:&p length:sizeof p options:MTLResourceStorageModeShared];
    NSMutableData *pix = [NSMutableData dataWithLength:(size_t)frames * D * D];
    uint8_t *out = pix.mutableBytes;
    NSMutableArray *stepAt = [NSMutableArray array];
    int cur = 0; long steps = 0; double gpuMs = 0;
    for (int f = 0; f < frames; f++) {
        const float *src = buf[cur].contents;
        for (uint32_t by = 0; by < D; by++)
            for (uint32_t bx = 0; bx < D; bx++) {
                double acc = 0;
                for (uint32_t y = 0; y < B; y++) for (uint32_t x = 0; x < B; x++) acc += src[(by*B + y)*W + bx*B + x];
                double v = fmax(0, fmin(1, acc / (B*B)));
                out[(size_t)f*D*D + by*D + bx] = (uint8_t)lround(255 * sqrt(v));
            }
        [stepAt addObject:@(steps)];
        int every = (int)lround(40 * pow(1.085, f));   /* fast change early, slower later */
        id<MTLCommandBuffer> cb = [q commandBuffer];
        for (int s = 0; s < every; s++) {
            id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
            [enc setComputePipelineState:ps];
            [enc setBuffer:buf[cur] offset:0 atIndex:0];
            [enc setBuffer:buf[1-cur] offset:0 atIndex:1];
            [enc setBuffer:pbuf offset:0 atIndex:2];
            [enc dispatchThreadgroups:MTLSizeMake(W/16, W/16, 1) threadsPerThreadgroup:MTLSizeMake(16, 16, 1)];
            [enc endEncoding];
            cur = 1 - cur;
        }
        [cb commit]; [cb waitUntilCompleted];
        gpuMs += (cb.GPUEndTime - cb.GPUStartTime) * 1000.0;
        steps += every;
    }
    return @{@"grid": @(W), @"size": @(D), @"frames": @(frames), @"stepAt": stepAt,
             @"msPerStep": @(gpuMs / steps), @"encoding": @"uint8, round(255 * sqrt(temperature)), row-major frames",
             @"data": [pix base64EncodedStringWithOptions:0]};
}

/* The galaxy collision the page's hero shows, so the recording and the live
   WebGPU version start alike (see site/hero.js, galaxies()): two discs of
   bodies, each around a heavy core, spinning the same way and passing close.
   Same force law as nbody_update, but with no wrap-around at the edges, so
   flung-out bodies fly off instead of reappearing on the far side. */
static NSString *const GALAXY_MSL = @"#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "struct Particle { float2 pos; float2 vel; float mass; float _pad; };\n"
    "struct NBodyParams { uint N; float dt; float softening; float G; };\n"
    "kernel void galaxy_step(device const Particle *src [[buffer(0)]], device Particle *dst [[buffer(1)]],\n"
    "                        constant NBodyParams &p [[buffer(2)]], uint i [[thread_position_in_grid]]) {\n"
    "  if (i >= p.N) return;\n"
    "  Particle me = src[i]; float2 f = 0;\n"
    "  for (uint j = 0; j < p.N; j++) { float2 r = src[j].pos - me.pos; float inv = rsqrt(dot(r, r) + p.softening);\n"
    "    f += src[j].mass * r * (inv * inv * inv); }\n"
    "  me.vel += p.G * f * p.dt; me.pos += me.vel * p.dt; dst[i] = me;\n"
    "}\n";

/* matches galaxies() in site/hero.js */
static void galaxy_init(Particle *P, uint32_t N, uint64_t seed) {
    srand48((long)seed);
    uint32_t half = N / 2;
    float cx[2] = {-0.45f, 0.45f}, cy[2] = {0.2f, -0.2f}, vx[2] = {0.55f, -0.55f}, vy[2] = {-0.12f, 0.12f};
    const float Mc = 3.0f, Md = 1.0f, soft = 0.0009f;
    for (int g = 0; g < 2; g++) {
        uint32_t o = g * half;
        P[o] = (Particle){{cx[g], cy[g]}, {vx[g], vy[g]}, Mc, 0};
        for (uint32_t k = 1; k < half; k++) {
            float u = (float)k / half, r = 0.04f + 0.26f * powf(u, 0.8f);
            float a = (float)drand48() * 2 * M_PI;
            float inside = Mc + Md * u;                       /* bodies are added outward */
            float v = sqrtf(inside / sqrtf(r * r + soft));
            P[o + k] = (Particle){{cx[g] + r * cosf(a), cy[g] + r * sinf(a)},
                                  {vx[g] + v * sinf(a), vy[g] - v * cosf(a)},   /* clockwise, with the passage */
                                  Md / (half - 1), 0};
        }
    }
}

static NSDictionary *record_nbody(id<MTLDevice> dev, id<MTLCommandQueue> q) {
    const uint32_t N = 8192;
    const int frames = 96, every = 60;
    NSError *err = nil;
    id<MTLLibrary> lib = [dev newLibraryWithSource:GALAXY_MSL options:nil error:&err];
    if (!lib) { fprintf(stderr, "galaxy kernel: %s\n", err.localizedDescription.UTF8String); exit(1); }
    id<MTLComputePipelineState> ps = [dev newComputePipelineStateWithFunction:[lib newFunctionWithName:@"galaxy_step"] error:&err];
    id<MTLBuffer> buf[2] = {[dev newBufferWithLength:N * sizeof(Particle) options:MTLResourceStorageModeShared],
                            [dev newBufferWithLength:N * sizeof(Particle) options:MTLResourceStorageModeShared]};
    galaxy_init(buf[0].contents, N, 7);
    NBodyParams prm = {N, 0.0008f, 0.0009f, 1.0f};
    id<MTLBuffer> pbuf = [dev newBufferWithBytes:&prm length:sizeof prm options:MTLResourceStorageModeShared];
    NSMutableData *pos = [NSMutableData dataWithLength:(size_t)frames * N * 2 * sizeof(int16_t)];
    int16_t *po = pos.mutableBytes;
    const float span = 1.6f;   /* positions stored over [-1.6, 1.6] */
    int cur = 0; double gpuMs = 0;
    for (int f = 0; f < frames; f++) {
        Particle *P = buf[cur].contents;
        for (uint32_t i = 0; i < N; i++) {
            float x = P[i].pos[0] / span, y = P[i].pos[1] / span;
            /* a body flung outside the recorded square is marked gone, not
               pinned to the border */
            int out = !(fabsf(x) <= 1 && fabsf(y) <= 1);
            po[((size_t)f*N + i)*2]     = out ? INT16_MIN : (int16_t)lroundf(x * 32767);
            po[((size_t)f*N + i)*2 + 1] = out ? INT16_MIN : (int16_t)lroundf(y * 32767);
        }
        id<MTLCommandBuffer> cb = [q commandBuffer];
        for (int s = 0; s < every; s++) {
            id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
            [enc setComputePipelineState:ps];
            [enc setBuffer:buf[cur] offset:0 atIndex:0];
            [enc setBuffer:buf[1-cur] offset:0 atIndex:1];
            [enc setBuffer:pbuf offset:0 atIndex:2];
            [enc dispatchThreadgroups:MTLSizeMake(N / 256, 1, 1) threadsPerThreadgroup:MTLSizeMake(256, 1, 1)];
            [enc endEncoding];
            cur = 1 - cur;
        }
        [cb commit]; [cb waitUntilCompleted];
        gpuMs += (cb.GPUEndTime - cb.GPUStartTime) * 1000.0;
    }
    return @{@"bodies": @(N), @"frames": @(frames), @"stepsPerFrame": @(every), @"dt": @(prm.dt), @"span": @(span),
             @"msPerStep": @(gpuMs / (frames * every)), @"scene": @"galaxy collision (site/hero.js galaxies())",
             @"encoding": @"pos: int16 pairs (x, y) / 32767 * span, per body per frame; -32768 = outside the square",
             @"pos": [pos base64EncodedStringWithOptions:0]};
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        NSString *here = [[NSString stringWithUTF8String:argv[0]] stringByDeletingLastPathComponent];
        NSString *root = [here stringByAppendingPathComponent:@".."];
        BOOL quick = argc > 1 && strcmp(argv[1], "--quick") == 0;

        id<MTLDevice> dev = MTLCreateSystemDefaultDevice();
        if (!dev) { fprintf(stderr, "no Metal device\n"); return 1; }
        id<MTLCommandQueue> q = [dev newCommandQueue];
        int nThreads = (int)NSProcessInfo.processInfo.activeProcessorCount;
        pthread_t threads[64];

        if (argc > 1 && strcmp(argv[1], "--frames") == 0) {
            id<MTLComputePipelineState> st = pipeline(dev, [root stringByAppendingPathComponent:@"stencil/Shaders.metal"], @"stencil_step");
            NSDateFormatter *df = [NSDateFormatter new];
            df.dateFormat = @"yyyy-MM-dd";
            df.locale = [NSLocale localeWithLocaleIdentifier:@"en_US_POSIX"];
            NSDictionary *rec = @{@"date": [df stringFromDate:[NSDate date]],
                                  @"machine": @{@"cpu": sysctl_str("machdep.cpu.brand_string"), @"model": sysctl_str("hw.model"), @"gpu": dev.name},
                                  @"stencil": record_stencil(dev, q, st), @"nbody": record_nbody(dev, q)};
            NSData *json = [NSJSONSerialization dataWithJSONObject:rec options:0 error:nil];
            NSString *dir = [root stringByAppendingPathComponent:@"results"];
            [[NSFileManager defaultManager] createDirectoryAtPath:dir withIntermediateDirectories:YES attributes:nil error:nil];
            NSString *path = [dir stringByAppendingPathComponent:[NSString stringWithFormat:@"frames-%@.json", rec[@"date"]]];
            [json writeToFile:path atomically:YES];
            printf("stencil: %.4f ms/step on the GPU · n-body: %.4f ms/step\nwrote %s (%.1f MB)\nthen: python3 export.py\n",
                   [rec[@"stencil"][@"msPerStep"] doubleValue], [rec[@"nbody"][@"msPerStep"] doubleValue], path.UTF8String, json.length / 1e6);
            return 0;
        }

        NSMutableArray *nbodyRows = [NSMutableArray array], *stencilRows = [NSMutableArray array];

        /* ── N-body ── */
        id<MTLComputePipelineState> nbPS = pipeline(dev, [root stringByAppendingPathComponent:@"nbody/Shaders.metal"], @"nbody_update");
        uint32_t nbSizes[] = {1024, 2048, 4096, 8192, 16384, 32768, 65536};
        printf("N-body (%d CPU threads)\n%8s %12s %12s %8s\n", nThreads, "N", "CPU ms/step", "GPU ms/step", "speedup");
        for (int s = 0; s < (int)(sizeof nbSizes / sizeof *nbSizes); s++) {
            uint32_t N = nbSizes[s];
            if (quick && N > 8192) break;
            id<MTLBuffer> buf = [dev newBufferWithLength:N * sizeof(Particle) options:MTLResourceStorageModeShared];
            Particle *ps = buf.contents;
            srand48(1);
            for (uint32_t i = 0; i < N; i++) {
                ps[i] = (Particle){{(float)(drand48()*2-1), (float)(drand48()*2-1)}, {0, 0}, (float)(0.5 + drand48()), 0};
            }
            NBodyParams pr = {N, 0.0005f, 0.0025f, 1e-4f};
            id<MTLBuffer> pbuf = [dev newBufferWithBytes:&pr length:sizeof pr options:MTLResourceStorageModeShared];

            /* CPU: fewer repeats at large N (65k is ~4 billion interactions) */
            int cpuReps = N <= 8192 ? 9 : N <= 32768 ? 5 : 3;
            double cpu[9];
            for (int r = 0; r < cpuReps; r++) {
                NBArgs args[64]; uint32_t chunk = (N + nThreads - 1) / nThreads;
                double t0 = now_ms();
                for (int t = 0; t < nThreads; t++) {
                    args[t] = (NBArgs){ps, &pr, (uint32_t)(t * chunk), (uint32_t)MIN((t + 1) * chunk, N)};
                    pthread_create(&threads[t], NULL, nbody_worker, &args[t]);
                }
                for (int t = 0; t < nThreads; t++) pthread_join(threads[t], NULL);
                cpu[r] = now_ms() - t0;
            }
            /* GPU: warm up, then timed dispatches */
            warm(q, ^(id<MTLComputeCommandEncoder> enc) {
                [enc setComputePipelineState:nbPS];
                [enc setBuffer:buf offset:0 atIndex:0];
                [enc setBuffer:pbuf offset:0 atIndex:1];
                NSUInteger tg = MIN(256, nbPS.maxTotalThreadsPerThreadgroup);
                [enc dispatchThreadgroups:MTLSizeMake((N + tg - 1) / tg, 1, 1) threadsPerThreadgroup:MTLSizeMake(tg, 1, 1)];
            });
            double gpu[11];
            for (int r = 0; r < 11; r++) {
                id<MTLCommandBuffer> cb = [q commandBuffer];
                id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
                [enc setComputePipelineState:nbPS];
                [enc setBuffer:buf offset:0 atIndex:0];
                [enc setBuffer:pbuf offset:0 atIndex:1];
                NSUInteger tg = MIN(256, nbPS.maxTotalThreadsPerThreadgroup);
                [enc dispatchThreadgroups:MTLSizeMake((N + tg - 1) / tg, 1, 1) threadsPerThreadgroup:MTLSizeMake(tg, 1, 1)];
                [enc endEncoding];
                [cb commit]; [cb waitUntilCompleted];
                gpu[r] = (cb.GPUEndTime - cb.GPUStartTime) * 1000.0;
            }
            double c = best(cpu, cpuReps), g = best(gpu + 1, 10);
            printf("%8u %12.3f %12.3f %7.1fx\n", N, c, g, c / g);
            double pairs = (double)N * (N - 1);
            [nbodyRows addObject:@{@"n": @(N), @"cpuMs": @(c), @"gpuMs": @(g),
                                   @"cpuInteractionsPerSec": @(pairs / (c / 1000)), @"gpuInteractionsPerSec": @(pairs / (g / 1000))}];
        }

        /* ── Stencil ── */
        id<MTLComputePipelineState> stPS = pipeline(dev, [root stringByAppendingPathComponent:@"stencil/Shaders.metal"], @"stencil_step");
        uint32_t stSizes[] = {256, 512, 1024, 2048, 4096, 8192};
        printf("\nHeat stencil\n%8s %12s %12s %8s\n", "grid", "CPU ms/step", "GPU ms/step", "speedup");
        for (int s = 0; s < (int)(sizeof stSizes / sizeof *stSizes); s++) {
            uint32_t W = stSizes[s], H = W;
            if (quick && W > 2048) break;
            size_t bytes = (size_t)W * H * sizeof(float);
            id<MTLBuffer> a = [dev newBufferWithLength:bytes options:MTLResourceStorageModeShared];
            id<MTLBuffer> b = [dev newBufferWithLength:bytes options:MTLResourceStorageModeShared];
            float *ga = a.contents;
            for (size_t i = 0; i < (size_t)W * H; i++) ga[i] = 0;
            for (uint32_t y = H/2 - H/16; y < H/2 + H/16; y++)
                for (uint32_t x = W/2 - W/16; x < W/2 + W/16; x++) ga[y*W + x] = 1;
            StencilParams p = {W, H, 0.24f};
            id<MTLBuffer> pbuf = [dev newBufferWithBytes:&p length:sizeof p options:MTLResourceStorageModeShared];

            double cpu[9], gpu[11];
            int cpuReps = W <= 4096 ? 9 : 5;
            for (int r = 0; r < cpuReps; r++) {
                STArgs args[64]; uint32_t chunk = (H + nThreads - 1) / nThreads;
                const float *src = r % 2 ? b.contents : a.contents; float *dst = r % 2 ? a.contents : b.contents;
                double t0 = now_ms();
                for (int t = 0; t < nThreads; t++) {
                    args[t] = (STArgs){src, dst, &p, (uint32_t)(t * chunk), (uint32_t)MIN((t + 1) * chunk, H)};
                    pthread_create(&threads[t], NULL, stencil_worker, &args[t]);
                }
                for (int t = 0; t < nThreads; t++) pthread_join(threads[t], NULL);
                cpu[r] = now_ms() - t0;
            }
            warm(q, ^(id<MTLComputeCommandEncoder> enc) {
                [enc setComputePipelineState:stPS];
                [enc setBuffer:a offset:0 atIndex:0];
                [enc setBuffer:b offset:0 atIndex:1];
                [enc setBuffer:pbuf offset:0 atIndex:2];
                [enc dispatchThreadgroups:MTLSizeMake((W + 15) / 16, (H + 15) / 16, 1) threadsPerThreadgroup:MTLSizeMake(16, 16, 1)];
            });
            for (int r = 0; r < 11; r++) {
                id<MTLCommandBuffer> cb = [q commandBuffer];
                id<MTLComputeCommandEncoder> enc = [cb computeCommandEncoder];
                [enc setComputePipelineState:stPS];
                [enc setBuffer:(r % 2 ? b : a) offset:0 atIndex:0];
                [enc setBuffer:(r % 2 ? a : b) offset:0 atIndex:1];
                [enc setBuffer:pbuf offset:0 atIndex:2];
                [enc dispatchThreadgroups:MTLSizeMake((W + 15) / 16, (H + 15) / 16, 1) threadsPerThreadgroup:MTLSizeMake(16, 16, 1)];
                [enc endEncoding];
                [cb commit]; [cb waitUntilCompleted];
                gpu[r] = (cb.GPUEndTime - cb.GPUStartTime) * 1000.0;
            }
            double c = best(cpu, cpuReps), g = best(gpu + 1, 10);
            double cells = (double)W * H;
            printf("%5ux%-5u %9.3f %12.3f %7.1fx\n", W, H, c, g, c / g);
            /* each cell reads 5 floats and writes 1; with caching the real
               DRAM traffic is closer to 1 read + 1 write = 8 bytes per cell */
            [stencilRows addObject:@{@"size": @(W), @"cpuMs": @(c), @"gpuMs": @(g),
                                     @"cpuCellsPerSec": @(cells / (c / 1000)), @"gpuCellsPerSec": @(cells / (g / 1000)),
                                     @"gpuGBps8": @(cells * 8 / (g / 1000) / 1e9)}];
        }

        NSDateFormatter *df = [NSDateFormatter new];
        df.dateFormat = @"yyyy-MM-dd";
        df.locale = [NSLocale localeWithLocaleIdentifier:@"en_US_POSIX"];
        NSString *date = [df stringFromDate:[NSDate date]];
        double load[3] = {0};
        getloadavg(load, 3);
        NSDictionary *out = @{
            @"date": date,
            @"loadAverage1m": @(load[0]),
            @"machine": @{@"cpu": sysctl_str("machdep.cpu.brand_string"), @"model": sysctl_str("hw.model"),
                          @"cpuThreads": @(nThreads), @"gpu": dev.name,
                          @"memoryGB": @(NSProcessInfo.processInfo.physicalMemory / (1024.0*1024*1024))},
            @"method": @"Best of repeated single steps (the least disturbed by other work on the machine). CPU: one pthread per core, wall time. GPU: one compute dispatch per command buffer, GPU execution time (GPUEndTime - GPUStartTime), after ~500 ms of warm-up dispatches so the GPU clock has ramped up. Kernels compiled from nbody/Shaders.metal and stencil/Shaders.metal at runtime.",
            @"nbody": nbodyRows, @"stencil": stencilRows,
        };
        NSData *json = [NSJSONSerialization dataWithJSONObject:out options:NSJSONWritingPrettyPrinted | NSJSONWritingSortedKeys error:nil];
        NSString *dir = [root stringByAppendingPathComponent:@"results"];
        [[NSFileManager defaultManager] createDirectoryAtPath:dir withIntermediateDirectories:YES attributes:nil error:nil];
        NSString *path = [dir stringByAppendingPathComponent:[NSString stringWithFormat:@"bench-%@.json", date]];
        [json writeToFile:path atomically:YES];
        printf("\nwrote %s\n", path.UTF8String);
        printf("then: python3 export.py   (bakes the results into site/data/native.js)\n");
    }
    return 0;
}
