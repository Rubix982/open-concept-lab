/*
 * StencilSimulator.m
 * ───────────────────
 * CPU path:  pthreads — 12 threads, each owns a horizontal band of rows
 * GPU path:  Metal compute — 2D dispatch, one thread per cell
 *
 * Two MTLBuffers (gridA, gridB) in shared storage mode.
 * Each frame we ping-pong: read from one, write to the other, then swap.
 * The GPU reads a buffer pointer; the CPU reads float* directly.
 * Because storage is shared, no copies are needed in either direction.
 */

#import "StencilSimulator.h"
#import <pthread.h>
#import <mach/mach_time.h>

/* ── CPU worker ─────────────────────────────────────────────────────────── */

typedef struct {
    const float   *src;
    float         *dst;
    StencilParams *params;
    uint32_t       row_start;   /* first row this thread owns */
    uint32_t       row_end;     /* one-past-last row          */
} StencilWorkerArgs;

/*
 * cpu_worker: update rows [row_start, row_end) of the grid.
 *
 * Boundary rows (0 and H-1) are skipped — they hold fixed temperature.
 * Each interior cell reads 4 neighbours from src and writes one value to dst.
 * No synchronisation needed because no two threads write the same cell.
 *
 * Memory access pattern: sequential row-major reads — good cache behaviour.
 * Stride between rows = W floats = W×4 bytes. For W=512: 2 KB per row stride.
 * Fits comfortably in L1. The col-neighbour reads (x±1) are adjacent in memory.
 */
static void *cpu_worker(void *arg)
{
    StencilWorkerArgs *w = (StencilWorkerArgs *)arg;
    uint32_t W = w->params->W;
    uint32_t H = w->params->H;
    float alpha = w->params->alpha;

    for (uint32_t y = w->row_start; y < w->row_end; y++) {
        if (y == 0 || y == H - 1) {
            /* boundary: copy unchanged */
            memcpy(w->dst + y * W, w->src + y * W, W * sizeof(float));
            continue;
        }
        /* boundary columns */
        w->dst[y * W]         = w->src[y * W];
        w->dst[y * W + W - 1] = w->src[y * W + W - 1];

        /* interior cells */
        for (uint32_t x = 1; x < W - 1; x++) {
            float centre = w->src[ y      * W + x    ];
            float left   = w->src[ y      * W + x - 1];
            float right  = w->src[ y      * W + x + 1];
            float up     = w->src[(y - 1) * W + x    ];
            float down   = w->src[(y + 1) * W + x    ];
            w->dst[y * W + x] = centre + alpha * (left + right + up + down - 4.0f * centre);
        }
    }
    return NULL;
}

/* ─────────────────────────────────────────────────────────────────────────── */

@interface StencilSimulator ()
{
    NSUInteger  _W, _H;
    StencilParams _params;

    /* ping-pong pair — swap each frame */
    id<MTLBuffer>  _gridA;
    id<MTLBuffer>  _gridB;
    BOOL           _pingA;   /* YES: src=A dst=B, NO: src=B dst=A */

    id<MTLBuffer>  _paramBuf;
    id<MTLComputePipelineState>  _computePipeline;
    id<MTLRenderPipelineState>   _renderPipeline;

    /* CPU thread pool */
    NSUInteger         _nThreads;
    pthread_t         *_threads;
    StencilWorkerArgs *_workerArgs;
}
@end

@implementation StencilSimulator

- (instancetype)initWithWidth:(NSUInteger)W height:(NSUInteger)H
{
    self = [super initWithTitle:[NSString stringWithFormat:@"Heat Stencil  %lu×%lu", W, H]
                          width:1024 height:768];
    if (!self) return nil;

    _W = W; _H = H;
    _pingA    = YES;
    _nThreads = 12;

    _params.W     = (uint32_t)W;
    _params.H     = (uint32_t)H;
    _params.alpha = 0.24f;   /* just below stability limit of 0.25 */

    /* ── Allocate grid buffers (shared CPU+GPU) ── */
    NSUInteger sz = W * H * sizeof(float);
    _gridA    = [self.device newBufferWithLength:sz options:MTLResourceStorageModeShared];
    _gridB    = [self.device newBufferWithLength:sz options:MTLResourceStorageModeShared];
    _paramBuf = [self.device newBufferWithLength:sizeof(StencilParams)
                                         options:MTLResourceStorageModeShared];
    memcpy(_paramBuf.contents, &_params, sizeof(StencilParams));

    /* ── Initial conditions ── */
    [self _resetGrid];

    /* ── Thread pool ── */
    _threads    = calloc(_nThreads, sizeof(pthread_t));
    _workerArgs = calloc(_nThreads, sizeof(StencilWorkerArgs));

    return self;
}

/*
 * _resetGrid: cold everywhere, hot disc at the centre.
 *
 * We also place four smaller hot spots at the quarter points to create a
 * more interesting diffusion pattern — multiple sources merging over time.
 */
- (void)_resetGrid
{
    float *grid = (float *)_gridA.contents;
    uint32_t W = _params.W, H = _params.H;

    memset(grid, 0, W * H * sizeof(float));

    /* hot disc at centre */
    float cx = W / 2.0f, cy = H / 2.0f;
    float r2  = (W * 0.06f) * (W * 0.06f);
    for (uint32_t y = 0; y < H; y++)
        for (uint32_t x = 0; x < W; x++) {
            float d2 = (x - cx)*(x - cx) + (y - cy)*(y - cy);
            if (d2 < r2) grid[y * W + x] = 1.0f;
        }

    /* four smaller sources at quarter points */
    float pts[4][2] = {{W*0.25f, H*0.25f}, {W*0.75f, H*0.25f},
                       {W*0.25f, H*0.75f}, {W*0.75f, H*0.75f}};
    float r2s = (W * 0.035f) * (W * 0.035f);
    for (int p = 0; p < 4; p++)
        for (uint32_t y = 0; y < H; y++)
            for (uint32_t x = 0; x < W; x++) {
                float d2 = (x - pts[p][0])*(x - pts[p][0]) +
                           (y - pts[p][1])*(y - pts[p][1]);
                if (d2 < r2s) grid[y * W + x] = 0.8f;
            }

    /* copy initial state to gridB too */
    memcpy(_gridB.contents, _gridA.contents, W * H * sizeof(float));
}

/* ── Pipeline setup ─────────────────────────────────────────────────────── */

- (void)setupPipelines
{
    [super setupPipelines];

    NSString *exeDir  = [[[NSBundle mainBundle] executablePath]
                          stringByDeletingLastPathComponent];
    NSString *libPath = [exeDir stringByAppendingPathComponent:@"Shaders.metallib"];
    id<MTLLibrary> lib = [self loadMetalLibrary:libPath];

    NSError *err = nil;

    /* compute */
    id<MTLFunction> fn = [lib newFunctionWithName:@"stencil_step"];
    NSAssert(fn, @"stencil_step not found");
    _computePipeline = [self.device newComputePipelineStateWithFunction:fn error:&err];
    NSAssert(_computePipeline, @"Compute pipeline: %@", err);

    /* render */
    MTLRenderPipelineDescriptor *rpd = [[MTLRenderPipelineDescriptor alloc] init];
    rpd.vertexFunction   = [lib newFunctionWithName:@"stencil_vert"];
    rpd.fragmentFunction = [lib newFunctionWithName:@"stencil_frag"];
    rpd.colorAttachments[0].pixelFormat = MTLPixelFormatBGRA8Unorm;
    _renderPipeline = [self.device newRenderPipelineStateWithDescriptor:rpd error:&err];
    NSAssert(_renderPipeline, @"Render pipeline: %@", err);
}

/* ── CPU step ───────────────────────────────────────────────────────────── */

- (void)stepCPU
{
    float *src = _pingA ? (float *)_gridA.contents : (float *)_gridB.contents;
    float *dst = _pingA ? (float *)_gridB.contents : (float *)_gridA.contents;

    /* divide rows across threads */
    NSUInteger chunk = (_H + _nThreads - 1) / _nThreads;
    for (NSUInteger t = 0; t < _nThreads; t++) {
        _workerArgs[t].src       = src;
        _workerArgs[t].dst       = dst;
        _workerArgs[t].params    = &_params;
        _workerArgs[t].row_start = (uint32_t)(t * chunk);
        _workerArgs[t].row_end   = (uint32_t)MIN((t + 1) * chunk, _H);
        pthread_create(&_threads[t], NULL, cpu_worker, &_workerArgs[t]);
    }
    for (NSUInteger t = 0; t < _nThreads; t++)
        pthread_join(_threads[t], NULL);

    _pingA = !_pingA;   /* swap for next frame */
}

/* ── CPU render: draw current grid as heatmap ─────────────────────────────
 *
 * The fragment shader reads temperature values directly from the buffer.
 * We bind whichever buffer holds the most recently computed state (dst).
 */
- (void)encodeCPURender:(id<MTLCommandBuffer>)buf
               drawable:(id<CAMetalDrawable>)drawable
{
    /* after stepCPU swapped _pingA, dst is now the grid we just wrote */
    id<MTLBuffer> currentGrid = _pingA ? _gridB : _gridA;
    [self _encodeRenderWithGrid:currentGrid commandBuffer:buf drawable:drawable];
}

/* ── GPU frame: compute dispatch + render pass ─────────────────────────── */

- (void)encodeGPUFrame:(id<MTLCommandBuffer>)buf
              drawable:(id<CAMetalDrawable>)drawable
{
    id<MTLBuffer> src = _pingA ? _gridA : _gridB;
    id<MTLBuffer> dst = _pingA ? _gridB : _gridA;

    /* Compute pass */
    {
        id<MTLComputeCommandEncoder> enc = [buf computeCommandEncoder];
        [enc setComputePipelineState:_computePipeline];
        [enc setBuffer:src      offset:0 atIndex:0];
        [enc setBuffer:dst      offset:0 atIndex:1];
        [enc setBuffer:_paramBuf offset:0 atIndex:2];

        /*
         * 2D dispatch: threadgroup is 16×16 (256 threads total per group).
         * Grid covers the full W×H domain, rounded up.
         * The kernel guards out-of-bounds threads.
         *
         * 16×16 threadgroup on M2 Pro: 256 × 4 bytes × 5 (centre + 4 nbrs)
         * = 5 KB of device-memory reads per threadgroup per step.
         * A threadgroup-shared-memory tile would cut this to 1 read per cell
         * (with a halo load) — noted as a next step in PLAN.md.
         */
        MTLSize tgSize = MTLSizeMake(16, 16, 1);
        MTLSize grid   = MTLSizeMake((_W + 15) / 16, (_H + 15) / 16, 1);
        [enc dispatchThreadgroups:grid threadsPerThreadgroup:tgSize];
        [enc endEncoding];
    }

    __weak typeof(self) weak = self;
    [buf addCompletedHandler:^(id<MTLCommandBuffer> cb) {
        weak.gpuMs = (cb.GPUEndTime - cb.GPUStartTime) * 1000.0;
    }];

    [self _encodeRenderWithGrid:dst commandBuffer:buf drawable:drawable];
    _pingA = !_pingA;
}

/* ── Shared render encoding ─────────────────────────────────────────────── */

- (void)_encodeRenderWithGrid:(id<MTLBuffer>)grid
                commandBuffer:(id<MTLCommandBuffer>)buf
                     drawable:(id<CAMetalDrawable>)drawable
{
    MTLRenderPassDescriptor *rpd = [MTLRenderPassDescriptor renderPassDescriptor];
    rpd.colorAttachments[0].texture     = drawable.texture;
    rpd.colorAttachments[0].loadAction  = MTLLoadActionClear;
    rpd.colorAttachments[0].storeAction = MTLStoreActionStore;
    rpd.colorAttachments[0].clearColor  = MTLClearColorMake(0, 0, 0, 1);

    id<MTLRenderCommandEncoder> enc = [buf renderCommandEncoderWithDescriptor:rpd];
    [enc setRenderPipelineState:_renderPipeline];
    /* fragment shader reads grid buffer directly — no texture upload needed */
    [enc setFragmentBuffer:grid      offset:0 atIndex:0];
    [enc setFragmentBuffer:_paramBuf offset:0 atIndex:1];
    [enc drawPrimitives:MTLPrimitiveTypeTriangleStrip
            vertexStart:0 vertexCount:4];
    [enc endEncoding];
}

- (void)dealloc
{
    free(_threads);
    free(_workerArgs);
}

@end
