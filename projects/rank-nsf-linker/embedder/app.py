"""
Self-Hosted Embedding Service
High-performance semantic embeddings with batch processing
Uses Sentence-Transformers for state-of-the-art embeddings
"""

import re
import os
import uuid
import time
import logging
import traceback
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

import dotenv
from colorama import Fore, Style, init
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_compress import Compress
from sentence_transformers import SentenceTransformer
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import numpy as np

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)
Compress(app)

# Initialize colorama
init(autoreset=True)

# --- Prometheus Metrics ---

# Request metrics
embed_requests_total = Counter(
    "embed_requests_total", "Total embedding requests", ["endpoint", "status"]
)

embed_request_duration = Histogram(
    "embed_request_duration_seconds",
    "Time spent processing embedding requests",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

embed_batch_size = Histogram(
    "embed_batch_size",
    "Number of texts in batch requests",
    buckets=[1, 5, 10, 20, 32, 50, 100, 128],
)

embed_token_count = Histogram(
    "embed_token_count",
    "Number of tokens processed",
    ["endpoint"],
    buckets=[10, 50, 100, 200, 500, 1000, 5000],
)

# System metrics
system_cpu_usage = Gauge("system_cpu_usage_percent", "Current CPU usage percentage")

system_memory_usage = Gauge(
    "system_memory_usage_bytes", "Current memory usage in bytes"
)

system_memory_percent = Gauge(
    "system_memory_percent", "Current memory usage percentage"
)

python_memory_rss = Gauge(
    "python_memory_rss_bytes", "Python process RSS memory in bytes"
)

python_memory_vms = Gauge(
    "python_memory_vms_bytes", "Python process VMS memory in bytes"
)

# Model metrics
model_load_duration = Gauge(
    "model_load_duration_seconds", "Time taken to load the model"
)

model_memory_usage = Gauge(
    "model_memory_usage_bytes", "Estimated model memory usage in bytes"
)

torch_memory_allocated = Gauge(
    "torch_memory_allocated_bytes", "PyTorch memory allocated"
)

torch_memory_reserved = Gauge("torch_memory_reserved_bytes", "PyTorch memory reserved")

# Cache metrics (if using cache later)
cache_hits = Counter("cache_hits_total", "Total cache hits")
cache_misses = Counter("cache_misses_total", "Total cache misses")

# Service info
service_info = Info("embedder_service", "Embedder service information")
service_info.info(
    {
        "version": "1.0.0",
        "model": os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"),
        "embedding_dim": "384",
        "max_tokens": "128",
    }
)


class SystemMonitor:
    """Background thread to collect system metrics"""

    def __init__(self, interval=5.0):
        self.interval = interval
        self.running = True
        self.process = psutil.Process()
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def _monitor_loop(self):
        """Continuously collect system metrics"""
        while self.running:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                system_cpu_usage.set(cpu_percent)

                # System memory
                mem = psutil.virtual_memory()
                system_memory_usage.set(mem.used)
                system_memory_percent.set(mem.percent)

                # Process memory
                mem_info = self.process.memory_info()
                python_memory_rss.set(mem_info.rss)
                python_memory_vms.set(mem_info.vms)

                # PyTorch memory (if CUDA available)
                if torch.cuda.is_available():
                    torch_memory_allocated.set(torch.cuda.memory_allocated())
                    torch_memory_reserved.set(torch.cuda.memory_reserved())

            except Exception as e:
                logger.error(f"System monitoring error: {e}")

            time.sleep(self.interval)

    def stop(self):
        self.running = False


# Start system monitor
system_monitor = SystemMonitor(interval=5.0)


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.before_request
def add_request_id():
    request.request_id = str(uuid.uuid4())[:8]
    logger.debug(f"[{request.request_id}] {request.method} {request.path}")


@app.after_request
def log_response(response):
    if hasattr(request, "request_id"):
        logger.debug(f"[{request.request_id}] Response: {response.status_code}")
    return response


# Update error responses to include request_id
@app.errorhandler(500)
def internal_error(e):
    request_id = getattr(request, "request_id", "unknown")
    logger.error(f"[{request_id}] Internal error: {e}\n{traceback.format_exc()}")
    return (
        jsonify(
            {
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id,
            }
        ),
        500,
    )


# --- Configuration ---
class Config:
    """Service configuration"""

    # Environment
    ENV = os.getenv("ENVIRONMENT", "production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Model settings
    MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
    EMBEDDING_DIM = 384
    MAX_TOKENS = 128

    # Performance
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "32"))
    MAX_BATCH_SIZE = 128

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG" if DEBUG else "INFO")

    # Service
    PORT = int(os.getenv("PORT", "8000"))
    HOST = os.getenv("HOST", "0.0.0.0")

    # Monitoring
    MONITOR_INTERVAL = float(os.getenv("MONITOR_INTERVAL", "5.0"))


# --- Content Type Enum (matching Go implementation) ---
class ContentType(str, Enum):
    """Content type classification for weighted embeddings"""

    PUBLICATION = "publication"
    PROJECT = "project"
    CODE = "code"
    DATASET = "dataset"
    TALK = "talk"
    TEACHING = "teaching"
    STUDENTS = "students"
    AWARD = "award"
    NEWS = "news"
    BIOGRAPHY = "biography"
    HOMEPAGE = "homepage"


# Content type weights (matching Go)
CONTENT_TYPE_WEIGHTS: Dict[ContentType, float] = {
    ContentType.PUBLICATION: 2.0,
    ContentType.PROJECT: 1.8,
    ContentType.CODE: 1.6,
    ContentType.DATASET: 1.6,
    ContentType.TALK: 1.4,
    ContentType.TEACHING: 1.2,
    ContentType.STUDENTS: 1.0,
    ContentType.AWARD: 1.0,
    ContentType.NEWS: 0.8,
    ContentType.BIOGRAPHY: 0.6,
    ContentType.HOMEPAGE: 0.5,
}


# --- Data Models ---
@dataclass
class EmbedRequest:
    """Single embedding request"""

    text: str


@dataclass
class EmbedResponse:
    """Single embedding response"""

    embedding: List[float]
    token_count: int
    dimension: int


@dataclass
class BatchEmbedRequest:
    """Batch embedding request"""

    texts: List[str]


@dataclass
class BatchEmbedResponse:
    """Batch embedding response"""

    embeddings: List[List[float]]
    token_counts: List[int]
    dimension: int
    count: int


@dataclass
class ContentEmbedRequest:
    """Content-aware embedding request (with type and chunking)"""

    text: str
    content_type: str
    chunk: bool = True


@dataclass
class ContentEmbedResult:
    """Single chunk result"""

    embedding: List[float]
    content_type: str
    chunk_index: int
    total_chunks: int
    weight: float
    text: str
    token_count: int


@dataclass
class ContentEmbedResponse:
    """Content embedding response with multiple chunks"""

    results: List[Dict[str, Any]]
    total_chunks: int
    dimension: int


# --- Structured Logger (matching your style) ---
class StructuredLogger:
    """Enhanced logging with colors and structure"""

    LEVEL_COLORS = {
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
        "DEBUG": Fore.CYAN,
    }

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, Config.LOG_LEVEL))
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Custom formatter with colors
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _colorize(self, level: str, message: str) -> str:
        """Add color to log message"""
        color = self.LEVEL_COLORS.get(level.upper(), "")
        return f"{color}{message}{Style.RESET_ALL}"

    def info(self, message: str):
        self.logger.info(self._colorize("INFO", message))

    def warning(self, message: str):
        self.logger.warning(self._colorize("WARNING", message))

    def error(self, message: str):
        self.logger.error(self._colorize("ERROR", message))

    def debug(self, message: str):
        self.logger.debug(self._colorize("DEBUG", message))

    def critical(self, message: str):
        self.logger.critical(self._colorize("CRITICAL", message))


logger = StructuredLogger("embedder")


# --- Model Manager ---
class ModelManager:
    """Singleton model manager with lazy loading"""

    _instance: Optional["ModelManager"] = None
    _model: Optional[SentenceTransformer] = None
    _loading: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance

    def load_model(self) -> SentenceTransformer:
        """Load model with exponential backoff on failure"""
        if self._model is not None:
            return self._model

        if self._loading:
            while self._loading:
                time.sleep(0.1)
            return self._model

        self._loading = True

        try:
            logger.info(f"📦 Loading model: {Config.MODEL_NAME}")

            # Track memory before loading
            mem_before = psutil.Process().memory_info().rss

            start = time.time()
            self._model = SentenceTransformer(Config.MODEL_NAME)
            self._model.max_seq_length = Config.MAX_TOKENS
            elapsed = time.time() - start

            # Track memory after loading
            mem_after = psutil.Process().memory_info().rss
            model_memory = mem_after - mem_before

            # Update metrics
            model_load_duration.set(elapsed)
            model_memory_usage.set(model_memory)

            logger.info(f"✅ Model loaded in {elapsed:.2f}s")
            logger.info(f"📊 Embedding dimension: {Config.EMBEDDING_DIM}")
            logger.info(f"🔢 Max tokens: {Config.MAX_TOKENS}")
            logger.info(f"💾 Model memory: {model_memory / 1024 / 1024:.2f} MB")

            # Warm-up model
            logger.info("🔥 Warming up model...")
            warmup_start = time.time()
            _ = self._model.encode(
                ["warmup text", "another warmup"], show_progress_bar=False
            )
            logger.info(f"✅ Model warmed up in {time.time() - warmup_start:.2f}s")

            return self._model

        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            self._loading = False

    @property
    def model(self) -> SentenceTransformer:
        """Get loaded model"""
        if self._model is None:
            return self.load_model()
        return self._model


# Global model manager
model_manager = ModelManager()


# --- Embedding Functions ---
def estimate_token_count(text: str) -> int:
    """Rough token count estimation (4 chars ≈ 1 token)"""
    return max(1, len(text) // 4)


def embed_single(text: str) -> tuple[List[float], int]:
    """Embed single text with metrics tracking"""
    if not text or not text.strip():
        return [0.0] * Config.EMBEDDING_DIM, 0

    model = model_manager.model

    # Track memory before
    gc.collect()
    mem_before = psutil.Process().memory_info().rss

    start = time.time()
    embedding = model.encode(text, show_progress_bar=False, convert_to_numpy=True)
    duration = time.time() - start

    # Track memory after
    mem_after = psutil.Process().memory_info().rss
    mem_delta = mem_after - mem_before

    # Ensure L2 normalization
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    token_count = estimate_token_count(text)

    # Log if slow or memory-intensive
    if duration > 1.0:
        logger.warning(f"Slow embedding: {duration:.2f}s for {token_count} tokens")
    if mem_delta > 10 * 1024 * 1024:  # 10MB
        logger.warning(f"High memory delta: {mem_delta / 1024 / 1024:.2f}MB")

    return embedding.tolist(), token_count


def embed_batch(texts: List[str]) -> tuple[List[List[float]], List[int]]:
    """Embed batch of texts efficiently with metrics"""
    if not texts:
        return [], []

    # Track batch size
    embed_batch_size.observe(len(texts))

    # Filter empty texts
    non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
    non_empty_texts = [texts[i] for i in non_empty_indices]

    if not non_empty_texts:
        # All texts empty
        return [[0.0] * Config.EMBEDDING_DIM] * len(texts), [0] * len(texts)

    model = model_manager.model

    # Track memory
    gc.collect()
    mem_before = psutil.Process().memory_info().rss

    embeddings = model.encode(
        non_empty_texts,
        batch_size=Config.BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  # L2 normalize
    )

    mem_after = psutil.Process().memory_info().rss
    mem_delta = mem_after - mem_before

    if mem_delta > 50 * 1024 * 1024:  # 50MB
        logger.warning(
            f"High batch memory: {mem_delta / 1024 / 1024:.2f}MB "
            f"for {len(texts)} texts"
        )

    # Reconstruct full results
    full_embeddings: List[List[float]] = []
    full_token_counts: List[int] = []

    j = 0
    for i, text in enumerate(texts):
        if i in non_empty_indices:
            full_embeddings.append(embeddings[j].tolist())
            full_token_counts.append(estimate_token_count(text))
            j += 1
        else:
            full_embeddings.append([0.0] * Config.EMBEDDING_DIM)
            full_token_counts.append(0)

    return full_embeddings, full_token_counts


def scale_embedding(embedding: List[float], weight: float) -> List[float]:
    """Apply content type weight to embedding"""
    return [val * weight for val in embedding]


def preprocess_by_type(text: str, content_type: ContentType) -> str:
    """Clean text based on content type"""
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    if content_type == ContentType.PUBLICATION:
        # Remove download noise
        text = re.sub(r"(?i)(download|view)\s+(pdf|paper|full text)", "", text)

    elif content_type == ContentType.CODE:
        # Remove excess newlines but preserve structure
        text = re.sub(r"\n{3,}", "\n\n", text)

    elif content_type == ContentType.BIOGRAPHY:
        # Remove CV boilerplate
        text = re.sub(r"(?i)(curriculum vitae|download cv)", "", text)

    return text


def chunk_by_type(text: str, content_type: ContentType) -> List[str]:
    """Intelligent chunking based on content type"""
    max_chars = Config.MAX_TOKENS * 4  # ~4 chars per token
    overlap_chars = 50

    if content_type == ContentType.PUBLICATION:
        boundaries = [
            "Abstract:",
            "Introduction:",
            "Methods:",
            "Results:",
            "Conclusion:",
        ]
        return semantic_chunk(text, max_chars, overlap_chars, boundaries)

    elif content_type == ContentType.PROJECT:
        boundaries = ["Overview:", "Objectives:", "Team:", "Publications:"]
        return semantic_chunk(text, max_chars, overlap_chars, boundaries)

    else:
        return sliding_window_chunk(text, max_chars, overlap_chars)


def semantic_chunk(
    text: str, max_chars: int, overlap: int, boundaries: List[str]
) -> List[str]:
    """Split on semantic boundaries"""
    chunks = []

    # Find boundary positions
    positions = [0]
    for boundary in boundaries:
        idx = text.find(boundary)
        if idx != -1:
            positions.append(idx)
    positions.append(len(text))

    # Sort positions
    positions = sorted(set(positions))

    # Create chunks
    for i in range(len(positions) - 1):
        start = positions[i]
        end = positions[i + 1]

        if end - start > max_chars:
            # Section too large, fallback to sliding window
            chunks.extend(sliding_window_chunk(text[start:end], max_chars, overlap))
        else:
            chunks.append(text[start:end])

    # Fallback if no chunks
    if not chunks:
        return sliding_window_chunk(text, max_chars, overlap)

    return chunks


def sliding_window_chunk(text: str, max_chars: int, overlap: int) -> List[str]:
    """Sliding window with overlap"""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    i = 0
    while i < len(text):
        end = min(i + max_chars, len(text))
        chunks.append(text[i:end])

        if end == len(text):
            break

        i += max_chars - overlap

    return chunks


def add_type_context(text: str, content_type: ContentType) -> str:
    """Add content type prefix for better embedding context"""
    prefixes = {
        ContentType.PUBLICATION: "Research publication: ",
        ContentType.PROJECT: "Research project: ",
        ContentType.CODE: "Code repository: ",
        ContentType.TEACHING: "Course material: ",
        ContentType.BIOGRAPHY: "Biography: ",
    }

    prefix = prefixes.get(content_type, "")
    return prefix + text


# --- API Endpoints ---
@app.route("/health", methods=["GET"])
def health_check():
    """Health check with resource information"""
    try:
        model = model_manager.model

        # Get current resource usage
        process = psutil.Process()
        mem_info = process.memory_info()
        cpu_percent = process.cpu_percent(interval=0.1)

        return (
            jsonify(
                {
                    "status": "healthy",
                    "service": "embedder-service",
                    "version": "1.0.0",
                    "model": Config.MODEL_NAME,
                    "embedding_dim": Config.EMBEDDING_DIM,
                    "max_tokens": Config.MAX_TOKENS,
                    "batch_size": Config.BATCH_SIZE,
                    "resources": {
                        "memory_rss_mb": mem_info.rss / 1024 / 1024,
                        "memory_vms_mb": mem_info.vms / 1024 / 1024,
                        "cpu_percent": cpu_percent,
                        "torch_cuda_available": torch.cuda.is_available(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/embed", methods=["POST"])
def embed_endpoint():
    """
    Embed single text

    Request:
    {
        "text": "Your text here"
    }

    Response:
    {
        "embedding": [0.123, -0.456, ...],
        "token_count": 42,
        "dimension": 384
    }
    """
    endpoint_name = "embed"
    try:
        data = request.get_json(silent=True)

        if not data or "text" not in data:
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return jsonify({"status": "error", "message": "Missing 'text' field"}), 400

        text = data["text"]

        # Track request
        embed_requests_total.labels(endpoint=endpoint_name, status="success").inc()

        start = time.time()
        embedding, token_count = embed_single(text)
        duration = time.time() - start

        # Update metrics
        embed_request_duration.labels(endpoint=endpoint_name).observe(duration)
        embed_token_count.labels(endpoint=endpoint_name).observe(token_count)

        logger.debug(
            f"[{g.request_id}] Embedded {token_count} tokens in {duration*1000:.1f}ms"
        )

        return (
            jsonify(
                {
                    "status": "success",
                    "embedding": embedding,
                    "token_count": token_count,
                    "dimension": Config.EMBEDDING_DIM,
                    "latency_ms": round(duration * 1000, 2),
                    "request_id": g.request_id,
                }
            ),
            200,
        )

    except Exception as e:
        embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
        logger.error(
            f"[{g.request_id}] Embedding failed: {e}\n{traceback.format_exc()}"
        )
        return (
            jsonify({"status": "error", "message": str(e), "request_id": g.request_id}),
            500,
        )


@app.route("/embed/batch", methods=["POST"])
def embed_batch_endpoint():
    """
    Embed batch of texts

    Request:
    {
        "texts": ["Text 1", "Text 2", ...]
    }

    Response:
    {
        "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...]],
        "token_counts": [10, 15],
        "dimension": 384,
        "count": 2
    }
    """
    try:
        data = request.get_json(silent=True)

        if not data or "texts" not in data:
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return jsonify({"status": "error", "message": "Missing 'texts' field"}), 400

        texts = data["texts"]

        if not isinstance(texts, list):
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify({"status": "error", "message": "'texts' must be an array"}),
                400,
            )

        if len(texts) > Config.MAX_BATCH_SIZE:
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Batch size exceeds maximum ({Config.MAX_BATCH_SIZE})",
                    }
                ),
                400,
            )

        embed_requests_total.labels(endpoint=endpoint_name, status="success").inc()

        start = time.time()
        embeddings, token_counts = embed_batch(texts)
        duration = time.time() - start

        total_tokens = sum(token_counts)

        # Update metrics
        embed_request_duration.labels(endpoint=endpoint_name).observe(duration)
        embed_token_count.labels(endpoint=endpoint_name).observe(total_tokens)

        logger.debug(
            f"[{g.request_id}] Batch: {len(texts)} texts, "
            f"{total_tokens} tokens in {duration*1000:.1f}ms"
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "embeddings": embeddings,
                    "token_counts": token_counts,
                    "dimension": Config.EMBEDDING_DIM,
                    "count": len(texts),
                    "latency_ms": round(duration * 1000, 2),
                    "request_id": g.request_id,
                }
            ),
            200,
        )

    except Exception as e:
        embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
        logger.error(f"[{g.request_id}] Batch failed: {e}\n{traceback.format_exc()}")
        return (
            jsonify({"status": "error", "message": str(e), "request_id": g.request_id}),
            500,
        )


@app.route("/embed/content", methods=["POST"])
def embed_content_endpoint():
    """
    Content-aware embedding with chunking and weighting

    Request:
    {
        "text": "Long text...",
        "content_type": "publication",
        "chunk": true
    }

    Response:
    {
        "results": [
            {
                "embedding": [...],
                "content_type": "publication",
                "chunk_index": 0,
                "total_chunks": 3,
                "weight": 2.0,
                "text": "chunk text",
                "token_count": 120
            }
        ],
        "total_chunks": 3,
        "dimension": 384
    }
    """
    try:
        data = request.get_json(silent=True)

        if not data or "text" not in data:
            return jsonify({"status": "error", "message": "Missing 'text' field"}), 400

        text = data["text"]
        content_type_str = data.get("content_type", "homepage")
        should_chunk = data.get("chunk", True)

        # Parse content type
        try:
            content_type = ContentType(content_type_str)
        except ValueError:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Invalid content_type. Must be one of: {[t.value for t in ContentType]}",
                    }
                ),
                400,
            )

        start = time.time()

        # Preprocess
        cleaned = preprocess_by_type(text, content_type)

        # Chunk if requested
        if should_chunk:
            chunks = chunk_by_type(cleaned, content_type)
        else:
            chunks = [cleaned]

        # Add context and embed
        contextual_chunks = [add_type_context(chunk, content_type) for chunk in chunks]
        embeddings, token_counts = embed_batch(contextual_chunks)

        # Apply weighting
        weight = CONTENT_TYPE_WEIGHTS.get(content_type, 1.0)
        weighted_embeddings = [scale_embedding(emb, weight) for emb in embeddings]

        # Build results
        results = []
        for i, (embedding, token_count, chunk_text) in enumerate(
            zip(weighted_embeddings, token_counts, chunks)
        ):
            results.append(
                {
                    "embedding": embedding,
                    "content_type": content_type.value,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "weight": weight,
                    "text": (
                        chunk_text[:200] + "..."
                        if len(chunk_text) > 200
                        else chunk_text
                    ),  # Truncate for response
                    "token_count": token_count,
                }
            )

        elapsed = (time.time() - start) * 1000

        logger.debug(f"Content embedded: {len(chunks)} chunks in {elapsed:.1f}ms")

        return (
            jsonify(
                {
                    "status": "success",
                    "results": results,
                    "total_chunks": len(chunks),
                    "dimension": Config.EMBEDDING_DIM,
                    "latency_ms": round(elapsed, 2),
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Content embedding failed: {e}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/", methods=["GET"])
def root():
    """Root endpoint with stats"""
    process = psutil.Process()
    mem_info = process.memory_info()

    return (
        jsonify(
            {
                "service": "embedder-service",
                "version": "1.0.0",
                "model": Config.MODEL_NAME,
                "endpoints": {
                    "health": "/health",
                    "metrics": "/metrics",
                    "embed": "/embed",
                    "batch": "/embed/batch",
                    "content": "/embed/content",
                },
                "stats": {
                    "memory_mb": round(mem_info.rss / 1024 / 1024, 2),
                    "cpu_percent": process.cpu_percent(interval=0.1),
                },
            }
        ),
        200,
    )


# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e):
    return (
        jsonify(
            {
                "status": "error",
                "message": f"Endpoint not found: {request.path}",
                "request_id": getattr(g, "request_id", "unknown"),
            }
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(e):
    request_id = getattr(g, "request_id", "unknown")
    logger.error(f"[{request_id}] Internal error: {e}\n{traceback.format_exc()}")
    return (
        jsonify(
            {
                "status": "error",
                "message": "Internal server error",
                "request_id": request_id,
            }
        ),
        500,
    )


# --- Main ---
if __name__ == "__main__":
    print("🚀 Starting Embedding Service")
    print(
        """
███████ ███    ███ ██████  ███████ ██████  ██████  ███████ ██████  
██      ████  ████ ██   ██ ██      ██   ██ ██   ██ ██      ██   ██ 
█████   ██ ████ ██ ██████  █████   ██   ██ ██   ██ █████   ██████  
██      ██  ██  ██ ██   ██ ██      ██   ██ ██   ██ ██      ██   ██ 
███████ ██      ██ ██████  ███████ ██████  ██████  ███████ ██   ██ 
    """
    )

    logger.info(f"📦 Model: {Config.MODEL_NAME}")
    logger.info(f"📊 Embedding dimension: {Config.EMBEDDING_DIM}")
    logger.info(f"🔢 Max tokens: {Config.MAX_TOKENS}")
    logger.info(f"⚡ Batch size: {Config.BATCH_SIZE}")

    # Pre-load model
    try:
        model_manager.load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.warning("Service will start but embedding will fail until model loads")

    logger.info(f"🌐 Server running on http://{Config.HOST}:{Config.PORT}")
    logger.info("\n📚 Endpoints:")
    logger.info("  GET  /                  - Service info")
    logger.info("  GET  /health            - Health check")
    logger.info("  GET  /metrics           - Prometheus metrics")
    logger.info("  POST /embed             - Embed single text")
    logger.info("  POST /embed/batch       - Embed batch of texts")
    logger.info("  POST /embed/content     - Content-aware embedding")

    # Enable debug mode via environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    try:
        app.run(host=Config.HOST, port=Config.PORT, debug=debug_mode)
    finally:
        system_monitor.stop()
