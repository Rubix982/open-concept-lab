#!/bin/sh
set -e

# Configuration
MODEL_DIR="/app/models/all-MiniLM-L6-v2-onnx"
EMBEDDED_MODEL_DIR="/embedded-models/all-MiniLM-L6-v2-onnx"

# Logging helpers
log_info() {
    echo "→ [$(date +%H:%M:%S)] $1"
}

log_success() {
    echo "✓ [$(date +%H:%M:%S)] $1"
}

log_error() {
    echo "✗ [$(date +%H:%M:%S)] ERROR: $1" >&2
}

log_debug() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo "  [$(date +%H:%M:%S)] DEBUG: $1"
    fi
}

# Validation functions
validate_model_files() {
    local dir="$1"
    local required_files="model.onnx tokenizer_config.json config.json"
    
    log_debug "Validating model files in: $dir"
    
    for file in $required_files; do
        if [ ! -f "$dir/$file" ]; then
            log_error "Missing required file: $file"
            return 1
        fi
        log_debug "Found: $file ($(du -h "$dir/$file" | cut -f1))"
    done
    
    return 0
}

# Main logic
main() {
    log_info "Starting model initialization"
    log_debug "Model mount point: $MODEL_DIR"
    log_debug "Embedded models: $EMBEDDED_MODEL_DIR"
    
    # Check if models already exist in mounted volume
    if [ -f "$MODEL_DIR/model.onnx" ]; then
        log_success "Models already present in mounted volume"
        
        # Validate existing models
        if validate_model_files "$MODEL_DIR"; then
            log_success "Model validation passed"
            log_info "Using models from host volume"
            return 0
        else
            log_error "Model validation failed, will re-copy"
            log_info "Removing corrupted models"
            rm -rf "$MODEL_DIR"/*
        fi
    else
        log_info "Models not found in mounted volume"
    fi
    
    # Check if embedded models exist
    if [ ! -d "$EMBEDDED_MODEL_DIR" ]; then
        log_error "Embedded models not found at: $EMBEDDED_MODEL_DIR"
        log_error "Image may be corrupted or incorrectly built"
        exit 1
    fi
    
    log_debug "Embedded models directory found"
    
    # Validate embedded models before copying
    if ! validate_model_files "$EMBEDDED_MODEL_DIR"; then
        log_error "Embedded models are invalid"
        exit 1
    fi
    
    log_success "Embedded models validated"
    
    # Create destination directory
    log_info "Creating model directory: $MODEL_DIR"
    mkdir -p "$MODEL_DIR"
    
    # Copy models with progress
    log_info "Copying models from image to mounted volume (one-time operation)"
    log_debug "Source: $EMBEDDED_MODEL_DIR"
    log_debug "Destination: $MODEL_DIR"
    
    if cp -rv "$EMBEDDED_MODEL_DIR/"* "$MODEL_DIR/" 2>&1 | while read line; do
        log_debug "$line"
    done; then
        log_success "Models copied successfully"
    else
        log_error "Failed to copy models"
        exit 1
    fi
    
    # Validate copied models
    log_info "Validating copied models"
    if validate_model_files "$MODEL_DIR"; then
        log_success "Model validation passed"
    else
        log_error "Copied models failed validation"
        exit 1
    fi
    
    # Print summary
    local model_size=$(du -sh "$MODEL_DIR" | cut -f1)
    log_success "Model initialization complete"
    log_info "Location: $MODEL_DIR"
    log_info "Total size: $model_size"
    log_info "Subsequent runs will use cached models from host"
    
    return 0
}

# Run main function
main
