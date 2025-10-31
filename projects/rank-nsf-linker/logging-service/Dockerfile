# Single-Stage Build: Using the most minimal and secure Wolfi base
FROM cgr.dev/chainguard/wolfi-base:latest

WORKDIR /app

# 1. Install Python 3 and the core package manager (apk)
# We must use 'python3' explicitly since the base image is empty.
RUN apk add --no-cache python3 py3-pip

# 2. Copy requirements and install dependencies
# We use the explicit 'pip3' here, as 'pip' often points to the wrong binary or is unset.
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 3. Copy application code and environment file
COPY app.py .
COPY .env .

# 4. Create logs directory and fix permissions
# Ensure the nonroot user can write logs.
RUN mkdir -p /app/logs && chown 65532:65532 /app/logs

# Set configuration variables
ENV ELASTICSEARCH_HOST="http://elasticsearch:9200"
ENV PYTHONUNBUFFERED=1

# Expose the port
EXPOSE 5000

# Run as nonroot user (UID 65532)
USER 65532

# Command to run the application
# We wrap it in /bin/sh -c to allow the environment variables to resolve correctly,
# and to ensure the script executes properly on the minimal Wolfi environment.
CMD ["python3", "app.py"]