# Stage 1: Use Chainguard's Go builder
FROM cgr.dev/chainguard/go AS builder

WORKDIR /app

# Copy go module files and download dependencies
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Copy the env file
COPY .env /app/

# Copy the migration folder
COPY migrations /app/

# Copy the scripts folder
COPY scripts /app/

# Copy the certificates
COPY certs /app/

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o go-server .

# Stage 2: Minimal distroless image from Chainguard
FROM cgr.dev/chainguard/wolfi-base

WORKDIR /app

RUN mkdir -p /app/data/nsfdata
RUN mkdir -p /app/data/scraped_cache
RUN mkdir -p /app/target/

# Install Python3 and pip for scraper
RUN apk add --no-cache python3 py3-pip

# Copy built binary from builder stage
COPY --from=builder /app/go-server .
COPY --from=builder /app/.env /app/.env
COPY --from=builder /app/migrations /app/migrations
COPY --from=builder /app/scripts /app/scripts
COPY --from=builder /app/certs /app/certs

# Make sure certs and the data directory are readable by the non-root user
RUN chown -R 65532:65532 /app/certs && \
    chown -R 65532:65532 /app/target && \
    chmod 600 /app/data && \
    chmod 600 /app/certs/client.key /app/certs/client.crt /app/certs/ca.crt

EXPOSE 8193

# Run as non-root (Chainguard images often use non-root by default)
USER 65532

# An environment variable to check the type of enviroment. If empty, we will assume it is local
ENV APP_ENV=development

ENTRYPOINT ["./go-server"]
