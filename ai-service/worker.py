"""
AI Service Worker

This worker processes AI-related jobs from the Redis queue:
- Magic trick detection from text
- Similarity calculations and cross-references  
- Model training and fine-tuning
"""

import os
import sys
import logging
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AI processing functions
from ai_processor import process_text, train_model

def main():
    """Main worker process"""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    logger.info(f"Starting AI worker, connecting to Redis: {redis_url}")
    
    # Connect to Redis
    redis_conn = redis.from_url(redis_url, decode_responses=True)
    
    # Create queues to listen to
    ai_queue = Queue('ai', connection=redis_conn)
    training_queue = Queue('training', connection=redis_conn)
    
    # Create worker that listens to both queues
    worker = Worker([ai_queue, training_queue], connection=redis_conn, name='ai-worker')
    
    logger.info("AI worker started, waiting for jobs...")
    
    try:
        # Start processing jobs
        worker.work(with_scheduler=True, logging_level='INFO')
    except KeyboardInterrupt:
        logger.info("Worker interrupted, shutting down...")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()