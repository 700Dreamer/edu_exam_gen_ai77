import asyncio
import os
import sys

from core.models import create_db_and_tables
from core.worker_engine import process_worker_loop, get_queue_metrics

async def main():
    print("=" * 60)
    print("      EDULYTICS DEDICATED BACKGROUND WORKER PROCESS     ")
    print("=" * 60)
    print("Initializing Database and Task Queues...")
    await create_db_and_tables()
    
    metrics = await get_queue_metrics()
    print(f"Initial Queue Metrics: {metrics}")
    
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "3"))
    poll_interval = float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))
    
    print(f"Worker process active. Polling queue every {poll_interval}s with concurrency {concurrency}...")
    try:
        await process_worker_loop(single_run=False, poll_interval=poll_interval, max_concurrency=concurrency)
    except KeyboardInterrupt:
        print("Worker process shutting down gracefully...")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
