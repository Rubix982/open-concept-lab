package main

import (
	"database/sql"
	"fmt"
	"os"
	"sync"
	"time"

	_ "github.com/lib/pq"
)

var (
	globalDB *sql.DB
	initOnce sync.Once
	initErr  error
)

const (
	SCRIPTS_DIR      = "scripts"
	APP_ENV_FLAG     = "APP_ENV"
	EMBEDDER_SCRIPT  = "embedder.py"
	SCRAPE_CACHE_DIR = "scraped_cache"

	ENV_POSTGRES_USER     = "POSTGRES_USER"
	ENV_POSTGRES_PASSWORD = "POSTGRES_PASSWORD"
	ENV_POSTGRES_DB_NAME  = "POSTGRES_DB_NAME"
	ENV_POSTGRES_HOST     = "POSTGRES_HOST"
	ENV_POSTGRES_PORT     = "POSTGRES_PORT"
	ENV_QDRANT_HOST       = "QDRANT_HOST"
	ENV_QDRANT_PORT       = "QDRANT_PORT"

	LOGGING_SERVICE_ROUTE = "http://logging-service:5257"

	WORKER_COUNT = 20
	MAX_PAGES    = 40
)

func GetGlobalDB() (*sql.DB, error) {
	if globalDB == nil {
		if _, err := InitPostgres(); err != nil {
			return nil, err
		}
	}
	if globalDB == nil {
		return nil, fmt.Errorf("database not initialized")
	}
	return globalDB, nil
}

// InitPostgres ensures the DB is initialized only once, safely under concurrency.
func InitPostgres() (*sql.DB, error) {
	initOnce.Do(func() {
		postgresUser := os.Getenv(ENV_POSTGRES_USER)
		if len(postgresUser) == 0 {
			postgresUser = "postgres"
		}
		postgresPassword := os.Getenv(ENV_POSTGRES_PASSWORD)
		if len(postgresPassword) == 0 {
			postgresPassword = "postgres"
		}
		postgresDBName := os.Getenv(ENV_POSTGRES_DB_NAME)
		if len(postgresDBName) == 0 {
			postgresDBName = "rank-nsf-linker"
		}
		postgresHost := os.Getenv(ENV_POSTGRES_HOST)
		if len(postgresHost) == 0 {
			postgresHost = "postgres"
		}
		postgresPort := os.Getenv(ENV_POSTGRES_PORT)
		if len(postgresPort) == 0 {
			postgresPort = "5432"
		}

		dbURL := fmt.Sprintf("postgres://%s:%s@%s:%s/%s?sslmode=disable",
			postgresUser, postgresPassword, postgresHost, postgresPort, postgresDBName)

		db, err := sql.Open("postgres", dbURL)
		if err != nil {
			initErr = fmt.Errorf("failed to open DB: %w", err)
			return
		}

		// Configure the pool
		db.SetMaxOpenConns(30)                  // max total connections
		db.SetMaxIdleConns(15)                  // max idle
		db.SetConnMaxLifetime(30 * time.Minute) // recycle connections
		db.SetConnMaxIdleTime(10 * time.Minute) // optional, for cleanup

		// Verify connection
		if err := db.Ping(); err != nil {
			initErr = fmt.Errorf("failed to ping DB: %w", err)
			return
		}

		globalDB = db
	})

	return globalDB, initErr
}

func getScrapedDataFilePath() string {
	if appEnv := os.Getenv(APP_ENV_FLAG); len(appEnv) > 0 {
		return fmt.Sprintf("/app/data/%v", SCRAPE_CACHE_DIR)
	}

	return SCRAPE_CACHE_DIR
}
