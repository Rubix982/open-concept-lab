package scraperworker

import (
	"fmt"
	"log"
	"math"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/sugarme/tokenizer"
	"github.com/sugarme/tokenizer/pretrained"
	ort "github.com/yalue/onnxruntime_go"
)

const (
	MINILM_L6_V2_ONNX_MODEL_DIR        = "./models/all-MiniLM-L6-v2-onnx"
	MINILM_L6_V2_ONNX_MODEL_DIM_OUT    = 384
	MINILM_L6_V2_ONNX_MODEL_MAX_TOKENS = 128
)

// ContentTypeWeight defines importance multipliers for retrieval
var ContentTypeWeight = map[ContentType]float32{
	ContentPublication: 2.0, // Highest priority
	ContentProject:     1.8,
	ContentCode:        1.6,
	ContentDataset:     1.6,
	ContentTalk:        1.4,
	ContentTeaching:    1.2,
	ContentStudents:    1.0,
	ContentAward:       1.0,
	ContentNews:        0.8,
	ContentBiography:   0.6,
	ContentHomepage:    0.5, // Lowest priority
}

type EmbeddingResult struct {
	Embedding   []float32
	ContentType ContentType
	ChunkIndex  int
	TotalChunks int
	Weight      float32 // For retrieval scoring
	Text        string  // Original chunk text
	TokenCount  int
}

type Embedder struct {
	session   *ort.DynamicAdvancedSession
	tokenizer *tokenizer.Tokenizer
}

func NewEmbedder() (*Embedder, error) {
	// Initialize ONNX Runtime
	err := ort.InitializeEnvironment()
	if err != nil {
		return nil, fmt.Errorf("failed to init ONNX: %w", err)
	}

	// Load ONNX model
	modelPath := filepath.Join(MINILM_L6_V2_ONNX_MODEL_DIR, "model.onnx")
	session, err := ort.NewDynamicAdvancedSession(
		modelPath,
		[]string{"input_ids", "attention_mask", "token_type_ids"},
		[]string{"last_hidden_state"},
		nil,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to load model: %w", err)
	}

	// Load tokenizer
	tk := pretrained.BertBaseUncased()

	log.Printf("✓ Model loaded: %s", modelPath)

	return &Embedder{
		session:   session,
		tokenizer: tk,
	}, nil
}

func (e *Embedder) Embed(text string) ([]float32, int, error) {
	if text == "" {
		return make([]float32, MINILM_L6_V2_ONNX_MODEL_DIM_OUT), 0, nil
	}

	// Tokenize
	encoding, err := e.tokenizer.EncodeSingle(text, true)
	if err != nil {
		return nil, 0, fmt.Errorf("tokenization failed: %w", err)
	}

	ids := encoding.GetIds()
	attentionMask := encoding.GetAttentionMask()
	typeIds := encoding.GetTypeIds()

	// Pad or truncate to max length
	maxLen := MINILM_L6_V2_ONNX_MODEL_MAX_TOKENS
	tokenCount := len(ids)
	inputIDs := padOrTruncate(ids, maxLen)
	attnMask := padOrTruncate(attentionMask, maxLen)
	tokenTypeIDs := padOrTruncate(typeIds, maxLen)

	// Create input tensors
	inputShape := ort.NewShape(1, int64(maxLen))

	inputIDsTensor, err := ort.NewTensor(inputShape, inputIDs)
	if err != nil {
		return nil, 0, err
	}
	defer inputIDsTensor.Destroy()

	attnMaskTensor, err := ort.NewTensor(inputShape, attnMask)
	if err != nil {
		return nil, 0, err
	}
	defer attnMaskTensor.Destroy()

	tokenTypeIDsTensor, err := ort.NewTensor(inputShape, tokenTypeIDs)
	if err != nil {
		return nil, 0, err
	}
	defer tokenTypeIDsTensor.Destroy()

	// Prepare inputs and outputs
	inputs := []ort.Value{inputIDsTensor, attnMaskTensor, tokenTypeIDsTensor}
	outputs := []ort.Value{nil} // nil = auto-allocate output

	// Run inference
	err = e.session.Run(inputs, outputs)
	if err != nil {
		return nil, 0, fmt.Errorf("inference failed: %w", err)
	}
	defer outputs[0].Destroy()

	// Type assert to concrete tensor type
	outputTensor, ok := outputs[0].(*ort.Tensor[float32])
	if !ok {
		return nil, 0, fmt.Errorf("output is not a float32 tensor")
	}

	// Extract data
	data := outputTensor.GetData()

	// Mean pool over sequence dimension
	embedding := meanPool(data, maxLen, MINILM_L6_V2_ONNX_MODEL_DIM_OUT)

	// L2 normalize for cosine similarity
	e.normalizeEmbedding(embedding)

	return embedding, tokenCount, nil
}

// normalizeEmbedding applies L2 normalization for cosine similarity
func (e *Embedder) normalizeEmbedding(embedding []float32) {
	var norm float32
	for _, v := range embedding {
		norm += v * v
	}
	norm = float32(math.Sqrt(float64(norm)))

	if norm > 0 {
		for i := range embedding {
			embedding[i] /= norm
		}
	}
}

// EmbedContent processes content with type-aware chunking and weighting
func (e *Embedder) EmbedContent(text string, contentType ContentType) ([]*EmbeddingResult, error) {
	// Preprocess based on content type
	cleaned := e.preprocessByType(text, contentType)

	// Smart chunking based on content type
	chunks := e.chunkByType(cleaned, contentType)

	results := make([]*EmbeddingResult, 0, len(chunks))
	weight := ContentTypeWeight[contentType]

	for i, chunk := range chunks {
		// Add content type context to improve embedding quality
		contextualChunk := e.addTypeContext(chunk, contentType)

		embedding, tokenCount, err := e.Embed(contextualChunk)
		if err != nil {
			log.Printf("Warning: failed to embed chunk %d: %v", i, err)
			continue
		}

		// Apply content type weighting to embedding vector
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

// preprocessByType cleans text based on content type
func (e *Embedder) preprocessByType(text string, contentType ContentType) string {
	// Remove excessive whitespace
	text = regexp.MustCompile(`\s+`).ReplaceAllString(text, " ")
	text = strings.TrimSpace(text)

	switch contentType {
	case ContentPublication:
		// Keep DOI, arXiv IDs, citations
		// Remove "Download PDF" type noise
		text = regexp.MustCompile(`(?i)(download|view) (pdf|paper|full text)`).ReplaceAllString(text, "")

	case ContentCode:
		// Keep code structure markers
		// Remove excess newlines but preserve some structure
		text = regexp.MustCompile(`\n{3,}`).ReplaceAllString(text, "\n\n")

	case ContentBiography:
		// Remove CV boilerplate
		text = regexp.MustCompile(`(?i)(curriculum vitae|download cv)`).ReplaceAllString(text, "")
	}

	return text
}

// chunkByType splits text intelligently based on content type
func (e *Embedder) chunkByType(text string, contentType ContentType) []string {
	// Rough token estimate: ~4 chars per token
	maxChars := MINILM_L6_V2_ONNX_MODEL_MAX_TOKENS * 4
	overlapChars := 50 // Small overlap to preserve context

	switch contentType {
	case ContentPublication:
		// Try to keep abstracts together
		return e.semanticChunk(text, maxChars, overlapChars, []string{
			"Abstract:", "Introduction:", "Methods:", "Results:", "Conclusion:",
		})

	case ContentProject:
		return e.semanticChunk(text, maxChars, overlapChars, []string{
			"Overview:", "Objectives:", "Team:", "Publications:",
		})

	default:
		// Simple sliding window for other types
		return e.slidingWindowChunk(text, maxChars, overlapChars)
	}
}

// semanticChunk tries to split on semantic boundaries
func (e *Embedder) semanticChunk(text string, maxChars, overlap int, boundaries []string) []string {
	chunks := []string{}

	// Find boundary positions
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

	// Create chunks from boundaries
	for i := 0; i < len(positions)-1; i++ {
		start := positions[i]
		end := positions[i+1]

		if end-start > maxChars {
			// Section too large, fallback to sliding window
			chunks = append(chunks, e.slidingWindowChunk(text[start:end], maxChars, overlap)...)
		} else {
			chunks = append(chunks, text[start:end])
		}
	}

	// Fallback if no boundaries found
	if len(chunks) == 0 {
		return e.slidingWindowChunk(text, maxChars, overlap)
	}

	return chunks
}

// slidingWindowChunk creates overlapping chunks
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

// addTypeContext prepends content type for better embedding context
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

// scaleEmbedding applies content type weight
func (e *Embedder) scaleEmbedding(embedding []float32, weight float32) {
	for i := range embedding {
		embedding[i] *= weight
	}
}

func (e *Embedder) Close() {
	if e.session != nil {
		e.session.Destroy()
	}
	ort.DestroyEnvironment()
}

// Helper: Pad or truncate to target length and convert to int64 for ONNX
func padOrTruncate(slice []int, length int) []int64 {
	result := make([]int64, length)
	for i := 0; i < len(slice) && i < length; i++ {
		result[i] = int64(slice[i])
	}
	return result
}

// Helper: Mean pooling
func meanPool(data []float32, seqLen, hiddenDim int) []float32 {
	result := make([]float32, hiddenDim)
	for i := 0; i < seqLen; i++ {
		for j := 0; j < hiddenDim; j++ {
			result[j] += data[i*hiddenDim+j]
		}
	}
	for j := 0; j < hiddenDim; j++ {
		result[j] /= float32(seqLen)
	}
	return result
}
