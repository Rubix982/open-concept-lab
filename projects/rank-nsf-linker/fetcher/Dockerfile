# Fetcher: runs the data-fetch scripts (server/scripts) for the pipeline; see fetcher/app.py.
# Build from the project root: docker build -f fetcher/Dockerfile .
FROM python:3.12-slim

# pdftotext parses the ERC result PDFs (grants/erc_lists.py)
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY server/scripts /app/server/scripts
COPY fetcher/app.py /app/fetcher/app.py

# data/ and backup/ are mounted; API keys come from the environment, never from the image
RUN useradd --uid 65532 --create-home fetcher && mkdir -p /app/data /app/backup && chown -R 65532 /app
USER 65532
EXPOSE 8090
CMD ["python3", "-u", "/app/fetcher/app.py"]
