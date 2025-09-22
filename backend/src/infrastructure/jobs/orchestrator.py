"""
Job Processing Orchestrator

Coordinates the execution of complex jobs across multiple services.
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from src.infrastructure.queue.job_queue import JobQueue

logger = logging.getLogger(__name__)

class JobOrchestrator:
    """Orchestrates complex multi-step jobs"""
    
    def __init__(self, job_queue: JobQueue):
        self.job_queue = job_queue
    
    def create_pdf_processing_pipeline(
        self, 
        file_path: str, 
        book_id: str, 
        original_filename: str, 
        reprocess: bool = False
    ) -> str:
        """
        Create a complete PDF processing pipeline.
        
        This creates a parent job that orchestrates:
        1. OCR processing (extract text from PDF)
        2. AI processing (detect tricks, calculate similarities)
        3. Database updates (save results)
        
        Returns the parent job ID for tracking.
        """
        
        # Create parent job data
        parent_job_data = {
            'type': 'pdf_processing_pipeline',
            'file_path': file_path,
            'book_id': book_id, 
            'original_filename': original_filename,
            'reprocess': reprocess,
            'created_at': datetime.utcnow().isoformat(),
            'steps': ['ocr', 'ai_processing', 'finalization']
        }
        
        # Submit parent job
        parent_job_id = self.job_queue.enqueue_pdf_processing(
            file_path=file_path,
            book_id=book_id,
            original_filename=original_filename,
            reprocess=reprocess
        )
        
        logger.info(f"Created PDF processing pipeline job: {parent_job_id}")
        return parent_job_id

def process_pdf_pipeline(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    RQ job function: Complete PDF processing pipeline
    
    This orchestrates the full processing workflow:
    1. OCR extraction
    2. AI trick detection  
    3. Database persistence
    """
    
    logger.info(f"Starting PDF processing pipeline: {job_data}")
    
    try:
        file_path = job_data['file_path']
        book_id = job_data['book_id']
        original_filename = job_data['original_filename']
        reprocess = job_data.get('reprocess', False)
        
        job_queue = JobQueue()
        
        # Step 1: OCR Processing
        logger.info("Step 1: Starting OCR processing...")
        
        ocr_job_data = {
            'file_path': file_path,
            'book_id': book_id,
            'parent_job_id': job_data.get('job_id', 'unknown')
        }
        
        # Submit OCR job and wait for completion
        ocr_job_id = job_queue.enqueue_ocr_processing(**ocr_job_data)
        
        # Wait for OCR completion (increased timeout for large PDFs)
        ocr_result = job_queue._wait_for_job_completion(ocr_job_id, timeout=3600)  # 60 min timeout
        
        if ocr_result['status'] != 'completed':
            raise Exception(f"OCR processing failed: {ocr_result.get('error', 'Unknown error')}")
        
        extracted_text = ocr_result['text_content']
        
        if not extracted_text or len(extracted_text.strip()) < 100:
            raise Exception("OCR extracted insufficient text content")
        
        logger.info(f"OCR completed successfully: {len(extracted_text)} characters")
        
        # Step 2: AI Processing
        logger.info("Step 2: Starting AI processing...")
        
        ai_job_data = {
            'text_content': extracted_text,
            'book_id': book_id,
            'parent_job_id': job_data.get('job_id', 'unknown')
        }
        
        # Submit AI processing job
        ai_job_id = job_queue.enqueue_ai_processing(**ai_job_data)
        
        # Wait for AI completion
        ai_result = job_queue._wait_for_job_completion(ai_job_id, timeout=900)  # 15 min timeout
        
        if ai_result['status'] != 'completed':
            raise Exception(f"AI processing failed: {ai_result.get('error', 'Unknown error')}")
        
        tricks = ai_result['tricks']
        similarities = ai_result.get('similarities', [])
        
        logger.info(f"AI processing completed: {len(tricks)} tricks detected")
        
        # Step 3: Database Finalization
        logger.info("Step 3: Finalizing database updates...")
        
        # Persist tricks to database
        persisted_count = 0
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from ..database.models import TrickModel, EffectTypeModel
            
            # Connect to database
            db_path = '/app/shared/magic_tricks.db'
            engine = create_engine(f'sqlite:///{db_path}')
            Session = sessionmaker(bind=engine)
            session = Session()
            
            # Get or create effect types mapping
            effect_type_mapping = {}
            existing_types = session.query(EffectTypeModel).all()
            for et in existing_types:
                effect_type_mapping[et.name.lower()] = et.id
            
            # Persist each trick
            for trick_data in tricks:
                try:
                    # Map effect type to ID
                    effect_type_name = trick_data.get('effect_type', 'Other')
                    effect_type_id = effect_type_mapping.get(effect_type_name.lower())
                    
                    if not effect_type_id:
                        # Create new effect type if doesn't exist
                        new_effect_type = EffectTypeModel(name=effect_type_name)
                        session.add(new_effect_type)
                        session.flush()  # Get the ID
                        effect_type_id = new_effect_type.id
                        effect_type_mapping[effect_type_name.lower()] = effect_type_id
                    
                    # Create trick record
                    trick_model = TrickModel(
                        book_id=trick_data['book_id'],
                        effect_type_id=effect_type_id,
                        name=trick_data['name'],
                        description=trick_data['description'],
                        difficulty=trick_data.get('difficulty', 'Unknown'),
                        page_start=trick_data.get('page_start'),
                        confidence=trick_data.get('confidence', 0.7)
                    )
                    
                    session.add(trick_model)
                    persisted_count += 1
                    
                except Exception as trick_error:
                    logger.error(f"Error persisting individual trick: {trick_error}")
                    continue
            
            # Commit all tricks
            session.commit()
            logger.info(f"Successfully persisted {persisted_count}/{len(tricks)} tricks to database")
            
            session.close()
            
        except Exception as persistence_error:
            logger.error(f"Error during database persistence: {persistence_error}")
            if 'session' in locals():
                session.rollback()
                session.close()
        
        result = {
            'status': 'completed',
            'book_id': book_id,
            'file_path': file_path,
            'original_filename': original_filename,
            'ocr_result': {
                'character_count': len(extracted_text),
                'confidence': ocr_result.get('validation', {}).get('confidence', 0.0)
            },
            'ai_result': {
                'tricks_detected': len(tricks),
                'tricks_persisted': persisted_count,
                'similarities_found': len(similarities)
            },
            'processing_steps': ['ocr', 'ai_processing', 'finalization'],
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"PDF processing pipeline completed successfully for book {book_id}")
        return result
        
    except Exception as e:
        logger.error(f"PDF processing pipeline failed: {e}")
        return {
            'status': 'failed',
            'error': str(e),
            'failed_at': datetime.utcnow().isoformat()
        }