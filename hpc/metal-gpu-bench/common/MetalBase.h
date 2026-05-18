/*
 * MetalBase.h
 * ───────────
 * Shared boilerplate for all Metal demos in this project.
 *
 * Provides:
 *   - MTLDevice + MTLCommandQueue acquisition
 *   - NSWindow + CAMetalLayer setup (no Storyboard, no XIB — pure code)
 *   - CVDisplayLink-driven render loop (synced to display refresh, not a busy loop)
 *   - FPS + benchmark overlay rendered as Core Graphics text into the Metal layer
 *   - Results logger: auto-saves benchmark lines to results/<timestamp>_<cpu>.txt
 *
 * Usage:
 *   Subclass MetalBase. Override:
 *     -setupPipelines   called once after Metal device is ready
 *     -updateCPU:       advance simulation on CPU, return wall time in ms
 *     -updateGPU:       encode compute + render into commandBuffer, return GPU ms
 *     -encodeRender:    encode the render pass (called by base after compute)
 *
 *   Call [self runLoop] to start.
 */

#pragma once

#import <Cocoa/Cocoa.h>
#import <Metal/Metal.h>
#import <QuartzCore/CAMetalLayer.h>

/* One benchmark sample stored per frame */
typedef struct {
    double fps;
    double cpu_ms;
    double gpu_ms;
} BenchSample;

@interface MetalBase : NSObject <NSWindowDelegate>

/* Metal objects — available to subclasses after -setupPipelines */
@property (nonatomic, strong) id<MTLDevice>        device;
@property (nonatomic, strong) id<MTLCommandQueue>  commandQueue;
@property (nonatomic, strong) CAMetalLayer        *metalLayer;
@property (nonatomic, strong) NSWindow            *window;

/* Current benchmark numbers — subclass may read/write */
@property (nonatomic, assign) double cpuMs;   /* last CPU step time   */
@property (nonatomic, assign) double gpuMs;   /* last GPU step time   */
@property (nonatomic, assign) BOOL   useGPU;  /* toggled with G key   */

/* Window size in pixels */
@property (nonatomic, assign) NSUInteger width;
@property (nonatomic, assign) NSUInteger height;

/* Designated init */
- (instancetype)initWithTitle:(NSString *)title
                        width:(NSUInteger)w
                       height:(NSUInteger)h;

/* Start the display-link render loop (blocks until window closes) */
- (void)runLoop;

/* ── Override points ─────────────────────────────────────────────────────── */

/* Called once after device + commandQueue are ready. Build pipelines here. */
- (void)setupPipelines;

/* Advance simulation one step on CPU. Return elapsed wall time in ms. */
- (double)stepCPU;

/* Encode compute dispatch + render pass into buf. Return GPU time estimate. */
- (void)encodeGPUFrame:(id<MTLCommandBuffer>)buf
           drawable:(id<CAMetalDrawable>)drawable;

/* ── Utilities ───────────────────────────────────────────────────────────── */

/* Load a .metallib compiled into the same directory as the executable */
- (id<MTLLibrary>)loadMetalLibrary:(NSString *)path;

/* Save a benchmark line to the results file */
- (void)logResult:(NSString *)line;

@end
