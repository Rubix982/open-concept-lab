# ADR-002: Local LLM Strategy with Ollama

## Status
Accepted

## Context
Fact extraction requires LLM capabilities. We need to decide between cloud APIs (OpenAI) and local inference.

## Decision
Support both OpenAI and local Ollama, with Ollama as the recommended default for:
- Data privacy
- Cost control
- Reproducibility

## Implementation
- Use OpenAI-compatible API interface
- Environment variable `LLM_BACKEND` switches between providers
- Default to Ollama with `mistral` model

## Consequences

### Positive
- **Privacy**: Data never leaves the machine
- **Cost**: No per-token charges
- **Reproducibility**: Fixed model version
- **Offline**: Works without internet

### Negative
- **Performance**: Slower than cloud APIs
- **Quality**: 7B models less capable than GPT-4
- **Hardware**: Requires significant RAM/GPU

## Metrics
- Fact extraction quality (precision/recall)
- Inference latency
- Resource utilization

## Future Considerations
- Support for quantized models (4-bit)
- GPU acceleration via Metal/CUDA
- Model fine-tuning on domain data
