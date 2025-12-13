package scraperworker

import (
	"fmt"
	"net/http"
	"time"

	"github.com/joho/godotenv"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func startResearchPipeline() error {
	logger.Info("🚀 Starting Go-based Research Pipeline...")

	// 2. Init Service
	svc, err := NewResearchService()
	if err != nil {
		return fmt.Errorf("failed to init research service: %w", err)
	}

	// 4. Start Processing (Background)
	logger.Infof("🚀 Starting %d queue workers", WORKER_COUNT)
	for i := range WORKER_COUNT {
		svc.wg.Add(1)
		go svc.workerLoop(i)
	}
	logger.Info("🚀 Research Queue Processor started in background")

	return nil
}

func waitForLoggingService() {
	client := &http.Client{}
	delay := 1 * time.Second
	maxDelay := 30 * time.Second
	attempts := 0
	fmt.Println("Waiting for Logging Service to be ready...")

	for {
		attempts += 1
		resp, err := client.Get(fmt.Sprintf("%v/health", LOGGING_SERVICE_ROUTE))
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
	logger.Infof("%s", banner)
}

func waitForServices() {
	waitForLoggingService()
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
	go syncProfessorsWithScrapeQueue()

	if processResearchErr := startResearchPipeline(); processResearchErr != nil {
		logger.Errorf("❌ Failed to process research: %v", processResearchErr)
		return
	}
}
