# Headless CPU vs GPU timing; needs only the Command Line Tools (the Metal
# shaders are compiled from source at runtime, not with Xcode's `metal`).
bench: bench.m
	clang -std=gnu11 -O2 -fobjc-arc -framework Foundation -framework Metal bench.m -o bench

run: bench
	./bench
	python3 export.py

# bake results/*.json into site/data/native.js for the page
export:
	python3 export.py

clean:
	rm -f bench
