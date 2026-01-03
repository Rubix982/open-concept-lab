package main

import (
	"database/sql"
	"fmt"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/sirupsen/logrus"
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
	scraper      *Scraper
	embedder     *Embedder
	qdrant       *QdrantClient
	wg           sync.WaitGroup
	shutdownChan chan struct{} // Signal that the service is shutting down
	shutdownOnce sync.Once     // Ensure shutdown channel is closed exactly once
	idleWorkers  int           // Number of workers currently idle (waiting for jobs)
	workerMu     sync.Mutex    // Protects idleWorkers counter
	totalWorkers int           // Total number of workers
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
		WITH next_job AS (
			SELECT id
			FROM scrape_queue
			WHERE status IN ('pending', 'failed')
			AND attempts < 3
			AND (worker_id IS NULL OR worker_id = $1)  -- Allow retry by same worker
			ORDER BY created_at ASC
			FOR UPDATE SKIP LOCKED
			LIMIT 1
		)
		UPDATE scrape_queue
		SET 
			status = 'processing',
			updated_at = NOW(),
			attempts = attempts + 1,
			last_attempt = NOW(),
			worker_id = $1
		FROM next_job
		WHERE scrape_queue.id = next_job.id
		RETURNING scrape_queue.id, scrape_queue.professor_name, scrape_queue.url;
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
		scraper:      NewScraper(),
		embedder:     embedder,
		qdrant:       qdrant,
		shutdownChan: make(chan struct{}),
	}, nil
}

func (s *ResearchService) workerLoop(id int) {
	defer s.wg.Done()
	defer activeWorkers.Dec()

	activeWorkers.Inc()
	workerID := fmt.Sprintf("worker-%d-%s", id+1, uuid.NewString()[:8])
	logPrefix := fmt.Sprintf("[Worker %d]", id+1)

	logger.WithFields(logrus.Fields{
		"worker_id":  workerID,
		"worker_num": id + 1,
		"component":  "worker_loop",
	})

	logger.Infof("%s - Worker starting up", logPrefix)

	db, err := GetGlobalDB()
	if err != nil {
		logger.WithError(err).Fatalf("%s - Failed to get global DB connection", logPrefix)
		return
	}

	logger.Infof("%s - Database connection established", logPrefix)

	// Worker lifecycle metrics
	var (
		jobsProcessed    int64
		jobsFailed       int64
		totalIdleTime    time.Duration
		lastJobStartTime time.Time
		workerStartTime  = time.Now()
	)

	consecutiveEmptyPolls := 0
	maxEmptyPolls := 3

	logger.WithFields(logrus.Fields{
		"max_empty_polls": maxEmptyPolls,
		"poll_interval":   "2s",
		"error_backoff":   "5s",
	}).Infof("%s - Worker loop configuration set", logPrefix)

	for {
		iterationStart := time.Now()

		// Check for shutdown before processing
		select {
		case <-s.shutdownChan:
			uptime := time.Since(workerStartTime)
			logger.WithFields(logrus.Fields{
				"uptime_sec":      uptime.Seconds(),
				"jobs_processed":  jobsProcessed,
				"jobs_failed":     jobsFailed,
				"total_idle_time": totalIdleTime.String(),
			}).Infof("%s - Worker received shutdown signal, exiting gracefully", logPrefix)
			return
		default:
		}

		// Poll for a job
		pollStart := time.Now()
		job := &ScrapeJob{}

		logger.WithFields(logrus.Fields{
			"claim_query":  "CLAIM_JOB_DB_QUERY",
			"worker_id":    workerID,
			"poll_attempt": consecutiveEmptyPolls + 1,
		}).Tracef("%s - Attempting to claim job from queue", logPrefix)

		err := db.QueryRow(CLAIM_JOB_DB_QUERY, workerID).Scan(&job.ID, &job.ProfessorName, &job.URL)
		pollDuration := time.Since(pollStart)

		if err != nil {
			if err == sql.ErrNoRows {
				// Track idle time
				idleStart := time.Now()

				// Mark this worker as idle
				s.workerMu.Lock()
				s.idleWorkers++
				currentIdle := s.idleWorkers
				totalWorkers := s.totalWorkers
				s.workerMu.Unlock()

				consecutiveEmptyPolls++

				logger.WithFields(logrus.Fields{
					"idle_workers":         currentIdle,
					"total_workers":        totalWorkers,
					"consecutive_polls":    consecutiveEmptyPolls,
					"max_empty_polls":      maxEmptyPolls,
					"poll_duration_ms":     pollDuration.Milliseconds(),
					"jobs_processed_total": jobsProcessed,
				}).Debugf("%s - Queue empty, no jobs available", logPrefix)

				// Check if all workers are idle and we've polled multiple times
				if currentIdle >= totalWorkers && consecutiveEmptyPolls >= maxEmptyPolls {
					logger.WithFields(logrus.Fields{
						"idle_workers":   currentIdle,
						"total_workers":  totalWorkers,
						"empty_polls":    consecutiveEmptyPolls,
						"jobs_processed": jobsProcessed,
						"jobs_failed":    jobsFailed,
						"worker_uptime":  time.Since(workerStartTime).String(),
					}).Infof("%s - All workers idle after max empty polls, initiating graceful shutdown", logPrefix)

					// Signal shutdown to everyone (including main)
					s.shutdownOnce.Do(func() {
						logger.Infof("%s - Worker triggering global shutdown signal", logPrefix)
						close(s.shutdownChan)
					})
					return
				}

				logger.WithFields(logrus.Fields{
					"sleep_duration": "2s",
					"reason":         "queue_empty",
				}).Tracef("%s - Worker entering idle sleep", logPrefix)

				// Sleep before retrying (interruptible)
				select {
				case <-s.shutdownChan:
					s.workerMu.Lock()
					s.idleWorkers--
					s.workerMu.Unlock()

					logger.WithFields(logrus.Fields{
						"jobs_processed": jobsProcessed,
						"jobs_failed":    jobsFailed,
					}).Infof("%s - Worker stopped during idle period", logPrefix)
					return
				case <-time.After(2 * time.Second):
					idleDuration := time.Since(idleStart)
					totalIdleTime += idleDuration

					logger.WithFields(logrus.Fields{
						"idle_duration_ms": idleDuration.Milliseconds(),
						"total_idle_time":  totalIdleTime.String(),
					}).Tracef("%s - Worker woke from idle sleep", logPrefix)
				}

				s.workerMu.Lock()
				s.idleWorkers--
				s.workerMu.Unlock()

				continue
			}

			// Non-ErrNoRows error
			logger.WithFields(logrus.Fields{
				"error":            err.Error(),
				"poll_duration_ms": pollDuration.Milliseconds(),
			}).Errorf("%s - Failed to claim job from queue", logPrefix)

			// Sleep on error (interruptible)
			logger.WithField("backoff_duration", "5s").Warnf("%s - Entering error backoff", logPrefix)

			select {
			case <-s.shutdownChan:
				logger.Infof("%s - Worker stopped during error backoff", logPrefix)
				return
			case <-time.After(5 * time.Second):
				logger.Debugf("%s - Worker resuming after error backoff", logPrefix)
				continue
			}
		}

		// Job claimed successfully
		consecutiveEmptyPolls = 0
		jobsProcessed++
		lastJobStartTime = time.Now()

		logger.WithFields(logrus.Fields{
			"job_id":           job.ID,
			"professor_name":   job.ProfessorName,
			"url":              job.URL,
			"poll_duration_ms": pollDuration.Milliseconds(),
			"claim_timestamp":  lastJobStartTime.Format(time.RFC3339),
		}).Infof("%s - Job claimed successfully", logPrefix)

		// Verify exclusive lock (debugging)
		var lockCheck int
		lockCheckStart := time.Now()
		err = db.QueryRow(`
			SELECT COUNT(*) FROM scrape_queue 
			WHERE id = $1 AND status = 'processing'
		`, job.ID).Scan(&lockCheck)

		lockCheckDuration := time.Since(lockCheckStart)

		if err != nil {
			logger.WithFields(logrus.Fields{
				"job_id": job.ID,
				"error":  err.Error(),
			}).Warnf("%s - Lock verification query failed", logPrefix)
		} else if lockCheck != 1 {
			logger.WithFields(logrus.Fields{
				"job_id":         job.ID,
				"lock_count":     lockCheck,
				"expected":       1,
				"professor_name": job.ProfessorName,
				"url":            job.URL,
				"worker_id":      workerID,
			}).Error("🚨 LOCK VIOLATION DETECTED! Job claimed by multiple workers")

			jobsFailed++
			continue // Skip processing this job
		} else {
			logger.WithFields(logrus.Fields{
				"job_id":                 job.ID,
				"lock_check_duration_ms": lockCheckDuration.Milliseconds(),
			}).Trace("Lock verification passed")
		}

		// Process the job
		logger.WithFields(logrus.Fields{
			"job_id":         job.ID,
			"professor_name": job.ProfessorName,
			"url":            job.URL,
		}).Infof("%s - Starting job processing", logPrefix)

		processingStart := time.Now()
		s.processJob(id, job)
		processingDuration := time.Since(processingStart)

		logger.WithFields(logrus.Fields{
			"job_id":              job.ID,
			"professor_name":      job.ProfessorName,
			"processing_time_sec": processingDuration.Seconds(),
			"total_iteration_ms":  time.Since(iterationStart).Milliseconds(),
			"jobs_processed":      jobsProcessed,
		}).Infof("%s - Job processing completed", logPrefix)

		// Check job outcome
		var finalStatus string
		db.QueryRow(`SELECT status FROM scrape_queue WHERE id = $1`, job.ID).Scan(&finalStatus)

		logger.WithFields(logrus.Fields{
			"job_id":       job.ID,
			"final_status": finalStatus,
		}).Debugf("%s - Job final status recorded", logPrefix)

		if finalStatus == "failed" {
			jobsFailed++
		}
	}
}

func (s *ResearchService) processJob(workerID int, job *ScrapeJob) {
	jobStart := time.Now()
	defer func() {
		duration := time.Since(jobStart).Seconds()
		jobDuration.Observe(duration)
		logger.Infof("[Worker %d] [Job %s] Job completed in %.2fs", workerID, job.ID, duration)
	}()

	logger.Infof("[Worker %d] [Job %s] 🚀 Starting job for professor: %s", workerID, job.ID, job.ProfessorName)

	// ============================================================================
	// PHASE 0: Check Pre-existing Data
	// ============================================================================
	logger.Debugf("[Worker %d] [Job %s] Phase 0: Checking for existing data", workerID, job.ID)

	existingContents, err := s.fetchContentFromDB(job.ProfessorName)
	if err != nil {
		logger.Warnf("[Worker %d] [Job %s] Failed to check DB for existing content: %v", workerID, job.ID, err)
	}

	dataFoundInDB := len(existingContents) > 0
	dataFoundInQdrant := false

	if dataFoundInDB {
		logger.Debugf("[Worker %d] [Job %s] Found %d existing content items in DB", workerID, job.ID, len(existingContents))
		hasEmbeddings, err := s.qdrant.HasEmbeddings(job.ProfessorName)
		if err != nil {
			logger.Warnf("[Worker %d] [Job %s] Failed to check Qdrant for existing embeddings: %v", workerID, job.ID, err)
		} else {
			dataFoundInQdrant = hasEmbeddings
			if hasEmbeddings {
				logger.Debugf("[Worker %d] [Job %s] Found existing embeddings in Qdrant", workerID, job.ID)
			}
		}
	} else {
		logger.Debugf("[Worker %d] [Job %s] No existing data found in DB", workerID, job.ID)
	}

	// Case 3: Data fully present
	if dataFoundInDB && dataFoundInQdrant {
		logger.Infof("[Worker %d] [Job %s] ✅ Data already complete (DB: %d items, Qdrant: ✓). Skipping.",
			workerID, job.ID, len(existingContents))
		jobsProcessedTotal.WithLabelValues("completed").Inc()
		s.completeJob(job.ID)
		return
	}

	var contents []ScrapedContent

	// ============================================================================
	// PHASE 1: Scrape or Load from DB
	// ============================================================================
	// Case 2: Data in DB but missing in Qdrant (Recovery)
	if dataFoundInDB && !dataFoundInQdrant {
		logger.Infof("[Worker %d] [Job %s] 🔄 Recovery mode: DB has %d items, Qdrant missing. Loading from DB.",
			workerID, job.ID, len(existingContents))
		contents = existingContents
	} else {
		// Case 1: New Job or Data missing (Scrape)
		logger.Infof("[Worker %d] [Job %s] Phase 1: Starting fresh scrape for %s",
			workerID, job.ID, job.ProfessorName)
		scrapeStart := time.Now()

		prof := ProfessorProfile{Name: job.ProfessorName, Homepage: job.URL}
		scrapedContents, err := s.scraper.ScrapeProfessor(workerID, prof)
		duration := time.Since(scrapeStart).Seconds()
		scrapeDuration.Observe(duration)

		if err != nil {
			if strings.Contains(err.Error(), "no content extracted") {
				logger.Warnf("[Worker %d] [Job %s] ⚠️  No content available for %s (empty result)",
					workerID, job.ID, job.ProfessorName)
				jobsProcessedTotal.WithLabelValues("completed").Inc()
				s.completeJob(job.ID)
				return
			}
			logger.Errorf("[Worker %d] [Job %s] ❌ Scrape failed after %.2fs: %v",
				workerID, job.ID, duration, err)
			scrapeErrorsTotal.WithLabelValues("scrape_failure").Inc()
			jobsProcessedTotal.WithLabelValues("failed").Inc()
			s.failJob(job.ID, fmt.Sprintf("scrape_error: %v", err))
			return
		}

		contents = scrapedContents
		logger.Infof("[Worker %d] [Job %s] ✓ Scrape completed: %d pages in %.2fs",
			workerID, job.ID, len(contents), duration)
	}

	if len(contents) == 0 {
		logger.Warnf("[Worker %d] [Job %s] ⚠️  No content available for %s (empty result)",
			workerID, job.ID, job.ProfessorName)
		jobsProcessedTotal.WithLabelValues("completed").Inc()
		s.completeJob(job.ID)
		return
	}

	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("[Worker %d] [Job %s] ❌ Failed to get DB connection: %v", workerID, job.ID, err)
		jobsProcessedTotal.WithLabelValues("failed").Inc()
		s.failJob(job.ID, fmt.Sprintf("db_connection_error: %v", err))
		return
	}

	// ============================================================================
	// PHASE 2: Process Content (DB → Embed → Qdrant)
	// ============================================================================
	logger.Infof("[Worker %d] [Job %s] Phase 2: Processing %d content items", workerID, job.ID, len(contents))

	// Track failures
	var (
		totalChunks       = 0
		dbFailures        = 0
		embeddingFailures = 0
		qdrantFailures    = 0
		contentProcessed  = 0
	)

	for i, content := range contents {
		contentStart := time.Now()
		logger.Debugf("[Worker %d] [Job %s] [%d/%d] Processing: %s (type: %s, url: %s)",
			workerID, job.ID, i+1, len(contents), content.Title, content.ContentType, content.URL)

		// Validate professor name
		if content.ProfessorName != job.ProfessorName {
			logger.Warnf("[Worker %d] [Job %s] [%d/%d] ⚠️  Name mismatch: got '%s', expected '%s'. Skipping.",
				workerID, job.ID, i+1, len(contents), content.ProfessorName, job.ProfessorName)
			continue
		}

		// --- Step 2.1: Save to DB ---
		if _, err := db.Exec(SERVICE_SAVE_TO_DB_QUERY,
			content.ProfessorName,
			content.URL,
			content.ContentType,
			content.Title,
			content.Content,
			content.ScrapedAt,
		); err != nil {
			logger.Errorf("[Worker %d] [Job %s] [%d/%d] ❌ DB insert failed: %v",
				workerID, job.ID, i+1, len(contents), err)
			dbFailures++
			continue // Skip embedding if DB fails
		}
		pagesScrapedTotal.WithLabelValues(content.ContentType).Inc()
		logger.Debugf("[Worker %d] [Job %s] [%d/%d] ✓ Saved to DB", workerID, job.ID, i+1, len(contents))

		// --- Step 2.2: Generate Embeddings ---
		embedStart := time.Now()
		results, err := s.embedder.EmbedContent(content.Content, ContentType(content.ContentType))
		embedDuration := time.Since(embedStart).Seconds()
		embeddingDuration.Observe(embedDuration)

		if err != nil {
			logger.Errorf("[Worker %d] [Job %s] [%d/%d] ❌ Embedding failed after %.2fs: %v",
				workerID, job.ID, i+1, len(contents), embedDuration, err)
			embeddingFailures++
			continue // Skip Qdrant if embedding fails
		}

		embeddingsGeneratedTotal.Add(float64(len(results)))
		chunksProcessedTotal.WithLabelValues(content.ContentType).Add(float64(len(results)))
		logger.Debugf("[Worker %d] [Job %s] [%d/%d] ✓ Generated %d embeddings in %.2fs",
			workerID, job.ID, i+1, len(contents), len(results), embedDuration)

		// --- Step 2.3: Upsert to Qdrant ---
		successCount := 0
		chunkFailures := 0

		for _, result := range results {
			pointID := fmt.Sprintf("%s_%s_chunk%d",
				s.sanitizeForID(content.ProfessorName),
				s.sanitizeForID(content.URL),
				result.ChunkIndex,
			)

			payload := map[string]interface{}{
				"identifier":     pointID,
				"professor_name": content.ProfessorName,
				"url":            content.URL,
				"content_type":   string(result.ContentType),
				"title":          content.Title,
				"scraped_at":     content.ScrapedAt.Format(time.RFC3339),
				"chunk_index":    result.ChunkIndex,
				"total_chunks":   result.TotalChunks,
				"chunk_text":     result.Text,
				"token_count":    result.TokenCount,
				"weight":         result.Weight,
			}

			qdrantStart := time.Now()
			if err := s.qdrant.Upsert(uuid.New().String(), result.Embedding, payload); err != nil {
				logger.Errorf("[Worker %d] [Job %s] [%d/%d] ❌ Qdrant upsert failed for chunk %d: %v",
					workerID, job.ID, i+1, len(contents), result.ChunkIndex, err)
				qdrantUpsertsTotal.WithLabelValues("error").Inc()
				chunkFailures++
				continue
			}
			qdrantDuration.Observe(time.Since(qdrantStart).Seconds())
			qdrantUpsertsTotal.WithLabelValues("success").Inc()
			successCount++
		}

		totalChunks += successCount
		qdrantFailures += chunkFailures

		contentDuration := time.Since(contentStart).Seconds()

		if chunkFailures > 0 {
			logger.Warnf("[Worker %d] [Job %s] [%d/%d] ⚠️  Partial success: %d/%d chunks in %.2fs (%s)",
				workerID, job.ID, i+1, len(contents), successCount, len(results), contentDuration, content.URL)
		} else {
			logger.Infof("[Worker %d] [Job %s] [%d/%d] ✅ Complete: %d chunks in %.2fs (%s)",
				workerID, job.ID, i+1, len(contents), successCount, contentDuration, content.Title)
		}

		contentProcessed++
	}

	// ============================================================================
	// PHASE 3: Final Decision
	// ============================================================================
	totalContent := len(contents)
	totalFailures := dbFailures + embeddingFailures + qdrantFailures

	logger.Infof("[Worker %d] [Job %s] Phase 3: Processing summary", workerID, job.ID)
	logger.Infof("[Worker %d] [Job %s]   Content: %d/%d processed", workerID, job.ID, contentProcessed, totalContent)
	logger.Infof("[Worker %d] [Job %s]   Chunks: %d successfully upserted", workerID, job.ID, totalChunks)
	logger.Infof("[Worker %d] [Job %s]   Failures: DB=%d, Embedding=%d, Qdrant=%d (total=%d)",
		workerID, job.ID, dbFailures, embeddingFailures, qdrantFailures, totalFailures)

	// Decision logic
	if contentProcessed == 0 {
		logger.Errorf("[Worker %d] [Job %s] ❌ FAILED: Zero content processed", workerID, job.ID)
		jobsProcessedTotal.WithLabelValues("failed").Inc()
		s.failJob(job.ID, fmt.Sprintf("no_content_processed: db=%d, embedding=%d, qdrant=%d",
			dbFailures, embeddingFailures, qdrantFailures))
		return
	}

	if dbFailures > 0 || embeddingFailures > 0 {
		logger.Errorf("[Worker %d] [Job %s] ❌ FAILED: Critical failures detected (DB=%d, Embedding=%d)",
			workerID, job.ID, dbFailures, embeddingFailures)
		jobsProcessedTotal.WithLabelValues("failed").Inc()
		s.failJob(job.ID, fmt.Sprintf("critical_failures: db=%d, embedding=%d, qdrant=%d",
			dbFailures, embeddingFailures, qdrantFailures))
		return
	}

	if qdrantFailures > 0 {
		failureRate := float64(qdrantFailures) / float64(totalChunks+qdrantFailures)
		if failureRate > 0.2 {
			logger.Errorf("[Worker %d] [Job %s] ❌ FAILED: High Qdrant failure rate %.1f%% (%d/%d chunks)",
				workerID, job.ID, failureRate*100, qdrantFailures, totalChunks+qdrantFailures)
			jobsProcessedTotal.WithLabelValues("failed").Inc()
			s.failJob(job.ID, fmt.Sprintf("high_qdrant_failure_rate: %.1f%% (%d/%d chunks)",
				failureRate*100, qdrantFailures, totalChunks+qdrantFailures))
			return
		}

		logger.Warnf("[Worker %d] [Job %s] ⚠️  COMPLETED with warnings: %.1f%% Qdrant failures (%d/%d chunks)",
			workerID, job.ID, failureRate*100, qdrantFailures, totalChunks+qdrantFailures)
	}

	logger.Infof("[Worker %d] [Job %s] ✅ SUCCESS: Processed %s (%d pages, %d chunks)",
		workerID, job.ID, job.ProfessorName, contentProcessed, totalChunks)
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

// Helper to fetch existing content from DB
func (s *ResearchService) fetchContentFromDB(professorName string) ([]ScrapedContent, error) {
	db, err := GetGlobalDB()
	if err != nil {
		return nil, err
	}

	// We verify that we are fetching content for the correct professor
	rows, err := db.Query(`
		SELECT professor_name, url, content_type, title, content, scraped_at 
		FROM scraped_content 
		WHERE professor_name = $1
	`, professorName)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var contents []ScrapedContent
	for rows.Next() {
		var c ScrapedContent
		if err := rows.Scan(&c.ProfessorName, &c.URL, &c.ContentType, &c.Title, &c.Content, &c.ScrapedAt); err != nil {
			return nil, err
		}
		contents = append(contents, c)
	}
	return contents, nil
}

func (s *ResearchService) failJob(id, errorMsg string) error {
	logPrefix := fmt.Sprintf("[FailJob %s] -", id)
	db, err := GetGlobalDB()
	if err != nil {
		logger.Errorf("%s Failed to get global DB: %v", logPrefix, err)
		return fmt.Errorf("%s failed to get db: %w", logPrefix, err)
	}

	const maxRetries = 3

	// Atomic update with RETURNING to check retry limit
	var newAttempts int
	err = db.QueryRow(`
		UPDATE scrape_queue 
		SET 
			status = CASE 
				WHEN attempts + 1 >= $2 THEN 'permanent_failure'
				ELSE 'failed'
			END,
			error_message = $3,
			updated_at = NOW(),
			attempts = attempts + 1
		WHERE id = $1
		RETURNING attempts
	`, id, maxRetries, errorMsg).Scan(&newAttempts)

	if err != nil {
		if err == sql.ErrNoRows {
			logger.Errorf("%s job not found in scrape_queue", logPrefix)
			return fmt.Errorf("job not found: %s", id)
		}
		logger.Errorf("%s failed to update job: %v", logPrefix, err)
		return fmt.Errorf("update job: %w", err)
	}

	if newAttempts >= maxRetries {
		logger.Warnf("%s job permanently failed after %d attempts: %s", logPrefix, newAttempts, errorMsg)
	} else {
		logger.Infof("%s job marked as failed (attempt %d/%d): %s", logPrefix, newAttempts, maxRetries, errorMsg)
	}

	return nil
}

func (s *ResearchService) Close() {
	s.shutdownOnce.Do(func() {
		close(s.shutdownChan)
	})
	s.wg.Wait()
	s.embedder.Close()
	s.qdrant.Close()
	s.scraper.Close()
}
