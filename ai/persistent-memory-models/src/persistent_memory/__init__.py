"""
Persistent Memory Models
=======================

A production-grade AI memory system with hierarchical attention, 
knowledge graphs, and research paper ingestion capabilities.
"""

# PATCH: Fix for chromadb 0.3.23 compatibility with Pydantic v2
try:
    import pydantic
    from pydantic_settings import BaseSettings
    pydantic.BaseSettings = BaseSettings
except ImportError:
    pass

# Core Memory Components
try:
    from .persistent_vector_store import PersistentVectorStore
except ImportError:
    PersistentVectorStore = None
except Exception:
    # Handle pydantic validation errors
    PersistentVectorStore = None

from .persistent_knowledge_graph import PersistentKnowledgeGraph
from .persistent_context import PersistentContextAI as PersistentContext

# Research & Data Components
from .arxiv_downloader import ArxivDownloader, ArxivPaper
from .data_repository import DataRepository, get_repository
from .conference_connector import ConferenceConnector, Conference

# Attention & Retrieval
from .hierarchical_attention import HierarchicalAttentionNetwork
from .attention_retrieval import AttentionEnhancedRetrieval

# Workflows
from .paper_ingestion_workflow import ResearchPaperIngestionWorkflow
from .ingestion_workflow import IngestBookWorkflow

# Utilities
from .fact_extractor import FactExtractor

__version__ = "0.1.0"

__all__ = [
    # Core
    "PersistentVectorStore",
    "PersistentKnowledgeGraph",
    "PersistentContext",
    
    # Research
    "ArxivDownloader",
    "ArxivPaper",
    "DataRepository",
    "get_repository",
    "ConferenceConnector",
    "Conference",
    
    # Attention
    "HierarchicalAttentionNetwork",
    "AttentionEnhancedRetrieval",
    
    # Workflows
    "ResearchPaperIngestionWorkflow",
    "IngestBookWorkflow",
    
    # Utils
    "FactExtractor",
]
