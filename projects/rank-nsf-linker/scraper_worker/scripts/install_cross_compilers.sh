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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

log_info "Starting cross-compiler installation"
log_info "Target architectures: amd64, arm64"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ] && ! command -v sudo &> /dev/null; then
    log_error "This script requires root privileges or sudo"
    exit 1
fi

# Detect package manager (for future compatibility)
if command -v apt-get &> /dev/null; then
    PKG_MANAGER="apt-get"
    log_info "Detected package manager: apt-get"
else
    log_error "apt-get not found. This script requires Debian/Ubuntu."
    exit 1
fi

# Enable multi-architecture support
log_step "Enabling multi-architecture support"

ARCHS_TO_ADD=("amd64" "arm64")
ADDED_ARCHS=0

for arch in "${ARCHS_TO_ADD[@]}"; do
    # Check if architecture already enabled
    if dpkg --print-foreign-architectures | grep -q "^${arch}$"; then
        log_info "  Architecture already enabled: $arch"
    else
        log_info "  Adding architecture: $arch"
        if dpkg --add-architecture "$arch"; then
            log_info "  ✓ Successfully added: $arch"
            ADDED_ARCHS=$((ADDED_ARCHS + 1))
        else
            log_error "  Failed to add architecture: $arch"
            exit 1
        fi
    fi
done

if [ $ADDED_ARCHS -gt 0 ]; then
    log_info "Added $ADDED_ARCHS new architecture(s)"
fi

# Update package lists
log_step "Updating package lists"

MAX_RETRIES=3
UPDATE_SUCCESS=false

for attempt in $(seq 1 $MAX_RETRIES); do
    log_info "  Attempt $attempt/$MAX_RETRIES..."
    
    if apt-get update; then
        log_info "  ✓ Package lists updated"
        UPDATE_SUCCESS=true
        break
    else
        log_warn "  Package list update failed"
        if [ $attempt -lt $MAX_RETRIES ]; then
            log_info "  Retrying in 5s..."
            sleep 5
        fi
    fi
done

if [ "$UPDATE_SUCCESS" = false ]; then
    log_error "Failed to update package lists after $MAX_RETRIES attempts"
    exit 1
fi

# Define packages to install
PACKAGES=(
    "gcc-aarch64-linux-gnu"
    "g++-aarch64-linux-gnu"
    "wget"
    "file"
)

log_step "Installing cross-compilation toolchains"
log_info "Packages to install: ${#PACKAGES[@]}"

# Check package availability before installation
log_info "Checking package availability..."

UNAVAILABLE_PACKAGES=()

for package in "${PACKAGES[@]}"; do
    if apt-cache show "$package" &> /dev/null; then
        log_info "  ✓ Available: $package"
    else
        log_warn "  ✗ Not available: $package"
        UNAVAILABLE_PACKAGES+=("$package")
    fi
done

if [ ${#UNAVAILABLE_PACKAGES[@]} -gt 0 ]; then
    log_warn "Some packages are not available in repositories:"
    for package in "${UNAVAILABLE_PACKAGES[@]}"; do
        log_warn "  - $package"
    done
    
    log_info "Searching for alternative package names..."
    
    # Try to find alternatives
    log_info "Available gcc cross-compilers:"
    apt-cache search "^gcc.*linux-gnu$" | grep -E "(aarch64|x86.64)" || log_warn "  No alternatives found"
    
    log_error "Cannot proceed with missing critical packages"
    log_info "Possible solutions:"
    log_info "  1. Use a different base image (e.g., golang:1.23-bookworm)"
    log_info "  2. Add additional package repositories"
    log_info "  3. Install compilers manually"
    exit 1
fi

# Install packages
log_info "Installing packages..."

INSTALL_SUCCESS=false

for attempt in $(seq 1 $MAX_RETRIES); do
    log_info "  Installation attempt $attempt/$MAX_RETRIES..."
    
    if apt-get install -y --no-install-recommends "${PACKAGES[@]}"; then
        log_info "  ✓ All packages installed successfully"
        INSTALL_SUCCESS=true
        break
    else
        log_warn "  Installation failed"
        if [ $attempt -lt $MAX_RETRIES ]; then
            log_info "  Retrying in 5s..."
            sleep 5
        fi
    fi
done

if [ "$INSTALL_SUCCESS" = false ]; then
    log_error "Failed to install packages after $MAX_RETRIES attempts"
    exit 1
fi

# Clean up package lists to reduce image size
log_step "Cleaning up package cache"
if rm -rf /var/lib/apt/lists/*; then
    log_info "✓ Package cache cleaned"
else
    log_warn "Failed to clean package cache (non-critical)"
fi

# Verify installations
log_step "Verifying cross-compiler installations"

COMPILERS=(
    "gcc-aarch64-linux-gnu:ARM64 GCC"
    "g++-aarch64-linux-gnu:ARM64 G++"
    "gcc-x86-64-linux-gnu:x86_64 GCC"
    "g++-x86-64-linux-gnu:x86_64 G++"
)

VERIFICATION_FAILED=false

for compiler_info in "${COMPILERS[@]}"; do
    IFS=':' read -r compiler_name compiler_desc <<< "$compiler_info"
    
    if command -v "$compiler_name" &> /dev/null; then
        version=$($compiler_name --version | head -n1)
        log_info "  ✓ $compiler_desc: $version"
    else
        log_error "  ✗ $compiler_desc not found: $compiler_name"
        VERIFICATION_FAILED=true
    fi
done

# Verify additional tools
TOOLS=("wget" "file")

for tool in "${TOOLS[@]}"; do
    if command -v "$tool" &> /dev/null; then
        log_info "  ✓ Tool available: $tool"
    else
        log_warn "  ✗ Tool not found: $tool"
        VERIFICATION_FAILED=true
    fi
done

if [ "$VERIFICATION_FAILED" = true ]; then
    log_error "Some compilers or tools are missing"
    exit 1
fi

# Display summary
echo ""
log_info "═══════════════════════════════════════════════════"
log_info "     CROSS-COMPILER INSTALLATION COMPLETE"
log_info "═══════════════════════════════════════════════════"
log_info "  Enabled architectures: amd64, arm64"
log_info "  ARM64 compiler: gcc-aarch64-linux-gnu"
log_info "  x86_64 compiler: gcc-x86-64-linux-gnu"
log_info "  Additional tools: wget, file"
log_info "═══════════════════════════════════════════════════"
echo ""

log_info "✓ Cross-compiler setup complete"
