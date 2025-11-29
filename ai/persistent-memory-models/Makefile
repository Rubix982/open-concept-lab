.PHONY: install up down shell test clean format lint lint-strict format-lint check pre-commit

install:
	pip install -e .

up:
	docker-compose up -d

down:
	docker-compose down

shell:
	docker-compose exec app bash

test:
	docker-compose exec app pytest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

pull-model:
	@echo "Pulling mistral model (via API)..."
	curl -X POST http://localhost:11434/api/pull -d '{"name": "mistral"}'

setup-host-llm:
	@echo "Installing Ollama..."
	brew list ollama || brew install ollama
	@echo "Starting Ollama service..."
	brew services start ollama || ollama serve &
	@echo "Waiting for Ollama to start..."
	sleep 5
	@echo "Pulling Mistral model..."
	ollama pull mistral
	@echo "Done! Ollama is running and Mistral is ready."

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/ -v -m unit

test-integration:
	pytest tests/ -v -m integration

test-benchmark:
	pytest tests/benchmarks/ -v --benchmark-only

test-coverage:
	pytest tests/ --cov=src/persistent_memory --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# Code Quality
format:
	@echo "🎨 Formatting code with ruff..."
	ruff format src/ tests/ *.py
	@echo "✅ Formatting complete!"

lint:
	@echo "🔍 Linting code with ruff..."
	ruff check src/ tests/ --fix
	@echo "🔍 Type checking with mypy..."
	mypy src/ --ignore-missing-imports --no-error-summary || true
	@echo "✅ Linting complete!"

lint-strict:
	@echo "🔍 Strict linting (no auto-fix)..."
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format-lint: format lint
	@echo "✅ Format and lint complete!"

check: format-lint test-unit
	@echo "✅ All checks passed!"

pre-commit:
	pre-commit run --all-files

# Monitoring
logs:
	docker-compose logs -f app

logs-api:
	docker-compose logs -f api

metrics:
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3000"
	@echo "API Metrics: http://localhost:8080/metrics"

# Maintenance
backup:
	@echo "Creating backup..."
	docker-compose exec postgres pg_dump -U temporal temporal > backup-$$(date +%Y%m%d).sql
	tar -czf backup-$$(date +%Y%m%d).tar.gz backup-$$(date +%Y%m%d).sql data/

rebuild-index:
	docker-compose exec app python -m persistent_memory.cli rebuild-index
