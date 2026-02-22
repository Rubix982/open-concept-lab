import unittest
import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from persistent_memory.processors import BatchProcessor, BatchConfig, DocumentScanner

logger = logging.getLogger(__name__)


class TestBatchProcessor(unittest.TestCase):
    def setUp(self):
        self.config = BatchConfig(batch_size=2, max_concurrent=2, retry_attempts=1)
        self.processor = BatchProcessor(self.config)

    def test_batch_creation(self):
        files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
        batches = self.processor._create_batches(files)
        self.assertEqual(len(batches), 2)
        self.assertEqual(len(batches[0]), 2)
        self.assertEqual(len(batches[1]), 2)

    def test_process_with_retry(self):
        mock_processor = MagicMock()
        mock_processor.return_value = "processed"
        result = self.processor._process_with_retry("file1.txt", mock_processor)
        self.assertEqual(result, "processed")
        mock_processor.assert_called_once_with("file1.txt")

    def test_process_with_retry_failure(self):
        mock_processor = MagicMock()
        mock_processor.side_effect = Exception("Error")
        with self.assertRaises(Exception):
            self.processor._process_with_retry("file1.txt", mock_processor)

    def test_process_documents(self):
        files = ["file1.txt", "file2.txt", "file3.txt", "file4.txt"]
        mock_processor = MagicMock()
        mock_processor.return_value = "processed"
        summary = self.processor.process_documents(files, mock_processor)
        self.assertEqual(summary["processed"], 4)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["success_rate"], 1.0)

    def test_document_scanner(self):
        scanner = DocumentScanner()
        files = scanner.scan_directory("./data", recursive=True)
        self.assertIsInstance(files, list)

    async def test_end_to_end_demo(self):
        """Demo batch processing."""
        logging.basicConfig(level=logging.INFO)

        async def mock_processor(file_path: str):
            """Mock document processor."""
            await asyncio.sleep(0.5)  # Simulate processing
            logger.info(f"Processed: {file_path}")
            return {"file": file_path, "chunks": 10}

        def progress_callback(current, total, file_path):
            """Progress callback."""
            percent = (current / total) * 100
            print(f"Progress: {current}/{total} ({percent:.1f}%) - {file_path}")

        # Scan for documents
        scanner = DocumentScanner()
        files = scanner.scan_directory("./data", recursive=True)

        # Process in batches
        processor = BatchProcessor(BatchConfig(batch_size=5, max_concurrent=3))

        summary = await processor.process_documents(
            files, mock_processor, progress_callback
        )

        print(f"\nSummary: {summary}")


if __name__ == "__main__":
    unittest.main()
