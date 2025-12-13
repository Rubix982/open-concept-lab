package scraperworker

import (
	"fmt"
	"log"
	"path/filepath"

	"github.com/sugarme/tokenizer"
	"github.com/sugarme/tokenizer/pretrained"
	ort "github.com/yalue/onnxruntime_go"
)

const (
	MINILM_L6_V2_ONNX_MODEL_DIR = "./models/all-MiniLM-L6-v2-onnx"
)

type Embedder struct {
	session   *ort.DynamicAdvancedSession
	tokenizer *tokenizer.Tokenizer
	dim       int
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

	dim := 384 // MiniLM-L6-v2 output dimension

	log.Printf("✓ Model loaded: %s (dim=%d)", modelPath, dim)

	return &Embedder{
		session:   session,
		tokenizer: tk,
		dim:       dim,
	}, nil
}

func (e *Embedder) Embed(text string) ([]float32, error) {
	if text == "" {
		return make([]float32, e.dim), nil
	}

	// Tokenize
	encoding, err := e.tokenizer.EncodeSingle(text, true)
	if err != nil {
		return nil, fmt.Errorf("tokenization failed: %w", err)
	}

	ids := encoding.GetIds()
	attentionMask := encoding.GetAttentionMask()
	typeIds := encoding.GetTypeIds()

	// Pad or truncate to max length
	maxLen := 128
	inputIDs := padOrTruncate(ids, maxLen)
	attnMask := padOrTruncate(attentionMask, maxLen)
	tokenTypeIDs := padOrTruncate(typeIds, maxLen)

	// Create input tensors
	inputShape := ort.NewShape(1, int64(maxLen))

	inputIDsTensor, err := ort.NewTensor(inputShape, inputIDs)
	if err != nil {
		return nil, err
	}
	defer inputIDsTensor.Destroy()

	attnMaskTensor, err := ort.NewTensor(inputShape, attnMask)
	if err != nil {
		return nil, err
	}
	defer attnMaskTensor.Destroy()

	tokenTypeIDsTensor, err := ort.NewTensor(inputShape, tokenTypeIDs)
	if err != nil {
		return nil, err
	}
	defer tokenTypeIDsTensor.Destroy()

	// Prepare inputs and outputs
	inputs := []ort.Value{inputIDsTensor, attnMaskTensor, tokenTypeIDsTensor}
	outputs := []ort.Value{nil} // nil = auto-allocate output

	// Run inference
	err = e.session.Run(inputs, outputs)
	if err != nil {
		return nil, fmt.Errorf("inference failed: %w", err)
	}
	defer outputs[0].Destroy()

	// Type assert to concrete tensor type
	outputTensor, ok := outputs[0].(*ort.Tensor[float32])
	if !ok {
		return nil, fmt.Errorf("output is not a float32 tensor")
	}

	// Extract data
	data := outputTensor.GetData()

	// Mean pool over sequence dimension
	embedding := meanPool(data, maxLen, e.dim)

	return embedding, nil
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
