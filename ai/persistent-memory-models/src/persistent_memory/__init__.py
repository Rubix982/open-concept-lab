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

# Subdirectories
from .stores import *
from .core import *
from .processors import *
from .stores import *

__version__ = "0.1.0"

__all__ = [
    *stores.__all__,
    *core.__all__,
    *processors.__all__,
]
