import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from persistent_memory.activities import (
    chunk_text_activity,
    download_book_activity,
    embed_and_store_activity,
    extract_facts_activity,
)

# Import workflows and activities
from persistent_memory.ingestion_workflow import IngestBookWorkflow


async def main():
    # Connect to Temporal server
    temporal_host = os.getenv("TEMPORAL_HOST", "localhost:7233")

    # Retry loop for connection
    while True:
        try:
            client = await Client.connect(temporal_host)
            print(f"Successfully connected to Temporal at {temporal_host}")
            break
        except Exception as e:
            print(f"Failed to connect to Temporal at {temporal_host}: {e}")
            print("Retrying in 5 seconds...")
            await asyncio.sleep(5)

    # Run the worker
    worker = Worker(
        client,
        task_queue="ingestion-task-queue",
        workflows=[IngestBookWorkflow],
        activities=[
            download_book_activity,
            chunk_text_activity,
            embed_and_store_activity,
            extract_facts_activity,
        ],
    )

    print(f"Worker started, connecting to {temporal_host}...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
