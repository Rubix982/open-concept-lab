package main

import (
	"crypto/tls"
	"encoding/json"
	"fmt"
	"math"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
	"github.com/gocolly/colly/v2"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type ContentType string

var (
	CleanTextRegex            = regexp.MustCompile(`[^\w\s.,;:!?()-]`)
	DisallowedURLFiltersRegex = []*regexp.Regexp{
		regexp.MustCompile(`\.pdf$`),
		regexp.MustCompile(`\.zip$`),
		regexp.MustCompile(`\.doc[x]?$`),
	}
)

const (
	ContentPublication ContentType = "publication"
	ContentProject     ContentType = "project"
	ContentBiography   ContentType = "biography"
	ContentTeaching    ContentType = "teaching"
	ContentStudents    ContentType = "students"
	ContentTalk        ContentType = "talk"
	ContentCode        ContentType = "code"
	ContentNews        ContentType = "news"
	ContentAward       ContentType = "award"
	ContentDataset     ContentType = "dataset"
	ContentHomepage    ContentType = "homepage"
)

// Classification rules with priority (higher = more specific)
var ClassificationRules = []struct {
	contentType ContentType
	keywords    []string
	priority    int
}{
	// High priority (very specific)
	{ContentPublication, []string{"publication", "papers", "proceedings", "article", "citations", "scholar"}, 10},
	{ContentCode, []string{"github", "gitlab", "bitbucket", "software", "code", "repository", "tool"}, 9},
	{ContentDataset, []string{"dataset", "data", "corpus", "benchmark"}, 9},
	{ContentTalk, []string{"talk", "presentation", "slides", "conference", "seminar", "workshop"}, 8},

	// Medium priority
	{ContentProject, []string{"project", "research", "grant", "lab", "group"}, 7},
	{ContentStudents, []string{"student", "phd", "postdoc", "collaborator", "team", "member"}, 7},
	{ContentTeaching, []string{"teaching", "course", "syllabus", "lecture", "class"}, 7},
	{ContentAward, []string{"award", "honor", "recognition", "prize", "fellow"}, 6},
	{ContentNews, []string{"news", "blog", "announcement", "update"}, 6},

	// Low priority (generic)
	{ContentBiography, []string{"bio", "about", "cv", "resume", "vita", "profile"}, 5},
}

type Scraper struct {
	collector      *colly.Collector
	browser        *rod.Browser
	scraperID      string
	totalRequests  *atomic.Int64
	failedRequests *atomic.Int64
	inFlight       *atomic.Int64
}

func NewScraper() *Scraper {
	scraperID := uuid.NewString()[:8] // Short ID for logs

	logger.WithFields(logrus.Fields{
		"scraper_id": scraperID,
		"component":  "scraper",
	})

	logger.Info("Initializing scraper...")

	// Ensure cache directory exists
	cachePath := getScrapedDataFilePath()
	if _, err := os.Stat(cachePath); os.IsNotExist(err) {
		if err := os.MkdirAll(cachePath, 0755); err != nil {
			logger.WithError(err).Fatal("Failed to create cache directory")
		}
		logger.WithField("path", cachePath).Debug("Created cache directory")
	} else {
		logger.WithField("path", cachePath).Debug("Cache directory exists")
	}

	collyCache := "./cache/colly"
	if _, err := os.Stat(collyCache); os.IsNotExist(err) {
		os.MkdirAll(collyCache, 0755)
		logger.WithField("path", collyCache).Debug("Created colly cache directory")
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
	logger.Warn("TLS verification disabled (InsecureSkipVerify=true)")

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

	logger.WithFields(logrus.Fields{
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

	// Request lifecycle tracking
	var inFlight atomic.Int64
	var totalRequests atomic.Int64
	var failedRequests atomic.Int64

	c.OnRequest(func(r *colly.Request) {
		totalRequests.Add(1)
		inFlight.Add(1)
		r.Ctx.Put("start_time", time.Now())

		logger.WithFields(logrus.Fields{
			"url":       r.URL.String(),
			"depth":     r.Depth,
			"in_flight": inFlight.Load(),
			"total":     totalRequests.Load(),
		}).Debug("Request started")
	})

	c.OnResponse(func(r *colly.Response) {
		inFlight.Add(-1)
		start, _ := r.Ctx.GetAny("start_time").(time.Time)
		duration := time.Since(start)

		fromCache := r.Headers.Get("X-From-Cache") != ""

		logger.WithFields(logrus.Fields{
			"url":         r.Request.URL.String(),
			"status":      r.StatusCode,
			"bytes":       len(r.Body),
			"duration_ms": duration.Milliseconds(),
			"from_cache":  fromCache,
			"in_flight":   inFlight.Load(),
		}).Debug("Response received")

		if r.StatusCode >= 400 {
			failedRequests.Add(1)
			logger.WithFields(logrus.Fields{
				"url":    r.Request.URL.String(),
				"status": r.StatusCode,
			}).Warn("HTTP error response")
		}
	})

	c.OnError(func(r *colly.Response, err error) {
		inFlight.Add(-1)
		failedRequests.Add(1)
		if r != nil {
			logger.WithFields(logrus.Fields{
				"url":    r.Request.URL.String(),
				"method": r.Request.Method,
				"depth":  r.Request.Depth,
			}).Warn("Request failed")
		}

		if r != nil {
			logger.WithFields(logrus.Fields{
				"url":    r.Request.URL.String(),
				"method": r.Request.Method,
				"depth":  r.Request.Depth,
			}).Warn("Request failed")
		}

		// Classify error type
		errorType := "unknown"
		switch {
		case strings.Contains(err.Error(), "timeout"):
			errorType = "timeout"
		case strings.Contains(err.Error(), "TLS"):
			errorType = "tls"
		case strings.Contains(err.Error(), "DNS"):
			errorType = "dns"
		case strings.Contains(err.Error(), "connection refused"):
			errorType = "connection_refused"
		}
		logger.WithFields(logrus.Fields{
			"url":        r.Request.URL.String(),
			"method":     r.Request.Method,
			"depth":      r.Request.Depth,
			"error_type": errorType,
		}).WithError(err).Error("Request failed")
	})

	// Log filtered URLs
	c.OnRequest(func(r *colly.Request) {
		for _, pattern := range DisallowedURLFiltersRegex {
			if pattern.MatchString(r.URL.String()) {
				logger.WithFields(logrus.Fields{
					"url":     r.URL.String(),
					"pattern": pattern.String(),
				}).Debug("URL blocked by disallowed filter")
				r.Abort()
				return
			}
		}
	})

	logger.Info("Setting up Chromium browser...")

	// Browser initialization
	systemBrowser := "/usr/bin/chromium"
	if _, err := os.Stat(systemBrowser); err != nil {
		logger.WithError(err).Fatal("System Chromium not found")
	}

	logger.WithField("chromium_bin", systemBrowser).Debug("Chromium binary validated")

	l := launcher.New().
		Bin(systemBrowser).
		Headless(true).
		Devtools(false).
		NoSandbox(true).
		Set("disable-gpu").
		Set("disable-dev-shm-usage")

	debugURL, err := l.Launch()
	if err != nil {
		logger.WithError(err).Fatal("Failed to launch Chromium")
	}

	logger.WithFields(logrus.Fields{
		"debug_url":  debugURL,
		"headless":   true,
		"no_sandbox": true,
	}).Info("Chromium launched successfully")

	browser := rod.New().ControlURL(debugURL).MustConnect()

	logger.WithFields(logrus.Fields{
		"scraper_id": scraperID,
		"browser":    "chromium",
		"collector":  "colly",
	}).Info("✓ Scraper initialized successfully")

	s := &Scraper{
		collector:      c,
		browser:        browser,
		scraperID:      scraperID,
		totalRequests:  &totalRequests,
		failedRequests: &failedRequests,
		inFlight:       &inFlight,
	}

	return s
}

func (s *Scraper) ScrapeProfessor(workerID int, prof ProfessorProfile) ([]ScrapedContent, error) {
	// Check cache first (with TTL)
	logPrefix := fmt.Sprintf("[Worker %d] -", workerID)
	safeName := strings.ReplaceAll(prof.Name, "/", "_")
	safeName = strings.ReplaceAll(safeName, " ", "_")
	cachePath := filepath.Join(getScrapedDataFilePath(), safeName+".json")
	if info, err := os.Stat(cachePath); err == nil {
		// Cache expires after 7 days
		if time.Since(info.ModTime()) < 7*24*time.Hour {
			content, err := os.ReadFile(cachePath)
			if err == nil {
				var cached []ScrapedContent
				if err := json.Unmarshal(content, &cached); err == nil {
					logger.Infof("%s - ✓ Cache hit for %s (age: %v)", logPrefix, prof.Name,
						time.Since(info.ModTime()).Round(time.Hour))
					return cached, nil
				}
			}
		} else {
			logger.Infof("%s - Cache expired for %s, re-scraping", logPrefix, prof.Name)
		}
	}

	var contents []ScrapedContent
	var mu sync.Mutex

	// Check if this is a Google Site
	if strings.Contains(prof.Homepage, "sites.google.com") {
		logger.Infof("%s - 🌐 Detected Google Site, using browser scraper", logPrefix)
		return s.scrapeGoogleSiteProfile(workerID, prof)
	}

	// Page count limiter
	visitCount := 0
	maxPages := 40

	s.collector.OnRequest(func(r *colly.Request) {
		visitCount++
		if visitCount > maxPages {
			logger.Warnf("Reached max pages (%d), stopping crawl for %s", maxPages, prof.Name)
			r.Abort()
			return
		}
		logger.Debugf("Visiting [%d/%d] for professor '%v' under route: %s", visitCount, maxPages, prof.Name, r.URL)
	})

	// OnHTML handlers
	s.collector.OnHTML("html", func(e *colly.HTMLElement) {
		// Clean DOM: Remove boilerplate
		e.DOM.Find("script, style, noscript, iframe, nav, footer, header, aside, .nav, .footer, .header, .menu").Remove()
		e.DOM.Find("svg, button, input, form, select, textarea").Remove() // Remove UI elements

		// Extract Title
		title := e.ChildText("title")
		if title == "" {
			title = e.ChildText("h1")
		}
		title = strings.TrimSpace(title)

		// Algorithm: Find the node with the highest Text Density Score.
		// Score = TextLength * (1 - LinkDensity) * TagBoost

		// Check if this is a publications/research page
		url := e.Request.URL.String()
		urlLower := strings.ToLower(url)
		titleLower := strings.ToLower(title)
		isPublicationPage := strings.Contains(urlLower, "publication") ||
			strings.Contains(urlLower, "research") ||
			strings.Contains(urlLower, "paper") ||
			strings.Contains(titleLower, "publication") ||
			strings.Contains(titleLower, "research")

		// Find the node with the highest Text Density Score
		var bestNode *goquery.Selection
		var maxScore float64

		// Candidates: Block elements that likely contain content
		e.DOM.Find("div, article, section, main, td").Each(func(_ int, s *goquery.Selection) {
			text := strings.TrimSpace(s.Text())
			if len(text) < 100 {
				return
			} // Too short to be main content

			// Calculate Link Density
			linkTextLength := 0
			s.Find("a").Each(func(_ int, a *goquery.Selection) {
				linkTextLength += len(strings.TrimSpace(a.Text()))
			})

			totalLength := len(text)
			if totalLength == 0 {
				return
			}

			linkDensity := float64(linkTextLength) / float64(totalLength)

			// Skip high-link-density nodes UNLESS it's a publication page
			// (Publication pages are legitimately link-heavy)
			if !isPublicationPage && linkDensity > 0.6 {
				return
			}

			// Scoring
			// 1. Base: Log of text length (diminishing returns, but generally more is better)
			// 2. Penalty: Link Density
			// 3. Boost: HTML5 tags
			// Scoring: Log(length) * (1 - linkDensity) * TagBoost
			score := math.Log(float64(totalLength)) * (1.0 - linkDensity)

			// Boost semantic HTML5 tags
			if s.Is("article") || s.Is("main") {
				score *= 1.5
			}
			if s.Is("section") {
				score *= 1.2
			}

			// Class-based heuristics
			if class, exists := s.Attr("class"); exists {
				classLower := strings.ToLower(class)
				if strings.Contains(classLower, "sidebar") ||
					strings.Contains(classLower, "menu") ||
					strings.Contains(classLower, "widget") {
					score *= 0.1
				}
				if strings.Contains(classLower, "content") ||
					strings.Contains(classLower, "body") ||
					strings.Contains(classLower, "main") {
					score *= 1.2
				}
			}

			if score > maxScore {
				maxScore = score
				bestNode = s
			}
		})

		var rawText string
		if bestNode != nil {
			rawText = bestNode.Text()
		} else {
			// Fallback to body if no good candidate found
			rawText = e.DOM.Find("body").Text()
		}

		// Clean Text
		cleanText := s.cleanText(rawText)

		// Truncate if too long (safety limit)
		if len(cleanText) > 50000 {
			cleanText = cleanText[:50000]
			logger.Warnf("%s - Truncated content for %s (was >50KB)", logPrefix, url)
		}

		// Classify content type
		contentType := s.classifyContent(url, title, cleanText)

		// Skip if content is too short (likely navigation/error page)
		if len(cleanText) < 200 {
			logger.Debugf("%s - Skipping %s: content too short (%d chars)", logPrefix, url, len(cleanText))
			return
		}

		content := ScrapedContent{
			ProfessorName: prof.Name,
			URL:           url,
			ContentType:   string(contentType),
			Title:         title,
			Content:       cleanText,
			ScrapedAt:     time.Now(),
		}

		logger.Debugf("%s -	✓ Extracted: '%s' (Type: %s, Length: %d chars) from %s", logPrefix,
			title, contentType, len(cleanText), url)

		mu.Lock()
		contents = append(contents, content)
		mu.Unlock()
	})

	// Find and visit links (Recursive)
	s.collector.OnHTML("a[href]", func(e *colly.HTMLElement) {
		link := e.Attr("href")
		// Resolve absolute URL
		absoluteURL := e.Request.AbsoluteURL(link)
		if absoluteURL == "" {
			return
		}

		// Security Check: Only visit if it shares the same host and path prefix
		// This prevents crawling the entire university website.
		// Only visit if it shares the same host and path prefix
		if isSafeToVisit(prof.Homepage, absoluteURL) {
			e.Request.Visit(absoluteURL)
		}
	})

	// Error handling
	s.collector.OnError(func(r *colly.Response, err error) {
		logger.Warnf("%s - Scraping error for %s: %v", logPrefix, r.Request.URL, err)
	})

	// Visit homepage
	logger.Infof("%s - 🕷️ Scraping homepage: %s", logPrefix, prof.Homepage)
	err := s.collector.Visit(prof.Homepage)
	if err != nil {
		return nil, fmt.Errorf("failed to visit homepage: %w", err)
	}

	s.collector.Wait()

	// Check if we got any content
	if len(contents) == 0 {
		logger.Warnf("%s - No content extracted for %s", logPrefix, prof.Name)
		return nil, fmt.Errorf("no content extracted from %s", prof.Homepage)
	}

	// Save to cache
	data, err := json.MarshalIndent(contents, "", "  ")
	if err != nil {
		logger.Errorf("%s - Failed to marshal cache for %s: %v", logPrefix, prof.Name, err)
	} else {
		if err := os.WriteFile(cachePath, data, 0644); err != nil {
			logger.Errorf("%s - Failed to write cache for %s: %v", logPrefix, prof.Name, err)
		} else {
			logger.Infof("%s - 💾 Saved cache for %s (%d pages, %d total chars)", logPrefix,
				prof.Name, len(contents), len(contents))
		}
	}

	return contents, nil
}

func (s *Scraper) cleanText(text string) string {
	// Normalize whitespace
	text = strings.Join(strings.Fields(text), " ")

	// Remove special chars but keep punctuation
	return strings.TrimSpace(CleanTextRegex.ReplaceAllString(text, ""))
}

func (s *Scraper) classifyContent(
	url string,
	title string,
	content string,
) ContentType {
	urlLower := strings.ToLower(url)
	titleLower := strings.ToLower(title)

	bestMatch := ContentHomepage
	bestScore := 0

	for _, rule := range ClassificationRules {
		score := 0

		// Check URL path (higher weight)
		for _, keyword := range rule.keywords {
			if strings.Contains(urlLower, keyword) {
				score += rule.priority * 2 // URL match is stronger signal
				break
			}
		}

		// Check title (lower weight)
		for _, keyword := range rule.keywords {
			if strings.Contains(titleLower, keyword) {
				score += rule.priority
				break
			}
		}

		if score > bestScore {
			bestScore = score
			bestMatch = rule.contentType
		}
	}

	if bestMatch == ContentHomepage {
		// Analyze content patterns
		contentLower := strings.ToLower(content)

		// Look for publication markers in text
		pubMarkers := []string{"abstract:", "doi:", "arxiv:", "published in", "conference:", "journal:"}
		pubCount := 0
		for _, marker := range pubMarkers {
			if strings.Contains(contentLower, marker) {
				pubCount++
			}
		}

		if pubCount >= 2 {
			return ContentPublication
		}

		// Look for project markers
		projMarkers := []string{"funded by", "nsf grant", "collaboration with", "research question"}
		projCount := 0
		for _, marker := range projMarkers {
			if strings.Contains(contentLower, marker) {
				projCount++
			}
		}

		if projCount >= 2 {
			return ContentProject
		}

		return ContentHomepage
	}

	return bestMatch
}

// Separate handler for Google Sites
func (s *Scraper) scrapeGoogleSiteProfile(workerID int, prof ProfessorProfile) ([]ScrapedContent, error) {
	logPrefix := fmt.Sprintf("[Worker %d] -", workerID)

	logger.Infof("%s - 🕷️ Scraping Google Site: %s", logPrefix, prof.Homepage)

	html, title, err := s.scrapeWithBrowser(prof.Homepage)
	if err != nil {
		return nil, fmt.Errorf("browser scraping failed: %w", err)
	}

	// Parse HTML with goquery
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(html))
	if err != nil {
		return nil, fmt.Errorf("failed to parse HTML: %w", err)
	}

	// Remove boilerplate
	doc.Find("script, style, noscript, iframe, nav, footer, header, aside").Remove()

	// Extract main content (Google Sites typically uses specific structure)
	var bestNode *goquery.Selection
	var maxScore float64

	// Google Sites content is usually in these containers
	doc.Find("div[class*='content'], div[role='main'], article, main").Each(func(_ int, s *goquery.Selection) {
		text := strings.TrimSpace(s.Text())
		if len(text) < 100 {
			return
		}

		// Simple scoring
		score := float64(len(text))

		if score > maxScore {
			maxScore = score
			bestNode = s
		}
	})

	var rawText string
	if bestNode != nil {
		rawText = bestNode.Text()
	} else {
		rawText = doc.Find("body").Text()
	}

	cleanText := s.cleanText(rawText)

	if len(cleanText) < 200 {
		return nil, fmt.Errorf("extracted content too short (%d chars)", len(cleanText))
	}

	// Truncate if needed
	if len(cleanText) > 50000 {
		cleanText = cleanText[:50000]
	}

	contentType := s.classifyContent(prof.Homepage, title, cleanText)

	content := ScrapedContent{
		ProfessorName: prof.Name,
		URL:           prof.Homepage,
		ContentType:   string(contentType),
		Title:         title,
		Content:       cleanText,
		ScrapedAt:     time.Now(),
	}

	logger.Infof("%s - ✓ Extracted from Google Site: '%s' (Length: %d chars)",
		logPrefix, title, len(cleanText))

	// Save to cache (reuse existing cache logic)
	safeName := strings.ReplaceAll(prof.Name, "/", "_")
	safeName = strings.ReplaceAll(safeName, " ", "_")
	cachePath := filepath.Join(getScrapedDataFilePath(), safeName+".json")

	contents := []ScrapedContent{content}
	data, _ := json.MarshalIndent(contents, "", "  ")
	os.WriteFile(cachePath, data, 0644)

	return contents, nil
}

func isSafeToVisit(rootURL, targetURL string) bool {
	rootObj, err := url.Parse(rootURL)
	if err != nil {
		return false
	}
	targetObj, err := url.Parse(targetURL)
	if err != nil {
		return false
	}

	// 1. Must be same host
	if rootObj.Host != targetObj.Host {
		return false
	}

	// 2. Must be same scheme (http vs https)
	if rootObj.Scheme != targetObj.Scheme {
		return false
	}

	// 3. Normalize paths
	rootPath := strings.TrimRight(rootObj.Path, "/")
	targetPath := strings.TrimRight(targetObj.Path, "/")

	// 4. Must be exact match OR start with root path + separator
	if targetPath == rootPath {
		return true
	}

	// 5. Check if target is a subpath (with path separator boundary)
	return strings.HasPrefix(targetPath, rootPath+"/")
}

// Add JS scraping method
func (s *Scraper) scrapeWithBrowser(url string) (string, string, error) {
	page := s.browser.MustPage(url)
	defer page.MustClose()

	// Wait for content to load
	page.MustWaitLoad()

	// Additional wait for dynamic content
	time.Sleep(2 * time.Second)

	// Extract title
	title, _ := page.MustElement("title").Text()

	// Remove unwanted elements
	page.MustEval(`() => {
        const selectors = 'script, style, noscript, iframe, nav, footer, header, aside, svg, button, input, form, select, textarea';
        document.querySelectorAll(selectors).forEach(el => el.remove());
    }`)

	// Get cleaned HTML
	return page.MustHTML(), title, nil
}

// Cleanup on exit
func (s *Scraper) Close() {
	logger.WithFields(logrus.Fields{
		"total_requests":  s.totalRequests.Load(),
		"failed_requests": s.failedRequests.Load(),
		"in_flight":       s.inFlight.Load(),
	}).Info("Scraper shutting down")

	if s.browser != nil {
		s.browser.MustClose()
		logger.Debug("Browser closed")
	}
}
