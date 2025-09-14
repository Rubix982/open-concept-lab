APP_NAME := go-server
DOCKER_COMPOSE := docker compose -f docker-compose.dev.yaml
SERVICE := pg17-local

.PHONY: all build run docker-build up down logs restart clean \
        exec exec-bash ps top start stop status rebuild

all: build

# Native Go build
build:
	go build -o $(APP_NAME) .

run:
	./$(APP_NAME)

# Compose build only
docker-build:
	$(DOCKER_COMPOSE) build

# Spin up services in background
up:
	$(DOCKER_COMPOSE) up -d

# Bring down all containers, networks
down:
	$(DOCKER_COMPOSE) down

# Tail logs
logs:
	$(DOCKER_COMPOSE) logs -f

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
rebuild:
	$(DOCKER_COMPOSE) down -v --remove-orphans
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d
