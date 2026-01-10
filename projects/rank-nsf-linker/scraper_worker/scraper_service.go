package main

import (
	"github.com/gocolly/colly/v2"
	"github.com/sirupsen/logrus"
)

// ScraperService provides an isolated scraping environment for a single worker.
// Each worker should create its own ScraperService instance to avoid race conditions.
type ScraperService struct {
	workerCtx *colly.Context
	scraper   *Scraper
}

// NewScraperService creates a new scraper service with its own dedicated scraper instance.
// This ensures complete isolation between workers - no shared state, no locks needed.
func NewScraperService(workerCtx *colly.Context) *ScraperService {
	logger.WithFields(workerCtx, logrus.Fields{
		"component": "scraper_service",
	}).Debug("Initializing new ScraperService instance")

	return &ScraperService{
		workerCtx: workerCtx,
		scraper:   NewScraper(),
	}
}

// Close cleans up the scraper resources (browser, etc.)
func (ss *ScraperService) Close() {
	if ss.scraper != nil {
		ss.scraper.Close()
		logger.WithFields(ss.workerCtx, logrus.Fields{
			"component": "scraper_service",
		}).Debug("ScraperService closed")
	}
}
