package main

import (
	"context"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	colly "github.com/gocolly/colly/v2"
	"github.com/joho/godotenv"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func printBanner(ctx *colly.Context) {
	banner := `

██████╗  █████╗ ███╗   ██╗██╗  ██╗    ██╗     ██╗███╗   ██╗██╗  ██╗███████╗██████╗ 
██╔══██╗██╔══██╗████╗  ██║██║ ██╔╝    ██║     ██║████╗  ██║██║ ██╔╝██╔════╝██╔══██╗
██████╔╝███████║██╔██╗ ██║█████╔╝     ██║     ██║██╔██╗ ██║█████╔╝ █████╗  ██████╔╝
██╔══██╗██╔══██║██║╚██╗██║██╔═██╗     ██║     ██║██║╚██╗██║██╔═██╗ ██╔══╝  ██╔══██╗
██║  ██║██║  ██║██║ ╚████║██║  ██╗    ███████╗██║██║ ╚████║██║  ██╗███████╗██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                   
`
	logger.Infof(ctx, "%s", banner)
}

func startMetricsServer() {
	http.Handle("/metrics", promhttp.Handler())
	go http.ListenAndServe(":2112", nil)
}

func main() {
	initLogger()
	mainCtx := colly.NewContext()

	if err := godotenv.Load(); err != nil {
		logger.Warnf(mainCtx, "⚠️  No .env file found, trying .env.local: %v", err)
		if err := godotenv.Load(".env.local"); err != nil {
			logger.Warnf(mainCtx, "⚠️  No .env.local file found either, continuing with system environment variables: %v", err)
		}
	}

	waitForServices(mainCtx)
	printBanner(mainCtx)
	startMetricsServer()

	// Setup your HTTP server
	srv := &http.Server{Addr: ":8080", Handler: GetRouter()}

	// Channel to listen for OS-level signals
	stop := make(chan os.Signal, 1)
	signal.Notify(stop,
		os.Interrupt,    // CTRL+C
		syscall.SIGTERM, // docker stop, kubectl stop
		syscall.SIGQUIT, // kill -3, etc.
	)

	go func() {
		logger.Infof(mainCtx, "🚀 Server is running on :8080")
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatalf(mainCtx, "❌ Server error: %v", err)
		}
	}()

	// We cannot couple the migrations with the populate function because state change for the pipelines
	// are irrespective of whether we are populating the DB or not.
	// We need to run migrations always when the server starts.
	if runMigrationsErr := runMigrations(mainCtx); runMigrationsErr != nil {
		logger.Errorf(mainCtx, "failed to execute migrations: %v", runMigrationsErr)
		return
	}

	// If we actually go to populate the DB, we mark the pipeline as in progress anyways, so
	// we can mark it as completed here.
	markPipelineAsCompleted(mainCtx, string(PIPELINE_POPULATE_POSTGRES), string(PIPELINE_STATUS_COMPLETED))

	if skipMigrations := os.Getenv(POPULATE_DB_FLAG); len(skipMigrations) == 0 {
		executeWorkflows(mainCtx)
	}

	// Block and wait for shutdown signal
	sig := <-stop
	logger.Warnf(mainCtx, "⚠️  Received signal: %s — starting graceful shutdown...", sig)

	// Graceful shutdown: stop accepting new connections
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	// Shutdown HTTP server
	if err := srv.Shutdown(ctx); err != nil {
		logger.Errorf(mainCtx, "❌ Server shutdown error: %v", err)
	} else {
		logger.Infof(mainCtx, "✅ HTTP server stopped gracefully.")
	}

	CloseDB(mainCtx)

	logger.Infof(mainCtx, "👋 Shutdown complete. Exiting now.")
}
