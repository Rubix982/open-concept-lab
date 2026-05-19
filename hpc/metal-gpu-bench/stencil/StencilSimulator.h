/*
 * StencilSimulator.h
 * ───────────────────
 * 2D heat diffusion stencil — CPU (pthreads) vs GPU (Metal compute).
 * Inherits MetalBase for window, render loop, overlay, and results logging.
 */

#pragma once
#import "../common/MetalBase.h"

typedef struct {
    unsigned int W;
    unsigned int H;
    float        alpha;
} StencilParams;

@interface StencilSimulator : MetalBase

- (instancetype)initWithWidth:(NSUInteger)W height:(NSUInteger)H;

@end
