FROM python:3.12-slim

WORKDIR /app
COPY . .

# Someone once needed to compile a package, so the tools stayed.
RUN apt-get update && apt-get install -y build-essential
RUN pip install -r requirements.txt

EXPOSE 8011
CMD ["python", "app.py"]
