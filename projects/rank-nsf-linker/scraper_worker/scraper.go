package scraperworker

import (
	"encoding/json"
	"fmt"
	"math"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"sync"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/gocolly/colly/v2"
)

var (
	CleanTextRegex = regexp.MustCompile(`[^\w\s.,;:!?()-]`)
)

type Scraper struct {
	collector *colly.Collector
}

func NewScraper() *Scraper {
	// Ensure cache directory exists
	if _, err := os.Stat(getScrapedDataFilePath()); os.IsNotExist(err) {
		os.MkdirAll(getScrapedDataFilePath(), 0755)
	}

	c := colly.NewCollector(
		colly.Async(true),
		colly.MaxDepth(2),
		colly.UserAgent("FacultyResearchBot/1.0"),
	)

	// Politeness
	c.Limit(&colly.LimitRule{
		DomainGlob:  "*",
		Parallelism: 4, // Concurrent requests!
		RandomDelay: 1 * time.Second,
	})

	return &Scraper{
		collector: c,
	}
}

func (s *Scraper) ScrapeProfessor(prof ProfessorProfile) ([]ScrapedContent, error) {
	// Check cache first (with TTL)
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
					logger.Infof("✓ Cache hit for %s (age: %v)", prof.Name, time.Since(info.ModTime()).Round(time.Hour))
					return cached, nil
				}
			}
		} else {
			logger.Infof("Cache expired for %s, re-scraping", prof.Name)
		}
	}

	var contents []ScrapedContent
	var mu sync.Mutex

	// Clone collector with limits
	c := s.collector.Clone()
	c.AllowURLRevisit = false
	c.MaxDepth = 2
	c.Async = true
	c.SetRequestTimeout(30 * time.Second)

	c.Limit(&colly.LimitRule{
		DomainGlob:  "*",
		Parallelism: 2,
		Delay:       200 * time.Millisecond,
	})

	// Page count limiter
	visitCount := 0
	maxPages := 20

	c.OnRequest(func(r *colly.Request) {
		visitCount++
		if visitCount > maxPages {
			logger.Warnf("Reached max pages (%d), stopping crawl for %s", maxPages, prof.Name)
			r.Abort()
			return
		}
		logger.Debugf("Visiting [%d/%d]: %s", visitCount, maxPages, r.URL)
	})

	// OnHTML handlers
	c.OnHTML("html", func(e *colly.HTMLElement) {
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
			logger.Warnf("Truncated content for %s (was >50KB)", url)
		}

		// Classify content type
		contentType := s.classifyContent(url, title)

		// Skip if content is too short (likely navigation/error page)
		if len(cleanText) < 200 {
			logger.Debugf("Skipping %s: content too short (%d chars)", url, len(cleanText))
			return
		}

		content := ScrapedContent{
			ProfessorName: prof.Name,
			URL:           url,
			ContentType:   contentType,
			Title:         title,
			Content:       cleanText,
			ScrapedAt:     time.Now(),
		}

		logger.Debugf("✓ Extracted: '%s' (Type: %s, Length: %d chars) from %s",
			title, contentType, len(cleanText), url)

		mu.Lock()
		contents = append(contents, content)
		mu.Unlock()
	})

	// Find and visit links (Recursive)
	c.OnHTML("a[href]", func(e *colly.HTMLElement) {
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
	c.OnError(func(r *colly.Response, err error) {
		logger.Warnf("Scraping error for %s: %v", r.Request.URL, err)
	})

	// Visit homepage
	logger.Infof("🕷️ Scraping homepage: %s", prof.Homepage)
	err := c.Visit(prof.Homepage)
	if err != nil {
		return nil, fmt.Errorf("failed to visit homepage: %w", err)
	}

	c.Wait()

	// Check if we got any content
	if len(contents) == 0 {
		logger.Warnf("No content extracted for %s", prof.Name)
		return nil, fmt.Errorf("no content extracted from %s", prof.Homepage)
	}

	// Save to cache
	data, err := json.MarshalIndent(contents, "", "  ")
	if err != nil {
		logger.Errorf("Failed to marshal cache for %s: %v", prof.Name, err)
	} else {
		if err := os.WriteFile(cachePath, data, 0644); err != nil {
			logger.Errorf("Failed to write cache for %s: %v", prof.Name, err)
		} else {
			logger.Infof("💾 Saved cache for %s (%d pages, %d total chars)",
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

func (s *Scraper) classifyContent(url, title string) string {
	urlLower := strings.ToLower(url)
	titleLower := strings.ToLower(title)

	// Check URL path for keywords
	if slices.Contains([]string{"publication", "paper", "pub"}, urlLower) {
		return "publication"
	}
	if slices.Contains([]string{"project", "research"}, urlLower) {
		return "project"
	}
	if slices.Contains([]string{"bio", "about", "cv", "resume"}, urlLower) {
		return "bio"
	}
	if slices.Contains([]string{"teaching", "course"}, urlLower) {
		return "teaching"
	}

	// Check title for keywords
	if slices.Contains([]string{"publications", "papers"}, titleLower) {
		return "publication"
	}
	if slices.Contains([]string{"research", "projects"}, titleLower) {
		return "project"
	}
	if slices.Contains([]string{"biography", "about", "cv"}, titleLower) {
		return "bio"
	}

	return "homepage"
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
