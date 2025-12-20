APP_NAME := go-server
DOCKER_COMPOSE := docker compose -f docker-compose.dev.yaml
REGISTRY_CONTAINER := local-registry
REGISTRY_PORT := 5128
REGISTRY := host.docker.internal:$(REGISTRY_PORT)
SERVICE := go-server

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

.PHONY: all build run docker-build up down logs restart clean \
	exec exec-bash ps top start stop status rebuild rm-all registry up-infra

all: build

# Native Go build
build:
	go build -o $(APP_NAME) .

run:
	./$(APP_NAME)

# Push images to local registry after build
push-images:
	@echo "📤 Tagging and pushing images to local registry..."
	@docker tag rank-nsf-linker-go-server:latest $(REGISTRY)/go-server:latest
	@docker tag rank-nsf-linker-scraper-worker:latest $(REGISTRY)/scraper-worker:latest
	@docker tag rank-nsf-linker-web:latest $(REGISTRY)/web-ui:latest
	@docker tag rank-nsf-linker-logging-service:latest $(REGISTRY)/logging-service:latest
	@docker push $(REGISTRY)/go-server:latest
	@docker push ${REGISTRY}/scraper-worker:latest
	@docker push $(REGISTRY)/web-ui:latest
	@docker push $(REGISTRY)/logging-service:latest
	@echo "✅ Images pushed to $(REGISTRY)"

# Registry Setup
registry:
	@if docker ps --format '{{.Names}}' | grep -q $(REGISTRY_CONTAINER); then \
		echo "✅ Local registry already running on :$(REGISTRY_PORT)"; \
	else \
		echo "🚀 Starting local Docker registry on :$(REGISTRY_PORT)..."; \
		docker run -d --restart=always \
			-p $(REGISTRY_PORT):5000 \
			--name $(REGISTRY_CONTAINER) registry:2; \
	fi

# Infrastructure setup (Postgres, ES, Qdrant)
up-infra:
	@if ! docker ps --format '{{.Names}}' | grep -q "pg17-local"; then \
		echo "📦 Starting PostgreSQL, Elasticsearch, and Qdrant..."; \
		$(DOCKER_COMPOSE) up -d postgres elasticsearch qdrant; \
	else \
		echo "✅ Infrastructure already running."; \
	fi

# We cannot provide a specific tag to postgres as CGR only provides 'latest' and 'latest-dev'
# Hence, we always pull the image with the latest tag by default
infra-images:
	$(call ensure_image,cgr.dev/chainguard/postgres)
	$(call ensure_image,docker.elastic.co/elasticsearch/elasticsearch:8.13.0)
	$(call ensure_image,qdrant/qdrant:v1.3.0)
	$(call ensure_image,prom/prometheus:latest)
	$(call ensure_image,grafana/grafana:12.3.0-18733571275-ubuntu)
	$(call ensure_image,prometheuscommunity/postgres-exporter:v0.18.1)

# App lifecycle
docker-build:
	$(DOCKER_COMPOSE) build --progress=plain $(if $(NO_CACHE),--no-cache,)
	docker image prune -f

# Spin up services in background
up: registry up-infra
	@if ! docker ps --format '{{.Names}}' | grep -q "$(SERVICE)"; then \
		echo "🚀 Launching main services (web, go-server, scraper-worker, logging-service)..."; \
		$(DOCKER_COMPOSE) up -d go-server scraper-worker web logging-service; \
	else \
		echo "✅ Main services already running."; \
	fi

# Bring down all containers, networks
down:
	$(DOCKER_COMPOSE) down

# Tail logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Tail logs for a specific serviceà
# Usage:
# 	make logs-go-server   # logs for go-server
#	make logs-scraper-worker # logs for scraper-worker
# 	make logs-postgres    # logs for postgres
# 	make logs-web         # logs for web
# 	make logs-logging-service # logs for logging-service
logs-%:
	$(DOCKER_COMPOSE) logs -f $*

# Restart cleanly
restart:
	$(DOCKER_COMPOSE) down && $(DOCKER_COMPOSE) up -d

# Remove local build binary
clean:
	rm -f $(APP_NAME)

# === 🔍 Docker utility commands ===

# Exec into go-server container
exec:
	$(DOCKER_COMPOSE) exec $(SERVICE) sh

# Run bash if image has bash
exec-bash:
	$(DOCKER_COMPOSE) exec $(SERVICE) bash

# Show container list
ps:
	$(DOCKER_COMPOSE) ps

# Show live container processes
top:
	$(DOCKER_COMPOSE) top

# Start containers
start:
	$(DOCKER_COMPOSE) start

# Stop containers
stop:
	$(DOCKER_COMPOSE) stop

# Check health & status
status:
	$(DOCKER_COMPOSE) ps --services --filter "status=running"

# Full rebuild with clean
# Usage: make rebuild
#
# For a no cache build
# make rebuild NO_CACHE=true
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
rm-all:
	$(DOCKER_COMPOSE) down -v --remove-orphans

rm-all-hard:
	$(DOCKER_COMPOSE) down --rmi all -v --remove-orphans

# Usage: make build-one SERVICE=go-server
build-one:
	@echo "🔨 Building image for service: $(SERVICE)"
	$(DOCKER_COMPOSE) build $(if $(NO_CACHE),--no-cache,) $(SERVICE)
	@echo "✅ Image for $(SERVICE) built successfully."

# Usage: make up-one SERVICE=go-server
up-one:
	@echo "🚀 Starting container for service: $(SERVICE)"
	$(DOCKER_COMPOSE) up -d $(SERVICE)
	@echo "✅ Service $(SERVICE) is up."

# Usage: make rebuild-one SERVICE=go-server
rebuild-one:
	@echo "♻️ Rebuilding and restarting $(SERVICE)..."
	export BUILDKIT_PROGRESS=plain
	$(DOCKER_COMPOSE) build --progress=plain $(if $(NO_CACHE),--no-cache,) $(SERVICE)
	$(DOCKER_COMPOSE) up -d $(SERVICE)
	@echo "✅ $(SERVICE) rebuilt and restarted successfully."
