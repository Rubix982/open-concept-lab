FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY README.md .

# Install dependencies
RUN pip install --no-cache-dir .

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "persistent_memory.worker"]
