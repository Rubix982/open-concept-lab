#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color output for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate TARGETARCH is set
if [ -z "${TARGETARCH:-}" ]; then
    log_error "TARGETARCH environment variable not set"
    exit 1
fi

# Determine ONNX Runtime URL based on architecture
case "$TARGETARCH" in
    amd64)
        ONNX_URL="https://github.com/microsoft/onnxruntime/releases/download/v1.23.2/onnxruntime-linux-x64-1.23.2.tgz"
        EXPECTED_DIR="onnxruntime-linux-x64-1.23.2"
        ;;
    arm64)
        ONNX_URL="https://github.com/microsoft/onnxruntime/releases/download/v1.23.2/onnxruntime-linux-aarch64-1.23.2.tgz"
        EXPECTED_DIR="onnxruntime-linux-aarch64-1.23.2"
        ;;
    *)
        log_error "Unsupported architecture: $TARGETARCH"
        log_info "Supported architectures: amd64, arm64"
        exit 1
        ;;
esac

log_info "Target architecture: $TARGETARCH"
log_info "ONNX Runtime URL: $ONNX_URL"

# Download with retry logic
MAX_RETRIES=3
RETRY_DELAY=5
DOWNLOAD_SUCCESS=false

for i in $(seq 1 $MAX_RETRIES); do
    log_info "Download attempt $i/$MAX_RETRIES..."
    
    if wget --timeout=30 --tries=3 --progress=dot:giga "$ONNX_URL" -O onnxruntime.tgz; then
        # Verify download integrity
        if [ -f onnxruntime.tgz ] && [ -s onnxruntime.tgz ]; then
            FILE_SIZE=$(stat -f%z onnxruntime.tgz 2>/dev/null || stat -c%s onnxruntime.tgz)
            log_info "Downloaded $FILE_SIZE bytes"
            
            # Check if file is valid gzip
            if gzip -t onnxruntime.tgz 2>/dev/null; then
                log_info "Download verification successful"
                DOWNLOAD_SUCCESS=true
                break
            else
                log_warn "Downloaded file is corrupted (invalid gzip)"
                rm -f onnxruntime.tgz
            fi
        else
            log_warn "Downloaded file is empty or missing"
            rm -f onnxruntime.tgz
        fi
    else
        log_warn "Download failed (wget exit code: $?)"
    fi
    
    if [ $i -lt $MAX_RETRIES ]; then
        log_info "Retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    fi
done

if [ "$DOWNLOAD_SUCCESS" = false ]; then
    log_error "Failed to download ONNX Runtime after $MAX_RETRIES attempts"
    exit 1
fi

# Extract archive
log_info "Extracting archive..."
if ! tar -xzf onnxruntime.tgz; then
    log_error "Failed to extract archive"
    exit 1
fi

# Verify extraction
if [ ! -d "$EXPECTED_DIR" ]; then
    log_error "Expected directory '$EXPECTED_DIR' not found after extraction"
    log_info "Contents of current directory:"
    ls -la
    exit 1
fi

# Move to installation directory
log_info "Installing to /usr/local/onnxruntime..."
if ! mv "$EXPECTED_DIR" /usr/local/onnxruntime; then
    log_error "Failed to move ONNX Runtime to /usr/local/onnxruntime"
    exit 1
fi

# Cleanup
log_info "Cleaning up temporary files..."
rm -f onnxruntime.tgz

# Verify installation
if [ ! -d /usr/local/onnxruntime/lib ]; then
    log_error "Installation verification failed: lib directory not found"
    exit 1
fi

# List installed libraries
log_info "Installed ONNX Runtime libraries:"
ls -lh /usr/local/onnxruntime/lib/

# Verify critical files exist
CRITICAL_FILES=(
    "/usr/local/onnxruntime/include/onnxruntime_c_api.h"
    "/usr/local/onnxruntime/lib/libonnxruntime.so"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        log_error "Critical file missing: $file"
        exit 1
    fi
done

log_info "✓ ONNX Runtime setup complete"
