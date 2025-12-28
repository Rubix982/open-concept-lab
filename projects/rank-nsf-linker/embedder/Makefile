.PHONY: help install format lint type-check test clean docker-build docker-run all

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# Configuration
PYTHON := python3
PIP := pip3
PROJECT_NAME := embedder
SRC_DIR := .
DOCKER_IMAGE := $(PROJECT_NAME):latest

help: ## Show this help message
	@echo "$(GREEN)Available targets:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install development dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-dev.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	black $(SRC_DIR) --line-length 100 --exclude venv/
	isort $(SRC_DIR) --profile black --line-length 100 --skip venv
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check if code is formatted (CI)
	@echo "$(GREEN)Checking code formatting...$(NC)"
	black $(SRC_DIR) --check --line-length 100 --exclude venv/
	isort $(SRC_DIR) --check --profile black --line-length 100 --skip venv
	@echo "$(GREEN)✓ Code formatting verified$(NC)"

lint: ## Run flake8 linter
	@echo "$(GREEN)Running flake8...$(NC)"
	flake8 $(SRC_DIR) \
		--max-line-length=100 \
		--exclude=venv,.git,__pycache__,.pytest_cache \
		--extend-ignore=E203,W503 \
		--max-complexity=10
	@echo "$(GREEN)✓ Linting passed$(NC)"

lint-pylint: ## Run pylint (stricter)
	@echo "$(GREEN)Running pylint...$(NC)"
	pylint $(SRC_DIR) \
		--max-line-length=100 \
		--disable=C0111,C0103,R0913 \
		--ignore=venv
	@echo "$(GREEN)✓ Pylint passed$(NC)"

type-check: ## Run mypy type checker
	@echo "$(GREEN)Running mypy type checker...$(NC)"
	mypy $(SRC_DIR) \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--exclude venv
	@echo "$(GREEN)✓ Type checking passed$(NC)"

security: ## Run bandit security checker
	@echo "$(GREEN)Running security checks...$(NC)"
	bandit -r $(SRC_DIR) \
		--exclude ./venv \
		--skip B101,B601
	@echo "$(GREEN)✓ Security checks passed$(NC)"

complexity: ## Check code complexity with radon
	@echo "$(GREEN)Analyzing code complexity...$(NC)"
	radon cc $(SRC_DIR) -a -nb --exclude venv
	radon mi $(SRC_DIR) --exclude venv
	@echo "$(GREEN)✓ Complexity analysis complete$(NC)"

test: ## Run tests with pytest
	@echo "$(GREEN)Running tests...$(NC)"
	pytest tests/ -v --cov=$(SRC_DIR) --cov-report=term-missing
	@echo "$(GREEN)✓ Tests passed$(NC)"

test-fast: ## Run tests without coverage
	@echo "$(GREEN)Running fast tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)✓ Tests passed$(NC)"

check: format-check lint type-check ## Run all checks (for CI)
	@echo "$(GREEN)✓ All checks passed$(NC)"

fix: format lint ## Auto-fix what can be fixed
	@echo "$(GREEN)✓ Auto-fixes applied$(NC)"

clean: ## Clean up generated files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/
	@echo "$(GREEN)✓ Cleaned$(NC)"

docker-build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t $(DOCKER_IMAGE) .
	@echo "$(GREEN)✓ Docker image built: $(DOCKER_IMAGE)$(NC)"

docker-run: ## Run Docker container
	@echo "$(GREEN)Starting Docker container...$(NC)"
	docker run --rm -p 8000:8000 $(DOCKER_IMAGE)

docker-test: ## Test Docker image
	@echo "$(GREEN)Testing Docker image...$(NC)"
	docker run --rm $(DOCKER_IMAGE) python -c "from sentence_transformers import SentenceTransformer; print('✓ Model loads')"
	@echo "$(GREEN)✓ Docker image works$(NC)"

pre-commit: format lint type-check test ## Run before committing
	@echo "$(GREEN)✓ Pre-commit checks passed - safe to commit!$(NC)"

ci: check test ## Run CI pipeline
	@echo "$(GREEN)✓ CI pipeline passed$(NC)"

all: clean install check test docker-build ## Run everything
	@echo "$(GREEN)✓ Complete build successful$(NC)"

deps-upgrade: ## Upgrade dependencies
	@echo "$(GREEN)Upgrading dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) list --outdated
	@echo "$(YELLOW)Review outdated packages above$(NC)"

deps-tree: ## Show dependency tree
	@echo "$(GREEN)Dependency tree:$(NC)"
	pipdeptree

profile: ## Profile the application
	@echo "$(GREEN)Profiling application...$(NC)"
	python -m cProfile -o profile.stats app.py
	python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(20)"

loc: ## Count lines of code
	@echo "$(GREEN)Lines of code:$(NC)"
	@find . -name '*.py' -not -path './venv/*' | xargs wc -l | sort -n

.DEFAULT_GOAL := help
