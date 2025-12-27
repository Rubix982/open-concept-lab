package main

import (
	"database/sql"
	"fmt"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/spf13/cast"
)

type SearchResult struct {
	// Professor metadata
	ProfessorName string

	// Document metadata
	URL         string
	Title       string
	ContentType string
	ScrapedAt   time.Time

	// Chunk metadata
	ChunkText   string // The actual text chunk that matched
	ChunkIndex  int    // Which chunk (0-based)
	TotalChunks int    // Total chunks in this document
	TokenCount  int    // Tokens in this chunk

	// Scoring
	Score    float32 // Final weighted score (cosine_sim * content_weight)
	RawScore float32 // Original cosine similarity before weighting
	Weight   float32 // Content type weight applied
}

// Optional: Helper to format chunk position
func (r *SearchResult) ChunkPosition() string {
	if r.TotalChunks <= 1 {
		return ""
	}
	return fmt.Sprintf("Chunk %d of %d", r.ChunkIndex+1, r.TotalChunks)
}

// Optional: Helper to get short snippet
func (r *SearchResult) Snippet(maxChars int) string {
	if len(r.ChunkText) <= maxChars {
		return r.ChunkText
	}
	return r.ChunkText[:maxChars] + "..."
}

// Prometheus metrics
var (
	// Job metrics
	jobsProcessedTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "scraper_jobs_total",
			Help: "Total number of scrape jobs processed",
		},
		[]string{"status"}, // completed, failed
	)

	jobDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "scraper_job_duration_seconds",
			Help:    "Duration of job processing",
			Buckets: prometheus.ExponentialBuckets(1, 2, 10), // 1s to ~17min
		},
	)

	activeWorkers = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "scraper_active_workers",
			Help: "Number of currently active workers",
		},
	)

	// Scraping metrics
	pagesScrapedTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "scraper_pages_scraped_total",
			Help: "Total pages scraped by content type",
		},
		[]string{"content_type"},
	)

	scrapeDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "scraper_scrape_duration_seconds",
			Help:    "Duration of scraping operation",
			Buckets: prometheus.ExponentialBuckets(0.1, 2, 10), // 100ms to ~1.7min
		},
	)

	scrapeErrorsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "scraper_scrape_errors_total",
			Help: "Total scraping errors by type",
		},
		[]string{"error_type"},
	)

	// Embedding metrics
	embeddingsGeneratedTotal = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "scraper_embeddings_generated_total",
			Help: "Total embeddings generated",
		},
	)

	embeddingDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "scraper_embedding_duration_seconds",
			Help:    "Duration of embedding operation",
			Buckets: prometheus.ExponentialBuckets(0.01, 2, 10), // 10ms to ~10s
		},
	)

	chunksProcessedTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "scraper_chunks_processed_total",
			Help: "Total chunks processed by content type",
		},
		[]string{"content_type"},
	)

	// Qdrant metrics
	qdrantUpsertsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "scraper_qdrant_upserts_total",
			Help: "Total Qdrant upserts by status",
		},
		[]string{"status"}, // success, error
	)

	qdrantDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "scraper_qdrant_duration_seconds",
			Help:    "Duration of Qdrant operations",
			Buckets: prometheus.ExponentialBuckets(0.001, 2, 10), // 1ms to ~1s
		},
	)

	// Search metrics
	searchesTotal = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "scraper_searches_total",
			Help: "Total search queries executed",
		},
	)

	searchDuration = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "scraper_search_duration_seconds",
			Help:    "Duration of search operations",
			Buckets: prometheus.ExponentialBuckets(0.01, 2, 10), // 10ms to ~10s
		},
	)

	searchResultsCount = promauto.NewHistogram(
		prometheus.HistogramOpts{
			Name:    "scraper_search_results_count",
			Help:    "Number of results returned per search",
			Buckets: []float64{0, 1, 5, 10, 25, 50, 100, 250, 500},
		},
	)
)

type ResearchService struct {
	scraper  *Scraper
	embedder *Embedder
	qdrant   *QdrantClient
	wg       sync.WaitGroup
	running  bool
}

type ScrapeJob struct {
	ID            string
	ProfessorName string
	URL           string
}

const (
	// Insert scraped content into the database
	SERVICE_SAVE_TO_DB_QUERY = `
		INSERT INTO scraped_content (professor_name, url, content_type, title, content, scraped_at)
		VALUES ($1, $2, $3, $4, $5, $6)
		ON CONFLICT (professor_name, url) DO UPDATE
		SET content_type = EXCLUDED.content_type,
		    title = EXCLUDED.title,
		    content = EXCLUDED.content,
		    scraped_at = EXCLUDED.scraped_at;
	`

	// Postgres FIFO Queue with SKIP LOCKED for concurrency safety
	CLAIM_JOB_DB_QUERY = `
		UPDATE scrape_queue
		SET status = 'processing', updated_at = NOW(), attempts = attempts + 1, last_attempt = NOW()
		WHERE id = (
			SELECT id
			FROM scrape_queue
			WHERE status = 'pending'
			-- OR (status = 'processing' AND last_attempt < NOW() - INTERVAL '10 minutes') -- Recover stuck jobs, commented out, will test later
			ORDER BY created_at ASC
			FOR UPDATE SKIP LOCKED
			LIMIT 1
		)
		RETURNING id, professor_name, url;
	`
)

func NewResearchService() (*ResearchService, error) {
	logger.Info("Initializing ResearchService...")
	start := time.Now()

	// Initialize embedder
	logger.Debug("Initializing embedder component")
	embedderStart := time.Now()
	embedder, err := NewEmbedder()
	if err != nil {
		logger.Errorf("Failed to initialize embedder: %v", err)
		return nil, fmt.Errorf("failed to init embedder: %w", err)
	}
	logger.Infof("✓ Embedder initialized in %v", time.Since(embedderStart))

	// Initialize Qdrant client
	logger.Debug("Initializing Qdrant client")
	qdrantStart := time.Now()
	qdrant, err := NewQdrantClient()
	if err != nil {
		embedder.Close() // Cleanup
		logger.Errorf("Failed to initialize Qdrant client: %v", err)
		return nil, fmt.Errorf("failed to init qdrant: %w", err)
	}
	logger.Infof("✓ Qdrant client initialized in %v", time.Since(qdrantStart))

	// Ensure collection exists (384 dim for all-MiniLM-L6-v2)
	logger.Debug("Ensuring Qdrant collection exists (dim=384)")
	if err := qdrant.EnsureCollection(384); err != nil {
		embedder.Close()
		qdrant.Close()
		logger.Errorf("Failed to ensure Qdrant collection: %v", err)
		return nil, fmt.Errorf("failed to ensure collection: %w", err)
	}
	logger.Debug("✓ Qdrant collection verified")

	logger.Infof("✓ ResearchService initialized successfully in %v", time.Since(start))

	return &ResearchService{
		scraper:  NewScraper(),
		embedder: embedder,
		qdrant:   qdrant,
		running:  true,
	}, nil
}

func (s *ResearchService) workerLoop(id int) {
	defer s.wg.Done()
	defer activeWorkers.Dec()

	activeWorkers.Inc()
	logger.Infof("Worker %d started", id)

	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("Worker %d: Failed to get global DB: %v", id, err)
		return
	}

	for s.running {
		// Poll for a job
		job := &ScrapeJob{}
		err := db.QueryRow(CLAIM_JOB_DB_QUERY).Scan(&job.ID, &job.ProfessorName, &job.URL)
		if err != nil {
			if err == sql.ErrNoRows {
				// No jobs, sleep and retry
				time.Sleep(2 * time.Second)
				continue
			}
			logger.Errorf("Worker %d: Failed to claim job: %v", id, err)
			time.Sleep(5 * time.Second)
			continue
		}

		logger.Infof("[Worker %d] [Job %s] Processing professor: %s (URL: %s)",
			id, job.ID, job.ProfessorName, job.URL)
		s.processJob(id, job)
	}

	logger.Infof("Worker %d stopped", id)
}

func (s *ResearchService) processJob(workerID int, job *ScrapeJob) {
	jobStart := time.Now()
	defer func() {
		duration := time.Since(jobStart).Seconds()
		jobDuration.Observe(duration)
		logger.Infof("[Worker %d] [Job %s] Completed in %.2fs", workerID, job.ID, duration)
	}()

	// 1. Scrape
	logger.Debugf("[Worker %d] [Job %s] Starting scrape phase", workerID, job.ID)
	scrapeStart := time.Now()

	prof := ProfessorProfile{Name: job.ProfessorName, Homepage: job.URL}
	contents, err := s.scraper.ScrapeProfessor(workerID, prof)
	scrapeDuration.Observe(time.Since(scrapeStart).Seconds())

	if err != nil {
		logger.Errorf("[Worker %d] [Job %s] Scrape failed for %s: %v",
			workerID, job.ID, job.ProfessorName, err)
		scrapeErrorsTotal.WithLabelValues("scrape_failure").Inc()
		jobsProcessedTotal.WithLabelValues("failed").Inc()
		s.failJob(job.ID, fmt.Sprintf("scrape_error: %v", err))
		return
	}

	if len(contents) == 0 {
		logger.Warnf("[Worker %d] [Job %s] No content found for %s",
			workerID, job.ID, job.ProfessorName)
		jobsProcessedTotal.WithLabelValues("completed").Inc()
		s.completeJob(job.ID)
		return
	}

	logger.Infof("[Worker %d] [Job %s] Scraped %d pages in %.2fs",
		workerID, job.ID, len(contents), time.Since(scrapeStart).Seconds())

	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("[Worker %d] [Job %s] Failed to get global DB: %v", workerID, job.ID, err)
		jobsProcessedTotal.WithLabelValues("failed").Inc()
		s.failJob(job.ID, fmt.Sprintf("db_error: %v", err))
		return
	}

	// 2. Process Results (Save DB, Embed, Vector DB)
	logger.Debugf("[Worker %d] [Job %s] Processing %d content items", workerID, job.ID, len(contents))
	totalChunks := 0

	for i, content := range contents {
		logger.Debugf("[Worker %d] [Job %s] Processing content %d/%d: %s (type: %s)",
			workerID, job.ID, i+1, len(contents), content.Title, content.ContentType)

		// Validate that the content belongs to the target professor
		if content.ProfessorName != job.ProfessorName {
			logger.Warnf("[Worker %d] [Job %s] Skipping content with mismatched professor name: got '%s', expected '%s'",
				workerID, job.ID, content.ProfessorName, job.ProfessorName)
			continue
		}

		// Save to DB
		if _, err := db.Exec(SERVICE_SAVE_TO_DB_QUERY,
			content.ProfessorName,
			content.URL,
			content.ContentType,
			content.Title,
			content.Content,
			content.ScrapedAt,
		); err != nil {
			logger.Errorf("[Worker %d] [Job %s] Failed to save content to DB: %v", workerID, job.ID, err)
			continue
		}
		pagesScrapedTotal.WithLabelValues(content.ContentType).Inc()

		// Embed with content-aware chunking
		embedStart := time.Now()
		results, err := s.embedder.EmbedContent(content.Content, ContentType(content.ContentType))
		embeddingDuration.Observe(time.Since(embedStart).Seconds())

		if err != nil {
			logger.Errorf("[Worker %d] [Job %s] Failed to embed content: %v", workerID, job.ID, err)
			continue
		}

		embeddingsGeneratedTotal.Add(float64(len(results)))
		chunksProcessedTotal.WithLabelValues(content.ContentType).Add(float64(len(results)))
		logger.Debugf("[Worker %d] [Job %s] Generated %d embeddings for %s",
			workerID, job.ID, len(results), content.Title)

		// Upsert each chunk as a separate vector
		successCount := 0
		for _, result := range results {
			// Generate unique ID: professor_url_chunkIndex
			pointID := fmt.Sprintf("%s_%s_chunk%d",
				s.sanitizeForID(content.ProfessorName),
				s.sanitizeForID(content.URL),
				result.ChunkIndex,
			)

			// Prepare payload with chunk metadata
			payload := map[string]interface{}{
				"professor_name": content.ProfessorName,
				"url":            content.URL,
				"content_type":   string(result.ContentType),
				"title":          content.Title,
				"scraped_at":     content.ScrapedAt.Format(time.RFC3339),

				// Chunk-specific metadata
				"chunk_index":  result.ChunkIndex,
				"total_chunks": result.TotalChunks,
				"chunk_text":   result.Text,
				"token_count":  result.TokenCount,

				// Weight for retrieval scoring
				"weight": result.Weight,
			}

			// Upsert to Qdrant
			qdrantStart := time.Now()
			if err := s.qdrant.Upsert(pointID, result.Embedding, payload); err != nil {
				logger.Errorf("[Worker %d] [Job %s] Failed to upsert chunk %d to Qdrant: %v",
					workerID, job.ID, result.ChunkIndex, err)
				qdrantUpsertsTotal.WithLabelValues("error").Inc()
				continue
			}
			qdrantDuration.Observe(time.Since(qdrantStart).Seconds())
			qdrantUpsertsTotal.WithLabelValues("success").Inc()
			successCount++
		}

		totalChunks += successCount
		logger.Infof("[Worker %d] [Job %s] ✓ Upserted %d/%d chunks for %s (%s)",
			workerID, job.ID, successCount, len(results), content.ProfessorName, content.URL)
	}

	// 3. Complete
	logger.Infof("[Worker %d] [Job %s] ✓ Successfully processed %s: %d pages, %d total chunks",
		workerID, job.ID, job.ProfessorName, len(contents), totalChunks)
	jobsProcessedTotal.WithLabelValues("completed").Inc()
	s.completeJob(job.ID)
}

func (s *ResearchService) sanitizeForID(sid string) string {
	// Remove special characters, keep alphanumeric + underscore
	reg := regexp.MustCompile(`[^a-zA-Z0-9_]+`)
	sanitized := reg.ReplaceAllString(sid, "_")

	// Limit length
	if len(sanitized) > 50 {
		sanitized = sanitized[:50]
	}

	return strings.Trim(sanitized, "_")
}

func (s *ResearchService) Search(query string, limit int) ([]SearchResult, error) {
	searchStart := time.Now()
	defer func() {
		searchDuration.Observe(time.Since(searchStart).Seconds())
		searchesTotal.Inc()
	}()

	logger.Debugf("Search query: %q (limit: %d)", query, limit)

	// Embed query
	embedStart := time.Now()
	queryVec, _, err := s.embedder.Embed(query)
	if err != nil {
		logger.Errorf("Failed to embed search query: %v", err)
		return nil, err
	}
	logger.Debugf("Query embedded in %v", time.Since(embedStart))

	// Search Qdrant (get more results than needed for re-ranking)
	qdrantStart := time.Now()
	points, err := s.qdrant.Search(queryVec, uint64(limit*3))
	if err != nil {
		logger.Errorf("Qdrant search failed: %v", err)
		return nil, err
	}
	logger.Debugf("Qdrant search returned %d points in %v", len(points), time.Since(qdrantStart))

	// Re-rank with content type weights
	results := make([]SearchResult, 0, len(points))
	for _, point := range points {
		// Extract payload fields (with type assertions)
		weight := float32(1.0)
		if w, ok := point.Payload["weight"].(float64); ok {
			weight = cast.ToFloat32(w)
		}

		chunkIndex := 0
		if idx, ok := point.Payload["chunk_index"].(int64); ok {
			chunkIndex = cast.ToInt(idx)
		}

		totalChunks := 1
		if total, ok := point.Payload["total_chunks"].(int64); ok {
			totalChunks = cast.ToInt(total)
		}

		tokenCount := 0
		if tc, ok := point.Payload["token_count"].(int64); ok {
			tokenCount = cast.ToInt(tc)
		}

		professorName := ""
		if pN, ok := point.Payload["professor_name"].(string); ok {
			professorName = cast.ToString(pN)
		}

		url := ""
		if uInterface, ok := point.Payload["url"].(string); ok {
			url = cast.ToString(uInterface)
		}

		title := ""
		if titleInterface, ok := point.Payload["title"].(string); ok {
			title = cast.ToString(titleInterface)
		}

		contentType := ""
		if contentTypeInterface, ok := point.Payload["content_type"].(string); ok {
			contentType = cast.ToString(contentTypeInterface)
		}

		chunkText := ""
		if chunkTextInterface, ok := point.Payload["chunk_text"].(string); ok {
			chunkText = cast.ToString(chunkTextInterface)
		}

		// Apply weight to score
		finalScore := point.Score * weight

		results = append(results, SearchResult{
			ProfessorName: professorName,
			URL:           url,
			Title:         title,
			ContentType:   contentType,
			ChunkText:     chunkText,
			ChunkIndex:    chunkIndex,
			TotalChunks:   totalChunks,
			TokenCount:    tokenCount,
			Score:         finalScore,
			RawScore:      point.Score,
			Weight:        weight,
		})
	}

	// Sort by weighted score
	sort.Slice(results, func(i, j int) bool {
		return results[i].Score > results[j].Score
	})

	// Deduplicate chunks from same document (optional)
	deduped := s.deduplicateByURL(results, limit)

	finalResults := deduped[:min(limit, len(deduped))]
	searchResultsCount.Observe(float64(len(finalResults)))

	logger.Infof("Search completed: %d results in %.2fs (query: %q)",
		len(finalResults), time.Since(searchStart).Seconds(), query)

	return finalResults, nil
}

func (s *ResearchService) deduplicateByURL(results []SearchResult, limit int) []SearchResult {
	seen := make(map[string]bool)
	deduped := []SearchResult{}

	for _, r := range results {
		if !seen[r.URL] {
			seen[r.URL] = true
			deduped = append(deduped, r)

			if len(deduped) >= limit {
				break
			}
		}
	}

	return deduped
}

func (s *ResearchService) completeJob(id string) {
	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("Failed to get global DB: %v", err)
		return
	}

	_, err = db.Exec("UPDATE scrape_queue SET status = 'completed', updated_at = NOW() WHERE id = $1", id)
	if err != nil {
		logger.Errorf("Failed to complete job %s: %v", id, err)
	}
}

func (s *ResearchService) failJob(id, errorMsg string) {
	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("Failed to get global DB: %v", err)
		return
	}

	_, err = db.Exec("UPDATE scrape_queue SET status = 'failed', error_message = $2, updated_at = NOW() WHERE id = $1", id, errorMsg)
	if err != nil {
		logger.Errorf("Failed to fail job %s: %v", id, err)
	}
}

func (s *ResearchService) Close() {
	s.running = false
	s.wg.Wait()
	s.embedder.Close()
	s.qdrant.Close()
}
