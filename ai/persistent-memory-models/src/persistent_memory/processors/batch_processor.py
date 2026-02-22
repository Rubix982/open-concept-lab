"""Batch processing for efficient ingestion."""

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""

    batch_size: int = 10
    max_concurrent: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0


class BatchProcessor:
    """
    Process multiple documents in batches for efficiency.

    Features:
    - Concurrent processing with limits
    - Automatic retries
    - Progress tracking
    - Error handling
    """

    def __init__(self, config: BatchConfig | None = None):
        self.config = config or BatchConfig()
        self.processed = 0
        self.failed = 0
        self.errors: list[dict[str, Any]] = []

        logger.info(f"Initialized BatchProcessor: {self.config}")

    async def process_documents(
        self, file_paths: list[str], processor_func, progress_callback=None
    ) -> dict[str, Any]:
        """
        Process multiple documents in batches.

        Args:
            file_paths: List of file paths to process
            processor_func: Async function to process each file
            progress_callback: Optional callback for progress updates

        Returns:
            Summary of processing results
        """
        total = len(file_paths)
        logger.info(f"Starting batch processing of {total} documents")

        # Create batches
        batches = [
            file_paths[i : i + self.config.batch_size]
            for i in range(0, total, self.config.batch_size)
        ]

        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processing batch {batch_idx + 1}/{len(batches)}")

            # Process batch with concurrency limit
            semaphore = asyncio.Semaphore(self.config.max_concurrent)

            async def process_with_semaphore(file_path):
                async with semaphore:
                    return await self._process_with_retry(file_path, processor_func)

            # Process all files in batch concurrently
            results = await asyncio.gather(
                *[process_with_semaphore(fp) for fp in batch], return_exceptions=True
            )

            # Track results
            for file_path, result in zip(batch, results):
                if isinstance(result, Exception):
                    self.failed += 1
                    self.errors.append({"file": file_path, "error": str(result)})
                else:
                    self.processed += 1

                # Progress callback
                if progress_callback:
                    progress_callback(self.processed + self.failed, total, file_path)

        summary = {
            "total": total,
            "processed": self.processed,
            "failed": self.failed,
            "success_rate": self.processed / total if total > 0 else 0,
            "errors": self.errors,
        }

        logger.info(f"Batch processing complete: {summary}")
        return summary

    async def _process_with_retry(self, file_path: str, processor_func):
        """Process a single file with retry logic."""
        last_error = None

        for attempt in range(self.config.retry_attempts):
            try:
                result = await processor_func(file_path)
                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.config.retry_attempts} "
                    f"failed for {file_path}: {e}"
                )

                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))

        # All retries failed
        if last_error:
            raise last_error
        raise Exception(f"Failed to process {file_path}")


class DocumentScanner:
    """Scan directories for documents to ingest."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".epub"}

    @staticmethod
    def scan_directory(
        directory: str, recursive: bool = True, extensions: set | None = None
    ) -> list[str]:
        """
        Scan directory for supported documents.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            extensions: Set of file extensions to include

        Returns:
            List of file paths
        """
        extensions = extensions or DocumentScanner.SUPPORTED_EXTENSIONS
        path = Path(directory)

        if not path.exists():
            raise ValueError(f"Directory not found: {directory}")

        files: list[str] = []

        if recursive:
            for ext in extensions:
                files.extend([str(f) for f in path.rglob(f"*{ext}")])
        else:
            for ext in extensions:
                files.extend([str(f) for f in path.glob(f"*{ext}")])

        file_paths = [str(f) for f in files]
        logger.info(f"Found {len(file_paths)} documents in {directory}")

        return file_paths
