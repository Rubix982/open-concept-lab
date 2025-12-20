#!/bin/bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Configuration
TIMEOUT=300
MAX_RETRIES=3
MIRRORS=(
    "https://pypi.org/simple"
    "https://mirrors.aliyun.com/pypi/simple/"
    "https://pypi.tuna.tsinghua.edu.cn/simple"
)

REQUIREMENTS_FILE="requirements.txt"

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    log_error "Requirements file not found: $REQUIREMENTS_FILE"
    exit 1
fi

log_info "Installing Python packages from $REQUIREMENTS_FILE"

# Read requirements line by line
while IFS= read -r package || [ -n "$package" ]; do
    # Skip empty lines and comments
    [[ -z "$package" || "$package" =~ ^[[:space:]]*# ]] && continue
    
    log_info "Installing: $package"
    
    INSTALLED=false
    
    # Try each mirror
    for mirror in "${MIRRORS[@]}"; do
        log_info "  Trying mirror: $mirror"
        
        for attempt in $(seq 1 $MAX_RETRIES); do
            log_info "    Attempt $attempt/$MAX_RETRIES..."
            
            if pip install \
                --root-user-action \
                --no-cache-dir \
                --timeout=$TIMEOUT \
                --index-url "$mirror" \
                "$package"; then
                
                log_info "  ✓ Successfully installed: $package"
                INSTALLED=true
                break 2
            else
                log_warn "    Failed (attempt $attempt)"
                [ $attempt -lt $MAX_RETRIES ] && sleep 5
            fi
        done
    done
    
    if [ "$INSTALLED" = false ]; then
        log_error "Failed to install: $package after trying all mirrors"
        exit 1
    fi
    
done < "$REQUIREMENTS_FILE"

log_info "✓ All packages installed successfully"