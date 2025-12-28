# Stage 1: Download and Cache Model
FROM python:3.11-slim AS model-downloader

WORKDIR /models

# Install model download dependencies
COPY requirements.model.txt .
RUN pip install --no-cache-dir -r requirements.model.txt && rm requirements.model.txt

# Download model and cache it
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); model.save('/models/all-MiniLM-L6-v2')" && echo "✓ Model downloaded and cached"

# Validate model files exist
RUN test -d /models/all-MiniLM-L6-v2 || (echo "ERROR: Model directory not found" && exit 1) && test -f /models/all-MiniLM-L6-v2/config.json || (echo "ERROR: Model config not found" && exit 1) && echo "✓ Model validation passed"

# Stage 2: Build Final Runtime Image
FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for psutil
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install runtime dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove gcc python3-dev && apt-get clean

# Copy cached model from stage 1
COPY --from=model-downloader /models /root/.cache/torch/sentence_transformers

# Verify model is accessible
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print(f'✓ Model loaded: {model.get_sentence_embedding_dimension()} dimensions')" || (echo "ERROR: Model verification failed" && exit 1)

# Copy application code
COPY app.py .

# Create non-root user
RUN useradd -m -u 1000 embedder && chown -R embedder:embedder /app /root/.cache

USER embedder

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5).raise_for_status()"

EXPOSE 8000

# Run application
CMD ["python", "app.py"]
