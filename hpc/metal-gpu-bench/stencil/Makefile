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

.PHONY: all clean run run_large

all: stencil Shaders.metallib

Shaders.air: Shaders.metal
	$(METAL) -c Shaders.metal -o Shaders.air

Shaders.metallib: Shaders.air
	$(METALLIB) Shaders.air -o Shaders.metallib

stencil: main.m StencilSimulator.m ../common/MetalBase.m Shaders.metallib
	$(CC) $(OBJC_FLAGS) \
	    main.m StencilSimulator.m ../common/MetalBase.m \
	    -o stencil

run: all
	./stencil

run_large: all
	./stencil --w 2048 --h 2048

clean:
	rm -f stencil Shaders.air Shaders.metallib
