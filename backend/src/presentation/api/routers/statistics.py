"""
Statistics API router - handles analytics and statistics endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ....application.use_cases.magic_use_cases import GetBookStatisticsUseCase

logger = logging.getLogger(__name__)


def create_router(statistics_use_case: GetBookStatisticsUseCase) -> APIRouter:
    """Create statistics router with injected dependencies."""
    
    router = APIRouter()
    
    @router.get("/overview", response_model=Dict[str, Any])
    async def get_collection_overview():
        """Get comprehensive statistics about the magic trick collection."""
        try:
            stats = await statistics_use_case.execute()
            return {
                "collection_summary": {
                    "total_books": stats["total_books"],
                    "total_tricks": stats["total_tricks"],
                    "processed_books": stats["processed_books"],
                    "processing_rate": (
                        stats["processed_books"] / stats["total_books"] * 100 
                        if stats["total_books"] > 0 else 0
                    )
                },
                "content_analysis": {
                    "effects_by_type": stats["effect_distribution"],
                    "difficulty_breakdown": stats["difficulty_distribution"],
                    "top_authors": stats["top_authors"]
                },
                "insights": {
                    "most_common_effect": max(
                        stats["effect_distribution"].items(), 
                        key=lambda x: x[1]
                    )[0] if stats["effect_distribution"] else None,
                    "most_common_difficulty": max(
                        stats["difficulty_distribution"].items(),
                        key=lambda x: x[1]
                    )[0] if stats["difficulty_distribution"] else None,
                    "average_tricks_per_book": (
                        stats["total_tricks"] / stats["processed_books"]
                        if stats["processed_books"] > 0 else 0
                    )
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating statistics: {str(e)}")
    
    @router.get("/effects")
    async def get_effect_statistics():
        """Get detailed statistics about effect types."""
        try:
            stats = await statistics_use_case.execute()
            effect_stats = stats["effect_distribution"]
            
            total_tricks = sum(effect_stats.values())
            
            return {
                "total_tricks": total_tricks,
                "effect_types": [
                    {
                        "effect_type": effect_type,
                        "count": count,
                        "percentage": (count / total_tricks * 100) if total_tricks > 0 else 0
                    }
                    for effect_type, count in sorted(
                        effect_stats.items(), 
                        key=lambda x: x[1], 
                        reverse=True
                    )
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating effect statistics: {str(e)}")
    
    @router.get("/difficulties")
    async def get_difficulty_statistics():
        """Get detailed statistics about difficulty levels."""
        try:
            stats = await statistics_use_case.execute()
            difficulty_stats = stats["difficulty_distribution"]
            
            total_tricks = sum(difficulty_stats.values())
            
            return {
                "total_tricks": total_tricks,
                "difficulty_levels": [
                    {
                        "difficulty": difficulty,
                        "count": count,
                        "percentage": (count / total_tricks * 100) if total_tricks > 0 else 0
                    }
                    for difficulty, count in sorted(
                        difficulty_stats.items(),
                        key=lambda x: ["beginner", "intermediate", "advanced", "expert"].index(x[0])
                    )
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating difficulty statistics: {str(e)}")
    
    @router.get("/authors")
    async def get_author_statistics():
        """Get statistics about authors and their contributions."""
        try:
            stats = await statistics_use_case.execute()
            top_authors = stats["top_authors"]
            
            return {
                "total_authors": len(top_authors),
                "top_contributors": [
                    {
                        "author": author,
                        "trick_count": count,
                        "rank": idx + 1
                    }
                    for idx, (author, count) in enumerate(top_authors)
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating author statistics: {str(e)}")
    
    @router.get("/dashboard")
    async def get_dashboard_stats():
        """Get dashboard statistics summary."""
        try:
            stats = await statistics_use_case.execute()
            
            return {
                "total_tricks": stats["total_tricks"],
                "pending_review": 0,  # TODO: Implement when review system is complete
                "books_processed": stats["processed_books"],
                "accuracy": 0.85  # TODO: Calculate based on actual model performance
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating dashboard statistics: {str(e)}")

    @router.get("/active-ocr-jobs")
    async def get_active_ocr_jobs():
        """Get currently active OCR processing jobs for dashboard display."""
        print("=== ACTIVE OCR JOBS ENDPOINT CALLED ===")
        try:
            from src.infrastructure.queue.job_queue import get_job_queue
            
            job_queue = get_job_queue()
            active_jobs = job_queue.get_active_jobs(job_type='ocr')
            
            print(f"=== Found {len(active_jobs)} active jobs ===")
            logger.info(f"Found {len(active_jobs)} active jobs from job_queue.get_active_jobs()")
            
            # Filter for truly active jobs (queued or started)
            ocr_jobs = []
            for job in active_jobs:
                print(f"=== Processing job {job.get('id')}: rq_status={job.get('rq_status')}, status={job.get('status')} ===")
                logger.info(f"Processing job {job.get('id')}: rq_status={job.get('rq_status')}, status={job.get('status')}")
                
                # Get RQ status first for better accuracy
                rq_status = job.get('rq_status', 'unknown')
                metadata_status = job.get('status', 'queued')
                
                # Determine actual status - prioritize RQ status if it's meaningful
                if rq_status in ['queued', 'started', 'finished', 'failed']:
                    actual_status = rq_status
                    # Update our metadata status to match RQ status for consistency
                    if actual_status != metadata_status:
                        try:
                            job_id = job.get('id')
                            if job_id:
                                job_key = f"job:{job_id}"
                                job_queue.redis_conn.hset(job_key, 'status', actual_status)
                                print(f"=== Updated job {job_id} status from {metadata_status} to {actual_status} ===")
                                logger.info(f"Updated job {job_id} status from {metadata_status} to {actual_status}")
                        except Exception as e:
                            logger.warning(f"Failed to sync job status for {job_id}: {e}")
                else:
                    # Fallback to metadata status if RQ status is problematic
                    actual_status = metadata_status
                
                # Only include active jobs
                if actual_status in ['queued', 'started']:
                    # Convert bytes to strings for JSON serialization
                    clean_job = {}
                    for key, value in job.items():
                        if isinstance(value, bytes):
                            try:
                                clean_job[key] = value.decode('utf-8')
                            except UnicodeDecodeError:
                                clean_job[key] = str(value, errors='replace')
                        else:
                            clean_job[key] = value
                    
                    # Determine display message based on status
                    if actual_status == 'started':
                        message = clean_job.get('message', 'Processing...')
                        if message == 'Queued for processing':  # Update stale message
                            message = 'Processing...'
                    else:
                        message = clean_job.get('message', 'Queued for processing')
                    
                    # Add OCR-specific display information
                    ocr_jobs.append({
                        'job_id': clean_job.get('id', 'unknown'),
                        'book_title': clean_job.get('book_title', 'Unknown Book'),
                        'status': actual_status,
                        'created_at': clean_job.get('created_at'),
                        'file_path': clean_job.get('file_path', ''),
                        'progress': clean_job.get('progress', None),
                        'message': message
                    })
            
            return {
                'active_ocr_jobs': ocr_jobs,
                'count': len(ocr_jobs)
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Error getting active OCR jobs: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error getting active OCR jobs: {str(e)}")
    
    @router.delete("/jobs/{job_id}")
    async def cancel_job(job_id: str):
        """Cancel a specific job by ID."""
        try:
            from src.infrastructure.queue.job_queue import get_job_queue
            
            job_queue = get_job_queue()
            
            # Check if job exists
            job_status = job_queue.get_job_status(job_id)
            if not job_status:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Cancel the job
            success = job_queue.cancel_job(job_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Job {job_id} has been cancelled",
                    "job_id": job_id
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to cancel job")
                
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Error cancelling job {job_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error cancelling job: {str(e)}")
    
    @router.delete("/jobs/{job_id}/remove")
    async def remove_job(job_id: str):
        """Completely remove a job from the system."""
        try:
            from src.infrastructure.queue.job_queue import get_job_queue
            
            job_queue = get_job_queue()
            
            # Check if job exists
            job_status = job_queue.get_job_status(job_id)
            if not job_status:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Remove the job
            success = job_queue.remove_job(job_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"Job {job_id} has been removed",
                    "job_id": job_id
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to remove job")
                
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Error removing job {job_id}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error removing job: {str(e)}")
    
    @router.delete("/jobs/clear/{status}")
    async def clear_jobs_by_status(status: str):
        """Clear all jobs with a specific status (completed, failed, cancelled, etc.)."""
        try:
            from src.infrastructure.queue.job_queue import get_job_queue
            
            job_queue = get_job_queue()
            
            # Validate status
            valid_statuses = ['completed', 'failed', 'cancelled', 'finished']
            if status not in valid_statuses:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                )
            
            # Clear jobs with the specified status
            cleared_count = job_queue.clear_jobs_by_status(status)
            
            return {
                "success": True,
                "message": f"Cleared {cleared_count} jobs with status '{status}'",
                "cleared_count": cleared_count,
                "status": status
            }
                
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            logger.error(f"Error clearing jobs with status {status}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error clearing jobs: {str(e)}")
    
    @router.delete("/jobs/clear-completed")
    async def clear_completed_jobs(max_age_hours: int = 24):
        """Clear completed jobs older than specified hours."""
        try:
            from src.infrastructure.queue.job_queue import get_job_queue
            
            job_queue = get_job_queue()
            
            # Clear completed jobs
            cleared_count = job_queue.clear_completed_jobs(max_age_hours)
            
            return {
                "success": True,
                "message": f"Cleared {cleared_count} completed jobs older than {max_age_hours} hours",
                "cleared_count": cleared_count,
                "max_age_hours": max_age_hours
            }
                
        except Exception as e:
            import traceback
            logger.error(f"Error clearing completed jobs: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error clearing completed jobs: {str(e)}")
    
    return router
