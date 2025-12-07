package main

import (
	"encoding/json"
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
	// Check cache first
	safeName := strings.ReplaceAll(prof.Name, "/", "_")
	safeName = strings.ReplaceAll(safeName, " ", "_")
	cachePath := filepath.Join(getScrapedDataFilePath(), safeName+".json")
	if _, err := os.Stat(cachePath); err == nil {
		content, err := os.ReadFile(cachePath)
		if err == nil {
			var cached []ScrapedContent
			if err := json.Unmarshal(content, &cached); err == nil {
				logger.Infof("✓ Cache hit for %s", prof.Name)
				return cached, nil
			}
		}
	}

	var contents []ScrapedContent
	var mu sync.Mutex

	// Clone collector for isolation if needed, but here we reuse
	c := s.collector.Clone()

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

			// Skip if it's mostly links (navigation, lists of papers usually have high density but we might want them?
			// Actually for "Research", lists of papers ARE the content.
			// But for "Homepage", we want bio.
			// Let's be lenient on linkDensity for academic pages, but usually sidebar nav is > 0.7
			if linkDensity > 0.6 {
				return
			}

			// Scoring
			// 1. Base: Log of text length (diminishing returns, but generally more is better)
			// 2. Penalty: Link Density
			// 3. Boost: HTML5 tags

			score := math.Log(float64(totalLength)) * (1.0 - linkDensity)

			if s.Is("article") || s.Is("main") {
				score *= 1.5
			}
			if s.Is("section") {
				score *= 1.2
			}

			// Slight penalty for common sidebar classes (heuristic)
			if class, exists := s.Attr("class"); exists {
				class = strings.ToLower(class)
				if strings.Contains(class, "sidebar") || strings.Contains(class, "menu") || strings.Contains(class, "widget") {
					score *= 0.1
				}
				if strings.Contains(class, "content") || strings.Contains(class, "body") || strings.Contains(class, "main") {
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
		if len(cleanText) > 50000 {
			cleanText = cleanText[:50000]
		}

		// Classify
		url := e.Request.URL.String()
		contentType := s.classifyContent(url, title)

		content := ScrapedContent{
			ProfessorName: prof.Name,
			URL:           url,
			ContentType:   contentType,
			Title:         title,
			Content:       cleanText,
			ScrapedAt:     time.Now(),
		}

		// Log extraction details
		logger.Debugf("Extracted: '%s' (Type: %s, Length: %d chars) from %s", title, contentType, len(cleanText), url)

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
	c.OnRequest(func(r *colly.Request) {
		logger.Debugf("Visiting: %s", r.URL)
	})

	err := c.Visit(prof.Homepage)
	if err != nil {
		return nil, err
	}

	c.Wait()

	// Save to cache
	if len(contents) > 0 {
		data, err := json.MarshalIndent(contents, "", "  ")
		if err == nil {
			if err := os.WriteFile(cachePath, data, 0644); err != nil {
				logger.Errorf("Failed to write cache for %s: %v", prof.Name, err)
			} else {
				logger.Infof("Saved cache for %s (%d items)", prof.Name, len(contents))
			}
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

	// Keywords
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

	// Title keywords
	if slices.Contains([]string{"publications", "papers"}, titleLower) {
		return "publication"
	}
	if slices.Contains([]string{"research", "projects"}, titleLower) {
		return "project"
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

	// 2. Must start with the same path prefix
	// Normalize paths by removing trailing slashes
	rootPath := strings.TrimRight(rootObj.Path, "/")
	targetPath := strings.TrimRight(targetObj.Path, "/")

	return strings.HasPrefix(targetPath, rootPath)
}
