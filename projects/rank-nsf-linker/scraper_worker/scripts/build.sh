#!/bin/bash
set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_build() {
    echo -e "${BLUE}[BUILD]${NC} $1"
}

# Validate required environment variables
REQUIRED_VARS=("TARGETARCH" "TARGETOS")
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        log_error "$var environment variable not set"
        exit 1
    fi
done

log_info "Build configuration:"
log_info "  Target OS: $TARGETOS"
log_info "  Target Architecture: $TARGETARCH"
log_info "  Build Platform: ${BUILDPLATFORM:-unknown}"

# Select appropriate C/C++ compiler for target architecture
case "$TARGETARCH" in
    arm64)
        export CC=aarch64-linux-gnu-gcc
        export CXX=aarch64-linux-gnu-g++
        log_info "Using ARM64 cross-compiler"
        ;;
    amd64)
        # Use x86_64 cross-compiler instead of native gcc
        if command -v x86_64-linux-gnu-gcc &> /dev/null; then
            export CC=x86_64-linux-gnu-gcc
            export CXX=x86_64-linux-gnu-g++
            log_info "Using x86_64 cross-compiler"
        else
            # Fallback to native gcc with proper flags
            export CC=gcc
            export CXX=g++
            # Disable -m64 flag by using CGO_CFLAGS
            export CGO_CFLAGS="${CGO_CFLAGS:-} -march=x86-64"
            log_warn "x86_64-linux-gnu-gcc not found, using native gcc"
            log_warn "This may cause issues on non-x86 build platforms"
        fi
        ;;
    *)
        log_error "Unsupported target architecture: $TARGETARCH"
        log_info "Supported architectures: amd64, arm64"
        exit 1
        ;;
esac

# Verify compiler exists and is executable
if ! command -v "$CC" &> /dev/null; then
    log_error "Compiler not found: $CC"
    log_info "Available compilers:"
    compilers=$(find /usr/bin -name '*gcc*' 2>/dev/null || echo "  none found")
    echo "$compilers"
    exit 1
fi

# Display compiler information
log_info "Compiler details:"
COMPILER_VERSION=$($CC --version | head -n1)
log_info "  CC: $CC ($COMPILER_VERSION)"
log_info "  CXX: $CXX"

# Verify CGO configuration
if [ -z "${CGO_CFLAGS:-}" ] || [ -z "${CGO_LDFLAGS:-}" ]; then
    log_warn "CGO_CFLAGS or CGO_LDFLAGS not set"
    log_warn "This may cause linking issues with ONNX Runtime"
fi

log_info "CGO configuration:"
log_info "  CGO_CFLAGS: ${CGO_CFLAGS:-not set}"
log_info "  CGO_LDFLAGS: ${CGO_LDFLAGS:-not set}"

# Verify ONNX Runtime libraries exist
ONNX_LIB="/usr/local/onnxruntime/lib/libonnxruntime.so"
if [ ! -f "$ONNX_LIB" ]; then
    log_error "ONNX Runtime library not found: $ONNX_LIB"
    log_info "Expected location: /usr/local/onnxruntime/lib/"
    if [ -d "/usr/local/onnxruntime/lib/" ]; then
        log_info "Contents of ONNX Runtime lib directory:"
        ls -lh /usr/local/onnxruntime/lib/
    fi
    exit 1
fi

log_info "✓ ONNX Runtime library found: $ONNX_LIB"

# Verify Go dependencies are downloaded
if [ ! -d "vendor" ] && [ ! -f "go.sum" ]; then
    log_warn "go.sum not found - dependencies may not be downloaded"
fi

# Build configuration
OUTPUT_BINARY="scraper-worker"

log_build "Starting Go build..."
log_build "  Output: $OUTPUT_BINARY"
log_build "  Linker flags: -w -s (strip debug info and symbol table)"
log_build "  CGO: enabled"

# Execute build with detailed error handling
BUILD_START=$(date +%s)

if CGO_ENABLED=1 \
   GOOS="$TARGETOS" \
   GOARCH="$TARGETARCH" \
   CC="$CC" \
   CXX="$CXX" \
   go build -ldflags "-w -s" -o "$OUTPUT_BINARY" .; then
    
    BUILD_END=$(date +%s)
    BUILD_DURATION=$((BUILD_END - BUILD_START))
    
    log_info "✓ Build completed in ${BUILD_DURATION}s"
else
    BUILD_EXIT_CODE=$?
    log_error "Build failed with exit code $BUILD_EXIT_CODE"
    
    # Provide helpful debugging information
    log_info "Troubleshooting hints:"
    log_info "  1. Check if all Go dependencies are available"
    log_info "  2. Verify ONNX Runtime headers are in: /usr/local/onnxruntime/include/"
    log_info "  3. Ensure CGO_LDFLAGS points to correct library path"
    log_info "  4. Check for architecture mismatch in dependencies"
    log_info "  5. Verify correct cross-compiler is installed for target arch"
    
    exit $BUILD_EXIT_CODE
fi

# Verify output binary exists
if [ ! -f "$OUTPUT_BINARY" ]; then
    log_error "Build reported success but binary not found: $OUTPUT_BINARY"
    exit 1
fi

# Get binary size
BINARY_SIZE=$(stat -f%z "$OUTPUT_BINARY" 2>/dev/null || stat -c%s "$OUTPUT_BINARY")
BINARY_SIZE_MB=$(awk "BEGIN {printf \"%.2f\", $BINARY_SIZE/1024/1024}")

log_info "Binary information:"
log_info "  Size: ${BINARY_SIZE_MB} MB"

# Verify binary architecture using 'file' command
if command -v file &> /dev/null; then
    BINARY_INFO=$(file "$OUTPUT_BINARY")
    log_info "  Type: $BINARY_INFO"
    
    # Validate architecture matches target
    case "$TARGETARCH" in
        amd64)
            if ! echo "$BINARY_INFO" | grep -q "x86-64\|x86_64"; then
                log_error "Binary architecture mismatch!"
                log_error "Expected: x86-64, Got: $BINARY_INFO"
                exit 1
            fi
            ;;
        arm64)
            if ! echo "$BINARY_INFO" | grep -q "aarch64\|ARM64"; then
                log_error "Binary architecture mismatch!"
                log_error "Expected: aarch64, Got: $BINARY_INFO"
                exit 1
            fi
            ;;
    esac
    
    log_info "✓ Binary architecture verified: $TARGETARCH"
else
    log_warn "'file' command not available - skipping architecture verification"
fi

# Check for dynamic library dependencies
if command -v ldd &> /dev/null && [ "$TARGETARCH" = "amd64" ]; then
    log_info "Checking dynamic library dependencies..."
    LDD_OUTPUT=$(ldd "$OUTPUT_BINARY" 2>&1 || true)
    
    if echo "$LDD_OUTPUT" | grep -q "not found"; then
        log_error "Missing dynamic library dependencies:"
        echo "$LDD_OUTPUT" | grep "not found"
        exit 1
    fi
    
    # Check for ONNX Runtime dependency
    if echo "$LDD_OUTPUT" | grep -q "libonnxruntime.so"; then
        log_info "✓ ONNX Runtime library linked correctly"
    else
        log_warn "ONNX Runtime library not found in dependencies"
        log_warn "Binary may fail at runtime if ONNX functions are called"
    fi
elif [ "$TARGETARCH" = "arm64" ]; then
    log_info "Skipping ldd check for cross-compiled ARM64 binary"
fi

# Display build summary
echo ""
log_info "═══════════════════════════════════════════════════"
log_info "           BUILD SUMMARY"
log_info "═══════════════════════════════════════════════════"
log_info "  Binary: $OUTPUT_BINARY"
log_info "  Size: ${BINARY_SIZE_MB} MB"
log_info "  Target: $TARGETOS/$TARGETARCH"
log_info "  Compiler: $CC"
log_info "  Duration: ${BUILD_DURATION}s"
log_info "═══════════════════════════════════════════════════"
echo ""

log_info "✓ Build process complete"
