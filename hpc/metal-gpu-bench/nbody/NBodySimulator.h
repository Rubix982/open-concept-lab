/*
 * NBodySimulator.h
 * ─────────────────
 * Manages particle state and exposes CPU + GPU step methods.
 * MetalBase calls these from the render loop.
 */

#pragma once
#import "../common/MetalBase.h"

/* Must match the struct in Shaders.metal exactly */
typedef struct {
    float pos[2];
    float vel[2];
    float mass;
    float _pad;
} Particle;

typedef struct {
    unsigned int N;
    float        dt;
    float        softening;
    float        G;
} NBodyParams;

@interface NBodySimulator : MetalBase

- (instancetype)initWithN:(NSUInteger)N;

@end
