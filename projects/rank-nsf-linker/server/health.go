package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"time"
)

func waitForElasticsearch() {
	client := &http.Client{}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	fmt.Println("Waiting for ElasticSearch to be ready...")

	for {
		attempts += 1
		resp, err := client.Get("http://elasticsearch:9200/_cluster/health")
		if err == nil && resp.StatusCode == 200 {
			fmt.Println("✅ Elasticsearch is ready")
			return
		}

		fmt.Printf("Waiting for Elasticsearch to be ready for attempt %d... retrying in %s\n", attempts, delay)
		time.Sleep(delay)

		// Exponential backoff: double the delay each time, up to maxDelay
		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func waitForPostgres() {
	dsn := "postgres://postgres:postgres@postgres:5432/mydb?sslmode=disable"
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0

	fmt.Println("Waiting for Postgres to be ready...")

	for {
		attempts++

		db, err := sql.Open("postgres", dsn)
		if err == nil {
			err = db.Ping()
		}

		if err == nil {
			fmt.Println("✅ Postgres is ready")
			db.Close()
			return
		}

		fmt.Printf("Attempt %d: Postgres not ready yet, retrying in %s...\n", attempts, delay)
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
	fmt.Println("Waiting for Logging Service to be ready...")

	for {
		attempts += 1
		resp, err := client.Get("http://logging-service:5257/health")
		if err == nil && resp.StatusCode == 200 {
			fmt.Println("✅ Logging Service is ready")
			return
		}

		fmt.Printf("Waiting for Logging Service to be ready for attempt %d... retrying in %s\n", attempts, delay)
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
