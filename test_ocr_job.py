#!/usr/bin/env python3
"""
Test script to create a mock OCR job for testing dashboard display.
"""

import redis
from datetime import datetime

def create_test_ocr_job():
    """Create a test OCR job in Redis for dashboard testing."""
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Create a test job ID
    test_job_id = "test-ocr-job-123"
    job_key = f"job:{test_job_id}"
    
    # Create job metadata
    job_data = {
        'id': test_job_id,
        'type': 'ocr',
        'status': 'started',  # Make it appear as active
        'function': 'ocr_processor.process_pdf',
        'created_at': datetime.utcnow().isoformat(),
        'queue': 'ocr',
        'book_title': 'Test Magic Book - OCR Processing',
        'file_path': '/app/temp/test_book.pdf',
        'message': 'Extracting text and images from PDF...',
        'progress': '45'  # 45% complete
    }
    
    # Store in Redis
    r.hset(job_key, mapping=job_data)
    r.expire(job_key, 3600)  # Expire in 1 hour
    
    print(f"Created test OCR job: {test_job_id}")
    print("Job data:", job_data)

if __name__ == "__main__":
    create_test_ocr_job()