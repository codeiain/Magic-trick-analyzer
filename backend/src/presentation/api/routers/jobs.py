"""
Jobs API Router

Handles asynchronous job management and status tracking.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.infrastructure.queue.job_queue import JobQueue

logger = logging.getLogger(__name__)

# Pydantic models for job responses
class JobStatusResponse(BaseModel):
    job_id: str
    status: str  # queued, started, finished, failed
    progress: Optional[int] = None  # 0-100
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None

class JobSubmissionResponse(BaseModel):
    job_id: str
    status: str
    message: str

# Create router
router = APIRouter(prefix="/jobs", tags=["jobs"])

# Job queue instance (will be injected in main.py)
job_queue: Optional[JobQueue] = None

def get_job_queue():
    """Dependency to get job queue instance"""
    if not job_queue:
        raise HTTPException(status_code=500, detail="Job queue not initialized")
    return job_queue

@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, queue: JobQueue = Depends(get_job_queue)):
    """Get the status of a specific job"""
    
    try:
        status = queue.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(**status)
        
    except Exception as e:
        logger.error(f"Error getting job status {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving job status")

@router.delete("/{job_id}")
async def cancel_job(job_id: str, queue: JobQueue = Depends(get_job_queue)):
    """Cancel a running or queued job"""
    
    try:
        success = queue.cancel_job(job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or already completed")
        
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Error cancelling job")

@router.get("/")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    queue: JobQueue = Depends(get_job_queue)
):
    """List all jobs with optional status filter"""
    
    try:
        jobs = queue.list_jobs(status_filter=status, limit=limit)
        return {
            "jobs": [JobStatusResponse(**job) for job in jobs],
            "total": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail="Error listing jobs")

@router.delete("/")
async def cleanup_completed_jobs(queue: JobQueue = Depends(get_job_queue)):
    """Clean up completed and failed jobs"""
    
    try:
        cleaned_count = queue.cleanup_completed_jobs()
        return {
            "message": f"Cleaned up {cleaned_count} completed jobs"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up jobs: {e}")
        raise HTTPException(status_code=500, detail="Error cleaning up jobs")

# Function to initialize the job queue (called from main.py)
def initialize_job_queue(queue_instance: JobQueue):
    """Initialize the global job queue instance"""
    global job_queue
    job_queue = queue_instance