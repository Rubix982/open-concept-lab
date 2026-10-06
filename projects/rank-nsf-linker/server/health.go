package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os"
	"time"

	colly "github.com/gocolly/colly/v2"
)

// waitForElasticsearch waits up to esWaitLimit for Elasticsearch, then carries on: the explorer
// doesn't need it, and waiting forever left the server stuck at startup (site down) whenever
// Elasticsearch was stopped.
const esWaitLimit = 2 * time.Minute

func waitForElasticsearch(ctx *colly.Context) {
	client := &http.Client{Timeout: 10 * time.Second}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	deadline := time.Now().Add(esWaitLimit)
	logger.Info(ctx, "Waiting for ElasticSearch to be ready...")

	for {
		attempts += 1
		resp, err := client.Get(fmt.Sprintf("%v/_cluster/health", ELASTICSEARCH_SERVICE_ROUTE))
		if err == nil {
			resp.Body.Close()
		}
		if err == nil && resp.StatusCode == 200 {
			logger.Info(ctx, "✅ Elasticsearch is ready")
			return
		}
		if time.Now().After(deadline) {
			logger.Warnf(ctx, "⚠️ Elasticsearch not reachable after %s; starting without it", esWaitLimit)
			return
		}

		logger.Infof(ctx, "Waiting for Elasticsearch to be ready for attempt %d... retrying in %s\n", attempts, delay)
		time.Sleep(delay)

		// Exponential backoff: double the delay each time, up to maxDelay
		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func waitForPostgres(ctx *colly.Context) {
	postgresPort := os.Getenv("POSTGRES_PORT")
	if postgresPort == "" {
		postgresPort = "5432"
	}

	postgresUser := os.Getenv("POSTGRES_USER")
	if postgresUser == "" {
		postgresUser = "postgres"
	}

	postgresPassword := os.Getenv("POSTGRES_PASSWORD")
	if postgresPassword == "" {
		postgresPassword = "postgres"
	}

	postgresDbName := os.Getenv("POSTGRES_DB")
	if postgresDbName == "" {
		postgresDbName = "rank-nsf-linker"
	}

	dsn := fmt.Sprintf("postgres://%s:%s@postgres:%s/%s?sslmode=disable", postgresUser, postgresPassword, postgresPort, postgresDbName)
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0

	logger.Infof(ctx, "Waiting for Postgres to be ready...")

	for {
		attempts++

		db, err := sql.Open("postgres", dsn)
		if err == nil {
			err = db.Ping()
		}

		if err == nil {
			logger.Infof(ctx, "✅ Postgres is ready")
			db.Close()
			return
		}

		logger.Infof(ctx, "Attempt %d: Postgres not ready yet, retrying in %s...", attempts, delay)
		time.Sleep(delay)

		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func waitForLoggingService(ctx *colly.Context) {
	client := &http.Client{Timeout: 10 * time.Second}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	deadline := time.Now().Add(esWaitLimit) // optional too: logs are dropped while it is away
	logger.Infof(ctx, "Waiting for Logging Service to be ready...")

	for {
		attempts += 1
		resp, err := client.Get(fmt.Sprintf("%v/health", LOGGING_SERVICE_ROUTE))
		if err == nil {
			resp.Body.Close()
		}
		if err == nil && resp.StatusCode == 200 {
			logger.Infof(ctx, "✅ Logging Service is ready")
			return
		}
		if time.Now().After(deadline) {
			logger.Warnf(ctx, "⚠️ Logging Service not reachable after %s; starting without it", esWaitLimit)
			return
		}

		logger.Infof(ctx, "Waiting for Logging Service to be ready for attempt %d... retrying in %s...", attempts, delay)
		time.Sleep(delay)

		// Exponential backoff: double the delay each time, up to maxDelay
		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

// serveOnly (SERVE_ONLY=1): the minimal deployment (docker-compose.minimal.yaml). The server only
// serves the database it was given (a golden dataset): it waits for Postgres alone, and never runs
// the pipeline or its scheduler, which would fail without the fetcher and the data/ downloads.
func serveOnly() bool { return os.Getenv("SERVE_ONLY") == "1" }

func waitForServices(ctx *colly.Context) {
	if serveOnly() {
		waitForPostgres(ctx)
		return
	}
	waitForElasticsearch(ctx)
	waitForPostgres(ctx)
	waitForLoggingService(ctx)
}
