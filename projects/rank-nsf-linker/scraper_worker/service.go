package scraperworker

import (
	"fmt"
	"sync"
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
