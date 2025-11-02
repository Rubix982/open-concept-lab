package main

import (
	"net/http"
	"os"
	"time"

	"github.com/joho/godotenv"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func printBanner() {
	banner := `

██████╗  █████╗ ███╗   ██╗██╗  ██╗    ██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ 
██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝    ██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗
██████╔╝███████║██╔██╗ ██║█████╔╝     ██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██████╔╝
██╔══██╗██╔══██║██║╚██╗██║██╔═██╗     ██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║██║  ██║██║ ╚████║██║  ██╗    ███████╗██║██║ ╚████║██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                   
`
	logger.Infof("%s", banner)
}

func startMetricsServer() {
	http.Handle("/metrics", promhttp.Handler())
	go http.ListenAndServe(":2112", nil)
}

func main() {
	if err := godotenv.Load(); err != nil {
		logger.Warnf("⚠️  No .env file found, trying .env.local: %v", err)
		if err := godotenv.Load(".env.local"); err != nil {
			logger.Warnf("⚠️  No .env.local file found either, continuing with system environment variables: %v", err)
		}
	}

	waitForServices()
	printBanner()
	startMetricsServer()
	logger.Info("Server running on 8080")
	go http.ListenAndServe(":8080", GetRouter())

	// We cannot couple the migrations with the populate function because state change for the pipelines
	// are irrespective of whether we are populating the DB or not.
	// We need to run migrations always when the server starts.
	if runMigrationsErr := runMigrations(); runMigrationsErr != nil {
		logger.Errorf("failed to execute migrations: %v", runMigrationsErr)
		return
	}

	// If we actually go to populate the DB, we mark the pipeline as in progress anyways, so
	// we can mark it as completed here.
	markPipelineAsCompleted(string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_COMPLETED))

	if skipMigrations := os.Getenv(POPULATE_DB_FLAG); len(skipMigrations) == 0 {
		populatePostgres()
	}

	// If the server shuts down, it is restarted and so we see "main" running again from the logs. We need to
	for {
		// Sleep to avoid spinning and consuming 100% CPU
		time.Sleep(1 * time.Second)
	}
}
