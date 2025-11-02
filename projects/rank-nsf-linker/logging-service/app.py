"""
Self-Hosted Logging Service - A Sentry Alternative
Receives, processes, and stores client-side logs with rich metadata
Uses Elasticsearch for powerful search and analytics
"""

import os
import json
import time
import random
import dotenv
import logging
import hashlib
import traceback
import inspect

from colorama import Fore, Style, init
from flask import Flask, request, jsonify
from flask_cors import CORS
from dataclasses import dataclass, asdict
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from logging.handlers import RotatingFileHandler

dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for client-side requests


# --- Configuration ---
class Config:
    LOG_DIR = Path("logs")
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB per log file
    BACKUP_COUNT = 5  # Keep 5 rotated log files
    LOG_LEVELS = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    # Elasticsearch Configuration
    ES_HOST = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
    ES_TIMEOUT = 30

    # Index names
    ERRORS_INDEX = "logging-errors"
    OCCURRENCES_INDEX = "logging-occurrences"


# Create logs directory
Config.LOG_DIR.mkdir(exist_ok=True)


# --- Data Models ---
@dataclass
class LogEntry:
    """Structured log entry with rich metadata"""

    timestamp: str
    level: str
    message: str
    url: Optional[str] = None
    user_agent: Optional[str] = None
    client_ip: Optional[str] = None
    fingerprint: Optional[str] = None
    stack_trace: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    environment: Optional[str] = "production"
    extra_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


# --- Elasticsearch Client ---
es_client: Optional[Elasticsearch] = None


def init_elasticsearch():
    """Initialize Elasticsearch client and indices with exponential backoff"""
    global es_client

    base_delay = 1.0  # starting delay in seconds
    max_delay = 60.0  # cap max sleep time to 60s
    attempt: int = 0

    while True:
        attempt += 1
        try:
            es_client = Elasticsearch(
                [Config.ES_HOST],
                request_timeout=Config.ES_TIMEOUT,
                retry_on_timeout=True,
                max_retries=3,
                verify_certs=False,
            )

            if es_client.ping():
                app.logger.info("✅ Elasticsearch connected")
                create_indices()
                return es_client

            raise ConnectionError("Ping failed")

        except Exception as e:
            wait_time = min(base_delay * (2 ** (attempt - 1)), max_delay)
            # Add a bit of jitter to avoid sync retries
            wait_time += random.uniform(0, 0.5)
            app.logger.warning(
                f"⚠️ Attempt {attempt} has failed to connect to Elasticsearch: {e} at {Config.ES_HOST}. Retrying..."
            )

            app.logger.info(f"⏳ Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)


def create_indices():
    """Create Elasticsearch indices with proper mappings"""

    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    # Errors index mapping
    errors_mapping: Dict[str, Any] = {
        "mappings": {
            "properties": {
                "fingerprint": {"type": "keyword"},
                "first_seen": {"type": "date"},
                "last_seen": {"type": "date"},
                "count": {"type": "integer"},
                "level": {"type": "keyword"},
                "message": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "url": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "resolved": {"type": "boolean"},
                "latest_stack_trace": {"type": "text"},
                "latest_extra_data": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    }

    # Occurrences index mapping
    occurrences_mapping: Dict[str, Any] = {
        "mappings": {
            "properties": {
                "error_fingerprint": {"type": "keyword"},
                "timestamp": {"type": "date"},
                "client_ip": {"type": "ip"},
                "user_agent": {"type": "text"},
                "user_id": {"type": "keyword"},
                "session_id": {"type": "keyword"},
                "level": {"type": "keyword"},
                "message": {"type": "text"},
                "url": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "stack_trace": {"type": "text"},
                "extra_data": {"type": "object", "enabled": True},
            }
        },
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    }

    # Create indices if they don't exist
    if not es_client.indices.exists(index=Config.ERRORS_INDEX):
        es_client.indices.create(index=Config.ERRORS_INDEX, body=errors_mapping)
        app.logger.info(f"✅ Created index: {Config.ERRORS_INDEX}")

    if not es_client.indices.exists(index=Config.OCCURRENCES_INDEX):
        es_client.indices.create(
            index=Config.OCCURRENCES_INDEX, body=occurrences_mapping
        )
        app.logger.info(f"✅ Created index: {Config.OCCURRENCES_INDEX}")

init(autoreset=True)  # ensures color reset after each print

# --- Logging Configuration ---
class StructuredLogger:
    """Enhanced logging with rotation, structured output, line info, and colors"""

    LEVEL_COLORS = {
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "WARN": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.MAGENTA,
    }

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear()

        # Rotating file handler
        log_file = Config.LOG_DIR / "client_errors.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=Config.MAX_LOG_SIZE,
            backupCount=Config.BACKUP_COUNT,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
            datefmt="%H:%M:%S",
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

    def log(self, level: str, entry: LogEntry):
        """Log a structured entry with line info and colors"""
        log_data = entry.to_dict()
        message = json.dumps(log_data, ensure_ascii=False)

        # Get caller info
        current_frame = inspect.currentframe()
        frame = current_frame.f_back if current_frame is not None else None
        filename = frame.f_code.co_filename if frame is not None else "<unknown>"
        lineno = frame.f_lineno if frame is not None else 0

        log_level = Config.LOG_LEVELS.get(level.lower(), logging.INFO)

        # Add color for console output
        color = self.LEVEL_COLORS.get(level.upper(), "")
        colored_message = f"{color}{message}{Style.RESET_ALL}"

        # Log to console and file
        self.logger.log(log_level, f"{filename}:{lineno} | {colored_message}")


logger = StructuredLogger("client_logger")


# --- Error Fingerprinting ---
def generate_fingerprint(
    message: str, url: str, stack_trace: Optional[str] = None
) -> str:
    """
    Generate a unique fingerprint for error grouping
    Similar errors will have the same fingerprint
    """
    # Normalize the message (remove dynamic parts like IDs, timestamps)
    normalized = f"{message}|{url}"

    if stack_trace:
        # Use first 3 lines of stack trace for fingerprinting
        stack_lines = stack_trace.split("\n")[:3]
        normalized += "|" + "".join(stack_lines)

    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


# --- Elasticsearch Operations ---
def store_error(entry: LogEntry) -> str:

    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Store or update error in Elasticsearch with occurrence tracking"""

    # Search for existing error by fingerprint
    search_query = {"query": {"term": {"fingerprint": entry.fingerprint}}}

    result = es_client.search(index=Config.ERRORS_INDEX, body=search_query, size=1)

    now = datetime.now(timezone.utc).isoformat()

    if result["hits"]["total"]["value"] > 0:
        # Update existing error
        doc = result["hits"]["hits"][0]
        doc_id = doc["_id"]
        current_count = doc["_source"].get("count", 0)

        update_body: Dict[str, Any] = {
            "doc": {
                "count": current_count + 1,
                "last_seen": now,
                "updated_at": now,
                "latest_stack_trace": entry.stack_trace,
                "latest_extra_data": entry.extra_data,
            }
        }

        es_client.update(index=Config.ERRORS_INDEX, id=doc_id, body=update_body)
        error_id = doc_id
    else:
        # Create new error
        error_doc: Dict[str, Any] = {
            "fingerprint": entry.fingerprint,
            "first_seen": now,
            "last_seen": now,
            "count": 1,
            "level": entry.level,
            "message": entry.message,
            "url": entry.url,
            "environment": entry.environment,
            "resolved": False,
            "latest_stack_trace": entry.stack_trace,
            "latest_extra_data": entry.extra_data,
            "created_at": now,
            "updated_at": now,
        }

        result = es_client.index(index=Config.ERRORS_INDEX, document=error_doc)
        error_id = result["_id"]

    # Store occurrence
    occurrence_doc: Dict[str, Any] = {
        "error_fingerprint": entry.fingerprint,
        "timestamp": now,
        "client_ip": entry.client_ip,
        "user_agent": entry.user_agent,
        "user_id": entry.user_id,
        "session_id": entry.session_id,
        "level": entry.level,
        "message": entry.message,
        "url": entry.url,
        "environment": entry.environment,
        "stack_trace": entry.stack_trace,
        "extra_data": entry.extra_data,
    }

    es_client.index(index=Config.OCCURRENCES_INDEX, document=occurrence_doc)

    # Refresh indices to make documents searchable immediately
    es_client.indices.refresh(index=Config.ERRORS_INDEX)

    return error_id


# --- API Endpoints ---
@app.route("/health", methods=["GET"])
def health_check():
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Health check endpoint with Elasticsearch connectivity check"""
    try:
        es_health = es_client.cluster.health()

        return (
            jsonify(
                {
                    "status": "healthy",
                    "service": "logging-service",
                    "version": "1.0.0",
                    "elasticsearch": {
                        "status": es_health["status"],
                        "cluster_name": es_health["cluster_name"],
                    },
                }
            ),
            200,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "service": "logging-service",
                    "elasticsearch": "disconnected",
                    "error": str(e),
                }
            ),
            503,
        )


@app.route("/logs/log", methods=["POST"])
def receive_log():
    """
    Main endpoint for receiving client logs

    Expected payload:
    {
        "level": "error",
        "message": "Something went wrong",
        "url": "https://example.com/page",
        "stack_trace": "Error: ...\n at ...",
        "user_id": "user123",
        "session_id": "sess456",
        "environment": "production",
        "extra": { "customField": "value" }
    }
    """
    try:
        data = request.get_json(silent=True)

        if not data:
            app.logger.warning(f"Invalid JSON payload from {request.remote_addr}")
            return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400

        # Validate required fields
        if "message" not in data:
            return (
                jsonify(
                    {"status": "error", "message": "Missing required field: message"}
                ),
                400,
            )

        # Extract and structure log data
        level = data.get("level", "info").lower()
        message = data.get("message", "No message provided")
        url = data.get("url", "N/A")

        # Generate fingerprint for error grouping
        fingerprint = generate_fingerprint(message, url, data.get("stack_trace"))

        # Create structured log entry
        entry = LogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level,
            message=message,
            url=url,
            user_agent=request.headers.get("User-Agent"),
            client_ip=request.remote_addr,
            fingerprint=fingerprint,
            stack_trace=data.get("stack_trace"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            environment=data.get("environment", "production"),
            extra_data=data.get("extra"),
        )

        # Log to file
        logger.log(level, entry)

        # Store in Elasticsearch for errors and above
        if level in ["error", "critical"]:
            error_id = store_error(entry)
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Log received and stored",
                        "error_id": error_id,
                        "fingerprint": fingerprint,
                    }
                ),
                200,
            )

        return jsonify({"status": "success", "message": "Log received"}), 200

    except Exception as e:
        app.logger.error(
            f"Failed to process log: {e}\n{traceback.format_exc()}", exc_info=True
        )
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/logs/errors", methods=["GET"])
def get_errors():
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Get list of errors with filtering and pagination"""
    try:
        # Query parameters
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))
        environment = request.args.get("environment")
        resolved = request.args.get("resolved", "false").lower() == "true"
        level = request.args.get("level")

        # Build Elasticsearch query
        must_conditions: List[Dict[str, Dict[str, Any]]] = [
            {"term": {"resolved": resolved}}
        ]

        if environment:
            must_conditions.append({"term": {"environment": environment}})

        if level:
            must_conditions.append({"term": {"level": level}})

        search_body: Dict[str, Any] = {
            "query": {"bool": {"must": must_conditions}},
            "sort": [{"last_seen": {"order": "desc"}}],
            "from": offset,
            "size": limit,
        }

        result = es_client.search(index=Config.ERRORS_INDEX, body=search_body)

        errors: List[Dict[str, Any]] = []
        for hit in result["hits"]["hits"]:
            error_doc: Dict[str, Any] = hit["_source"]
            error_doc["id"] = hit["_id"]
            errors.append(error_doc)

        return (
            jsonify(
                {
                    "status": "success",
                    "errors": errors,
                    "total": result["hits"]["total"]["value"],
                    "limit": limit,
                    "offset": offset,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Failed to fetch errors: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/errors/<error_id>", methods=["GET"])
def get_error_detail(error_id: str):
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Get detailed information about a specific error"""
    try:
        # Get error details
        error_doc = es_client.get(index=Config.ERRORS_INDEX, id=error_id)
        error = error_doc["_source"]
        error["id"] = error_doc["_id"]

        # Get recent occurrences
        occurrences_query: Dict[str, Any] = {
            "query": {"term": {"error_fingerprint": error["fingerprint"]}},
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": 20,
        }

        occurrences_result = es_client.search(
            index=Config.OCCURRENCES_INDEX, body=occurrences_query
        )

        occurrences: List[Dict[str, Any]] = []
        for hit in occurrences_result["hits"]["hits"]:
            occ = hit["_source"]
            occ["id"] = hit["_id"]
            occurrences.append(occ)

        return (
            jsonify(
                {"status": "success", "error": error, "recent_occurrences": occurrences}
            ),
            200,
        )

    except NotFoundError:
        return jsonify({"status": "error", "message": "Error not found"}), 404
    except Exception as e:
        app.logger.error(f"Failed to fetch error detail: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/errors/<error_id>/resolve", methods=["POST"])
def resolve_error(error_id: str):
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Mark an error as resolved"""
    try:
        update_body: Dict[str, Any] = {
            "doc": {
                "resolved": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        es_client.update(index=Config.ERRORS_INDEX, id=error_id, body=update_body)

        return (
            jsonify({"status": "success", "message": "Error marked as resolved"}),
            200,
        )

    except NotFoundError:
        return jsonify({"status": "error", "message": "Error not found"}), 404
    except Exception as e:
        app.logger.error(f"Failed to resolve error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/errors/<error_id>/unresolve", methods=["POST"])
def unresolve_error(error_id: str):
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Mark an error as unresolved"""
    try:
        update_body: Dict[str, Any] = {
            "doc": {
                "resolved": False,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        es_client.update(index=Config.ERRORS_INDEX, id=error_id, body=update_body)

        return (
            jsonify({"status": "success", "message": "Error marked as unresolved"}),
            200,
        )

    except NotFoundError:
        return jsonify({"status": "error", "message": "Error not found"}), 404
    except Exception as e:
        app.logger.error(f"Failed to unresolve error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/stats", methods=["GET"])
def get_stats():
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Get error statistics using Elasticsearch aggregations"""
    try:
        environment = request.args.get("environment")

        # Build filter
        filter_conditions: List[Dict[str, Any]] = []
        if environment:
            filter_conditions.append({"term": {"environment": environment}})

        # Aggregation query
        agg_body: Dict[str, Any] = {
            "size": 0,
            "query": (
                {"bool": {"filter": filter_conditions}}
                if filter_conditions
                else {"match_all": {}}
            ),
            "aggs": {
                "total_errors": {"value_count": {"field": "fingerprint"}},
                "unresolved_errors": {"filter": {"term": {"resolved": False}}},
                "by_level": {"terms": {"field": "level", "size": 10}},
                "top_errors": {
                    "terms": {
                        "field": "fingerprint",
                        "size": 10,
                        "order": {"_count": "desc"},
                    },
                    "aggs": {
                        "top_error_docs": {
                            "top_hits": {
                                "size": 1,
                                "_source": [
                                    "message",
                                    "count",
                                    "level",
                                    "environment",
                                    "url",
                                ],
                            }
                        }
                    },
                },
            },
        }

        result = es_client.search(index=Config.ERRORS_INDEX, body=agg_body)

        # Recent occurrences (last 24 hours)
        recent_24h_query = {"query": {"range": {"timestamp": {"gte": "now-24h"}}}}
        recent_24h = es_client.count(
            index=Config.OCCURRENCES_INDEX, body=recent_24h_query
        )

        # Recent occurrences (last hour)
        recent_1h_query = {"query": {"range": {"timestamp": {"gte": "now-1h"}}}}
        recent_1h = es_client.count(
            index=Config.OCCURRENCES_INDEX, body=recent_1h_query
        )

        # Parse aggregations
        aggs = result["aggregations"]
        by_level = {
            bucket["key"]: bucket["doc_count"] for bucket in aggs["by_level"]["buckets"]
        }

        top_errors: List[Dict[str, Any]] = []
        for bucket in aggs["top_errors"]["buckets"]:
            error_doc = bucket["top_error_docs"]["hits"]["hits"][0]["_source"]
            error_doc["occurrence_count"] = bucket["doc_count"]
            top_errors.append(error_doc)

        return (
            jsonify(
                {
                    "status": "success",
                    "stats": {
                        "total_errors": aggs["total_errors"]["value"],
                        "unresolved_errors": aggs["unresolved_errors"]["doc_count"],
                        "recent_occurrences_24h": recent_24h["count"],
                        "recent_occurrences_1h": recent_1h["count"],
                        "by_level": by_level,
                        "top_errors": top_errors,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Failed to fetch stats: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/search", methods=["GET"])
def search_errors():
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Search errors using Elasticsearch full-text search"""
    try:
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 20)), 100)
        environment = request.args.get("environment")

        if not query:
            return (
                jsonify(
                    {"status": "error", "message": "Query parameter 'q' is required"}
                ),
                400,
            )

        # Build search query
        must_conditions: List[Dict[str, Dict[str, Any]]] = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["message^2", "url", "fingerprint"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        if environment:
            must_conditions.append({"term": {"environment": environment}})

        search_body: Dict[str, Any] = {
            "query": {"bool": {"must": must_conditions}},
            "sort": [{"_score": {"order": "desc"}}, {"last_seen": {"order": "desc"}}],
            "size": limit,
            "highlight": {"fields": {"message": {}, "url": {}}},
        }

        result = es_client.search(index=Config.ERRORS_INDEX, body=search_body)

        errors: List[Dict[str, Any]] = []
        for hit in result["hits"]["hits"]:
            error_doc = hit["_source"]
            error_doc["id"] = hit["_id"]
            error_doc["score"] = hit["_score"]
            if "highlight" in hit:
                error_doc["highlight"] = hit["highlight"]
            errors.append(error_doc)

        return (
            jsonify(
                {
                    "status": "success",
                    "results": errors,
                    "total": result["hits"]["total"]["value"],
                    "count": len(errors),
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Search failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/timeline", methods=["GET"])
def get_timeline():
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Get error occurrence timeline using date histogram aggregation"""
    try:
        interval = request.args.get("interval", "1h")  # 1h, 1d, 1w, etc.
        hours = int(request.args.get("hours", 24))
        environment = request.args.get("environment")

        # Build filter
        filter_conditions: List[Dict[str, Any]] = [
            {"range": {"timestamp": {"gte": f"now-{hours}h"}}}
        ]

        if environment:
            filter_conditions.append({"term": {"environment": environment}})

        # Date histogram aggregation
        agg_body: Dict[str, Any] = {
            "size": 0,
            "query": {"bool": {"filter": filter_conditions}},
            "aggs": {
                "timeline": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0,
                        "extended_bounds": {"min": f"now-{hours}h", "max": "now"},
                    },
                    "aggs": {"by_level": {"terms": {"field": "level"}}},
                }
            },
        }

        result = es_client.search(index=Config.OCCURRENCES_INDEX, body=agg_body)

        timeline: List[Dict[str, Any]] = []
        for bucket in result["aggregations"]["timeline"]["buckets"]:
            by_level = {b["key"]: b["doc_count"] for b in bucket["by_level"]["buckets"]}
            timeline.append(
                {
                    "timestamp": bucket["key_as_string"],
                    "total": bucket["doc_count"],
                    "by_level": by_level,
                }
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "timeline": timeline,
                    "interval": interval,
                    "hours": hours,
                }
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Failed to fetch timeline: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/logs/errors/bulk-resolve", methods=["POST"])
def bulk_resolve():
    global es_client
    if es_client is None:
        raise Exception("Elasticsearch client is not initialized")

    """Bulk resolve errors by fingerprints"""
    try:
        data = request.get_json()
        fingerprints = data.get("fingerprints", [])

        if not fingerprints:
            return (
                jsonify({"status": "error", "message": "No fingerprints provided"}),
                400,
            )

        # Update all matching documents
        update_body: Dict[str, Any] = {
            "query": {"terms": {"fingerprint": fingerprints}},
            "script": {
                "source": "ctx._source.resolved = true; ctx._source.updated_at = params.now",
                "params": {"now": datetime.now(timezone.utc).isoformat()},
            },
        }

        result = es_client.update_by_query(index=Config.ERRORS_INDEX, body=update_body)

        return (
            jsonify(
                {"status": "success", "message": f"Resolved {result['updated']} errors"}
            ),
            200,
        )

    except Exception as e:
        app.logger.error(f"Bulk resolve failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# --- Error Handlers ---
@app.errorhandler(404)
def not_found(e: Exception):
    return jsonify({"status": "error", "message": f"Endpoint not found: {e}"}), 404


@app.errorhandler(500)
def internal_error(e: Exception):
    return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500


if __name__ == "__main__":
    print("🚀 Starting Self-Hosted Logging Service")
    print(
        """
██████   █████  ███    ██ ██   ██     ███    ██ ███████ ███████     ██      ██ ███    ██ ██   ██ ███████ ██████  
██   ██ ██   ██ ████   ██ ██  ██      ████   ██ ██      ██          ██      ██ ████   ██ ██  ██  ██      ██   ██ 
██████  ███████ ██ ██  ██ █████       ██ ██  ██ ███████ █████       ██      ██ ██ ██  ██ █████   █████   ██████  
██   ██ ██   ██ ██  ██ ██ ██  ██      ██  ██ ██      ██ ██          ██      ██ ██  ██ ██ ██  ██  ██      ██   ██ 
██   ██ ██   ██ ██   ████ ██   ██     ██   ████ ███████ ██          ███████ ██ ██   ████ ██   ██ ███████ ██   ██"""
    )
    print(f"📁 Logs directory: {Config.LOG_DIR.absolute()}")

    # Initialize Elasticsearch
    try:
        init_elasticsearch()
        print(f"🔍 Elasticsearch: {Config.ES_HOST}")
        print(f"📊 Indices: {Config.ERRORS_INDEX}, {Config.OCCURRENCES_INDEX}")
    except Exception as e:
        print(f"❌ Elasticsearch initialization failed: {e}")
        print("⚠️  Service will start but storage features will be unavailable")

    print("🌐 Server running on http://0.0.0.0:5000")
    print("\n📚 Endpoints:")
    print("  POST /logs/log                      - Receive logs")
    print("  GET  /logs/errors                   - List errors (with filters)")
    print("  GET  /logs/errors/<id>              - Error details")
    print("  POST /logs/errors/<id>/resolve      - Resolve error")
    print("  POST /logs/errors/<id>/unresolve    - Unresolve error")
    print("  POST /logs/errors/bulk-resolve      - Bulk resolve errors")
    print("  GET  /logs/stats                    - Statistics")
    print("  GET  /logs/search?q=<query>         - Full-text search")
    print("  GET  /logs/timeline                 - Error timeline")
    print("  GET  /health                       - Health check")
    print("\n💡 Environment variables:")
    print("  ELASTICSEARCH_HOST (default: http://elasticsearch:9200)")

    app.run(host="0.0.0.0", port=5257, debug=False)
