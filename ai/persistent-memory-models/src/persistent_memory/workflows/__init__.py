from .book_ingestion_workflow import IngestBookWorkflow
from .paper_ingestion_workflow import (
    PaperIngestionParams,
    PaperMetadata,
    ResearchPaperIngestionWorkflow,
    fetch_papers_activity,
    process_paper_activity,
    extract_facts_from_paper_activity,
    update_attention_model_activity,
)

__version__ = "0.1.0"

__all__ = [
    "IngestBookWorkflow",
    "PaperIngestionParams",
    "PaperMetadata",
    "ResearchPaperIngestionWorkflow",
    "fetch_papers_activity",
    "process_paper_activity",
    "extract_facts_from_paper_activity",
    "update_attention_model_activity",
]
