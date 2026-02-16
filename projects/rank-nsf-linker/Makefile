APP_NAME := go-server
DOCKER_COMPOSE := docker compose -f docker-compose.dev.yaml
REGISTRY_CONTAINER := local-registry
REGISTRY_PORT := 5128
REGISTRY := host.docker.internal:$(REGISTRY_PORT)
SERVICE := scraper-worker

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
RESET  := \033[0m

# Project structure
SERVER_DIR := server
GO_MODULE  := github.com/Rubix982/open-concept-lab

# Helper: pull or cache image in registry if missing
define ensure_image
	@IMAGE=$(1); \
	if ! docker manifest inspect $(REGISTRY)/$$IMAGE >/dev/null 2>&1; then \
		echo "📥 Pulling $$IMAGE from internet..."; \
		docker pull $$IMAGE; \
		echo "📦 Tagging & pushing to local registry..."; \
		docker tag $$IMAGE $(REGISTRY)/$$IMAGE; \
		docker push $(REGISTRY)/$$IMAGE; \
	else \
		echo "✅ Image already cached locally: $(REGISTRY)/$$IMAGE"; \
	fi
endef

# Utility function to check container existence
define container_exists
	@docker ps -a --format '{{.Names}}' | grep -q "^$(1)$$"
endef

# Utility function to check running status
define container_running
	@docker ps --format '{{.Names}}' | grep -q "^$(1)$$"
endef

.PHONY: all build run docker-build up down logs restart clean exec exec-bash ps top start stop \
	status rebuild rm-all registry up-infra lint lint-fix semgrep lint-all install-tools

all: build

## build: Build Go binary natively
build:
	go build -o $(APP_NAME) .

## run: Run the built binary
run:
	./$(APP_NAME)

## push-images: Tag and push all Docker images to local registry
push-images:
	@echo "📤 Tagging and pushing images to local registry..."
	@docker tag rank-nsf-linker-go-server:latest $(REGISTRY)/go-server:latest
	@docker tag rank-nsf-linker-scraper-worker:latest $(REGISTRY)/scraper-worker:latest
	@docker tag rank-nsf-linker-web:latest $(REGISTRY)/web-ui:latest
	@docker tag rank-nsf-linker-logging-service:latest $(REGISTRY)/logging-service:latest
	@docker tag rank-nsf-linker-embedder:latest $(REGISTRY)/embedder:latest
	@docker push $(REGISTRY)/go-server:latest
	@docker push ${REGISTRY}/scraper-worker:latest
	@docker push $(REGISTRY)/web-ui:latest
	@docker push $(REGISTRY)/logging-service:latest
	@docker push $(REGISTRY)/embedder:latest
	@echo "✅ Images pushed to $(REGISTRY)"

## registry: Start or verify local Docker registry
registry:
	@if docker ps --format '{{.Names}}' | grep -q $(REGISTRY_CONTAINER); then \
		echo "✅ Local registry already running on :$(REGISTRY_PORT)"; \
	else \
		echo "🚀 Starting local Docker registry on :$(REGISTRY_PORT)..."; \
		docker run -d --restart=always \
			-p $(REGISTRY_PORT):5000 \
			--name $(REGISTRY_CONTAINER) registry:2; \
	fi

## up-infra: Start infrastructure services (Postgres, Elasticsearch, Qdrant)
up-infra:
	@if ! docker ps --format '{{.Names}}' | grep -q "pg17-local"; then \
		echo "📦 Starting PostgreSQL, Elasticsearch, and Qdrant..."; \
		$(DOCKER_COMPOSE) up -d postgres elasticsearch qdrant; \
	else \
		echo "✅ Infrastructure already running."; \
	fi

# We cannot provide a specific tag to postgres as CGR only provides 'latest' and 'latest-dev'
# Hence, we always pull the image with the latest tag by default
## infra-images: Pull and cache infrastructure images in local registry
infra-images:
	$(call ensure_image,cgr.dev/chainguard/postgres)
	$(call ensure_image,docker.elastic.co/elasticsearch/elasticsearch:8.13.0)
	$(call ensure_image,qdrant/qdrant:v1.3.0)
	$(call ensure_image,prom/prometheus:latest)
	$(call ensure_image,grafana/grafana:12.3.0-18733571275-ubuntu)
	$(call ensure_image,prometheuscommunity/postgres-exporter:v0.18.1)

# App lifecycle
## docker-build: Build all Docker images
docker-build:
	$(DOCKER_COMPOSE) build --progress=plain $(if $(NO_CACHE),--no-cache,)
	docker image prune -f

# Spin up services in background
## up: Start all services (registry + infra + app)
up: registry up-infra
	@if ! docker ps --format '{{.Names}}' | grep -q "$(SERVICE)"; then \
		echo "🚀 Launching main services (web, go-server, scraper-worker, logging-service, embedder)..."; \
		$(DOCKER_COMPOSE) up -d go-server scraper-worker web logging-service embedder; \
	else \
		echo "✅ Main services already running."; \
	fi

# Bring down all containers, networks
## down: Stop all containers and remove networks
down:
	$(DOCKER_COMPOSE) down

# Tail logs
## logs: Tail logs for all services
logs:
	$(DOCKER_COMPOSE) logs -f

# Tail logs for a specific serviceà
# Usage:
# 	make logs-go-server   # logs for go-server
#	make logs-scraper-worker # logs for scraper-worker
# 	make logs-postgres    # logs for postgres
# 	make logs-web         # logs for web
# 	make logs-logging-service # logs for logging-service
# 	make logs-embedder   # logs for embedder
## logs-<service>: Tail logs for specific service (e.g., make logs-go-server)
logs-%:
	$(DOCKER_COMPOSE) logs -f $*

# Restart cleanly
## restart: Restart all services cleanly
restart:
	$(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) up -d

# Exec into go-server container
## exec: Execute shell in scraper-worker container
exec:
	$(DOCKER_COMPOSE) exec $(SERVICE) sh

# Run bash if image has bash
## exec-bash: Execute bash in scraper-worker container
exec-bash:
	$(DOCKER_COMPOSE) exec $(SERVICE) bash

# Show container list
## ps: Show all container statuses
ps:
	$(DOCKER_COMPOSE) ps

# Show live container processes
## top: Show live container processes
top:
	$(DOCKER_COMPOSE) top

# Start containers
## start: Start stopped containers
start:
	$(DOCKER_COMPOSE) start

# Stop containers
## stop: Stop running containers
stop:
	$(DOCKER_COMPOSE) stop

# Check health & status
## status: Show running services only
status:
	$(DOCKER_COMPOSE) ps --services --filter "status=running"

# Full rebuild with clean
# Usage: make rebuild
#
# For a no cache build
# make rebuild NO_CACHE=true
## rebuild: Full rebuild - clean, pull images, build, start, tail logs
rebuild:
	export BUILDKIT_PROGRESS=plain
	export DOCKER_BUILDKIT=1
	make rm-all
	make registry
	make infra-images
	make docker-build
	make push-images
	make up
	@if pgrep -f "docker compose.*logs -f go-server" >/dev/null; then \
		echo "🛑 Killing existing go-server log daemon..."; \
		pkill -f "docker compose.*logs -f go-server"; \
	fi
	@echo "🚀 Starting go-server log daemon in background..."
	$(DOCKER_COMPOSE) logs -f go-server > go-server.log 2>&1 &
	$(DOCKER_COMPOSE) logs -f scraper-worker > scraper-worker.log 2>&1 &
	make logs-go-server

# Remove all
## rm-all: Remove all containers, volumes, and networks
rm-all:
	$(DOCKER_COMPOSE) down -v --remove-orphans

## rm-all-hard: Remove all containers, volumes, networks, and images
rm-all-hard:
	$(DOCKER_COMPOSE) down --rmi all -v --remove-orphans

# Usage: make build-one SERVICE=go-server
## build-one: Build single service (usage: make build-one SERVICE=go-server)
build-one:
	@echo "🔨 Building image for service: $(SERVICE)"
	$(DOCKER_COMPOSE) build $(if $(NO_CACHE),--no-cache,) $(SERVICE)
	@echo "✅ Image for $(SERVICE) built successfully."

# Usage: make up-one SERVICE=go-server
## up-one: Start single service (usage: make up-one SERVICE=go-server)
up-one:
	@echo "🚀 Starting container for service: $(SERVICE)"
	$(DOCKER_COMPOSE) up -d $(SERVICE)
	@echo "✅ Service $(SERVICE) is up."

# Usage: make rebuild-one SERVICE=go-server
## rebuild-one: Rebuild and restart single service (usage: make rebuild-one SERVICE=go-server)
rebuild-one:
	@echo "♻️ Rebuilding and restarting $(SERVICE)..."
	export BUILDKIT_PROGRESS=plain
	$(DOCKER_COMPOSE) build --progress=plain $(if $(NO_CACHE),--no-cache,) $(SERVICE)
	$(DOCKER_COMPOSE) up -d $(SERVICE)
	@echo "✅ $(SERVICE) rebuilt and restarted successfully."

# Bring down specific service(s)
# Example usage: make down-service SERVICE=scraper-worker
# Or multiple: make down-service SERVICE="scraper-worker db"
## down-service: Stop and remove specific service(s) (usage: make down-service SERVICE=go-server)
down-service:
	$(DOCKER_COMPOSE) stop $(SERVICE)
	$(DOCKER_COMPOSE) rm -f $(SERVICE)


# ===================================================================
# LINTING COMMANDS
# ===================================================================

## lint: Run golangci-lint
lint:
	@echo "$(YELLOW)Running golangci-lint in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && golangci-lint run ./... || (echo "$(RED)✗ Linting failed$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Linting passed$(RESET)"

## lint-fix: Run golangci-lint with auto-fix
lint-fix:
	@echo "$(YELLOW)Running golangci-lint with auto-fix in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && golangci-lint run --fix ./...
	@echo "$(GREEN)✓ Auto-fixes applied$(RESET)"

## semgrep: Run semgrep security checks
semgrep:
	@echo "$(YELLOW)Running semgrep in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && semgrep --config ../.semgrep.yml --config "p/golang" --error --quiet . || \
		(semgrep --config ../.semgrep.yml --config "p/golang" --json --output=semgrep-results.json . && \
		echo "$(RED)✗ Semgrep found issues. Results saved to semgrep-results.json$(RESET)" && exit 1)
	@echo "$(GREEN)✓ Semgrep passed$(RESET)"

## semgrep-verbose: Run semgrep with detailed output
semgrep-verbose:
	@echo "$(YELLOW)Running semgrep (verbose) in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && semgrep --config .semgrep.yml --config "p/golang" .

## lint-all: Run all linters (golangci-lint + semgrep)
lint-all: lint semgrep
	@echo "$(GREEN)✓ All linting checks passed$(RESET)"

## lint-ci: Run linters for CI with JUnit output
lint-ci:
	@echo "$(YELLOW)Running linters for CI in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && golangci-lint run --out-format=github-actions ./...
	@cd $(SERVER_DIR) && semgrep --config .semgrep.yml --config "p/golang" --json --output=semgrep-results.json .

# ===================================================================
# TOOL INSTALLATION
# ===================================================================

## install-tools: Install linting tools
install-tools: install-golangci install-semgrep install-goimports
	@echo "$(GREEN)✓ All tools installed$(RESET)"

## install-golangci: Install golangci-lint
install-golangci:
	@echo "$(YELLOW)Installing golangci-lint...$(RESET)"
	@which golangci-lint > /dev/null || \
		(curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(shell go env GOPATH)/bin v1.55.2)
	@golangci-lint --version
	@echo "$(GREEN)✓ golangci-lint installed$(RESET)"

## install-semgrep: Install semgrep
install-semgrep:
	@echo "$(YELLOW)Installing semgrep...$(RESET)"
	@which semgrep > /dev/null || \
		(python3 -m pip install semgrep)
	@semgrep --version
	@echo "$(GREEN)✓ semgrep installed$(RESET)"

## install-goimports: Install goimports
install-goimports:
	@echo "$(YELLOW)Installing goimports...$(RESET)"
	@which goimports > /dev/null || \
		go install golang.org/x/tools/cmd/goimports@latest
	@goimports -version || echo "goimports installed at $(shell go env GOPATH)/bin/goimports"
	@echo "$(GREEN)✓ goimports installed$(RESET)"

# ===================================================================
# QUICK FIX COMMANDS
# ===================================================================

## fmt: Format code
fmt:
	@echo "$(YELLOW)Formatting code in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && gofmt -s -w .
	@cd $(SERVER_DIR) && goimports -w -local $(GO_MODULE) .
	@echo "$(GREEN)✓ Code formatted$(RESET)"

## vet: Run go vet
vet:
	@echo "$(YELLOW)Running go vet in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && go vet ./...
	@echo "$(GREEN)✓ go vet passed$(RESET)"

## tidy: Run go mod tidy
tidy:
	@echo "$(YELLOW)Tidying modules in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && go mod tidy
	@echo "$(GREEN)✓ Modules tidied$(RESET)"

# ===================================================================
# PRE-COMMIT HOOK
# ===================================================================

## pre-commit: Run checks before committing (fast subset)
pre-commit: fmt vet lint
	@echo "$(GREEN)✓ Pre-commit checks passed$(RESET)"

## pre-push: Run full checks before pushing
pre-push: tidy lint-all test
	@echo "$(GREEN)✓ Pre-push checks passed$(RESET)"

## lint-report: Generate HTML report
lint-report:
	@echo "$(YELLOW)Generating lint report in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && golangci-lint run --out-format=html > lint-report.html
	@echo "$(GREEN)✓ Report generated: $(SERVER_DIR)/lint-report.html$(RESET)"

## complexity: Show complexity metrics
complexity:
	@echo "$(YELLOW)Analyzing complexity in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && golangci-lint run --enable=gocyclo,gocognit --out-format=tab ./...

## security: Run security-focused checks
security: semgrep
	@echo "$(YELLOW)Running gosec in $(SERVER_DIR)...$(RESET)"
	@cd $(SERVER_DIR) && golangci-lint run --disable-all --enable=gosec ./...
	@echo "$(GREEN)✓ Security checks complete$(RESET)"

## clean: Clean build artifacts
clean:
	@echo "$(YELLOW)Cleaning...$(RESET)"
	@cd $(SERVER_DIR) && rm -f lint-report.html semgrep-results.json coverage.out
	@cd $(SERVER_DIR) && go clean -cache -testcache
	@echo "$(YELLOW)Remove local build binary$(RESET)"
	@rm -f $(APP_NAME)
	@echo "$(GREEN)✓ Cleaned$(RESET)"

## help: Show this help
help:
	@echo "$(GREEN)Available targets:$(RESET)"
	@sed -n 's/^## //p' Makefile | column -t -s ':'

## hooks: Install git pre-commit hooks
hooks:
	@echo "$(GREEN)Moving hooks to git directory:$(RESET)"
	@cp hooks/pre-commit.sh .git/hooks/pre-commit

## deps: Download and verify dependencies
deps:
	@cd $(SERVER_DIR) && go mod download
	@cd $(SERVER_DIR) && go mod verify

## outdated: Check for outdated dependencies
outdated:
	@cd $(SERVER_DIR) && go list -u -m all

.DEFAULT_GOAL := help
