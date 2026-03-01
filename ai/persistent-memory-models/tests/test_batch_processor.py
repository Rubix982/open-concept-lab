import unittest
from unittest.mock import MagicMock

from persistent_memory.processors import BatchProcessor, BatchConfig, DocumentScanner


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


if __name__ == "__main__":
    unittest.main()
