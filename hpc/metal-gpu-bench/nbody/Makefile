# N-body Metal demo Makefile
#
# Build steps:
#   1. Compile Shaders.metal → Shaders.air (Metal IR)
#   2. Link Shaders.air      → Shaders.metallib (Metal library)
#   3. Compile .m + .c       → nbody executable
#
# The executable and Shaders.metallib must be in the same directory
# because MetalBase loads the metallib relative to the executable path.

SDK         = macosx
METAL       = xcrun -sdk $(SDK) metal
METALLIB    = xcrun -sdk $(SDK) metallib
CC          = clang
OBJC_FLAGS  = -std=gnu11 -fobjc-arc \
              -I../common \
              -framework Metal \
              -framework QuartzCore \
              -framework Cocoa \
              -framework CoreVideo \
              -framework CoreGraphics

.PHONY: all clean run

all: nbody Shaders.metallib

# Step 1+2: Metal shader compilation
Shaders.air: Shaders.metal
	$(METAL) -c Shaders.metal -o Shaders.air

Shaders.metallib: Shaders.air
	$(METALLIB) Shaders.air -o Shaders.metallib

# Step 3: Objective-C + C compilation
nbody: main.m NBodySimulator.m ../common/MetalBase.m Shaders.metallib
	$(CC) $(OBJC_FLAGS) \
	    main.m NBodySimulator.m ../common/MetalBase.m \
	    -o nbody

run: all
	./nbody

run_large: all
	./nbody --n 16384

clean:
	rm -f nbody Shaders.air Shaders.metallib
