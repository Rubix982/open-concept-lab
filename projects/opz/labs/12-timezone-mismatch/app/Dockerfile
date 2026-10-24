# Moved off python:3.12-slim to plain Alpine to cut the image size.
FROM alpine:3
RUN apk add --no-cache python3
WORKDIR /app
COPY scheduler.py .
CMD ["python3", "scheduler.py"]
