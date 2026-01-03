package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os"
	"time"
)

func waitForElasticsearch() {
	client := &http.Client{}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	logger.Info("Waiting for ElasticSearch to be ready...")

	for {
		attempts += 1
		resp, err := client.Get(fmt.Sprintf("%v/_cluster/health", ELASTICSEARCH_SERVICE_ROUTE))
		if err == nil && resp.StatusCode == 200 {
			logger.Info("✅ Elasticsearch is ready")
			return
		}

		logger.Infof("Waiting for Elasticsearch to be ready for attempt %d... retrying in %s\n", attempts, delay)
		time.Sleep(delay)

		// Exponential backoff: double the delay each time, up to maxDelay
		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func waitForPostgres() {
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

	logger.Info("Waiting for Postgres to be ready...")

	for {
		attempts++

		db, err := sql.Open("postgres", dsn)
		if err == nil {
			err = db.Ping()
		}

		if err == nil {
			logger.Info("✅ Postgres is ready")
			db.Close()
			return
		}

		logger.Infof("Attempt %d: Postgres not ready yet, retrying in %s...", attempts, delay)
		time.Sleep(delay)

		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func waitForLoggingService() {
	client := &http.Client{}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	logger.Info("Waiting for Logging Service to be ready...")

	for {
		attempts += 1
		resp, err := client.Get(fmt.Sprintf("%v/health", LOGGING_SERVICE_ROUTE))
		if err == nil && resp.StatusCode == 200 {
			logger.Info("✅ Logging Service is ready")
			return
		}

		logger.Infof("Waiting for Logging Service to be ready for attempt %d... retrying in %s...", attempts, delay)
		time.Sleep(delay)

		// Exponential backoff: double the delay each time, up to maxDelay
		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func waitForServices() {
	waitForElasticsearch()
	waitForPostgres()
	waitForLoggingService()
}
