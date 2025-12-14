package scraperworker

import (
	"database/sql"
	"fmt"
	"regexp"
	"sort"
	"strings"
	"regexp"
	"sort"
	"strings"
	"sync"
	"time"

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

// Optional: Helper to check if this is the main/first chunk
func (r *SearchResult) IsMainChunk() bool {
	return r.ChunkIndex == 0
}

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

// Optional: Helper to check if this is the main/first chunk
func (r *SearchResult) IsMainChunk() bool {
	return r.ChunkIndex == 0
}

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
	SERVICE_SAVE_TO_DB_QUERY = `
		UPDATE scrape_queue
		SET status = 'processing', updated_at = NOW(), attempts = attempts + 1, last_attempt = NOW()
		WHERE id = (
			SELECT id
			FROM scrape_queue
			WHERE status = 'pending'
			-- TODO: OR (status = 'processing' AND last_attempt < NOW() - INTERVAL '10 minutes') -- Recover stuck jobs, commented out, will test later
			ORDER BY created_at ASC
			FOR UPDATE SKIP LOCKED
			LIMIT 1
		)
		RETURNING id, professor_name, url;
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

func (s *ResearchService) workerLoop(id int) {
	defer s.wg.Done()
	logger.Debugf("Worker %d started", id)

	for s.running {
		// Poll for a job
		job := &ScrapeJob{}
		err := globalDB.QueryRow(CLAIM_JOB_DB_QUERY).Scan(&job.ID, &job.ProfessorName, &job.URL)
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
		if _, err := globalDB.Exec(SERVICE_SAVE_TO_DB_QUERY,
			content.ProfessorName,
			content.URL,
			content.ContentType,
			content.Title,
			content.Content,
			content.ScrapedAt,
		); err != nil {
			logger.Errorf("Failed to save content: %v", err)
			continue
		}

		// Embed with content-aware chunking
		results, err := s.embedder.EmbedContent(content.Content, ContentType(content.ContentType))
		// Embed with content-aware chunking
		results, err := s.embedder.EmbedContent(content.Content, ContentType(content.ContentType))
		if err != nil {
			logger.Errorf("Failed to embed: %v", err)
			continue
		}

		// Upsert each chunk as a separate vector
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
			if err := s.qdrant.Upsert(pointID, result.Embedding, payload); err != nil {
				logger.Errorf("Failed to upsert chunk %d to Qdrant: %v", result.ChunkIndex, err)
				continue
			}
		}

		logger.Infof("✓ Upserted %d chunks for %s (%s)",
			len(results), content.ProfessorName, content.URL)
		// Upsert each chunk as a separate vector
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
			if err := s.qdrant.Upsert(pointID, result.Embedding, payload); err != nil {
				logger.Errorf("Failed to upsert chunk %d to Qdrant: %v", result.ChunkIndex, err)
				continue
			}
		}

		logger.Infof("✓ Upserted %d chunks for %s (%s)",
			len(results), content.ProfessorName, content.URL)
	}

	// 3. Complete
	logger.Infof("Worker %d: Successfully processed %s (%d items)", workerID, job.ProfessorName, len(contents))
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
	// Embed query
	queryVec, _, err := s.embedder.Embed(query)
	if err != nil {
		return nil, err
	}

	// Search Qdrant (get more results than needed for re-ranking)
	points, err := s.qdrant.Search(queryVec, uint64(limit*3))
	if err != nil {
		return nil, err
	}

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

	return deduped[:min(limit, len(deduped))], nil
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
