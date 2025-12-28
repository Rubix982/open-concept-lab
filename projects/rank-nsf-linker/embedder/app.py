"""

Self-Hosted Embedding Service
High-performance semantic embeddings with batch processing
Uses Sentence-Transformers for state-of-the-art embeddings

"""

import gc
import logging
import os
import re
import threading
import time
import traceback
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

import dotenv
import numpy as np
import psutil
import torch
from colorama import Fore, Style, init
from flask import Flask, g, jsonify, request
from flask_compress import Compress
from flask_cors import CORS
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, Info, generate_latest
from sentence_transformers import SentenceTransformer

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

system_memory_usage = Gauge("system_memory_usage_bytes", "Current memory usage in bytes")

system_memory_percent = Gauge("system_memory_percent", "Current memory usage percentage")

python_memory_rss = Gauge("python_memory_rss_bytes", "Python process RSS memory in bytes")

python_memory_vms = Gauge("python_memory_vms_bytes", "Python process VMS memory in bytes")

# Model metrics
model_load_duration = Gauge("model_load_duration_seconds", "Time taken to load the model")

model_memory_usage = Gauge("model_memory_usage_bytes", "Estimated model memory usage in bytes")

torch_memory_allocated = Gauge("torch_memory_allocated_bytes", "PyTorch memory allocated")

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


# --- Configuration ---
class Config:
    """Service configuration."""

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


log = StructuredLogger("embedder")


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
                log.info(f"System monitoring error: {e}")

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
    g.request_id = str(uuid.uuid4())[:8]
    log.debug(f"[{g.request_id}] {request.method} {request.path}")


@app.after_request
def log_response(response):
    if hasattr(g, "request_id"):
        log.debug(f"[{g.request_id}] Response: {response.status_code}")
    return response


# Update error responses to include request_id
@app.errorhandler(500)
def internal_error(e):
    request_id = getattr(g, "request_id", "unknown")
    log.info(f"[{request_id}] Internal error: {e}\n{traceback.format_exc()}")
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
            log.info(f"📦 Loading model: {Config.MODEL_NAME}")

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

            log.info(f"✅ Model loaded in {elapsed:.2f}s")
            log.info(f"📊 Embedding dimension: {Config.EMBEDDING_DIM}")
            log.info(f"🔢 Max tokens: {Config.MAX_TOKENS}")
            log.info(f"💾 Model memory: {model_memory / 1024 / 1024:.2f} MB")

            # Warm-up model
            log.info("🔥 Warming up model...")
            warmup_start = time.time()
            _ = self._model.encode(["warmup text", "another warmup"], show_progress_bar=False)
            log.info(f"✅ Model warmed up in {time.time() - warmup_start:.2f}s")

            return self._model

        except Exception as e:
            log.info(f"❌ Failed to load model: {e}")
            log.info(traceback.format_exc())
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
        log.warning(f"Slow embedding: {duration:.2f}s for {token_count} tokens")
    if mem_delta > 10 * 1024 * 1024:  # 10MB
        log.warning(f"High memory delta: {mem_delta / 1024 / 1024:.2f}MB")

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
        log.warning(
            f"High batch memory: {mem_delta / 1024 / 1024:.2f}MB " f"for {len(texts)} texts"
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


def semantic_chunk(text: str, max_chars: int, overlap: int, boundaries: List[str]) -> List[str]:
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
        _ = model_manager.model

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
        log.info(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/embed", methods=["POST"])
def embed_endpoint():
    """Embed single text with comprehensive logging

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
    request_id = g.request_id

    # Log request start
    log.info(f"[{request_id}] POST /embed - Request received")

    try:
        # Parse request body
        log.debug(f"[{request_id}] Parsing request body")
        data = request.get_json(silent=True)

        # Validate request
        if not data:
            log.warning(f"[{request_id}] Empty request body")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Empty request body",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        if "text" not in data:
            log.warning(f"[{request_id}] Missing 'text' field in request")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing 'text' field",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        text = data["text"]
        text_length = len(text)
        text_preview = text[:50] + "..." if len(text) > 50 else text

        log.info(
            f"[{request_id}] Text received: {text_length} chars, " f"preview: '{text_preview}'"
        )

        # Validate text length
        if text_length == 0:
            log.warning(f"[{request_id}] Empty text provided")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Empty text provided",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        if text_length > 10000:
            log.warning(f"[{request_id}] Text too long: {text_length} chars (max: 10000)")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Text too long: {text_length} chars (max: 10000)",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        # Track request metrics
        embed_requests_total.labels(endpoint=endpoint_name, status="success").inc()
        log.debug(f"[{request_id}] Starting embedding process")

        # Perform embedding
        start = time.time()

        try:
            embedding, token_count = embed_single(text)
            duration = time.time() - start

            log.info(
                f"[{request_id}] Embedding successful: "
                f"{token_count} tokens, {duration*1000:.1f}ms, "
                f"dim={len(embedding)}"
            )

        except Exception as embed_error:
            log.error(f"[{request_id}] Embedding failed: {embed_error}", exc_info=True)
            raise

        # Update metrics
        embed_request_duration.labels(endpoint=endpoint_name).observe(duration)
        embed_token_count.labels(endpoint=endpoint_name).observe(token_count)

        # Log performance warnings
        if duration > 1.0:
            log.warning(f"[{request_id}] Slow embedding detected: {duration*1000:.1f}ms")

        if token_count > 100:
            log.debug(
                f"[{request_id}] Large text: {token_count} tokens " f"(~{token_count * 4} chars)"
            )

        # Build response
        response_data = {
            "status": "success",
            "embedding": embedding,
            "token_count": token_count,
            "dimension": Config.EMBEDDING_DIM,
            "latency_ms": round(duration * 1000, 2),
            "request_id": request_id,
        }

        log.info(
            f"[{request_id}] Response ready: " f"status=200, size={len(str(response_data))} bytes"
        )

        return jsonify(response_data), 200

    except Exception as e:
        # Log full error details
        log.error(f"[{request_id}] Unhandled exception in /embed endpoint", exc_info=True)
        log.error(f"[{request_id}] Error type: {type(e).__name__}, " f"Error message: {str(e)}")

        # Update error metrics
        embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()

        # Return error response
        error_response = {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "request_id": request_id,
        }

        log.info(f"[{request_id}] Error response sent: status=500")

        return jsonify(error_response), 500


@app.route("/embed/batch", methods=["POST"])
def embed_batch_endpoint():
    """
    Embed batch of texts with comprehensive logging

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
    endpoint_name = "embed_batch"
    request_id = g.request_id

    # Log request start
    log.info(f"[{request_id}] POST /embed/batch - Request received")

    try:
        # Parse request body
        log.debug(f"[{request_id}] Parsing batch request body")
        data = request.get_json(silent=True)

        # Validate request body exists
        if not data:
            log.warning(f"[{request_id}] Empty request body")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Empty request body",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        # Validate 'texts' field exists
        if "texts" not in data:
            log.warning(f"[{request_id}] Missing 'texts' field in batch request")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing 'texts' field",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        texts = data["texts"]

        # Validate 'texts' is a list
        if not isinstance(texts, list):
            log.warning(
                f"[{request_id}] Invalid 'texts' type: {type(texts).__name__} " f"(expected list)"
            )
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "'texts' must be an array",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        batch_size = len(texts)

        # Validate batch not empty
        if batch_size == 0:
            log.warning(f"[{request_id}] Empty texts array provided")
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Empty texts array",
                        "request_id": request_id,
                    }
                ),
                400,
            )

        # Calculate batch statistics
        total_chars = sum(len(str(t)) for t in texts)
        avg_chars = total_chars / batch_size
        max_text_len = max(len(str(t)) for t in texts)
        min_text_len = min(len(str(t)) for t in texts)

        log.info(
            f"[{request_id}] Batch request: {batch_size} texts, "
            f"total_chars={total_chars}, avg_chars={avg_chars:.1f}, "
            f"min={min_text_len}, max={max_text_len}"
        )

        # Validate batch size
        if batch_size > Config.MAX_BATCH_SIZE:
            log.warning(
                f"[{request_id}] Batch size {batch_size} exceeds "
                f"maximum {Config.MAX_BATCH_SIZE}"
            )
            embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Batch size exceeds maximum ({Config.MAX_BATCH_SIZE})",
                        "max_allowed": Config.MAX_BATCH_SIZE,
                        "provided": batch_size,
                        "request_id": request_id,
                    }
                ),
                400,
            )

        # Check for any extremely long texts
        long_texts = [i for i, t in enumerate(texts) if len(str(t)) > 5000]
        if long_texts:
            log.warning(
                f"[{request_id}] Found {len(long_texts)} texts longer than 5000 chars: "
                f"indices={long_texts[:5]}"  # Show first 5
            )

        # Log batch details
        log.debug(
            f"[{request_id}] Batch breakdown: "
            f"empty_texts={sum(1 for t in texts if not str(t).strip())}, "
            f"valid_texts={sum(1 for t in texts if str(t).strip())}"
        )

        # Track successful request
        embed_requests_total.labels(endpoint=endpoint_name, status="success").inc()
        log.debug(f"[{request_id}] Starting batch embedding process")

        # Perform batch embedding
        start = time.time()

        try:
            embeddings, token_counts = embed_batch(texts)
            duration = time.time() - start

            # Calculate batch statistics
            total_tokens = sum(token_counts)
            avg_tokens = total_tokens / batch_size
            max_tokens = max(token_counts)
            min_tokens = min(token_counts)
            avg_time_per_text = (duration / batch_size) * 1000

            log.info(
                f"[{request_id}] Batch embedding successful: "
                f"{batch_size} texts, {total_tokens} total tokens "
                f"(avg={avg_tokens:.1f}, min={min_tokens}, max={max_tokens}), "
                f"{duration*1000:.1f}ms total ({avg_time_per_text:.1f}ms/text)"
            )

        except Exception as embed_error:
            log.error(
                f"[{request_id}] Batch embedding failed during processing: {embed_error}",
                exc_info=True,
            )
            raise

        # Update metrics
        embed_request_duration.labels(endpoint=endpoint_name).observe(duration)
        embed_token_count.labels(endpoint=endpoint_name).observe(total_tokens)
        embed_batch_size.observe(batch_size)

        # Performance warnings
        if duration > 5.0:
            log.warning(
                f"[{request_id}] Slow batch embedding: {duration*1000:.1f}ms "
                f"for {batch_size} texts (>{5.0}s threshold)"
            )

        if avg_time_per_text > 200:
            log.warning(f"[{request_id}] High per-text latency: {avg_time_per_text:.1f}ms/text")

        # Check for failed embeddings (zero vectors)
        zero_embeddings = sum(1 for emb in embeddings if all(v == 0.0 for v in emb))
        if zero_embeddings > 0:
            log.warning(
                f"[{request_id}] Found {zero_embeddings} zero embeddings " f"(likely empty inputs)"
            )

        # Build response
        response_data = {
            "status": "success",
            "embeddings": embeddings,
            "token_counts": token_counts,
            "dimension": Config.EMBEDDING_DIM,
            "count": batch_size,
            "latency_ms": round(duration * 1000, 2),
            "request_id": request_id,
        }

        response_size = len(str(response_data))
        log.info(
            f"[{request_id}] Batch response ready: "
            f"status=200, size={response_size} bytes "
            f"(~{response_size/1024:.1f} KB)"
        )

        # Warn if response is large
        if response_size > 1_000_000:  # 1MB
            log.warning(f"[{request_id}] Large response size: {response_size/1024/1024:.2f} MB")

        return jsonify(response_data), 200

    except Exception as e:
        # Log full error details
        log.error(
            f"[{request_id}] Unhandled exception in /embed/batch endpoint",
            exc_info=True,
        )
        log.error(f"[{request_id}] Error type: {type(e).__name__}, " f"Error message: {str(e)}")

        # Log batch context if available
        if "batch_size" in locals():
            log.error(
                f"[{request_id}] Batch context: "
                f"batch_size={batch_size}, "
                f"total_chars={total_chars if 'total_chars' in locals() else 'N/A'}"
            )

        # Update error metrics
        embed_requests_total.labels(endpoint=endpoint_name, status="error").inc()

        # Return error response
        error_response = {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__,
            "request_id": request_id,
        }

        log.info(f"[{request_id}] Error response sent: status=500")

        return jsonify(error_response), 500


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
            content_type_res = [t.value for t in ContentType]
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Invalid content_type. Must be one of: {content_type_res}",
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
                        chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text
                    ),  # Truncate for response
                    "token_count": token_count,
                }
            )

        elapsed = (time.time() - start) * 1000

        log.debug(f"Content embedded: {len(chunks)} chunks in {elapsed:.1f}ms")

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
        log.info(f"Content embedding failed: {e}\n{traceback.format_exc()}")
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

    log.info(f"📦 Model: {Config.MODEL_NAME}")
    log.info(f"📊 Embedding dimension: {Config.EMBEDDING_DIM}")
    log.info(f"🔢 Max tokens: {Config.MAX_TOKENS}")
    log.info(f"⚡ Batch size: {Config.BATCH_SIZE}")

    # Pre-load model
    try:
        model_manager.load_model()
    except Exception as e:
        log.info(f"Failed to load model: {e}")
        log.warning("Service will start but embedding will fail until model loads")

    log.info(f"🌐 Server running on http://{Config.HOST}:{Config.PORT}")
    log.info("\n📚 Endpoints:")
    log.info("  GET  /                  - Service info")
    log.info("  GET  /health            - Health check")
    log.info("  GET  /metrics           - Prometheus metrics")
    log.info("  POST /embed             - Embed single text")
    log.info("  POST /embed/batch       - Embed batch of texts")
    log.info("  POST /embed/content     - Content-aware embedding")

    # Enable debug mode via environment variable
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    try:
        app.run(host=Config.HOST, port=Config.PORT, debug=debug_mode)
    finally:
        system_monitor.stop()
