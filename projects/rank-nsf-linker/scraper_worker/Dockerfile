# Stage 1: Export Model
FROM cgr.dev/chainguard/wolfi-base AS model-exporter

WORKDIR /export

# Install Python 3.12 specifically (not 3.14-dev)
RUN apk add --no-cache python-3.12 py3.12-pip

# Copy the requirements.txt file
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    python3.12 -m pip install --no-cache-dir -r requirements.txt

# Cache model downloads
COPY export_model.py .
RUN --mount=type=cache,target=/root/.cache/huggingface \
    python3.12 export_model.py || exit 1

# Validate
RUN test -f /export/models/all-MiniLM-L6-v2-onnx/model.onnx || \
    (echo "ERROR: model.onnx not found" && exit 1)

# Stage 2: Build Go Binary
FROM cgr.dev/chainguard/go AS builder

RUN mkdir -p /app/data
WORKDIR /app

# Copy Go modules first (better caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy source and build
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o scraper-worker .

# Validate binary
RUN test -x /app/scraper-worker || \
    (echo "ERROR: Binary not executable" && exit 1)

# Stage 3: Final Runtime Image
FROM cgr.dev/chainguard/wolfi-base:latest

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/scraper-worker ./scraper-worker

# Copy Go modules to SAME PATH as builder
COPY --from=builder /root/go/pkg/mod /root/go/pkg/mod

# Copy models from exporter
COPY --from=model-exporter /export/models/all-MiniLM-L6-v2-onnx ./models/all-MiniLM-L6-v2-onnx

# Copy init script
COPY scripts/init_models.sh /usr/local/bin/init_models.sh
RUN chmod +x /usr/local/bin/init_models.sh && \
    sh /usr/local/bin/init_models.sh

# Create directories and set permissions
RUN mkdir -p /app/data /app/models && \
    chown -R 65532:65532 /app /root/

# Validate everything is in place
RUN test -f /app/scraper-worker && \
    test -f /app/models/all-MiniLM-L6-v2-onnx/model.onnx && \
    echo "✓ All files present"

USER 65532

ENTRYPOINT ["./scraper-worker"]
