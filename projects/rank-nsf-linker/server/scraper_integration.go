package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

// scrapeProfessorHomepages triggers the Python scraper to scrape all professor homepages
func scrapeProfessorHomepages() error {
	logger.Info("🕷️  Starting professor homepage scraping...")

	// Get the scraper directory path
	// In Docker: /app/scraper
	// Locally: server/scraper
	scraperDir := "scraper"
	if _, err := os.Stat(scraperDir); os.IsNotExist(err) {
		scraperDir = filepath.Join("server", "scraper")
		if _, err := os.Stat(scraperDir); os.IsNotExist(err) {
			return fmt.Errorf("scraper directory not found")
		}
	}

	// Check if Python is available
	pythonCmd := "python3"
	if _, err := exec.LookPath(pythonCmd); err != nil {
		pythonCmd = "python"
		if _, err := exec.LookPath(pythonCmd); err != nil {
			logger.Warn("⚠️  Python not found, skipping scraper. Install Python to enable scraping.")
			return nil // Don't fail the pipeline, just skip
		}
	}

	// Install dependencies if needed
	logger.Info("📦 Checking scraper dependencies...")
	requirementsPath := filepath.Join(scraperDir, "requirements.txt")
	if _, err := os.Stat(requirementsPath); err == nil {
		installCmd := exec.Command(pythonCmd, "-m", "pip", "install", "-q", "-r", requirementsPath)
		installCmd.Dir = scraperDir
		if output, err := installCmd.CombinedOutput(); err != nil {
			logger.Warnf("⚠️  Failed to install scraper dependencies: %v\nOutput: %s", err, string(output))
			logger.Info("Continuing without scraper...")
			return nil // Don't fail pipeline
		}
	}

	// Run the scraper
	logger.Info("🚀 Running scraper for all professors with homepages...")

	// Set environment variables for scraper
	env := os.Environ()
	env = append(env, fmt.Sprintf("POSTGRES_HOST=%s", os.Getenv("POSTGRES_HOST")))
	env = append(env, fmt.Sprintf("POSTGRES_PORT=%s", os.Getenv("POSTGRES_PORT")))
	env = append(env, fmt.Sprintf("POSTGRES_USER=%s", os.Getenv("POSTGRES_USER")))
	env = append(env, fmt.Sprintf("POSTGRES_PASSWORD=%s", os.Getenv("POSTGRES_PASSWORD")))
	env = append(env, fmt.Sprintf("POSTGRES_DB_NAME=%s", os.Getenv("POSTGRES_DB_NAME")))

	// Run scraper with limit (scrape all professors)
	scraperCmd := exec.Command(pythonCmd, "example.py", "1000") // Limit to 1000 professors
	scraperCmd.Dir = scraperDir
	scraperCmd.Env = env
	scraperCmd.Stdout = os.Stdout
	scraperCmd.Stderr = os.Stderr

	if err := scraperCmd.Run(); err != nil {
		logger.Errorf("❌ Scraper failed: %v", err)
		// Don't fail the pipeline, just log the error
		logger.Info("Continuing pipeline despite scraper failure...")
		return nil
	}

	logger.Info("✅ Professor homepage scraping completed successfully")
	return nil
}
