package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"
)

const (
	MINILM_L6_V2_ONNX_MODEL_DIM_OUT    = 384
	MINILM_L6_V2_ONNX_MODEL_MAX_TOKENS = 128
)

var (
	// Get embedder service URL from environment
	embedderServiceURL = getEnv("EMBEDDER_SERVICE_URL", "http://embedder:8000")
)

// ContentTypeWeight defines importance multipliers for retrieval
var ContentTypeWeight = map[ContentType]float32{
	ContentPublication: 2.0,
	ContentProject:     1.8,
	ContentCode:        1.6,
	ContentDataset:     1.6,
	ContentTalk:        1.4,
	ContentTeaching:    1.2,
	ContentStudents:    1.0,
	ContentAward:       1.0,
	ContentNews:        0.8,
	ContentBiography:   0.6,
	ContentHomepage:    0.5,
}

type EmbeddingResult struct {
	Embedding   []float32
	ContentType ContentType
	ChunkIndex  int
	TotalChunks int
	Weight      float32
	Text        string
	TokenCount  int
}

type Embedder struct {
	httpClient *http.Client
	baseURL    string
}

// --- API Request/Response Types ---

type embedRequest struct {
	Text string `json:"text"`
}

type embedResponse struct {
	Status     string    `json:"status"`
	Embedding  []float32 `json:"embedding"`
	TokenCount int       `json:"token_count"`
	Dimension  int       `json:"dimension"`
	LatencyMs  float64   `json:"latency_ms,omitempty"`
}

type batchEmbedRequest struct {
	Texts []string `json:"texts"`
}

type batchEmbedResponse struct {
	Status      string      `json:"status"`
	Embeddings  [][]float32 `json:"embeddings"`
	TokenCounts []int       `json:"token_counts"`
	Dimension   int         `json:"dimension"`
	Count       int         `json:"count"`
	LatencyMs   float64     `json:"latency_ms,omitempty"`
}

type contentEmbedRequest struct {
	Text        string `json:"text"`
	ContentType string `json:"content_type"`
	Chunk       bool   `json:"chunk"`
}

type contentEmbedResult struct {
	Embedding   []float32 `json:"embedding"`
	ContentType string    `json:"content_type"`
	ChunkIndex  int       `json:"chunk_index"`
	TotalChunks int       `json:"total_chunks"`
	Weight      float32   `json:"weight"`
	Text        string    `json:"text"`
	TokenCount  int       `json:"token_count"`
}

type contentEmbedResponse struct {
	Status      string               `json:"status"`
	Results     []contentEmbedResult `json:"results"`
	TotalChunks int                  `json:"total_chunks"`
	Dimension   int                  `json:"dimension"`
	LatencyMs   float64              `json:"latency_ms,omitempty"`
}

// --- Embedder Implementation ---

func NewEmbedder() (*Embedder, error) {
	client := &http.Client{
		Timeout: 60 * time.Second, // Longer timeout for batch operations
		Transport: &http.Transport{
			MaxIdleConns:        100,
			MaxIdleConnsPerHost: 10,
			IdleConnTimeout:     90 * time.Second,
		},
	}

	embedder := &Embedder{
		httpClient: client,
		baseURL:    embedderServiceURL,
	}

	// Health check with retries
	maxRetries := 10
	retryDelay := 30 * time.Second

	logger.Infof("Connecting to embedder service at %s...", embedderServiceURL)

	for i := 0; i < maxRetries; i++ {
		resp, err := client.Get(embedder.baseURL + "/health")
		if err == nil && resp.StatusCode == 200 {
			resp.Body.Close()

			// Parse health response for info
			var healthResp map[string]interface{}
			resp, _ = client.Get(embedder.baseURL + "/health")
			if resp != nil {
				json.NewDecoder(resp.Body).Decode(&healthResp)
				resp.Body.Close()

				if model, ok := healthResp["model"].(string); ok {
					logger.Infof("✓ Embedder service connected")
					logger.Infof("  Model: %s", model)
					logger.Infof("  Dimension: %.0f", healthResp["embedding_dim"])
					logger.Infof("  Max tokens: %.0f", healthResp["max_tokens"])
				}
			}

			return embedder, nil
		}

		if resp != nil {
			resp.Body.Close()
		}

		logger.Warnf("Embedder service not ready (attempt %d/%d), retrying in %v...",
			i+1, maxRetries, retryDelay)
		time.Sleep(retryDelay)
	}

	return nil, fmt.Errorf("embedder service not reachable after %d attempts", maxRetries)
}

// postWithRetry handles HTTP POST requests with exponential backoff and retries
func (e *Embedder) postWithRetry(endpoint string, reqBody interface{}, respDest interface{}) error {
	maxRetries := 5
	baseDelay := 1 * time.Second
	var lastErr error

	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %w", err)
	}

	for i := 0; i < maxRetries; i++ {
		// Calculate current delay with exponential backoff
		delay := baseDelay * time.Duration(1<<uint(i))

		resp, err := e.httpClient.Post(
			e.baseURL+endpoint,
			"application/json",
			bytes.NewBuffer(jsonData),
		)

		if err != nil {
			lastErr = err
			logger.Warnf("Embedder request failed (attempt %d/%d): %v. Retrying in %v...",
				i+1, maxRetries, err, delay)
			time.Sleep(delay)
			continue
		}

		// Check status code
		if resp.StatusCode != 200 {
			var errorResp map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&errorResp)
			resp.Body.Close()

			errMsg := fmt.Sprintf("status %d", resp.StatusCode)
			if msg, ok := errorResp["message"].(string); ok {
				errMsg += ": " + msg
			}

			// Don't retry on client errors (4xx), only server errors (5xx)
			if resp.StatusCode >= 400 && resp.StatusCode < 500 {
				return fmt.Errorf("embedder returned %s", errMsg)
			}

			lastErr = fmt.Errorf("embedder returned %s", errMsg)
			logger.Warnf("Embedder server error (attempt %d/%d): %s. Retrying in %v...",
				i+1, maxRetries, errMsg, delay)
			time.Sleep(delay)
			continue
		}

		// Decode response
		defer resp.Body.Close()
		if err := json.NewDecoder(resp.Body).Decode(respDest); err != nil {
			return fmt.Errorf("failed to decode response: %w", err)
		}

		return nil
	}

	return fmt.Errorf("request failed after %d attempts: %w", maxRetries, lastErr)
}

// Embed embeds a single text using the /embed endpoint
func (e *Embedder) Embed(text string) ([]float32, int, error) {
	if text == "" {
		return make([]float32, MINILM_L6_V2_ONNX_MODEL_DIM_OUT), 0, nil
	}

	reqBody := embedRequest{Text: text}
	var embedResp embedResponse

	if err := e.postWithRetry("/embed", reqBody, &embedResp); err != nil {
		return nil, 0, err
	}

	if embedResp.Status != "success" {
		return nil, 0, fmt.Errorf("embedding failed: status=%s", embedResp.Status)
	}

	return embedResp.Embedding, embedResp.TokenCount, nil
}

// EmbedBatch efficiently embeds multiple texts using the /embed/batch endpoint
func (e *Embedder) EmbedBatch(texts []string) ([][]float32, []int, error) {
	if len(texts) == 0 {
		return nil, nil, nil
	}

	reqBody := batchEmbedRequest{Texts: texts}
	var embedResp batchEmbedResponse

	if err := e.postWithRetry("/embed/batch", reqBody, &embedResp); err != nil {
		return nil, nil, err
	}

	if embedResp.Status != "success" {
		return nil, nil, fmt.Errorf("batch embedding failed: status=%s", embedResp.Status)
	}

	return embedResp.Embeddings, embedResp.TokenCounts, nil
}

// EmbedContentDirect uses Python service's /embed/content endpoint directly
// This is the simplest approach - let Python handle all chunking/weighting
func (e *Embedder) EmbedContentDirect(text string, contentType ContentType) ([]*EmbeddingResult, error) {
	reqBody := contentEmbedRequest{
		Text:        text,
		ContentType: string(contentType),
		Chunk:       true,
	}

	var embedResp contentEmbedResponse
	if err := e.postWithRetry("/embed/content", reqBody, &embedResp); err != nil {
		return nil, err
	}

	if embedResp.Status != "success" {
		return nil, fmt.Errorf("content embedding failed: status=%s", embedResp.Status)
	}

	// Convert to EmbeddingResult format
	results := make([]*EmbeddingResult, 0, len(embedResp.Results))
	for _, res := range embedResp.Results {
		results = append(results, &EmbeddingResult{
			Embedding:   res.Embedding,
			ContentType: contentType,
			ChunkIndex:  res.ChunkIndex,
			TotalChunks: res.TotalChunks,
			Weight:      res.Weight,
			Text:        res.Text,
			TokenCount:  res.TokenCount,
		})
	}

	return results, nil
}

// EmbedContent processes content with Go-side chunking, then batch embeds
// This maintains your existing Go logic while using Python for inference
func (e *Embedder) EmbedContent(text string, contentType ContentType) ([]*EmbeddingResult, error) {
	// Option 1: Use Python's /embed/content endpoint (recommended - simpler)
	// Uncomment this line to delegate everything to Python:
	// return e.EmbedContentDirect(text, contentType)

	// Option 2: Keep Go-side chunking logic (what's below)
	// This is useful if you want Go to control chunking behavior

	// Preprocess based on content type
	cleaned := e.preprocessByType(text, contentType)

	// Smart chunking based on content type
	chunks := e.chunkByType(cleaned, contentType)

	// Add context to each chunk
	contextualChunks := make([]string, len(chunks))
	for i, chunk := range chunks {
		contextualChunks[i] = e.addTypeContext(chunk, contentType)
	}

	// Batch embed all chunks for efficiency
	embeddings, tokenCounts, err := e.EmbedBatch(contextualChunks)
	if err != nil {
		// Fallback to individual embedding if batch fails
		logger.Warnf("Batch embedding failed, falling back to individual: %v", err)
		return e.embedContentIndividual(chunks, contentType)
	}

	// Apply weighting and build results
	results := make([]*EmbeddingResult, 0, len(chunks))
	weight := ContentTypeWeight[contentType]

	for i := range chunks {
		embedding := embeddings[i]
		e.scaleEmbedding(embedding, weight)

		results = append(results, &EmbeddingResult{
			Embedding:   embedding,
			ContentType: contentType,
			ChunkIndex:  i,
			TotalChunks: len(chunks),
			Weight:      weight,
			Text:        chunks[i],
			TokenCount:  tokenCounts[i],
		})
	}

	return results, nil
}

// embedContentIndividual is fallback for when batch fails
func (e *Embedder) embedContentIndividual(chunks []string, contentType ContentType) ([]*EmbeddingResult, error) {
	results := make([]*EmbeddingResult, 0, len(chunks))
	weight := ContentTypeWeight[contentType]

	for i, chunk := range chunks {
		contextualChunk := e.addTypeContext(chunk, contentType)
		embedding, tokenCount, err := e.Embed(contextualChunk)
		if err != nil {
			logger.Warnf("Warning: failed to embed chunk %d: %v", i, err)
			continue
		}

		e.scaleEmbedding(embedding, weight)

		results = append(results, &EmbeddingResult{
			Embedding:   embedding,
			ContentType: contentType,
			ChunkIndex:  i,
			TotalChunks: len(chunks),
			Weight:      weight,
			Text:        chunk,
			TokenCount:  tokenCount,
		})
	}

	return results, nil
}

// --- Text Processing Functions (Keep your existing logic) ---

func (e *Embedder) preprocessByType(text string, contentType ContentType) string {
	// Remove excessive whitespace
	text = regexp.MustCompile(`\s+`).ReplaceAllString(text, " ")
	text = strings.TrimSpace(text)

	switch contentType {
	case ContentPublication:
		text = regexp.MustCompile(`(?i)(download|view) (pdf|paper|full text)`).ReplaceAllString(text, "")
	case ContentCode:
		text = regexp.MustCompile(`\n{3,}`).ReplaceAllString(text, "\n\n")
	case ContentBiography:
		text = regexp.MustCompile(`(?i)(curriculum vitae|download cv)`).ReplaceAllString(text, "")
	}

	return text
}

func (e *Embedder) chunkByType(text string, contentType ContentType) []string {
	maxChars := MINILM_L6_V2_ONNX_MODEL_MAX_TOKENS * 4
	overlapChars := 50

	switch contentType {
	case ContentPublication:
		return e.semanticChunk(text, maxChars, overlapChars, []string{
			"Abstract:", "Introduction:", "Methods:", "Results:", "Conclusion:",
		})
	case ContentProject:
		return e.semanticChunk(text, maxChars, overlapChars, []string{
			"Overview:", "Objectives:", "Team:", "Publications:",
		})
	default:
		return e.slidingWindowChunk(text, maxChars, overlapChars)
	}
}

func (e *Embedder) semanticChunk(text string, maxChars, overlap int, boundaries []string) []string {
	chunks := []string{}
	positions := []int{0}

	for _, boundary := range boundaries {
		if idx := strings.Index(text, boundary); idx != -1 {
			positions = append(positions, idx)
		}
	}
	positions = append(positions, len(text))

	// Sort positions
	for i := 0; i < len(positions)-1; i++ {
		for j := i + 1; j < len(positions); j++ {
			if positions[i] > positions[j] {
				positions[i], positions[j] = positions[j], positions[i]
			}
		}
	}

	for i := 0; i < len(positions)-1; i++ {
		start := positions[i]
		end := positions[i+1]

		if end-start > maxChars {
			chunks = append(chunks, e.slidingWindowChunk(text[start:end], maxChars, overlap)...)
		} else {
			chunks = append(chunks, text[start:end])
		}
	}

	if len(chunks) == 0 {
		return e.slidingWindowChunk(text, maxChars, overlap)
	}

	return chunks
}

func (e *Embedder) slidingWindowChunk(text string, maxChars, overlap int) []string {
	if len(text) <= maxChars {
		return []string{text}
	}

	chunks := []string{}
	for i := 0; i < len(text); i += maxChars - overlap {
		end := i + maxChars
		if end > len(text) {
			end = len(text)
		}
		chunks = append(chunks, text[i:end])
		if end == len(text) {
			break
		}
	}

	return chunks
}

func (e *Embedder) addTypeContext(text string, contentType ContentType) string {
	var prefix string
	switch contentType {
	case ContentPublication:
		prefix = "Research publication: "
	case ContentProject:
		prefix = "Research project: "
	case ContentCode:
		prefix = "Code repository: "
	case ContentTeaching:
		prefix = "Course material: "
	case ContentBiography:
		prefix = "Biography: "
	default:
		prefix = ""
	}
	return prefix + text
}

func (e *Embedder) scaleEmbedding(embedding []float32, weight float32) {
	for i := range embedding {
		embedding[i] *= weight
	}
}

func (e *Embedder) Close() {
	// HTTP client cleanup handled automatically
	e.httpClient.CloseIdleConnections()
}

// Helper function to get environment variable with default
func getEnv(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
