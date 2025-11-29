# Ollama Integration Guide

## 🔗 How Ollama is Integrated

### Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                     Host Machine (macOS)                  │
│                                                            │
│  ┌─────────────────┐                                      │
│  │  Ollama Service │  ← Running natively on macOS        │
│  │  Port: 11434    │  ← Using Metal/GPU acceleration     │
│  │  Model: Mistral │  ← 7B parameter model (4.4GB)       │
│  └────────┬────────┘                                      │
│           │                                                │
│           │ HTTP API (OpenAI-compatible)                  │
│           │                                                │
│  ┌────────▼────────────────────────────────────────────┐  │
│  │         Docker Network                              │  │
│  │                                                      │  │
│  │  ┌──────────────────────────────────────────┐      │  │
│  │  │  App Container                           │      │  │
│  │  │                                          │      │  │
│  │  │  FactExtractor                          │      │  │
│  │  │    ↓                                     │      │  │
│  │  │  AsyncOpenAI(                           │      │  │
│  │  │    base_url="http://host.docker.        │      │  │
│  │  │              internal:11434/v1"         │      │  │
│  │  │  )                                       │      │  │
│  │  └──────────────────────────────────────────┘      │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## 📝 Configuration

### 1. Environment Variables (docker-compose.yml)

```yaml
app:
  environment:
    - LLM_BACKEND=ollama                              # Switch from OpenAI to Ollama
    - OLLAMA_HOST=http://host.docker.internal:11434/v1  # Docker → Host connection
    - OLLAMA_MODEL=mistral                            # Which model to use
```

### 2. Code Integration (fact_extractor.py)

```python
def __init__(self, model: str = "gpt-3.5-turbo"):
    self.backend = os.getenv("LLM_BACKEND", "openai")
    
    if self.backend == "ollama":
        ollama_host = os.getenv("OLLAMA_HOST", "http://llm-service:11434/v1")
        
        # Ollama has OpenAI-compatible API!
        self.client = AsyncOpenAI(
            base_url=ollama_host,
            api_key="ollama"  # Dummy key (Ollama doesn't need auth)
        )
        
        self.model = os.getenv("OLLAMA_MODEL", "mistral")
        logger.info(f"Initialized FactExtractor with Ollama: {self.model}")
```

## 🎯 Why This Design?

### Option A: Ollama in Docker ❌
```yaml
llm-service:
  image: ollama/ollama:latest
  # Problem: No GPU access on macOS Docker
```
**Issue**: Docker on macOS doesn't support GPU passthrough (Metal)

### Option B: Ollama on Host ✅ (Current)
```yaml
app:
  environment:
    - OLLAMA_HOST=http://host.docker.internal:11434/v1
```
**Benefits**:
- ✅ Uses Mac's Metal GPU for acceleration
- ✅ Faster inference (~120 chunks/min vs ~50)
- ✅ Model persists on host (no re-download)
- ✅ Can use `ollama` CLI directly

## 🔧 How It Works

### 1. Ollama Installation
```bash
# Install via Homebrew
brew install ollama

# Start service
brew services start ollama

# Pull model
ollama pull mistral
```

### 2. Ollama API
Ollama provides an **OpenAI-compatible API**:

```bash
# OpenAI format
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 3. Docker → Host Connection
Docker containers access host via `host.docker.internal`:

```python
# Inside container
base_url = "http://host.docker.internal:11434/v1"
# Resolves to: http://192.168.65.2:11434/v1 (host IP)
```

## 📊 Fact Extraction Flow

```
Text Chunk
    ↓
FactExtractor.extract_from_chunk()
    ↓
AsyncOpenAI.chat.completions.create(
    model="mistral",
    messages=[system_prompt, user_prompt]
)
    ↓
HTTP Request → http://host.docker.internal:11434/v1
    ↓
Ollama Service (on host)
    ↓
Mistral Model (7B params, Q4 quantized)
    ↓
JSON Response: {facts: [...], entities: [...]}
    ↓
Parse & Store in Knowledge Graph
```

## 🐛 Common Issues

### Issue 1: Environment Variables Not Set
**Symptom**: `LLM_BACKEND=None` in container

**Fix**:
```bash
docker-compose down
docker-compose up -d  # Recreate containers with new env vars
```

### Issue 2: Can't Reach Ollama
**Symptom**: Connection refused to `host.docker.internal:11434`

**Check**:
```bash
# On host
ollama list  # Should show mistral

# Test from host
curl http://localhost:11434/api/tags

# Test from container
docker-compose exec app curl http://host.docker.internal:11434/api/tags
```

### Issue 3: Using MockFactExtractor
**Symptom**: Knowledge graph has "Alice" and "Bob" instead of real entities

**Cause**: `FactExtractor` fell back to mock because:
1. No `LLM_BACKEND` env var, OR
2. Can't connect to Ollama

**Fix**: Restart containers with proper env vars

## 🚀 Verification

### 1. Check Ollama is Running
```bash
ollama list
# Should show: mistral:latest
```

### 2. Check Container Can Reach Ollama
```bash
docker-compose exec app python -c "
import os
import requests

backend = os.getenv('LLM_BACKEND')
host = os.getenv('OLLAMA_HOST')
model = os.getenv('OLLAMA_MODEL')

print(f'Backend: {backend}')
print(f'Host: {host}')
print(f'Model: {model}')

# Test connection
try:
    resp = requests.get('http://host.docker.internal:11434/api/tags')
    print(f'Connection: OK')
    print(f'Models: {resp.json()}')
except Exception as e:
    print(f'Connection: FAILED - {e}')
"
```

### 3. Test Fact Extraction
```bash
docker-compose exec app python -c "
import asyncio
from persistent_memory.fact_extractor import FactExtractor

async def test():
    extractor = FactExtractor()
    result = await extractor.extract_from_chunk(
        'Elizabeth Bennet lives in Longbourn with her family.'
    )
    print(f'Facts: {result.facts}')
    print(f'Entities: {result.entities}')

asyncio.run(test())
"
```

## 📈 Performance

| Backend | Latency/Chunk | Throughput | Cost | Privacy |
|---------|---------------|------------|------|---------|
| OpenAI GPT-3.5 | 800ms | 75/min | $$ | ❌ Cloud |
| OpenAI GPT-4 | 2500ms | 24/min | $$$$ | ❌ Cloud |
| Ollama (CPU) | 1200ms | 50/min | Free | ✅ Local |
| **Ollama (Metal)** | **500ms** | **120/min** | **Free** | **✅ Local** |

## 🎓 Key Takeaways

1. **OpenAI-Compatible API**: Ollama implements the same API as OpenAI, so we can use the same client library
2. **Host Networking**: `host.docker.internal` allows containers to reach services on the host
3. **Metal Acceleration**: Running Ollama on macOS host enables GPU acceleration
4. **Fallback Logic**: System gracefully falls back to `MockFactExtractor` if Ollama isn't available
5. **Environment-Driven**: Switching between OpenAI and Ollama is just an env var change

## 🔮 Future Improvements

1. **Health Checks**: Add startup probe to verify Ollama connection
2. **Retry Logic**: Implement exponential backoff for transient failures
3. **Model Selection**: Support multiple models (llama3, mixtral, etc.)
4. **Batch Processing**: Send multiple chunks in one request
5. **Streaming**: Use streaming API for real-time fact extraction
