import asyncio
from datetime import timedelta

from temporalio import workflow

# Import activities (we will define these next)
with workflow.unsafe.imports_passed_through():
    from persistent_memory.activities import (
        IngestBookParams,
        IngestBookResult,
        chunk_text_activity,
        download_book_activity,
        embed_and_store_activity,
        extract_facts_activity,
    )


@workflow.defn
class IngestBookWorkflow:
    @workflow.run
    async def run(self, params: IngestBookParams) -> IngestBookResult:
        # 1. Download/Read Book
        text_content = await workflow.execute_activity(
            download_book_activity, params.book_path, start_to_close_timeout=timedelta(seconds=60)
        )

        # 2. Chunk Text
        chunks = await workflow.execute_activity(
            chunk_text_activity, text_content, start_to_close_timeout=timedelta(seconds=60)
        )

        # 3. Process Chunks (Embed & Extract) in Parallel
        # We batch them to avoid overwhelming downstream services
        results = []
        batch_size = 10

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            # Launch parallel activities for this batch
            batch_futures = []
            for chunk in batch:
                # Embed and Store (Vector DB)
                batch_futures.append(
                    workflow.execute_activity(
                        embed_and_store_activity,
                        chunk,
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                )
                # Extract Facts (Knowledge Graph)
                batch_futures.append(
                    workflow.execute_activity(
                        extract_facts_activity, chunk, start_to_close_timeout=timedelta(seconds=60)
                    )
                )

            # Wait for batch to complete
            batch_results = await asyncio.gather(*batch_futures)
            results.extend(batch_results)

        return IngestBookResult(total_chunks=len(chunks), status="COMPLETED")
