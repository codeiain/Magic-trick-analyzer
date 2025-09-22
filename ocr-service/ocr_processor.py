"""
OCR Processing Functions

Core OCR functionality extracted from the main application for microservice architecture.
"""

import os
import logging
import tempfile
import shutil
import requests
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# OCR and PDF processing imports
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# Database imports  
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Redis imports for progress updates
import redis
import json
from rq import get_current_job

logger = logging.getLogger(__name__)

class OCRProcessor:
    """OCR processing functionality with enhanced progress reporting"""
    
    def __init__(self, job_id: Optional[str] = None):
        self.db_engine = None
        self.db_session = None
        self.job_id = job_id
        self.redis_client = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database and Redis connections"""
        try:
            # Initialize database
            db_url = os.getenv("DATABASE_URL", "sqlite:///data/magic_tricks.db")
            self.db_engine = create_engine(db_url)
            Session = sessionmaker(bind=self.db_engine)
            self.db_session = Session()
            
            # Initialize Redis for progress updates
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.Redis.from_url(redis_url)
            
            logger.info("OCR processor initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OCR processor: {e}")
            raise
    
    def _update_progress(self, progress: int, message: str, details: Optional[Dict] = None):
        """Update job progress in Redis using the same format as backend job queue"""
        if not self.job_id or not self.redis_client:
            return
            
        try:
            progress_data = {
                'progress': progress,
                'message': message,
                'updated_at': datetime.utcnow().isoformat(),
                'details': details or {}
            }
            
            # Update the main job metadata that backend queries (job:{job_id})
            job_key = f"job:{self.job_id}"
            update_data = {
                'progress': str(progress),
                'message': message,
                'last_update': datetime.utcnow().isoformat()
            }
            
            # Update status based on progress
            if progress > 0 and progress < 100:
                update_data['status'] = 'started'
            elif progress == 100:
                update_data['status'] = 'completed'
            
            self.redis_client.hset(job_key, mapping=update_data)
            
            # Also store detailed progress in a separate key for debugging
            progress_key = f"ocr_job_progress:{self.job_id}"
            self.redis_client.hset(progress_key, mapping={
                'progress_data': json.dumps(progress_data)
            })
            self.redis_client.expire(progress_key, 3600)  # Expire after 1 hour
            
            logger.info(f"Progress update: {progress}% - {message}")
            
        except Exception as e:
            logger.warning(f"Failed to update progress: {e}")
    
    def extract_text_from_pdf(self, file_path: str, book_id: str) -> str:
        """Extract text from PDF using multiple methods with progress reporting"""
        
        logger.info(f"Starting text extraction for {file_path}")
        self._update_progress(10, "Starting text extraction", {"file_path": file_path})
        
        extracted_text = ""
        
        try:
            # Method 1: Try PyMuPDF first (fastest for text-based PDFs)
            logger.info("Attempting PyMuPDF text extraction...")
            self._update_progress(20, "Analyzing PDF structure", {"method": "PyMuPDF"})
            
            extracted_text = self._extract_with_pymupdf(file_path)
            
            if len(extracted_text.strip()) > 100:  # If we got substantial text
                logger.info(f"PyMuPDF extraction successful: {len(extracted_text)} characters")
                self._update_progress(80, f"Text extraction completed ({len(extracted_text)} characters)", 
                                    {"method": "PyMuPDF", "character_count": len(extracted_text)})
                return extracted_text
            
            # Method 2: Fall back to OCR for image-based PDFs
            logger.info("PyMuPDF yielded minimal text, trying OCR...")
            self._update_progress(30, "PDF appears to be image-based, starting OCR", {"method": "OCR"})
            
            extracted_text = self._extract_with_ocr(file_path)
            
            logger.info(f"OCR extraction completed: {len(extracted_text)} characters")
            self._update_progress(90, f"OCR extraction completed ({len(extracted_text)} characters)", 
                                {"method": "OCR", "character_count": len(extracted_text)})
            return extracted_text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            self._update_progress(0, f"Text extraction failed: {str(e)}", {"error": str(e)})
            return ""
    
    def _extract_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF (for text-based PDFs)"""
        
        text_content = ""
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                if text.strip():  # Only add if page has text
                    text_content += f"\\n\\n--- Page {page_num + 1} ---\\n\\n"
                    text_content += text
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PyMuPDF extraction error: {e}")
        
        return text_content
    
    def _extract_with_ocr(self, file_path: str) -> str:
        """Extract text using OCR (for image-based PDFs) with detailed progress reporting"""
        
        text_content = ""
        temp_dir = None
        
        try:
            # Create temporary directory for images
            temp_dir = tempfile.mkdtemp()
            
            # Convert PDF to images
            logger.info("Converting PDF to images...")
            self._update_progress(35, "Converting PDF pages to images for OCR processing")
            
            images = convert_from_path(
                file_path,
                dpi=200,  # Good balance of quality vs processing time
                output_folder=temp_dir,
                fmt='png'
            )
            
            total_pages = len(images)
            logger.info(f"Converted {total_pages} pages to images")
            self._update_progress(40, f"Converted PDF to {total_pages} images, starting OCR", 
                                {"total_pages": total_pages})
            
            # Process each image with OCR
            for i, image in enumerate(images):
                page_num = i + 1
                progress = 40 + int((page_num / total_pages) * 40)  # Progress from 40% to 80%
                
                logger.info(f"Processing page {page_num}/{total_pages} with OCR...")
                self._update_progress(progress, f"Processing page {page_num} of {total_pages} with OCR", 
                                    {"current_page": page_num, "total_pages": total_pages})
                
                try:
                    # Use Tesseract OCR
                    page_text = pytesseract.image_to_string(
                        image, 
                        lang='eng',
                        config='--psm 6'  # Uniform block of text
                    )
                    
                    if page_text.strip():  # Only add if page has text
                        text_content += f"\\n\\n--- Page {page_num} ---\\n\\n"
                        text_content += page_text
                        logger.info(f"Extracted {len(page_text)} characters from page {page_num}")
                    else:
                        logger.info(f"No text found on page {page_num}")
                        
                except Exception as e:
                    logger.warning(f"OCR failed for page {page_num}: {e}")
                    continue
            
            self._update_progress(80, f"OCR processing completed for all {total_pages} pages", 
                                {"total_pages": total_pages, "total_characters": len(text_content)})
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            self._update_progress(0, f"OCR extraction failed: {str(e)}", {"error": str(e)})
        
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return text_content
    
    def validate_extracted_text(self, text: str) -> Dict[str, Any]:
        """Validate and analyze extracted text quality"""
        
        if not text or not text.strip():
            return {
                'is_valid': False,
                'reason': 'No text extracted',
                'character_count': 0,
                'word_count': 0,
                'confidence': 0.0
            }
        
        # Basic text analysis
        char_count = len(text)
        word_count = len(text.split())
        
        # Simple quality heuristics
        if char_count < 100:
            confidence = 0.2
            reason = 'Very little text extracted'
        elif word_count < 50:
            confidence = 0.4
            reason = 'Limited text content'
        elif char_count < 1000:
            confidence = 0.6
            reason = 'Moderate text extraction'
        else:
            confidence = 0.8
            reason = 'Good text extraction'
        
        return {
            'is_valid': char_count >= 100,
            'reason': reason,
            'character_count': char_count,
            'word_count': word_count,
            'confidence': confidence
        }

def trigger_ai_processing(book_id: str, text_content: str, parent_job_id: str = '') -> Optional[str]:
    """Trigger AI processing by sending a request to the backend job queue"""
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://backend:8000')
        ai_queue_endpoint = f"{backend_url}/api/v1/jobs/ai/queue"
        
        # Prepare the AI processing job data
        ai_job_data = {
            'book_id': book_id,
            'text_content': text_content,
            'parent_job_id': parent_job_id,
            'source': 'ocr_service',
            'queued_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Triggering AI processing for book_id: {book_id}")
        
        # Send request to backend to queue AI job
        response = requests.post(
            ai_queue_endpoint,
            json=ai_job_data,
            timeout=30,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_job_id = result.get('job_id')
            logger.info(f"AI processing job queued successfully: {ai_job_id}")
            return ai_job_id
        else:
            logger.error(f"Failed to queue AI processing job: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error triggering AI processing: {e}")
        logger.error(traceback.format_exc())
        return None

def update_job_status_with_ai_info(ocr_job_id: str, ai_job_id: str, ocr_result: Dict[str, Any]):
    """Update OCR job status to include AI job information"""
    try:
        backend_url = os.getenv('BACKEND_URL', 'http://backend:8000')
        update_endpoint = f"{backend_url}/api/v1/jobs/{ocr_job_id}/ai-info"
        
        update_data = {
            'ai_job_id': ai_job_id,
            'ocr_completed': True,
            'ai_queued': True,
            'ocr_result': {
                'character_count': ocr_result.get('validation', {}).get('character_count', 0),
                'confidence': ocr_result.get('validation', {}).get('confidence', 0),
                'database_saved': ocr_result.get('database_saved', False)
            },
            'updated_at': datetime.utcnow().isoformat()
        }
        
        response = requests.patch(
            update_endpoint,
            json=update_data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"Updated OCR job {ocr_job_id} with AI job info: {ai_job_id}")
        else:
            logger.warning(f"Failed to update OCR job status: {response.status_code} - {response.text}")
            
    except Exception as e:
        logger.error(f"Error updating OCR job status: {e}")

# RQ job function (called by the worker)

def process_pdf(job_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process PDF file for text extraction (RQ job function) with enhanced progress reporting"""
    
    # Get the actual RQ job ID - try multiple approaches
    job_id = None
    
    # First try: get from RQ context
    try:
        import rq
        current_job = rq.get_current_job()
        if current_job:
            job_id = current_job.id
            logger.info(f"Got RQ job ID from get_current_job(): {job_id}")
        else:
            logger.warning("rq.get_current_job() returned None")
    except Exception as e:
        logger.warning(f"Failed to get current RQ job with rq.get_current_job(): {e}")
    
    # Second try: get from get_current_job function we imported
    if not job_id:
        try:
            current_job = get_current_job()
            if current_job:
                job_id = current_job.id
                logger.info(f"Got RQ job ID from get_current_job(): {job_id}")
            else:
                logger.warning("get_current_job() returned None")
        except Exception as e:
            logger.warning(f"Failed to get current RQ job with get_current_job(): {e}")
    
    # Third try: fallback to job_id from data
    if not job_id:
        job_id = job_data.get('job_id') or job_data.get('parent_job_id')
        if job_id:
            logger.info(f"Using fallback job ID from job_data: {job_id}")
        else:
            logger.error("No job ID available from any source!")
    
    logger.info(f"Starting OCR processing job: {job_id}")
    
    try:
        processor = OCRProcessor(job_id=job_id)
        processor._update_progress(5, "Initializing OCR processor")
        
        file_path = job_data['file_path']
        book_id = job_data['book_id']
        book_metadata = job_data.get('book_metadata', {})
        title = book_metadata.get('title', 'Unknown Title')
        
        # Check if file exists
        if not os.path.exists(file_path):
            processor._update_progress(0, f"File not found: {file_path}", {"error": "File not found"})
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Extract text with progress reporting
        logger.info(f"Extracting text from: {file_path}")
        extracted_text = processor.extract_text_from_pdf(file_path, book_id)
        
        # Validate extraction
        processor._update_progress(92, "Validating extracted text quality")
        validation = processor.validate_extracted_text(extracted_text)
        
        # Save results to database
        processor._update_progress(95, "Saving results to database")
        from database import save_book_ocr_results
        database_saved = save_book_ocr_results(
            book_id=book_id,
            title=title,
            file_path=file_path,
            text_content=extracted_text,
            confidence=validation['confidence'],
            character_count=validation['character_count']
        )
        
        result = {
            'status': 'completed',
            'book_id': book_id,
            'file_path': file_path,
            'text_content': extracted_text,
            'validation': validation,
            'database_saved': database_saved,
            'processed_at': datetime.utcnow().isoformat(),
            'next_stage': 'ai_processing'  # Indicate next stage
        }
        
        # Trigger AI processing if we have sufficient text content
        ai_job_id = None
        if validation['character_count'] > 50:  # Only process if we have reasonable text
            processor._update_progress(98, "Triggering AI processing stage")
            try:
                ai_job_id = trigger_ai_processing(book_id, extracted_text, job_data.get('parent_job_id', ''))
                result['ai_job_id'] = ai_job_id
                logger.info(f"AI processing job triggered: {ai_job_id}")
            except Exception as e:
                logger.warning(f"Failed to trigger AI processing: {e}")
                result['ai_processing_error'] = str(e)
        else:
            logger.warning(f"Insufficient text content ({validation['character_count']} chars) - skipping AI processing")
            result['ai_processing_skipped'] = True
            result['ai_skip_reason'] = f"Insufficient text content ({validation['character_count']} chars)"
        
        processor._update_progress(100, "OCR processing completed successfully", 
                                 {"character_count": validation['character_count'], 
                                  "confidence": validation['confidence']})
        
        logger.info(f"OCR processing completed successfully for {title}")
        return result
        
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        # Try to update progress even on failure
        try:
            processor = OCRProcessor(job_id=job_id)
            processor._update_progress(0, f"OCR processing failed: {str(e)}", {"error": str(e)})
        except:
            pass
        raise
        
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        
        # Try to mark book as failed in database
        try:
            from database import get_database_connection, BookModel
            db = get_database_connection()
            db.create_tables()
            session = db.get_session()
            
            existing_book = session.query(BookModel).filter(BookModel.id == job_data.get('book_id')).first()
            if existing_book:
                existing_book.processing_status = 'failed'
                existing_book.updated_at = datetime.utcnow()
                session.commit()
            
            session.close()
            db.close()
        except Exception as db_error:
            logger.error(f"Failed to update database with error status: {db_error}")
        
        return {
            'status': 'failed',
            'book_id': job_data.get('book_id'),
            'error': str(e),
            'processed_at': datetime.utcnow().isoformat()
        }