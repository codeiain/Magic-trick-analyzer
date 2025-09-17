"""
OCR Service Worker

Redis Queue worker for processing OCR tasks in the OCR service.
"""

import os
import sys
import logging
from redis import Redis
from rq import Worker, Queue, Connection

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
    redis_conn = Redis.from_url(redis_url)
    
    logger.info(f"Connecting to Redis: {redis_url}")
    
    # Test Redis connection
    try:
        redis_conn.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        sys.exit(1)
    
    # Create queue
    queue = Queue('ocr_queue', connection=redis_conn)
    
    logger.info("Starting OCR worker...")
    
    # Start worker
    with Connection(redis_conn):
        worker = Worker([queue], name=f"ocr-worker-{os.getpid()}")
        logger.info(f"Worker started: {worker.name}")
        worker.work(with_scheduler=True)

if __name__ == '__main__':
    main()