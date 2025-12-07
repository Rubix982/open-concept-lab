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

# Install Python, Pip, and create directories in one layer
RUN apk add --no-cache python3 py3-pip && \
    mkdir -p /app/data/hf_cache

# Copy binary
COPY --from=builder /app/scraper-worker .

# Copy Python dependencies first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy remaining Python scripts
COPY embedder.py .

# Set permissions
RUN chown -R 65532:65532 /app && \
    chmod 755 /app/embedder.py && \
    chmod 755 /app/scraper-worker

USER 65532

ENTRYPOINT ["./scraper-worker"]
