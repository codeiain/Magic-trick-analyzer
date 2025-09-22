"""
OCR Service Worker

Redis Queue worker for processing OCR tasks in the OCR service.
"""

import os
import sys
import logging
from datetime import datetime
from redis import Redis
from rq import Worker, Queue

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import OCR processor
from ocr_processor import process_pdf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/ocr_worker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main worker function"""
    
    # Redis connection
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_conn = Redis.from_url(redis_url, decode_responses=True, encoding='utf-8', encoding_errors='replace')
    
    logger.info(f"Connecting to Redis: {redis_url}")
    
    # Test Redis connection
    try:
        redis_conn.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        sys.exit(1)
    
    # Create queue
    queue = Queue('ocr', connection=redis_conn)
    
    logger.info("Starting OCR worker...")
    
    # Start worker
    worker_name = f"ocr-worker-{os.getpid()}-{int(datetime.now().timestamp())}"
    worker = Worker([queue], connection=redis_conn, name=worker_name)
    logger.info(f"Worker started: {worker.name}")
    worker.work(with_scheduler=True)

if __name__ == '__main__':
    main()