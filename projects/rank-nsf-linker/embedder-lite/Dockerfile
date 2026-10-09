# Query embedder for the minimal deployment (see app.py). Build from this directory.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV FASTEMBED_CACHE=/models
COPY app.py .
# Download the model at build time, so the container starts offline and fast
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2', cache_dir='/models')"
RUN useradd --uid 65532 app && chown -R 65532 /models
USER 65532
EXPOSE 8000
CMD ["python", "-u", "app.py"]
