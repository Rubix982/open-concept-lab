package main

import (
	"crypto/tls"
	"net/http"
	"os"
	"time"

	"github.com/gocolly/colly/v2"
	"github.com/sirupsen/logrus"
)

func getDefaultCollyConfig(scraperCtx *colly.Context) *colly.Collector {
	collyCache := "./cache/colly"
	if _, err := os.Stat(collyCache); os.IsNotExist(err) {
		os.MkdirAll(collyCache, 0755)
		logger.WithField(scraperCtx, "path", collyCache).Debug("Created colly cache directory")
	}

	c := colly.NewCollector(
		colly.Async(true),
		colly.MaxDepth(2),
		colly.UserAgent("FacultyResearchBot/1.0"),
		colly.CacheDir(collyCache),
	)

	// Disable TLS verification
	c.WithTransport(&http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
	})
	logger.Warn(scraperCtx, "TLS verification disabled (InsecureSkipVerify=true)")

	// Politeness configuration
	c.Limit(&colly.LimitRule{
		DomainGlob:  "*",
		Parallelism: 4,
		RandomDelay: 1 * time.Second,
	})
	c.SetRequestTimeout(30 * time.Second)
	c.MaxBodySize = 10 * 1024 * 1024
	c.MaxRequests = 10000
	c.IgnoreRobotsTxt = true
	c.DetectCharset = true
	c.DisallowedURLFilters = DisallowedURLFiltersRegex
	c.ParseHTTPErrorResponse = true
	c.AllowURLRevisit = false
	c.MaxDepth = 2
	c.Async = true

	logger.WithFields(scraperCtx, logrus.Fields{
		"async":           true,
		"max_depth":       2,
		"max_requests":    10000,
		"parallelism":     4,
		"random_delay":    "1s",
		"request_timeout": "30s",
		"max_body_size":   "10MB",
		"ignore_robots":   true,
		"cache_dir":       collyCache,
		"user_agent":      "FacultyResearchBot/1.0",
	}).Info("Colly collector configured")
	return c
}
