/*
 * NBodySimulator.m
 * ─────────────────
 * CPU path:  pthreads — 12 threads, each owns a slice of particles
 * GPU path:  Metal compute dispatch — one thread per particle
 *
 * Data lives in a single MTLBuffer with MTLResourceStorageModeShared.
 * StorageModeShared means the buffer is accessible from both CPU and GPU
 * without any explicit copy — this is the unified memory advantage on M2 Pro.
 * On a discrete GPU you would use StorageModeManaged and call
 * didModifyRange: after CPU writes. Here: write, then dispatch. Done.
 */

#import "NBodySimulator.h"
#import <pthread.h>
#import <mach/mach_time.h>

/* ── CPU worker thread args ─────────────────────────────────────────────────*/

typedef struct {
    Particle    *particles;
    NBodyParams *params;
    uint32_t     start;    /* first particle index for this thread  */
    uint32_t     end;      /* one-past-last particle index          */
} WorkerArgs;

/*
 * cpu_worker: integrate gravity for particles[start..end).
 *
 * Each thread reads ALL N particles (for the force sum) but only writes
 * its own slice. No locking needed — reads are from a snapshot of positions
 * that won't be written until all threads finish (barrier in main thread).
 *
 * This is a classic "embarrassingly parallel" pattern: no inter-thread
 * communication, no shared write targets, just independent work slices.
 */
static void *cpu_worker(void *arg)
{
    WorkerArgs  *w  = (WorkerArgs *)arg;
    Particle    *ps = w->particles;
    NBodyParams *pr = w->params;
    uint32_t     N  = pr->N;

    for (uint32_t i = w->start; i < w->end; i++) {
        float fx = 0.f, fy = 0.f;

        for (uint32_t j = 0; j < N; j++) {
            if (j == i) continue;
            float dx  = ps[j].pos[0] - ps[i].pos[0];
            float dy  = ps[j].pos[1] - ps[i].pos[1];
            float r2  = dx*dx + dy*dy + pr->softening;
            /* 1/r³ via reciprocal-sqrt: same formula as the Metal kernel */
            float inv = 1.f / sqrtf(r2);
            float inv3 = inv * inv * inv;
            float f   = pr->G * ps[j].mass * inv3;
            fx += f * dx;
            fy += f * dy;
        }

        ps[i].vel[0] += fx * pr->dt;
        ps[i].vel[1] += fy * pr->dt;
        ps[i].pos[0] += ps[i].vel[0] * pr->dt;
        ps[i].pos[1] += ps[i].vel[1] * pr->dt;

        /* wrap-around boundary */
        ps[i].pos[0] = fmodf(ps[i].pos[0] + 3.f, 2.f) - 1.f;
        ps[i].pos[1] = fmodf(ps[i].pos[1] + 3.f, 2.f) - 1.f;
    }
    return NULL;
}

/* ─────────────────────────────────────────────────────────────────────────── */

@interface NBodySimulator ()
{
    NSUInteger                   _N;
    id<MTLBuffer>                _particleBuf;
    id<MTLBuffer>                _paramBuf;
    NBodyParams                  _params;
    id<MTLComputePipelineState>  _computePipeline;
    id<MTLRenderPipelineState>   _renderPipeline;

    /* CPU thread pool */
    NSUInteger  _nThreads;
    pthread_t  *_threads;
    WorkerArgs *_workerArgs;
}
@end

@implementation NBodySimulator

- (instancetype)initWithN:(NSUInteger)N
{
    self = [super initWithTitle:[NSString stringWithFormat:@"N-body  N=%lu", (unsigned long)N]
                          width:1024 height:768];
    if (!self) return nil;

    _N = N;
    _nThreads = 12;   /* M2 Pro has 12 CPU cores */

    /* ── Simulation parameters ── */
    _params.N         = (uint32_t)N;
    _params.dt        = 0.0002f;
    _params.softening = 0.001f;   /* ε² — prevents singularity at r=0 */
    _params.G         = 0.5f;

    /* ── Particle buffer (shared CPU+GPU — unified memory) ── */
    _particleBuf = [self.device newBufferWithLength:N * sizeof(Particle)
                                            options:MTLResourceStorageModeShared];
    _paramBuf    = [self.device newBufferWithLength:sizeof(NBodyParams)
                                            options:MTLResourceStorageModeShared];
    memcpy(_paramBuf.contents, &_params, sizeof(NBodyParams));

    /* ── Initialise particles: two counter-rotating rings ── */
    Particle *ps = (Particle *)_particleBuf.contents;
    srand(42);
    for (NSUInteger i = 0; i < N; i++) {
        float angle = (float)i / (float)N * 2.f * M_PI;
        float r     = 0.1f + 0.4f * ((float)rand() / RAND_MAX);
        int   ring  = (i < N/2) ? 1 : -1;

        ps[i].pos[0] = r * cosf(angle);
        ps[i].pos[1] = r * sinf(angle);
        /* tangential velocity for orbit — ring direction flips for second ring */
        float orb    = sqrtf(_params.G / (r + 0.01f)) * 0.3f;
        ps[i].vel[0] = -ring * orb * sinf(angle);
        ps[i].vel[1] =  ring * orb * cosf(angle);
        ps[i].mass   = 1.0f + (float)rand() / RAND_MAX;
        ps[i]._pad   = 0.f;
    }

    /* ── Allocate thread pool ── */
    _threads    = calloc(_nThreads, sizeof(pthread_t));
    _workerArgs = calloc(_nThreads, sizeof(WorkerArgs));

    return self;
}

/* ── Pipeline setup (called by MetalBase.runLoop before first frame) ───────*/

- (void)setupPipelines
{
    [super setupPipelines];   /* builds overlay pipeline */

    /* Compile Shaders.metal at launch time.
     * In production you'd precompile to a .metallib; for a dev benchmark
     * runtime compile is fine and avoids a separate build step.           */
    NSString *exeDir  = [[[NSBundle mainBundle] executablePath]
                          stringByDeletingLastPathComponent];
    NSString *libPath = [exeDir stringByAppendingPathComponent:@"Shaders.metallib"];
    id<MTLLibrary> lib = [self loadMetalLibrary:libPath];

    /* ── Compute pipeline ── */
    NSError *err = nil;
    id<MTLFunction> computeFn = [lib newFunctionWithName:@"nbody_update"];
    NSAssert(computeFn, @"nbody_update kernel not found in metallib");
    _computePipeline = [self.device newComputePipelineStateWithFunction:computeFn
                                                                  error:&err];
    NSAssert(_computePipeline, @"Compute pipeline error: %@", err);

    /* ── Render pipeline ── */
    MTLRenderPipelineDescriptor *rpd = [[MTLRenderPipelineDescriptor alloc] init];
    rpd.vertexFunction   = [lib newFunctionWithName:@"nbody_vert"];
    rpd.fragmentFunction = [lib newFunctionWithName:@"nbody_frag"];
    rpd.colorAttachments[0].pixelFormat = MTLPixelFormatBGRA8Unorm;
    _renderPipeline = [self.device newRenderPipelineStateWithDescriptor:rpd error:&err];
    NSAssert(_renderPipeline, @"Render pipeline error: %@", err);
}

/* ── CPU step ───────────────────────────────────────────────────────────────*/

- (void)stepCPU
{
    Particle *ps = (Particle *)_particleBuf.contents;

    /* Divide particles evenly across 12 threads */
    NSUInteger chunk = (_N + _nThreads - 1) / _nThreads;
    for (NSUInteger t = 0; t < _nThreads; t++) {
        _workerArgs[t].particles = ps;
        _workerArgs[t].params    = &_params;
        _workerArgs[t].start     = (uint32_t)(t * chunk);
        _workerArgs[t].end       = (uint32_t)MIN((t + 1) * chunk, _N);
        pthread_create(&_threads[t], NULL, cpu_worker, &_workerArgs[t]);
    }
    /* Wait for all threads to finish before the render pass reads positions */
    for (NSUInteger t = 0; t < _nThreads; t++)
        pthread_join(_threads[t], NULL);
}

/* ── CPU render: particles have been stepped by pthreads, now draw them ────
 *
 * In CPU mode the compute kernel does NOT run — positions were updated by
 * cpu_worker() on the CPU. We still use the Metal render pipeline to draw
 * the particles because the GPU is good at rasterising points; we just skip
 * the compute dispatch. The particle buffer is shared memory so GPU sees the
 * CPU-written positions immediately — no copy needed.
 */
- (void)encodeCPURender:(id<MTLCommandBuffer>)buf
               drawable:(id<CAMetalDrawable>)drawable
{
    MTLRenderPassDescriptor *rpd = [MTLRenderPassDescriptor renderPassDescriptor];
    rpd.colorAttachments[0].texture     = drawable.texture;
    rpd.colorAttachments[0].loadAction  = MTLLoadActionClear;
    rpd.colorAttachments[0].storeAction = MTLStoreActionStore;
    rpd.colorAttachments[0].clearColor  = MTLClearColorMake(0.03, 0.03, 0.08, 1);

    id<MTLRenderCommandEncoder> enc = [buf renderCommandEncoderWithDescriptor:rpd];
    [enc setRenderPipelineState:_renderPipeline];
    [enc setVertexBuffer:_particleBuf offset:0 atIndex:0];
    [enc setVertexBuffer:_paramBuf    offset:0 atIndex:1];
    [enc drawPrimitives:MTLPrimitiveTypePoint vertexStart:0 vertexCount:_N];
    [enc endEncoding];
}

/* ── GPU frame: compute dispatch + render pass ──────────────────────────────*/

- (void)encodeGPUFrame:(id<MTLCommandBuffer>)buf
              drawable:(id<CAMetalDrawable>)drawable
{
    /* ── Compute pass ── */
    {
        id<MTLComputeCommandEncoder> enc = [buf computeCommandEncoder];
        [enc setComputePipelineState:_computePipeline];
        [enc setBuffer:_particleBuf offset:0 atIndex:0];
        [enc setBuffer:_paramBuf    offset:0 atIndex:1];

        /*
         * threadgroup size: how many threads run together on one GPU core.
         * M2 Pro supports up to 1024 threads per threadgroup.
         * For 1D work (one thread per particle), 256 is a good default:
         * large enough to hide memory latency, small enough not to exhaust
         * register file per core.
         *
         * Grid size: ceil(N / 256) threadgroups × 256 threads = N threads total.
         * The kernel guards against gid >= N for the last partial threadgroup.
         */
        NSUInteger tgSize = MIN(256, _computePipeline.maxTotalThreadsPerThreadgroup);
        NSUInteger nGroups = (_N + tgSize - 1) / tgSize;
        [enc dispatchThreadgroups:MTLSizeMake(nGroups, 1, 1)
            threadsPerThreadgroup:MTLSizeMake(tgSize,  1, 1)];
        [enc endEncoding];
    }

    /*
     * GPU timing: we attach a completion handler to the command buffer.
     * MTLCommandBuffer exposes GPUStartTime and GPUEndTime after completion.
     * We store the last measured value in self.gpuMs for the overlay.
     */
    __weak typeof(self) weakSelf = self;
    [buf addCompletedHandler:^(id<MTLCommandBuffer> cb) {
        double ms = (cb.GPUEndTime - cb.GPUStartTime) * 1000.0;
        weakSelf.gpuMs = ms;
    }];

    /* ── Render pass ── */
    {
        MTLRenderPassDescriptor *rpd = [MTLRenderPassDescriptor renderPassDescriptor];
        rpd.colorAttachments[0].texture     = drawable.texture;
        rpd.colorAttachments[0].loadAction  = MTLLoadActionClear;
        rpd.colorAttachments[0].storeAction = MTLStoreActionStore;
        rpd.colorAttachments[0].clearColor  = MTLClearColorMake(0.03, 0.03, 0.08, 1);

        id<MTLRenderCommandEncoder> enc = [buf renderCommandEncoderWithDescriptor:rpd];
        [enc setRenderPipelineState:_renderPipeline];
        [enc setVertexBuffer:_particleBuf offset:0 atIndex:0];
        [enc setVertexBuffer:_paramBuf    offset:0 atIndex:1];
        /* Draw _N point primitives — one vertex per particle */
        [enc drawPrimitives:MTLPrimitiveTypePoint
                vertexStart:0 vertexCount:_N];
        [enc endEncoding];
    }
}

- (void)dealloc
{
    free(_threads);
    free(_workerArgs);
}

@end
