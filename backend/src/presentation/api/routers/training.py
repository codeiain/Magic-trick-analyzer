"""
Training API Router

Handles training data review, dataset management, and model retraining.
"""

import logging
from typing import Dict, Any, Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from src.infrastructure.queue.job_queue import JobQueue
from src.presentation.api.routers.jobs import JobStatusResponse

logger = logging.getLogger(__name__)

# Pydantic models for training data
class TrainingReviewRequest(BaseModel):
    trick_id: str
    is_accurate: Optional[bool] = None
    confidence_score: Optional[float] = None
    review_notes: Optional[str] = None
    corrected_name: Optional[str] = None
    corrected_effect_type: Optional[str] = None
    corrected_description: Optional[str] = None
    corrected_difficulty: Optional[str] = None
    use_for_training: bool = True
    quality_score: Optional[float] = None

class TrainingReviewResponse(BaseModel):
    id: str
    trick_id: str
    book_id: str
    is_accurate: Optional[bool]
    confidence_score: Optional[float]
    review_notes: Optional[str]
    corrected_name: Optional[str]
    corrected_effect_type: Optional[str]
    corrected_description: Optional[str]
    corrected_difficulty: Optional[str]
    use_for_training: bool
    quality_score: Optional[float]
    created_at: str
    updated_at: str

class TrickWithReviewResponse(BaseModel):
    # Trick information
    id: str
    book_id: str
    name: str
    effect_type: str
    description: str
    method: Optional[str]
    difficulty: str
    confidence: Optional[float]
    created_at: str
    # Review information (if exists)
    review: Optional[TrainingReviewResponse] = None
    review_status: str  # "pending", "approved", "rejected", "corrected"

class DatasetResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    version: str
    total_tricks: int
    reviewed_tricks: int
    accuracy_rate: Optional[float]
    status: str
    is_active: bool
    model_accuracy: Optional[float]
    created_at: str

class TrainingJobRequest(BaseModel):
    dataset_id: str
    training_parameters: Optional[Dict[str, Any]] = {}
    validation_split: float = 0.2
    epochs: int = 10
    learning_rate: float = 0.001

# Create router
router = APIRouter(tags=["training"])

# Job queue instance (will be injected in main.py)
job_queue: Optional[JobQueue] = None

def get_job_queue():
    """Dependency to get job queue instance"""
    if not job_queue:
        raise HTTPException(status_code=500, detail="Job queue not initialized")
    return job_queue

@router.get("/tricks", response_model=List[TrickWithReviewResponse])
async def get_tricks_for_review(
    book_id: Optional[str] = Query(None),
    review_status: Optional[str] = Query(None),  # pending, approved, rejected, corrected
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get detected tricks with their review status for training data curation"""
    
    try:
        from ....infrastructure.database.models import TrickModel, TrainingReviewModel
        from ....infrastructure.database.database import DatabaseManager
        from ....infrastructure.config import get_config
        
        # Get database connection using backend infrastructure
        config = get_config()
        db_manager = DatabaseManager(config)
        if db_manager.engine is None:
            db_manager.initialize()
        
        session = db_manager.get_session()
        
        # Build query for tricks with optional review info
        query = session.query(TrickModel).outerjoin(
            TrainingReviewModel, TrickModel.id == TrainingReviewModel.trick_id
        )
        
        # Apply filters
        if book_id:
            query = query.filter(TrickModel.book_id == book_id)
            
        if review_status:
            if review_status == "pending":
                query = query.filter(TrainingReviewModel.id.is_(None))
            elif review_status == "approved":
                query = query.filter(TrainingReviewModel.is_accurate == True)
            elif review_status == "rejected":
                query = query.filter(TrainingReviewModel.is_accurate == False)
            elif review_status == "corrected":
                query = query.filter(TrainingReviewModel.corrected_name.isnot(None))
        
        # Apply pagination
        tricks = query.offset(offset).limit(limit).all()
        
        # Convert to response format
        result = []
        for trick in tricks:
            # Get review if exists
            review_query = session.query(TrainingReviewModel).filter(
                TrainingReviewModel.trick_id == trick.id
            ).first()
            
            # Determine review status
            if not review_query:
                status = "pending"
                review_data = None
            elif review_query.corrected_name:
                status = "corrected"
            elif review_query.is_accurate == True:
                status = "approved"
            elif review_query.is_accurate == False:
                status = "rejected"
            else:
                status = "pending"
            
            # Convert review to response format
            if review_query:
                review_data = TrainingReviewResponse(
                    id=review_query.id,
                    trick_id=review_query.trick_id,
                    book_id=review_query.book_id,
                    is_accurate=review_query.is_accurate,
                    confidence_score=review_query.confidence_score,
                    review_notes=review_query.review_notes,
                    corrected_name=review_query.corrected_name,
                    corrected_effect_type=review_query.corrected_effect_type,
                    corrected_description=review_query.corrected_description,
                    corrected_difficulty=review_query.corrected_difficulty,
                    use_for_training=review_query.use_for_training,
                    quality_score=review_query.quality_score,
                    created_at=review_query.created_at.isoformat(),
                    updated_at=review_query.updated_at.isoformat()
                )
            else:
                review_data = None
            
            result.append(TrickWithReviewResponse(
                id=trick.id,
                book_id=trick.book_id,
                name=trick.name,
                effect_type=trick.effect_type,
                description=trick.description,
                method=trick.method,
                difficulty=trick.difficulty,
                confidence=trick.confidence,
                created_at=trick.created_at.isoformat(),
                review=review_data,
                review_status=status
            ))
        
        session.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting tricks for review: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tricks: {str(e)}")

@router.post("/tricks/{trick_id}/review", response_model=TrainingReviewResponse)
async def create_or_update_review(trick_id: str, review_request: TrainingReviewRequest):
    """Create or update a training review for a detected trick"""
    
    try:
        from ....infrastructure.database.models import TrickModel, TrainingReviewModel
        from ....infrastructure.database.database import DatabaseManager
        from ....infrastructure.config import get_config
        from datetime import datetime
        
        # Get database connection using backend infrastructure
        config = get_config()
        db_manager = DatabaseManager(config)
        if db_manager.engine is None:
            db_manager.initialize()
        
        session = db_manager.get_session()
        
        # Verify trick exists
        trick = session.query(TrickModel).filter(TrickModel.id == trick_id).first()
        if not trick:
            session.close()
            raise HTTPException(status_code=404, detail="Trick not found")
        
        # Check if review already exists
        existing_review = session.query(TrainingReviewModel).filter(
            TrainingReviewModel.trick_id == trick_id
        ).first()
        
        if existing_review:
            # Update existing review
            existing_review.is_accurate = review_request.is_accurate
            existing_review.confidence_score = review_request.confidence_score
            existing_review.review_notes = review_request.review_notes
            existing_review.corrected_name = review_request.corrected_name
            existing_review.corrected_effect_type = review_request.corrected_effect_type
            existing_review.corrected_description = review_request.corrected_description
            existing_review.corrected_difficulty = review_request.corrected_difficulty
            existing_review.use_for_training = review_request.use_for_training
            existing_review.quality_score = review_request.quality_score
            existing_review.updated_at = datetime.utcnow()
            
            review = existing_review
        else:
            # Create new review
            review = TrainingReviewModel(
                trick_id=trick_id,
                book_id=trick.book_id,
                is_accurate=review_request.is_accurate,
                confidence_score=review_request.confidence_score,
                review_notes=review_request.review_notes,
                corrected_name=review_request.corrected_name,
                corrected_effect_type=review_request.corrected_effect_type,
                corrected_description=review_request.corrected_description,
                corrected_difficulty=review_request.corrected_difficulty,
                use_for_training=review_request.use_for_training,
                quality_score=review_request.quality_score
            )
            session.add(review)
        
        session.commit()
        
        # Convert to response
        result = TrainingReviewResponse(
            id=review.id,
            trick_id=review.trick_id,
            book_id=review.book_id,
            is_accurate=review.is_accurate,
            confidence_score=review.confidence_score,
            review_notes=review.review_notes,
            corrected_name=review.corrected_name,
            corrected_effect_type=review.corrected_effect_type,
            corrected_description=review.corrected_description,
            corrected_difficulty=review.corrected_difficulty,
            use_for_training=review.use_for_training,
            quality_score=review.quality_score,
            created_at=review.created_at.isoformat(),
            updated_at=review.updated_at.isoformat()
        )
        
        session.close()
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating/updating review for trick {trick_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving review: {str(e)}")

@router.get("/datasets", response_model=List[DatasetResponse])
async def get_training_datasets():
    """Get all training datasets"""
    
    try:
        from ....infrastructure.database.models import TrainingDatasetModel
        from ....infrastructure.database.database import DatabaseManager
        from ....infrastructure.config import get_config
        
        # Get database connection using backend infrastructure
        config = get_config()
        db_manager = DatabaseManager(config)
        if db_manager.engine is None:
            db_manager.initialize()
        
        session = db_manager.get_session()
        
        datasets = session.query(TrainingDatasetModel).order_by(TrainingDatasetModel.created_at.desc()).all()
        
        result = [
            DatasetResponse(
                id=dataset.id,
                name=dataset.name,
                description=dataset.description,
                version=dataset.version,
                total_tricks=dataset.total_tricks,
                reviewed_tricks=dataset.reviewed_tricks,
                accuracy_rate=dataset.accuracy_rate,
                status=dataset.status,
                is_active=dataset.is_active,
                model_accuracy=dataset.model_accuracy,
                created_at=dataset.created_at.isoformat()
            )
            for dataset in datasets
        ]
        
        session.close()
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting training datasets: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving datasets: {str(e)}")

@router.post("/datasets/{dataset_id}/train")
async def start_training_job(dataset_id: str, training_request: TrainingJobRequest, queue: JobQueue = Depends(get_job_queue)):
    """Start a model training job using a prepared dataset"""
    
    try:
        from ....infrastructure.database.models import TrainingDatasetModel
        from ....infrastructure.database.database import DatabaseManager
        from ....infrastructure.config import get_config
        
        # Get database connection using backend infrastructure
        config = get_config()
        db_manager = DatabaseManager(config)
        if db_manager.engine is None:
            db_manager.initialize()
        
        session = db_manager.get_session()
        
        # Verify dataset exists and is ready
        dataset = session.query(TrainingDatasetModel).filter(TrainingDatasetModel.id == dataset_id).first()
        if not dataset:
            session.close()
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        if dataset.status != "ready":
            session.close()
            raise HTTPException(status_code=400, detail=f"Dataset status is '{dataset.status}', must be 'ready' to start training")
        
        # Update dataset status to training
        dataset.status = "training"
        session.commit()
        session.close()
        
        # Queue training job
        training_data = {
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "total_tricks": dataset.total_tricks,
            "reviewed_tricks": dataset.reviewed_tricks,
            "training_parameters": training_request.training_parameters,
            "validation_split": training_request.validation_split,
            "epochs": training_request.epochs,
            "learning_rate": training_request.learning_rate
        }
        
        job_id = queue.enqueue_training_job(training_data)
        
        logger.info(f"Training job queued: {job_id} for dataset: {dataset.name}")
        
        return {
            "job_id": job_id,
            "dataset_id": dataset_id,
            "dataset_name": dataset.name,
            "status": "training_queued",
            "message": f"Training job queued for dataset '{dataset.name}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting training job for dataset {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")

@router.post("/datasets/prepare")
async def prepare_training_dataset(request: dict, job_queue=Depends(get_job_queue)):
    """Prepare a training dataset from reviewed tricks"""
    
    try:
        from ....infrastructure.database.models import TrainingDatasetModel
        from ....infrastructure.database.database import DatabaseManager
        from ....infrastructure.config import get_config
        from datetime import datetime
        import uuid
        
        name = request.get('name')
        description = request.get('description', '')
        min_quality_score = request.get('min_quality_score', 0.5)
        include_corrected = request.get('include_corrected', True)
        
        if not name:
            raise HTTPException(status_code=400, detail="Dataset name is required")
        
        # Get database connection using backend infrastructure
        config = get_config()
        db_manager = DatabaseManager(config)
        if db_manager.engine is None:
            db_manager.initialize()
        
        session = db_manager.get_session()
        
        # Create new dataset record
        dataset_id = str(uuid.uuid4())
        version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        
        dataset = TrainingDatasetModel(
            id=dataset_id,
            name=name,
            description=description,
            version=version,
            status="preparing",
            total_tricks=0,
            reviewed_tricks=0,
            is_active=False
        )
        
        session.add(dataset)
        session.commit()
        session.close()
        
        # Queue dataset preparation job
        job = job_queue.enqueue(
            'ai_processor.prepare_training_dataset',
            dataset_id,
            {
                'name': name,
                'description': description,
                'min_quality_score': min_quality_score,
                'include_corrected': include_corrected
            },
            job_timeout='10m'
        )
        
        return {
            "message": "Dataset preparation started",
            "dataset_id": dataset_id,
            "job_id": job.id,
            "status": "preparing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting dataset preparation: {e}")
        raise HTTPException(status_code=500, detail=f"Error preparing dataset: {str(e)}")

@router.get("/stats")
async def get_training_stats():
    """Get training statistics including total tricks, reviewed tricks, and model info"""
    
    try:
        from ....infrastructure.database.models import TrickModel, TrainingReviewModel, TrainingDatasetModel
        from ....infrastructure.database.database import DatabaseManager
        from ....infrastructure.config import get_config
        from sqlalchemy import func
        
        # Get database connection using backend infrastructure
        config = get_config()
        db_manager = DatabaseManager(config)
        if db_manager.engine is None:
            db_manager.initialize()
        
        session = db_manager.get_session()
        
        # Get total tricks count
        total_tricks = session.query(TrickModel).count()
        
        # Get reviewed tricks count
        reviewed_tricks = session.query(TrainingReviewModel).filter(
            TrainingReviewModel.use_for_training == True
        ).count()
        
        # Get latest active dataset info
        latest_dataset = session.query(TrainingDatasetModel).filter(
            TrainingDatasetModel.is_active == True
        ).order_by(TrainingDatasetModel.created_at.desc()).first()
        
        # Calculate accuracy rate from reviewed data
        accurate_reviews = session.query(TrainingReviewModel).filter(
            TrainingReviewModel.is_accurate == True,
            TrainingReviewModel.use_for_training == True
        ).count()
        
        accuracy_rate = accurate_reviews / reviewed_tricks if reviewed_tricks > 0 else None
        
        # Get last training date
        last_training = None
        model_version = "v1.0.0"
        model_accuracy = None
        
        if latest_dataset:
            last_training = latest_dataset.created_at.isoformat()
            model_version = latest_dataset.version
            model_accuracy = latest_dataset.model_accuracy
        
        session.close()
        
        return {
            "total_tricks": total_tricks,
            "reviewed_tricks": reviewed_tricks,
            "accuracy_rate": accuracy_rate,
            "last_training": last_training,
            "model_version": model_version,
            "model_accuracy": model_accuracy,
            "ready_for_training": reviewed_tricks >= 10  # Minimum threshold
        }
        
    except Exception as e:
        logger.error(f"Error getting training statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving training stats: {str(e)}")

@router.post("/retrain")
async def start_simple_retraining(
    request: dict, 
    queue: JobQueue = Depends(get_job_queue)
):
    """Start a simple retraining process using all available quality data"""
    
    try:
        from datetime import datetime
        import uuid
        
        epochs = request.get('epochs', 10)
        learning_rate = request.get('learning_rate', 0.001)
        
        # Validate parameters
        if epochs < 1 or epochs > 100:
            raise HTTPException(status_code=400, detail="Epochs must be between 1 and 100")
        
        if learning_rate < 0.0001 or learning_rate > 0.1:
            raise HTTPException(status_code=400, detail="Learning rate must be between 0.0001 and 0.1")
        
        # Create dataset info (simple strings only)
        dataset_id = str(uuid.uuid4())
        version = datetime.now().strftime("v%Y%m%d_%H%M%S")
        dataset_name = f"Auto Retrain {version}"
        
        # Create minimal training data with only basic types
        training_data = {
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "epochs": int(epochs),
            "learning_rate": float(learning_rate),
            "auto_prepare": True,
            "min_quality_score": 0.7,
            "include_corrected": True,
            "validation_split": 0.2
        }
        
        # Queue the job
        job_id = queue.enqueue_training_job(training_data)
        
        logger.info(f"Simple retraining job queued: {job_id} for auto-dataset: {dataset_name}")
        
        return {
            "job_id": job_id,
            "dataset_id": dataset_id,
            "dataset_name": dataset_name,
            "status": "training_queued",
            "epochs": epochs,
            "learning_rate": learning_rate,
            "message": "Retraining started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting simple retraining: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting retraining: {str(e)}")

@router.get("/test")
async def test_training_router():
    """Test endpoint to verify training router is working"""
    return {"message": "Training router is working", "timestamp": "2025-09-22"}

@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def get_training_job_status(job_id: str):
    """Get the status of a specific training job"""
    try:
        # Create direct Redis connection to avoid binary data issues
        import redis
        redis_conn = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        
        # Get job metadata first
        job_key = f"job:{job_id}"
        job_data = redis_conn.hgetall(job_key)
        
        if not job_data:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        # Get RQ job status directly from Redis (avoid binary data issues)
        rq_job_key = f"rq:job:{job_id}"
        rq_status = redis_conn.hget(rq_job_key, 'status')
        
        # Use RQ status if available, otherwise fall back to metadata status
        status = rq_status if rq_status else job_data.get('status', 'unknown')
        
        # Determine progress based on status
        progress = 0
        if status in ['failed', 'finished']:
            progress = 100
        elif status == 'started':
            progress = 50
        
        # Create message based on status
        message_map = {
            'queued': 'Training job queued',
            'started': 'Training job in progress',
            'finished': 'Training job completed',
            'failed': 'Training job failed'
        }
        message = message_map.get(status, f'Training job status: {status}')
        
        return JobStatusResponse(
            job_id=job_id,
            status=status,
            progress=progress,
            message=message,
            created_at=job_data.get('created_at'),
            started_at=None,  # Could enhance this later
            finished_at=None,  # Could enhance this later
            result=None       # Could enhance this later
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training job status {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting training job status: {str(e)}")

# Function to initialize the job queue (called from main.py)
def initialize_job_queue(queue_instance: JobQueue):
    """Initialize the global job queue instance"""
    global job_queue
    job_queue = queue_instance