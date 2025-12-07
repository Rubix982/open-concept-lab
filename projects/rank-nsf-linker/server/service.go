package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

type ResearchService struct {
	scraper      *Scraper
	embedder     *Embedder
	qdrant       *QdrantClient
	resultsChan  chan ScrapedContent
	wg           sync.WaitGroup
	processedCnt atomic.Int32
	itemsCnt     atomic.Int32
}

func NewResearchService() (*ResearchService, error) {
	embedder, err := NewEmbedder()
	if err != nil {
		return nil, fmt.Errorf("failed to init embedder: %w", err)
	}

	qdrant, err := NewQdrantClient()
	if err != nil {
		embedder.Close()
		return nil, fmt.Errorf("failed to init qdrant: %w", err)
	}

	// Ensure collection exists (384 dim for all-MiniLM-L6-v2)
	if err := qdrant.EnsureCollection(384); err != nil {
		embedder.Close()
		qdrant.Close()
		return nil, fmt.Errorf("failed to ensure collection: %w", err)
	}

	return &ResearchService{
		scraper:     NewScraper(),
		embedder:    embedder,
		qdrant:      qdrant,
		resultsChan: make(chan ScrapedContent, 100), // Buffer
	}, nil
}

func (s *ResearchService) StartWorkerPool(workers int) {
	for i := range workers {
		s.wg.Add(1)
		go s.worker(i)
	}
}

func (s *ResearchService) worker(id int) {
	defer s.wg.Done()
	for content := range s.resultsChan {
		if err := s.saveToDB(content); err != nil {
			logger.Errorf("Worker %d: Failed to save to DB: %v", id, err)
			// Continue anyway
		}

		vector, err := s.embedder.Embed(content.Content)
		if err != nil {
			logger.Errorf("Worker %d: Failed to embed content from %s: %v", id, content.URL, err)
			continue
		}

		payload := map[string]string{
			"professor_name":  content.ProfessorName,
			"url":             content.URL,
			"title":           content.Title,
			"content_type":    content.ContentType,
			"scraped_at":      content.ScrapedAt.String(),
			"content_snippet": content.Content[:min(len(content.Content), 200)], // Snippet
		}

		// Use URL as naive ID seed or random
		if err := s.qdrant.Upsert("", vector, payload); err != nil {
			logger.Errorf("Worker %d: Failed to index %s: %v", id, content.URL, err)
			continue
		}

		s.itemsCnt.Add(1)
		if s.itemsCnt.Load()%10 == 0 {
			logger.Infof("Indexed %d items so far...", s.itemsCnt.Load())
		}
	}
}

func (s *ResearchService) ProcessProfessors(profs []ProfessorProfile) {
	// Start workers if not already (or we can just start here)
	s.StartWorkerPool(4)

	// Create a semaphore to limit concurrent professors being scraped
	sem := make(chan struct{}, 10)
	var scrapeWg sync.WaitGroup

	for _, prof := range profs {
		scrapeWg.Add(1)
		sem <- struct{}{} // Acquire

		go func(p ProfessorProfile) {
			defer scrapeWg.Done()
			defer func() { <-sem }() // Release

			contents, err := s.scraper.ScrapeProfessor(p)
			if err != nil {
				logger.Warnf("Failed to scrape %s: %v", p.Name, err)
				return
			}

			for _, c := range contents {
				s.resultsChan <- c
			}
			s.processedCnt.Add(1)
		}(prof)
	}

	scrapeWg.Wait()
	close(s.resultsChan) // Signal workers to stop
	s.wg.Wait()          // Wait for workers

	logger.Infof("✅ Completed research pipeline. Processed %d professors, indexed %d items.",
		s.processedCnt.Load(), s.itemsCnt.Load())
}

func (s *ResearchService) Close() {
	s.embedder.Close()
	s.qdrant.Close()
}

func (s *ResearchService) saveToDB(c ScrapedContent) error {
	query := `
		INSERT INTO scraped_content (professor_name, url, content_type, title, content, scraped_at, embedding_generated)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (professor_name, url) DO UPDATE SET
			content = EXCLUDED.content,
			last_updated = NOW(),
			embedding_generated = EXCLUDED.embedding_generated
	`
	_, err := globalDB.Exec(query, c.ProfessorName, c.URL, c.ContentType, c.Title, c.Content, c.ScrapedAt, true)
	return err
}
