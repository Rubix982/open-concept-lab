package main

import (
	"strings"
	"time"

	"github.com/cenkalti/backoff/v4"
	"github.com/gocolly/colly/v2"
)

func syncProfessorsWithScrapeQueue(ctx *colly.Context) {
	logger.Info(ctx, "Starting syncProfessorsWithScrapeQueue operation")

	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf(ctx, "Failed to get global DB: %v", err)
		return
	}

	operation := func() error {
		logger.Debug(ctx, "Preparing to execute INSERT INTO scrape_queue query")
		query := `
		INSERT INTO scrape_queue (professor_name, url, status)
		SELECT name, homepage, 'pending'
		FROM professors
		WHERE homepage IS NOT NULL AND homepage != ''
		ON CONFLICT (professor_name, url) DO NOTHING;
	`

		// Retry indefinitely with exponential backoff capped at 30s
		backoff := time.Second
		maxBackoff := 30 * time.Second

		for {
			res, err := db.Exec(query)
			if err != nil {
				// Check if it's a "table doesn't exist" error
				if strings.Contains(err.Error(), "does not exist") ||
					strings.Contains(err.Error(), "no such table") {
					logger.Warnf(ctx, "Table not ready yet, retrying in %v: %v", backoff, err)
					time.Sleep(backoff)

					// Exponential backoff
					backoff *= 2
					if backoff > maxBackoff {
						backoff = maxBackoff
					}
					continue
				}

				// Other errors should fail immediately
				logger.Errorf(ctx, "Failed to sync professors with scrape queue: %v", err)
				return err
			}

			count, _ := res.RowsAffected()
			logger.Infof(ctx, "Added %d new jobs to queue", count)
			return nil
		}
	}

	expBackoff := backoff.NewExponentialBackOff()
	expBackoff.MaxElapsedTime = 5 * time.Minute // or any suitable max time

	logger.Debugf(ctx, "Starting backoff retry with max elapsed time: %v", expBackoff.MaxElapsedTime)
	if err = backoff.Retry(operation, expBackoff); err != nil {
		logger.Errorf(ctx, "All retries failed for syncing professors: %v", err)
	} else {
		logger.Info(ctx, "syncProfessorsWithScrapeQueue operation completed successfully")
	}

	// Pause for a while before re-attempting DB query execution
	logger.Debug(ctx, "Sleeping for 1 minute before next sync attempt")
	time.Sleep(1 * time.Minute)
}
