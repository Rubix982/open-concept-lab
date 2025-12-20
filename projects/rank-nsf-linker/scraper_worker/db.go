package main

import (
	"time"

	"github.com/cenkalti/backoff/v4"
)

func syncProfessorsWithScrapeQueue() {
	logger.Info("Starting syncProfessorsWithScrapeQueue operation")

	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("Failed to get global DB: %v", err)
		return
	}

	operation := func() error {
		logger.Debug("Preparing to execute INSERT INTO scrape_queue query")
		query := `
			INSERT INTO scrape_queue (professor_name, url, status)
			SELECT name, homepage, 'pending'
			FROM professors
			WHERE homepage IS NOT NULL AND homepage != ''
			ON CONFLICT (professor_name, url) DO NOTHING;
		`
		res, err := db.Exec(query)
		if err != nil {
			logger.Errorf("Failed to sync professors with scrape queue: %v", err)
			return err
		}

		count, _ := res.RowsAffected()
		logger.Infof("Added %d new jobs to queue", count)
		return nil
	}

	expBackoff := backoff.NewExponentialBackOff()
	expBackoff.MaxElapsedTime = 5 * time.Minute // or any suitable max time

	logger.Debugf("Starting backoff retry with max elapsed time: %v", expBackoff.MaxElapsedTime)
	if err = backoff.Retry(operation, expBackoff); err != nil {
		logger.Errorf("All retries failed for syncing professors: %v", err)
	} else {
		logger.Info("syncProfessorsWithScrapeQueue operation completed successfully")
	}

	// Pause for a while before re-attempting DB query execution
	logger.Debug("Sleeping for 1 minute before next sync attempt")
	time.Sleep(1 * time.Minute)
}
