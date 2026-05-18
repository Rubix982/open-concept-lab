/*
 * MetalBase.m
 * ───────────
 * Implementation of shared Metal boilerplate.
 *
 * Metal concepts used here
 * ────────────────────────
 * MTLDevice        — the GPU. One per machine (or per discrete GPU).
 *                    On M2 Pro: this IS the 18-core GPU in the same die.
 *
 * MTLCommandQueue  — a queue of command buffers sent to the GPU.
 *                    Think of it as the pipe between CPU and GPU.
 *
 * CAMetalLayer     — a Core Animation layer that owns a pool of Metal
 *                    textures (drawables) that map directly to the screen.
 *                    nextDrawable() gives you the texture for this frame.
 *
 * CVDisplayLink    — a timer that fires in sync with the display refresh
 *                    (60 Hz or 120 Hz on ProMotion). Better than NSTimer
 *                    because it is phase-locked to the display hardware.
 *
 * MTLRenderPassDescriptor — describes a render target (which texture to
 *                    draw into, what to do at load/store: clear, load, etc.)
 *
 * Benchmark overlay
 * ─────────────────
 * We blit text over the Metal layer using Core Graphics into a CGBitmapContext,
 * then copy that into an MTLTexture, then composite it in a second render pass.
 * This avoids pulling in any text rendering framework.
 */

#import "MetalBase.h"
#import <mach/mach_time.h>   /* mach_absolute_time — nanosecond wall clock */
#import <sys/sysctl.h>        /* sysctl — CPU brand string */

/* ─────────────────────────────────────────────────────────────────────────── */
#pragma mark - Timing helpers

/*
 * mach_absolute_time() returns ticks in a hardware-specific unit.
 * mach_timebase_info gives us the numer/denom to convert to nanoseconds.
 * We call mach_timebase_info once and cache it.
 */
static double ticks_to_ms(uint64_t ticks)
{
    static mach_timebase_info_data_t tb;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ mach_timebase_info(&tb); });
    return (double)ticks * tb.numer / tb.denom / 1e6;   /* ns → ms */
}

/* ─────────────────────────────────────────────────────────────────────────── */
#pragma mark - CPU brand

static NSString *cpu_brand(void)
{
    char buf[256] = "unknown";
    size_t len = sizeof(buf);
    sysctlbyname("machdep.cpu.brand_string", buf, &len, NULL, 0);
    if (strcmp(buf, "unknown") == 0) {
        /* Apple Silicon doesn't always expose brand_string */
        sysctlbyname("hw.model", buf, &len, NULL, 0);
    }
    return [NSString stringWithUTF8String:buf];
}

static NSString *cpu_slug(void)
{
    NSString *brand = cpu_brand();
    NSMutableString *slug = [NSMutableString string];
    for (NSUInteger i = 0; i < brand.length; i++) {
        unichar c = [brand characterAtIndex:i];
        if (isalnum(c)) [slug appendFormat:@"%c", (char)c];
        else            [slug appendString:@"_"];
    }
    return slug;
}

/* ─────────────────────────────────────────────────────────────────────────── */
#pragma mark - CVDisplayLink callback

/*
 * CVDisplayLink fires on a background thread. We forward to our render method
 * on the main thread to avoid Metal + AppKit threading hazards.
 * The callback signature is required by the CVDisplayLink API.
 */
static CVReturn display_link_callback(CVDisplayLinkRef    displayLink,
                                      const CVTimeStamp  *now,
                                      const CVTimeStamp  *outputTime,
                                      CVOptionFlags       flagsIn,
                                      CVOptionFlags      *flagsOut,
                                      void               *ctx)
{
    (void)displayLink; (void)now; (void)outputTime;
    (void)flagsIn; (void)flagsOut;
    MetalBase *self = (__bridge MetalBase *)ctx;
    dispatch_async(dispatch_get_main_queue(), ^{ [self renderFrame]; });
    return kCVReturnSuccess;
}

/* ─────────────────────────────────────────────────────────────────────────── */
#pragma mark - MetalBase implementation

@interface MetalBase ()
{
    CVDisplayLinkRef  _displayLink;
    NSUInteger        _frameCount;
    uint64_t          _fpsTimer;       /* ticks at last FPS measurement     */
    double            _fps;
    FILE             *_logFile;

    /* overlay texture */
    id<MTLTexture>            _overlayTex;
    id<MTLRenderPipelineState>_overlayPipeline;
    id<MTLBuffer>             _overlayVerts;   /* fullscreen quad */
}
@end

@implementation MetalBase

/* ── Init ─────────────────────────────────────────────────────────────────── */

- (instancetype)initWithTitle:(NSString *)title
                        width:(NSUInteger)w
                       height:(NSUInteger)h
{
    self = [super init];
    if (!self) return nil;

    _width  = w;
    _height = h;
    _useGPU = YES;   /* start in GPU mode; press G to toggle */

    /* ── Acquire the GPU ── */
    _device = MTLCreateSystemDefaultDevice();
    NSAssert(_device, @"Metal is not supported on this device");

    _commandQueue = [_device newCommandQueue];

    /* ── Create window ── */
    NSRect frame = NSMakeRect(0, 0, (CGFloat)w, (CGFloat)h);
    NSWindowStyleMask style = NSWindowStyleMaskTitled
                            | NSWindowStyleMaskClosable
                            | NSWindowStyleMaskMiniaturizable;
    _window = [[NSWindow alloc] initWithContentRect:frame
                                          styleMask:style
                                            backing:NSBackingStoreBuffered
                                              defer:NO];
    [_window setTitle:title];
    [_window setDelegate:self];

    /* ── Attach CAMetalLayer to window's content view ── */
    NSView *view = _window.contentView;
    view.wantsLayer = YES;
    _metalLayer = [CAMetalLayer layer];
    _metalLayer.device        = _device;
    _metalLayer.pixelFormat   = MTLPixelFormatBGRA8Unorm;
    _metalLayer.framebufferOnly = NO;   /* allow reading back for overlay */
    _metalLayer.frame         = view.bounds;
    _metalLayer.drawableSize  = CGSizeMake((CGFloat)w, (CGFloat)h);
    [view.layer addSublayer:_metalLayer];

    /* ── Open results log file ── */
    NSString *ts = ({
        NSDateFormatter *df = [[NSDateFormatter alloc] init];
        df.dateFormat = @"yyyy-MM-dd_HH-mm-ss";
        [df stringFromDate:[NSDate date]];
    });
    NSString *slug = cpu_slug();
    NSString *name = [NSString stringWithFormat:@"%@_%@_%@.txt",
                      ts, slug, [title stringByReplacingOccurrencesOfString:@" " withString:@"_"]];

    /* results/ lives next to the executable */
    NSString *exeDir = [[[NSBundle mainBundle] executablePath]
                        stringByDeletingLastPathComponent];
    NSString *resultsDir = [exeDir stringByAppendingPathComponent:@"../results"];
    [[NSFileManager defaultManager] createDirectoryAtPath:resultsDir
                              withIntermediateDirectories:YES
                                               attributes:nil
                                                    error:nil];
    NSString *logPath = [resultsDir stringByAppendingPathComponent:name];
    _logFile = fopen(logPath.UTF8String, "w");
    if (_logFile) {
        fprintf(_logFile, "# %s\n", title.UTF8String);
        fprintf(_logFile, "# CPU: %s\n", cpu_brand().UTF8String);
        fprintf(_logFile, "# %s\n\n", ts.UTF8String);
        fprintf(stderr, "logging to: %s\n", logPath.UTF8String);
    }

    _fpsTimer  = mach_absolute_time();
    _frameCount = 0;

    return self;
}

/* ── Pipeline setup (called by subclass after super init, or override) ────── */

- (void)setupPipelines
{
    /* Base class builds the overlay pipeline. Subclasses call [super setupPipelines]
     * then add their own compute + render pipelines.                              */
    [self _buildOverlayPipeline];
}

/* ── Overlay: text rendered via Core Graphics into an MTLTexture ─────────── */

/*
 * We use Core Graphics (CG) rather than pulling in any UI text framework.
 * CG gives us a CPU-side bitmap context; we copy the bytes into an MTLTexture
 * each frame. This is not the fastest approach (GPU text would be faster) but
 * it is self-contained and clear.
 *
 * The overlay quad covers only the top-left corner to minimise overdraw.
 */

- (void)_buildOverlayPipeline
{
    /* Inline MSL for the overlay: sample a texture, blend over the framebuffer */
    NSString *src = @
        "#include <metal_stdlib>\n"
        "using namespace metal;\n"
        "struct OverlayV { float4 pos [[position]]; float2 uv; };\n"
        "vertex OverlayV overlay_vert(\n"
        "    uint vid [[vertex_id]],\n"
        "    constant float4 *verts [[buffer(0)]])\n"
        "{\n"
        "    OverlayV o;\n"
        "    o.pos = float4(verts[vid].xy, 0, 1);\n"
        "    o.uv  = verts[vid].zw;\n"
        "    return o;\n"
        "}\n"
        "fragment float4 overlay_frag(\n"
        "    OverlayV in [[stage_in]],\n"
        "    texture2d<float> tex [[texture(0)]])\n"
        "{\n"
        "    constexpr sampler s(filter::nearest);\n"
        "    return tex.sample(s, in.uv);\n"
        "}\n";

    NSError *err = nil;
    id<MTLLibrary> lib = [_device newLibraryWithSource:src options:nil error:&err];
    NSAssert(lib, @"Overlay shader compile error: %@", err);

    MTLRenderPipelineDescriptor *pd = [[MTLRenderPipelineDescriptor alloc] init];
    pd.vertexFunction   = [lib newFunctionWithName:@"overlay_vert"];
    pd.fragmentFunction = [lib newFunctionWithName:@"overlay_frag"];
    pd.colorAttachments[0].pixelFormat          = MTLPixelFormatBGRA8Unorm;
    /* Alpha blend: dst = src.a * src.rgb + (1-src.a) * dst.rgb */
    pd.colorAttachments[0].blendingEnabled      = YES;
    pd.colorAttachments[0].sourceRGBBlendFactor = MTLBlendFactorSourceAlpha;
    pd.colorAttachments[0].destinationRGBBlendFactor = MTLBlendFactorOneMinusSourceAlpha;
    pd.colorAttachments[0].sourceAlphaBlendFactor    = MTLBlendFactorOne;
    pd.colorAttachments[0].destinationAlphaBlendFactor = MTLBlendFactorOneMinusSourceAlpha;

    _overlayPipeline = [_device newRenderPipelineStateWithDescriptor:pd error:&err];
    NSAssert(_overlayPipeline, @"Overlay pipeline error: %@", err);

    /* Fullscreen quad for the overlay region (top-left quarter of screen) */
    /* format: x, y (NDC), u, v (texture coords)                           */
    float verts[] = {
        -1.0f,  1.0f,  0.0f, 0.0f,   /* top-left     */
        -0.1f,  1.0f,  1.0f, 0.0f,   /* top-right    */
        -1.0f,  0.55f, 0.0f, 1.0f,   /* bottom-left  */
        -0.1f,  0.55f, 1.0f, 1.0f,   /* bottom-right */
    };
    _overlayVerts = [_device newBufferWithBytes:verts
                                         length:sizeof(verts)
                                        options:MTLResourceStorageModeShared];

    /* Overlay texture: 300×120 pixels of BGRA8 */
    MTLTextureDescriptor *td = [MTLTextureDescriptor
        texture2DDescriptorWithPixelFormat:MTLPixelFormatBGRA8Unorm
                                     width:300 height:120 mipmapped:NO];
    td.usage = MTLTextureUsageShaderRead;
    td.storageMode = MTLStorageModeShared;
    _overlayTex = [_device newTextureWithDescriptor:td];
}

- (void)_updateOverlayTexture
{
    /* Render text into a CG bitmap, then blit into _overlayTex */
    size_t W = 300, H = 120;
    uint8_t *buf = calloc(W * H * 4, 1);   /* BGRA */

    CGColorSpaceRef cs  = CGColorSpaceCreateDeviceRGB();
    CGContextRef    ctx = CGBitmapContextCreate(buf, W, H, 8, W * 4, cs,
                              kCGImageAlphaPremultipliedFirst | kCGBitmapByteOrder32Little);
    CGColorSpaceRelease(cs);

    /* dark semi-transparent background */
    CGContextSetRGBFillColor(ctx, 0, 0, 0, 0.6);
    CGContextFillRect(ctx, CGRectMake(0, 0, W, H));

    /* white text */
    CGContextSetRGBFillColor(ctx, 1, 1, 1, 1);
    CGContextSelectFont(ctx, "Monaco", 13, kCGEncodingMacRoman);
    CGContextSetTextDrawingMode(ctx, kCGTextFill);
    /* CG text origin is bottom-left; flip Y */
    CGContextSetTextMatrix(ctx, CGAffineTransformMakeScale(1, -1));

    NSString *mode = _useGPU ? @"GPU" : @"CPU";
    NSString *line1 = [NSString stringWithFormat:@"Mode: %@  (G to toggle)", mode];
    NSString *line2 = [NSString stringWithFormat:@"FPS:  %.1f", _fps];
    NSString *line3 = [NSString stringWithFormat:@"CPU step: %.2f ms", _cpuMs];
    NSString *line4 = [NSString stringWithFormat:@"GPU step: %.2f ms", _gpuMs];

    CGFloat y = 20;
    for (NSString *s in @[line1, line2, line3, line4]) {
        CGContextShowTextAtPoint(ctx, 10, y, s.UTF8String, s.length);
        y += 22;
    }

    CGContextRelease(ctx);

    [_overlayTex replaceRegion:MTLRegionMake2D(0, 0, W, H)
                   mipmapLevel:0
                     withBytes:buf
                   bytesPerRow:W * 4];
    free(buf);
}

/* ── Render loop ──────────────────────────────────────────────────────────── */

- (void)runLoop
{
    [self setupPipelines];
    [_window center];
    [_window makeKeyAndOrderFront:nil];

    /* CVDisplayLink fires in sync with display refresh (60/120 Hz) */
    CVDisplayLinkCreateWithActiveCGDisplays(&_displayLink);
    CVDisplayLinkSetOutputCallback(_displayLink, display_link_callback,
                                   (__bridge void *)self);
    CVDisplayLinkStart(_displayLink);

    /* AppKit run loop — blocks here until window closes */
    [[NSApplication sharedApplication] run];
}

- (void)renderFrame
{
    /* ── FPS measurement ── */
    _frameCount++;
    uint64_t now = mach_absolute_time();
    double elapsed_ms = ticks_to_ms(now - _fpsTimer);
    if (elapsed_ms >= 500.0) {   /* update FPS display twice per second */
        _fps       = (double)_frameCount / (elapsed_ms / 1000.0);
        _frameCount = 0;
        _fpsTimer   = now;
    }

    /* ── CPU or GPU step ── */
    if (!_useGPU) {
        uint64_t t0 = mach_absolute_time();
        [self stepCPU];
        _cpuMs = ticks_to_ms(mach_absolute_time() - t0);
    }

    /* ── Update overlay texture (CG text) ── */
    [self _updateOverlayTexture];

    /* ── Get drawable ── */
    id<CAMetalDrawable> drawable = [_metalLayer nextDrawable];
    if (!drawable) return;

    id<MTLCommandBuffer> buf = [_commandQueue commandBuffer];

    if (_useGPU) {
        /* Subclass encodes compute pass + render pass */
        [self encodeGPUFrame:buf drawable:drawable];
    } else {
        /* CPU mode: just clear + render from CPU-updated data */
        [self encodeCPURender:buf drawable:drawable];
    }

    /* ── Overlay render pass (blended on top) ── */
    [self _encodeOverlay:buf drawable:drawable];

    [buf presentDrawable:drawable];
    [buf commit];
}

/* Default CPU render — subclasses override for their data */
- (void)encodeCPURender:(id<MTLCommandBuffer>)buf
               drawable:(id<CAMetalDrawable>)drawable
{
    MTLRenderPassDescriptor *rpd = [MTLRenderPassDescriptor renderPassDescriptor];
    rpd.colorAttachments[0].texture     = drawable.texture;
    rpd.colorAttachments[0].loadAction  = MTLLoadActionClear;
    rpd.colorAttachments[0].storeAction = MTLStoreActionStore;
    rpd.colorAttachments[0].clearColor  = MTLClearColorMake(0.05, 0.05, 0.1, 1);

    id<MTLRenderCommandEncoder> enc = [buf renderCommandEncoderWithDescriptor:rpd];
    [enc endEncoding];
}

- (void)_encodeOverlay:(id<MTLCommandBuffer>)buf
              drawable:(id<CAMetalDrawable>)drawable
{
    MTLRenderPassDescriptor *rpd = [MTLRenderPassDescriptor renderPassDescriptor];
    rpd.colorAttachments[0].texture     = drawable.texture;
    rpd.colorAttachments[0].loadAction  = MTLLoadActionLoad;   /* preserve scene */
    rpd.colorAttachments[0].storeAction = MTLStoreActionStore;

    id<MTLRenderCommandEncoder> enc = [buf renderCommandEncoderWithDescriptor:rpd];
    [enc setRenderPipelineState:_overlayPipeline];
    [enc setVertexBuffer:_overlayVerts offset:0 atIndex:0];
    [enc setFragmentTexture:_overlayTex atIndex:0];
    [enc drawPrimitives:MTLPrimitiveTypeTriangleStrip
            vertexStart:0 vertexCount:4];
    [enc endEncoding];
}

/* ── Override stubs ───────────────────────────────────────────────────────── */

- (void)stepCPU                                              {}
- (void)encodeGPUFrame:(id<MTLCommandBuffer>)buf
              drawable:(id<CAMetalDrawable>)drawable         { (void)buf; (void)drawable; }

/* ── Utilities ────────────────────────────────────────────────────────────── */

- (id<MTLLibrary>)loadMetalLibrary:(NSString *)path
{
    NSError *err = nil;
    NSURL *url = [NSURL fileURLWithPath:path];
    id<MTLLibrary> lib = [_device newLibraryWithURL:url error:&err];
    NSAssert(lib, @"Failed to load metallib at %@: %@", path, err);
    return lib;
}

- (void)logResult:(NSString *)line
{
    if (_logFile) fprintf(_logFile, "%s\n", line.UTF8String);
}

/* ── Window delegate ─────────────────────────────────────────────────────── */

- (void)windowWillClose:(NSNotification *)notification
{
    (void)notification;
    CVDisplayLinkStop(_displayLink);
    CVDisplayLinkRelease(_displayLink);
    if (_logFile) { fclose(_logFile); _logFile = NULL; }
    [NSApp terminate:nil];
}

/* ── Keyboard: G toggles CPU/GPU mode ────────────────────────────────────── */

- (void)keyDown:(NSEvent *)event
{
    if ([[event charactersIgnoringModifiers] isEqualToString:@"g"] ||
        [[event charactersIgnoringModifiers] isEqualToString:@"G"]) {
        _useGPU = !_useGPU;
        NSLog(@"Mode: %@", _useGPU ? @"GPU" : @"CPU");
    }
}

@end
