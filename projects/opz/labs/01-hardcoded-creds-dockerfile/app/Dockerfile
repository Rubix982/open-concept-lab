FROM python:3.12-slim
WORKDIR /app

# Copy only what the app needs. The token is supplied at run time:
#   docker run --env-file .env lab01
COPY app.py .

EXPOSE 8080
CMD ["python", "app.py"]
