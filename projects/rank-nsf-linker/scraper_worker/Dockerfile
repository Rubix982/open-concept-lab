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

# Stage 3: Final Runtime Image with Chrome
FROM debian:bookworm-slim

WORKDIR /app

# Install Chrome and dependencies for Rod
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libgdk-pixbuf2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (matching chainguard UID)
RUN useradd -m -u 65532 nonroot

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
RUN mkdir -p /app/data /app/models /home/nonroot/.cache/rod && \
    chown -R 65532:65532 /app /root/ /home/nonroot/

# Validate everything is in place
RUN test -f /app/scraper-worker && \
    test -f /app/models/all-MiniLM-L6-v2-onnx/model.onnx && \
    test -x /usr/bin/chromium && \
    echo "✓ All files present"

# Set Rod environment variables
ENV ROD_LAUNCHER=/usr/bin/chromium \
    CHROME_BIN=/usr/bin/chromium \
    CHROME_PATH=/usr/lib/chromium/

USER 65532

ENTRYPOINT ["./scraper-worker"]
