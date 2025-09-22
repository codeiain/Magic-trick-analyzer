"""
Job Queue Infrastructure using Redis and RQ

This module provides job queue functionality for asynchronous processing
of OCR and AI tasks.
"""

import json
import os
import redis
from rq import Queue, Worker
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class JobQueue:
    """Redis-based job queue manager"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_conn = redis.from_url(redis_url, decode_responses=True, encoding='utf-8', encoding_errors='replace')
        
        # Create different queues for different types of jobs
        self.ocr_queue = Queue('ocr', connection=self.redis_conn)
        self.ai_queue = Queue('ai', connection=self.redis_conn) 
        self.training_queue = Queue('training', connection=self.redis_conn)
        
        logger.info(f"Job queue initialized with Redis at {redis_url}")
    
    def enqueue_ocr_job(self, file_path: str, book_metadata: Dict[str, Any]) -> str:
        """Queue an OCR processing job"""
        # Create initial job data without job_id
        job_data = {
            'type': 'ocr',
            'file_path': file_path,
            'book_id': book_metadata.get('book_id'),
            'book_metadata': book_metadata,
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Enqueue the job
        job = self.ocr_queue.enqueue(
            'ocr_processor.process_pdf',
            job_data,
            job_timeout='60m'  # 60 minute timeout for OCR (increased for large PDFs)
        )
        
        # Update the job data to include the job ID by modifying the RQ job's data
        job_data['job_id'] = job.id
        job.save()
        
        # Store job metadata in Redis
        job_key = f"job:{job.id}"
        self.redis_conn.hset(job_key, mapping={
            'id': job.id,
            'type': 'ocr',
            'status': 'queued',
            'file_path': file_path,
            'book_title': book_metadata.get('title', 'Unknown'),
            'created_at': job_data['created_at'],
            'queue': 'ocr'
        })
        self.redis_conn.expire(job_key, timedelta(hours=24))  # Expire after 24 hours
        
        logger.info(f"OCR job queued: {job.id} for file: {file_path}")
        return job.id
    
    def enqueue_ai_job(self, book_id: str, text_content: str, parent_job_id: str = None, source: str = 'api') -> str:
        """Queue an AI processing job"""
        job_data = {
            'type': 'ai',
            'text_content': text_content,
            'book_id': book_id,
            'parent_job_id': parent_job_id,
            'source': source,
            'created_at': datetime.utcnow().isoformat()
        }
        
        job = self.ai_queue.enqueue(
            'ai_processor.process_text',  # Updated function name to match AI service
            job_data,
            timeout='15m',  # 15 minute timeout for AI
            job_timeout='15m'
        )
        
        # Store job metadata
        job_key = f"job:{job.id}"
        self.redis_conn.hset(job_key, mapping={
            'id': job.id,
            'type': 'ai',
            'status': 'queued',
            'book_id': book_id,
            'parent_job_id': parent_job_id or '',
            'source': source,
            'created_at': job_data['created_at'],
            'queue': 'ai'
        })
        self.redis_conn.expire(job_key, timedelta(hours=24))
        
        logger.info(f"AI job queued: {job.id} for book: {book_id} (source: {source})")
        return job.id
    
    def update_job_ai_info(self, job_id: str, ai_info: Dict[str, Any]) -> bool:
        """Update job with AI processing information"""
        try:
            job_key = f"job:{job_id}"
            
            # Check if job exists
            if not self.redis_conn.exists(job_key):
                logger.warning(f"Job {job_id} not found for AI info update")
                return False
            
            # Update job with AI information
            update_data = {}
            if 'ai_job_id' in ai_info:
                update_data['ai_job_id'] = ai_info['ai_job_id']
            if 'ocr_completed' in ai_info:
                update_data['ocr_completed'] = str(ai_info['ocr_completed'])
            if 'ai_queued' in ai_info:
                update_data['ai_queued'] = str(ai_info['ai_queued'])
            if 'ocr_result' in ai_info:
                update_data['ocr_result'] = json.dumps(ai_info['ocr_result'])
            if 'updated_at' in ai_info:
                update_data['updated_at'] = ai_info['updated_at']
            
            self.redis_conn.hset(job_key, mapping=update_data)
            
            logger.info(f"Updated job {job_id} with AI info: ai_job_id={ai_info.get('ai_job_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job {job_id} with AI info: {e}")
            return False
    
    def enqueue_training_job(self, training_data: Dict[str, Any]) -> str:
        """Queue a model training job"""
        job_data = {
            'type': 'training',
            'training_data': training_data,
            'created_at': datetime.utcnow().isoformat()
        }
        
        job = self.training_queue.enqueue(
            'ai_service.train_model',
            job_data,
            timeout='60m',  # 1 hour timeout for training
            job_timeout='60m'
        )
        
        # Store job metadata
        job_key = f"job:{job.id}"
        self.redis_conn.hset(job_key, mapping={
            'id': job.id,
            'type': 'training',
            'status': 'queued',
            'created_at': job_data['created_at'],
            'queue': 'training'
        })
        self.redis_conn.expire(job_key, timedelta(hours=24))
        
        logger.info(f"Training job queued: {job.id}")
        return job.id
    
    def enqueue(self, func_name: str, *args, job_timeout: str = '30m', **kwargs) -> Any:
        """Generic enqueue method for compatibility"""
        # Determine which queue to use based on function name
        if 'train' in func_name:
            queue = self.training_queue
        elif 'ocr' in func_name:
            queue = self.ocr_queue
        else:
            queue = self.ai_queue
        
        job = queue.enqueue(
            func_name,
            *args,
            timeout=job_timeout,
            job_timeout=job_timeout,
            **kwargs
        )
        
        # Store job metadata
        job_key = f"job:{job.id}"
        self.redis_conn.hset(job_key, mapping={
            'id': job.id,
            'type': 'generic',
            'status': 'queued',
            'function': func_name,
            'created_at': datetime.utcnow().isoformat(),
            'queue': queue.name
        })
        self.redis_conn.expire(job_key, timedelta(hours=24))
        
        logger.info(f"Generic job queued: {job.id} for function: {func_name}")
        return job
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and metadata"""
        job_key = f"job:{job_id}"
        
        # Get job metadata from Redis
        job_data = self.redis_conn.hgetall(job_key)
        if not job_data:
            return None
        
        # Get RQ job status
        queue_name = job_data.get('queue', 'ocr')
        queue = Queue(queue_name, connection=self.redis_conn)
        
        try:
            rq_job = queue.fetch_job(job_id)
            if rq_job:
                job_data['rq_status'] = rq_job.get_status()
                if rq_job.result:
                    try:
                        # Safely handle result conversion
                        if isinstance(rq_job.result, dict):
                            job_data['result'] = rq_job.result  # Keep as dict, let FastAPI serialize it
                        elif isinstance(rq_job.result, (str, int, float, bool, list)):
                            job_data['result'] = rq_job.result
                        else:
                            job_data['result'] = str(rq_job.result)
                    except Exception as result_error:
                        logger.warning(f"Could not serialize job result: {result_error}")
                        job_data['result'] = f"<serialization_error: {type(rq_job.result).__name__}>"
                if rq_job.exc_info:
                    job_data['error'] = str(rq_job.exc_info)
            else:
                job_data['rq_status'] = 'not_found'
        except UnicodeDecodeError as unicode_error:
            logger.warning(f"Unicode decode error for RQ job {job_id}: {unicode_error}")
            # Don't try to fetch RQ data if it contains binary data, rely on our metadata
            job_data['rq_status'] = 'metadata_only'
            job_data['warning'] = 'RQ job contains binary data, using metadata only'
        except Exception as e:
            logger.error(f"Error fetching RQ job {job_id}: {e}")
            job_data['rq_status'] = 'error'
            job_data['error'] = str(e)
        
        # Handle multi-stage job information
        if 'ai_job_id' in job_data:
            # This is a multi-stage job, get AI job status too
            ai_job_id = job_data['ai_job_id']
            ai_job_status = self.get_job_status(ai_job_id)
            
            if ai_job_status:
                job_data['ai_job_status'] = {
                    'job_id': ai_job_id,
                    'status': ai_job_status.get('rq_status', 'unknown'),
                    'result': ai_job_status.get('result'),
                    'error': ai_job_status.get('error')
                }
            else:
                job_data['ai_job_status'] = {
                    'job_id': ai_job_id,
                    'status': 'not_found'
                }
        
        # Parse OCR result if it exists
        if 'ocr_result' in job_data:
            try:
                job_data['ocr_result'] = json.loads(job_data['ocr_result'])
            except (json.JSONDecodeError, TypeError):
                pass  # Keep as string if not valid JSON
        
        # Convert boolean strings back to actual booleans
        for bool_field in ['ocr_completed', 'ai_queued']:
            if bool_field in job_data:
                job_data[bool_field] = job_data[bool_field].lower() == 'true'
        
        return job_data
    
    def update_job_status(self, job_id: str, status: str, **kwargs):
        """Update job status and metadata"""
        job_key = f"job:{job_id}"
        
        updates = {
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        updates.update(kwargs)
        
        self.redis_conn.hset(job_key, mapping=updates)
        logger.info(f"Job {job_id} status updated to: {status}")
    
    def get_active_jobs(self, job_type: str = None) -> List[Dict[str, Any]]:
        """Get list of active jobs, optionally filtered by type"""
        pattern = "job:*"
        job_keys = self.redis_conn.keys(pattern)
        
        active_jobs = []
        for job_key in job_keys:
            job_data = self.redis_conn.hgetall(job_key)
            if job_data and (not job_type or job_data.get('type') == job_type):
                job_id = job_data.get('id', '')
                
                # Try to get RQ status using the approach that works
                try:
                    # Direct Redis access for RQ status
                    rq_job_key = f"rq:job:{job_id}"
                    rq_status = self.redis_conn.hget(rq_job_key, 'status')
                    
                    if rq_status:
                        # Convert bytes to string if needed
                        if isinstance(rq_status, bytes):
                            rq_status = rq_status.decode('utf-8')
                        
                        # Update both rq_status and status fields
                        job_data['rq_status'] = rq_status
                        job_data['status'] = rq_status
                    else:
                        job_data['rq_status'] = 'not_found'
                        
                except Exception as e:
                    job_data['rq_status'] = 'error'
                    logger.warning(f"Could not get RQ status for job {job_id}: {e}")
                
                active_jobs.append(job_data)
        
        return active_jobs
    
    def list_jobs(self, status_filter: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List jobs with optional status filter and limit"""
        pattern = "job:*"
        job_keys = self.redis_conn.keys(pattern)
        
        jobs = []
        for job_key in job_keys:
            job_data = self.redis_conn.hgetall(job_key)
            if job_data:
                # Get current RQ status with error handling
                try:
                    queue_name = job_data.get('queue', 'ocr')
                    queue = Queue(queue_name, connection=self.redis_conn)
                    rq_job = queue.fetch_job(job_data['id'])
                    if rq_job:
                        job_data['rq_status'] = rq_job.get_status()
                        job_data['status'] = rq_job.get_status()  # For compatibility
                    else:
                        job_data['rq_status'] = 'not_found'
                        job_data['status'] = 'not_found'
                except UnicodeDecodeError:
                    # If RQ job contains binary data, rely on our metadata status
                    job_data['rq_status'] = 'metadata_only'
                    job_data['status'] = job_data.get('status', 'unknown')
                except Exception:
                    job_data['rq_status'] = 'unknown'
                    job_data['status'] = 'unknown'
                
                # Apply status filter if provided
                if not status_filter or job_data.get('status') == status_filter:
                    # Convert bytes to strings for JSON serialization
                    clean_job_data = {}
                    for key, value in job_data.items():
                        if isinstance(value, bytes):
                            clean_job_data[key] = value.decode('utf-8')
                        else:
                            clean_job_data[key] = value
                    
                    # Ensure required fields for JobStatusResponse
                    clean_job_data['job_id'] = clean_job_data.get('id', 'unknown')
                    if 'created_at' not in clean_job_data:
                        clean_job_data['created_at'] = datetime.utcnow().isoformat()
                    
                    jobs.append(clean_job_data)
                    
                    if len(jobs) >= limit:
                        break
        
        # Sort by creation time (most recent first)
        jobs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a specific job by ID"""
        try:
            # Get job metadata to determine which queue to check
            job_key = f"job:{job_id}"
            job_data = self.redis_conn.hgetall(job_key)
            
            if not job_data:
                logger.warning(f"Job {job_id} not found in metadata")
                return False
                
            queue_name = job_data.get('queue', 'ocr')
            
            # Get the appropriate queue
            if queue_name == 'training':
                queue = self.training_queue
            elif queue_name == 'ai':
                queue = self.ai_queue
            else:
                queue = self.ocr_queue
            
            # Try to cancel the RQ job
            try:
                rq_job = queue.fetch_job(job_id)
                if rq_job:
                    rq_job.cancel()
                    logger.info(f"Cancelled RQ job {job_id}")
                else:
                    logger.warning(f"RQ job {job_id} not found, may have already completed")
            except Exception as e:
                logger.warning(f"Error cancelling RQ job {job_id}: {e}")
            
            # Update our job metadata
            self.update_job_status(job_id, 'cancelled', 
                                 cancelled_at=datetime.utcnow().isoformat())
            
            logger.info(f"Job {job_id} marked as cancelled")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling job {job_id}: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job completely from the system"""
        try:
            job_key = f"job:{job_id}"
            job_data = self.redis_conn.hgetall(job_key)
            
            if not job_data:
                logger.warning(f"Job {job_id} not found in metadata")
                return False
            
            queue_name = job_data.get('queue', 'ocr')
            
            # Get the appropriate queue and try to cancel/remove the RQ job
            if queue_name == 'training':
                queue = self.training_queue
            elif queue_name == 'ai':
                queue = self.ai_queue
            else:
                queue = self.ocr_queue
            
            try:
                rq_job = queue.fetch_job(job_id)
                if rq_job:
                    # Cancel if it's running
                    if rq_job.get_status() in ['queued', 'started']:
                        rq_job.cancel()
                    # Delete the RQ job
                    rq_job.delete()
                    logger.info(f"Deleted RQ job {job_id}")
            except Exception as e:
                logger.warning(f"Error deleting RQ job {job_id}: {e}")
            
            # Remove our job metadata
            self.redis_conn.delete(job_key)
            logger.info(f"Removed job metadata for {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False
    
    def clear_jobs_by_status(self, status: str) -> int:
        """Clear all jobs with a specific status"""
        pattern = "job:*"
        job_keys = self.redis_conn.keys(pattern)
        
        cleared_count = 0
        for job_key in job_keys:
            job_data = self.redis_conn.hgetall(job_key)
            if job_data and job_data.get('status') == status:
                job_id = job_data.get('id')
                if job_id and self.remove_job(job_id):
                    cleared_count += 1
        
        logger.info(f"Cleared {cleared_count} jobs with status '{status}'")
        return cleared_count
    
    def clear_completed_jobs(self, max_age_hours: int = 24):
        """Clear completed jobs older than max_age_hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        pattern = "job:*"
        job_keys = self.redis_conn.keys(pattern)
        
        cleared_count = 0
        for job_key in job_keys:
            job_data = self.redis_conn.hgetall(job_key)
            if job_data:
                try:
                    created_at = datetime.fromisoformat(job_data.get('created_at', ''))
                    if created_at < cutoff_time:
                        # Check if job is completed
                        queue_name = job_data.get('queue', 'ocr')
                        queue = Queue(queue_name, connection=self.redis_conn)
                        rq_job = queue.fetch_job(job_data['id'])
                        
                        if not rq_job or rq_job.get_status() in ['finished', 'failed', 'canceled']:
                            self.redis_conn.delete(job_key)
                            cleared_count += 1
                except Exception as e:
                    logger.warning(f"Error checking job {job_key}: {e}")
        
        logger.info(f"Cleared {cleared_count} completed jobs")
        return cleared_count
    
    def get_job(self, job_id: str):
        """Get RQ job object by ID (for compatibility with training API)"""
        try:
            # Get job metadata to determine which queue to check
            job_key = f"job:{job_id}"
            job_data = self.redis_conn.hgetall(job_key)
            
            if not job_data:
                return None
                
            queue_name = job_data.get('queue', 'training')  # Default to training queue
            
            # Get the appropriate queue
            if queue_name == 'training':
                queue = self.training_queue
            elif queue_name == 'ai':
                queue = self.ai_queue
            else:
                queue = self.ocr_queue
            
            # Fetch the RQ job
            rq_job = queue.fetch_job(job_id)
            return rq_job
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {e}")
            return None

    def _wait_for_job_completion(self, job_id: str, timeout: int = 900) -> Dict[str, Any]:
        """
        Wait for a job to complete and return its result
        
        Args:
            job_id: The job ID to wait for
            timeout: Maximum time to wait in seconds (default: 15 minutes)
            
        Returns:
            Job result dictionary
        """
        import time
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if not status:
                raise Exception(f"Job {job_id} not found")
            
            if status['status'] == 'finished':
                return status.get('result', {})
            elif status['status'] == 'failed':
                raise Exception(f"Job {job_id} failed: {status.get('error', 'Unknown error')}")
            elif status['status'] == 'canceled':
                raise Exception(f"Job {job_id} was cancelled")
            
            # Wait before checking again
            time.sleep(5)
        
        # Timeout reached
        raise Exception(f"Job {job_id} did not complete within {timeout} seconds")

# Global job queue instance
_job_queue: Optional[JobQueue] = None

def get_job_queue() -> JobQueue:
    """Get or create the global job queue instance"""
    global _job_queue
    if _job_queue is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _job_queue = JobQueue(redis_url)
    return _job_queue

def init_job_queue(redis_url: str):
    """Initialize the job queue with a specific Redis URL"""
    global _job_queue
    _job_queue = JobQueue(redis_url)
    return _job_queue