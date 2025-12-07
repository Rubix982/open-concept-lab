# Stage 1: Build Go Binary
FROM cgr.dev/chainguard/go AS builder

WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Build as 'scraper-worker'
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o scraper-worker .

# Stage 2: Runtime
FROM cgr.dev/chainguard/wolfi-base

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/data/hf_cache

# Install Python and Pip
RUN apk add --no-cache python3 py3-pip

# Copy binary
COPY --from=builder /app/scraper-worker .

# Copy Python scripts
COPY embedder.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Permissions
RUN chown -R 65532:65532 /app && \
    chmod 755 /app/embedder.py

USER 65532

ENTRYPOINT ["./scraper-worker"]
