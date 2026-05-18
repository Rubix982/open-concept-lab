CC            = clang
CFLAGS_COMMON = -Wall -Wextra -std=c11
CFLAGS_OPT    = -O3 -march=native -ffast-math
CFLAGS_DBG    = -O0 -g
LIBS          = -lm

.PHONY: all debug clean run run_debug compare

all: bench

bench: bench.c
	$(CC) $(CFLAGS_COMMON) $(CFLAGS_OPT) -o bench bench.c $(LIBS)
	@echo "Built: bench  ($(CFLAGS_OPT))"

debug: bench_O0

bench_O0: bench.c
	$(CC) $(CFLAGS_COMMON) $(CFLAGS_DBG) -o bench_O0 bench.c $(LIBS)
	@echo "Built: bench_O0  ($(CFLAGS_DBG))"

run: bench
	@mkdir -p ../results
	./bench

run_debug: bench_O0
	@mkdir -p ../results
	./bench_O0

# Run both builds back to back to see what the compiler buys you
compare: bench bench_O0
	@mkdir -p ../results
	@echo "\n=== O3 (optimised) ==="
	./bench --mm 256
	@echo "\n=== O0 (no optimisation) ==="
	./bench_O0 --mm 256

clean:
	rm -f bench bench_O0
