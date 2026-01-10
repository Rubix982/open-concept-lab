package main

import (
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gocolly/colly/v2"
	"github.com/joho/godotenv"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func startResearchPipeline(ctx *colly.Context) (*ResearchService, error) {
	logger.Infof(ctx, "🚀 Starting Go-based Research Pipeline...")

	// 2. Init Service
	svc, err := NewResearchService()
	if err != nil {
		return nil, fmt.Errorf("failed to init research service: %w", err)
	}

	// 4. Start Processing (Background)
	logger.Infof(ctx, "🚀 Starting %d queue workers", WORKER_COUNT)
	svc.totalWorkers = WORKER_COUNT
	for i := range WORKER_COUNT {
		defer handlePanic(WORKER_GO_ROUTINE_NAME, fmt.Sprintf(WORKER_GO_ROUTINE_RECOVER_ID, i))
		svc.wg.Add(1)
		go svc.workerLoop(i)
	}
	logger.Infof(ctx, "🚀 Research Queue Processor started in background")

	return svc, nil
}

func waitForLoggingService(ctx *colly.Context) {
	client := &http.Client{}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	logger.Info(ctx, "Waiting for Logging Service to be ready...")

	for {
		attempts += 1
		resp, err := client.Get(fmt.Sprintf("%v/health", LOGGING_SERVICE_ROUTE))
		if err == nil && resp.StatusCode == 200 {
			logger.Info(ctx, "✅ Logging Service is ready")
			return
		}

		logger.Infof(ctx, "Waiting for Logging Service to be ready for attempt %d... retrying in %s\n", attempts, delay)
		time.Sleep(delay)

		// Exponential backoff: double the delay each time, up to maxDelay
		delay *= 2
		if delay > maxDelay {
			delay = maxDelay
		}
	}
}

func printBanner() {
	banner := `

  ░██████                                                                    ░██       ░██                     ░██                           
 ░██   ░██                                                                   ░██       ░██                     ░██                           
░██          ░███████  ░██░████  ░██████   ░████████   ░███████  ░██░████    ░██  ░██  ░██  ░███████  ░██░████ ░██    ░██ ░███████  ░██░████ 
 ░████████  ░██    ░██ ░███           ░██  ░██    ░██ ░██    ░██ ░███        ░██ ░████ ░██ ░██    ░██ ░███     ░██   ░██ ░██    ░██ ░███     
        ░██ ░██        ░██       ░███████  ░██    ░██ ░█████████ ░██         ░██░██ ░██░██ ░██    ░██ ░██      ░███████  ░█████████ ░██      
 ░██   ░██  ░██    ░██ ░██      ░██   ░██  ░███   ░██ ░██        ░██         ░████   ░████ ░██    ░██ ░██      ░██   ░██ ░██        ░██      
  ░██████    ░███████  ░██       ░█████░██ ░██░█████   ░███████  ░██         ░███     ░███  ░███████  ░██      ░██    ░██ ░███████  ░██      
                                           ░██                                                                                               
                                           ░██                                                                                               
                                                                                                                                             
                                                                                   
`
	logger.Infof(colly.NewContext(), "%s", banner)
}

func startMetricsServer() {
	http.Handle("/metrics", promhttp.Handler())
	go http.ListenAndServe(":2112", nil)
}

func main() {
	defer handlePanic(MAIN_GO_ROUTINE_NAME, MAIN_GO_ROUTINE_RECOVER_ID)

	mainCtx := colly.NewContext()
	monitor := NewMemoryMonitor()
	ticker := time.NewTicker(30 * time.Second)
	go func() {
		for range ticker.C {
			monitor.LogMemoryStats()
		}
	}()

	if err := godotenv.Load(); err != nil {
		logger.Warnf(mainCtx, "⚠️  No .env file found, trying .env.local: %v", err)
		if err := godotenv.Load(".env.local"); err != nil {
			logger.Warnf(mainCtx, "⚠️  No .env.local file found either, continuing with system environment variables: %v", err)
		}
	}

	waitForLoggingService(mainCtx)
	printBanner()
	startMetricsServer()
	InitPostgres()
	go syncProfessorsWithScrapeQueue(mainCtx)

	svc, processResearchErr := startResearchPipeline(mainCtx)
	if processResearchErr != nil {
		logger.Errorf(mainCtx, "❌ Failed to process research: %v", processResearchErr)
		os.Exit(1)
	}

	// Setup signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Wait for shutdown signal
	select {
	case sig := <-sigChan:
		logger.Infof(mainCtx, "🛑 Received signal %v, initiating graceful shutdown...", sig)
	case <-svc.shutdownChan:
		logger.Infof(mainCtx, "🛑 Service finished all jobs (idle), shutting down...")
	}

	// Stop accepting new jobs
	svc.Close()

	logger.Infof(mainCtx, "✅ All workers stopped gracefully")
	os.Exit(0) // Prevent docker from restarting
}
