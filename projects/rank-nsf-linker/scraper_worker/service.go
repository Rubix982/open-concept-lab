package scraperworker

import (
	"database/sql"
	"fmt"
	"sync"
	"time"
)

type ResearchService struct {
	scraper  *Scraper
	embedder *Embedder
	qdrant   *QdrantClient
	wg       sync.WaitGroup
	running  bool
}

func NewResearchService() (*ResearchService, error) {
	embedder, err := NewEmbedder()
	if err != nil {
		return nil, fmt.Errorf("failed to init embedder: %w", err)
	}

	qdrant, err := NewQdrantClient()
	if err != nil {
		embedder.Close() // Cleanup
		return nil, fmt.Errorf("failed to init qdrant: %w", err)
	}

	// Ensure collection exists (384 dim for all-MiniLM-L6-v2)
	if err := qdrant.EnsureCollection(384); err != nil {
		embedder.Close()
		qdrant.Close()
		return nil, fmt.Errorf("failed to ensure collection: %w", err)
	}

	return &ResearchService{
		scraper:  NewScraper(),
		embedder: embedder,
		qdrant:   qdrant,
		running:  true,
	}, nil
}

// StartQueueProcessor starts multiple workers to poll the DB queue
func (s *ResearchService) StartQueueProcessor() {
	logger.Infof("🚀 Starting %d queue workers", WORKER_COUNT)
	for i := range WORKER_COUNT {
		s.wg.Add(1)
		go s.workerLoop(i)
	}
}

func (s *ResearchService) workerLoop(id int) {
	defer s.wg.Done()
	logger.Debugf("Worker %d started", id)

	for s.running {
		// Poll for a job
		job, err := s.claimJob()
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

		logger.Infof("Worker %d: Processing %s (%s)", id, job.ProfessorName, job.URL)
		s.processJob(id, job)
	}
}

type ScrapeJob struct {
	ID            string
	ProfessorName string
	URL           string
}

func (s *ResearchService) claimJob() (*ScrapeJob, error) {
	var job ScrapeJob

	// Postgres FIFO Queue with SKIP LOCKED for concurrency safety
	query := `
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

	err := globalDB.QueryRow(query).Scan(&job.ID, &job.ProfessorName, &job.URL)
	return &job, err
}

func (s *ResearchService) processJob(workerID int, job *ScrapeJob) {
	// 1. Scrape
	prof := ProfessorProfile{Name: job.ProfessorName, Homepage: job.URL}
	contents, err := s.scraper.ScrapeProfessor(prof)
	if err != nil {
		logger.Errorf("Worker %d: Failed to scrape %s: %v", workerID, job.ProfessorName, err)
		s.failJob(job.ID, err.Error())
		return
	}

	if len(contents) == 0 {
		logger.Warnf("Worker %d: No content found for %s", workerID, job.ProfessorName)
		s.completeJob(job.ID) // Mark complete anyway to avoid infinite retries
		return
	}

	// 2. Process Results (Save DB, Embed, Vector DB)
	for _, content := range contents {
		// Save to Postgres
		if err := s.saveToDB(content); err != nil {
			logger.Errorf("Failed to save content: %v", err)
			continue
		}

		// Embed
		vector, err := s.embedder.Embed(content.Content)
		if err != nil {
			logger.Errorf("Failed to embed: %v", err)
			continue
		}

		// Upsert to Qdrant
		payload := map[string]string{
			"professor_name":  content.ProfessorName,
			"url":             content.URL,
			"content_type":    content.ContentType,
			"title":           content.Title,
			"content_snippet": content.Content, // Qdrant might truncate large payloads, check limits
			"scraped_at":      content.ScrapedAt.Format(time.RFC3339),
		}

		// Truncate snippet for payload if too long (vectors capture the semantic meaning)
		if len(content.Content) > 1000 {
			payload["content_snippet"] = content.Content[:1000] + "..."
		}

		if err := s.qdrant.Upsert("", vector, payload); err != nil {
			logger.Errorf("Failed to upsert to Qdrant: %v", err)
		}
	}

	// 3. Complete
	logger.Infof("Worker %d: Successfully processed %s (%d items)", workerID, job.ProfessorName, len(contents))
	s.completeJob(job.ID)
}

func (s *ResearchService) completeJob(id string) {
	_, err := globalDB.Exec("UPDATE scrape_queue SET status = 'completed', updated_at = NOW() WHERE id = $1", id)
	if err != nil {
		logger.Errorf("Failed to complete job %s: %v", id, err)
	}
}

func (s *ResearchService) failJob(id, errorMsg string) {
	_, err := globalDB.Exec("UPDATE scrape_queue SET status = 'failed', error_message = $2, updated_at = NOW() WHERE id = $1", id, errorMsg)
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

func (s *ResearchService) saveToDB(content ScrapedContent) error {
	query := `
		INSERT INTO scraped_content (professor_name, url, content_type, title, content, scraped_at, embedding_generated)
		VALUES ($1, $2, $3, $4, $5, $6, TRUE)
		ON CONFLICT (professor_name, url)
		DO UPDATE SET
			content = EXCLUDED.content,
			title = EXCLUDED.title,
			scraped_at = EXCLUDED.scraped_at,
			embedding_generated = TRUE;
	`
	_, err := globalDB.Exec(query,
		content.ProfessorName,
		content.URL,
		content.ContentType,
		content.Title,
		content.Content,
		content.ScrapedAt,
	)
	return err
}
