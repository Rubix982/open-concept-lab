# Stage 1: Build Go Binary
FROM cgr.dev/chainguard/go AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN go build -o scraper-worker .

# Stage 2: Export Model (with pip cache mount)
FROM cgr.dev/chainguard/wolfi-base AS model-exporter

WORKDIR /export

# Install Python 3.12 specifically (not 3.14-dev)
RUN apk add --no-cache python-3.12 py3.12-pip

# Copy the requirements.txt file
COPY requirements.txt .

# Install ONNX export dependencies
# Use BuildKit cache mount (no reinstall on rebuild)
RUN --mount=type=cache,target=/root/.cache/pip \
    python3.12 -m pip install --no-cache-dir -r requirements.txt

# Copy export script
COPY export_model.py .

# Run export (creates ./models/all-MiniLM-L6-v2-onnx/)
RUN python3.12 export_model.py && \
    ls -lah models/all-MiniLM-L6-v2-onnx/ && \
    echo "✓ ONNX export complete"

# Stage 3: Runtime (Go + ONNX model only, no Python)
FROM cgr.dev/chainguard/wolfi-base

WORKDIR /app

# Install ONNX Runtime library
RUN mkdir -p /app/data

# Copy Go binary
COPY --from=builder /app/scraper-worker .

# Copy ONNX model files only
COPY --from=model-exporter /export/models/all-MiniLM-L6-v2-onnx /app/models/all-MiniLM-L6-v2-onnx

# Set model path for Go service
ENV MODEL_DIR=/app/models/all-MiniLM-L6-v2-onnx

# Set permissions
RUN chown -R 65532:65532 /app && \
    chmod 755 /app/scraper-worker

USER 65532

ENTRYPOINT ["./scraper-worker"]